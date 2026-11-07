"""NABO 冒险之旅 · 八款游戏双人对战：两块工牌一起刷写，再把八款游戏各自动对战一局（开发者测试工具）。

用法（ESP-IDF 的 Python 环境，需要 esptool 和 pyserial）：
    python vs_all_games.py COM12 COM11              # 两块：各自备份 → 刷写 → 八款各对战一局
    python vs_all_games.py COM12 COM11 --test-only  # 已经刷好，只测
    python vs_all_games.py COM12 COM11 --flash-only # 只刷不测

跳一跳由 NABO 机器人代打，深潜用自带自动驾驶，横屏六款不按键（各自会在 40 秒内自然结束）。

刷写只写 0x8000 分区表和 0x10000 应用；bootloader 和 0x9000 存档不动。每块刷写前先整片备份 8MB。
测试全程用串口命令驱动（两块都开启自动对跳），不用手按。结果写入 vs-test-<时间>.json 和 .log。
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys
import threading
import time

import serial

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
IMAGES = [(0x8000, "partition-table.bin"), (0x10000, "nabo-adventure.bin")]
SHA256 = {
    "partition-table.bin": "feb7ea496adb63179bf197f87431e6c8ddade47ce0228c1e671ef01421effc0c",
    "nabo-adventure.bin": "91b850dd1654c456d9ccd609e7a09017274bdba5fa395f51d9604a4c26970827",
}
LOBBY, WAIT, INVITED, COUNTDOWN, PLAY, RESULT, NOTICE, PICK = range(8)
WIN, LOSE, DRAW = 1, 2, 3
NOTE_LEFT = 6
LOG = open(os.path.join(HERE, f"vs-all-{STAMP}.log"), "w", encoding="utf-8")


def log(*parts):
    line = " ".join(str(p) for p in parts)
    print(line, flush=True)
    LOG.write(line + "\n")
    LOG.flush()


# ---------- flashing ----------

def esptool(port, *args):
    cmd = [sys.executable, "-m", "esptool", "--chip", "esp32c3", "--port", port, *args]
    log(">>", " ".join(cmd))
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    LOG.write(out.stdout + out.stderr)
    if out.returncode:
        log(out.stdout[-2000:], out.stderr[-2000:])
        raise SystemExit(f"esptool 失败（{port}），已停止")
    return out.stdout


def flash(port):
    backup = os.path.join(HERE, f"backup-{port}-8MB-{STAMP}.bin")
    log(f"\n[{port}] 1/2 备份整片 8MB → {os.path.basename(backup)}")
    info = esptool(port, "--baud", "921600", "read-flash", "0", "0x800000", backup)
    for line in info.splitlines():
        if line.startswith(("Chip type", "MAC")) or "Chip is" in line:
            log("   ", line.strip())
    if os.path.getsize(backup) != 0x800000:
        raise SystemExit(f"[{port}] 备份大小不对，未写入任何东西")
    log(f"[{port}] 2/2 写分区表 + 应用（bootloader 与存档不动）")
    args = ["--baud", "921600", "write-flash", "--flash-mode", "keep", "--flash-freq", "keep", "--flash-size", "keep"]
    for off, name in IMAGES:
        args += [hex(off), os.path.join(HERE, name)]
    out = esptool(port, *args)
    verified = [l.strip() for l in out.splitlines() if "verified" in l or l.startswith("Wrote")]
    for l in verified:
        log("   ", l)
    if sum("verified" in l for l in verified) != len(IMAGES):
        raise SystemExit(f"[{port}] 校验行不足，停止")


# ---------- serial driver ----------

class Badge:
    def __init__(self, port, label):
        self.port, self.label = port, label
        self.ser = serial.Serial(port, 115200, timeout=0.1)
        self.lines, self.lock = [], threading.Lock()
        self.alive = True
        threading.Thread(target=self.reader, daemon=True).start()

    def reader(self):
        buf = b""
        while self.alive:
            try:
                buf += self.ser.read(512)
            except serial.SerialException:
                time.sleep(0.2)
                continue
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                text = raw.decode("utf-8", "replace").strip()
                # @ replies can be glued to boot log text: keep from the first '@'.
                at = text.find("@")
                LOG.write(f"[{self.label}] {text}\n")
                if at >= 0:
                    with self.lock:
                        self.lines.append(text[at:])

    def send(self, cmd):
        LOG.write(f"[{self.label}] >> {cmd}\n")
        self.ser.write((cmd + "\n").encode())

    def wait(self, prefix, timeout=3.0):
        end = time.time() + timeout
        while time.time() < end:
            with self.lock:
                for i, line in enumerate(self.lines):
                    if line.startswith(prefix):
                        del self.lines[: i + 1]
                        return line
            time.sleep(0.03)
        return None

    def cmd(self, cmd, prefix, timeout=3.0):
        with self.lock:
            self.lines.clear()
        self.send(cmd)
        return self.wait(prefix, timeout)

    def vs(self):
        # A reply can reach the PC seconds late (seen 2026-11-07 on the 热气球 result page): retry,
        # and let callers treat None as "not yet" instead of crashing.
        for _ in range(3):
            line = self.cmd(">vs.status", "@vs {")
            if line:
                try:
                    return json.loads(line[4:])
                except ValueError:
                    pass
        return None

    def adv(self):
        line = self.cmd(">adv.status", "@adv {")
        return json.loads(line[5:]) if line else None

    def key(self, name):
        self.send(">adv.key=" + name)
        time.sleep(0.25)

    def close(self):
        self.alive = False
        time.sleep(0.2)
        self.ser.close()


def until(fn, timeout, step=0.5):
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(step)
    return None


def open_room(b):
    for _ in range(3):
        st = b.adv()
        if st and st.get("page") == 1 and st.get("owner") == 0:
            if b.cmd(">vs.open", "@vs open"):
                return True
        elif st and st.get("page") == 0:
            b.key("ok")   # cover -> map
            time.sleep(0.8)
        time.sleep(0.5)
    return False


GAMES = {1: "跳一跳", 2: "深潜", 3: "小火车", 4: "萤火虫", 5: "登山", 6: "滑雪", 7: "热气球", 8: "火箭登月"}


def to_map(b):
    for _ in range(6):
        st = b.adv()
        if not st:
            time.sleep(0.5)
            continue
        if st["page"] == 1 and st["owner"] == 0:
            return True
        if st["owner"] != 0:
            b.key("double_up")          # leave the room (result page)
        elif st["page"] == 0:
            b.key("ok")                 # cover -> map
        elif st["page"] == 2:
            for _ in range((3 - st.get("kiosk", 2)) % 4):
                b.key("down")
            b.key("ok")                 # kiosk -> 返回地图
        else:
            b.key("double_up")
        time.sleep(1.0)
    return False


def one_game(A, B, game):
    row = {"game": game, "name": GAMES[game]}
    for b in (A, B):
        if not to_map(b):
            row["error"] = f"{b.label} 回不到地图"
            return row
        if not b.cmd(f">vs.open={game}", "@vs open"):
            row["error"] = f"{b.label} 打不开对战"
            return row
        b.cmd(">vs.auto=1", "@vs auto")
    found = until(lambda: (lambda x, y: x and y and y["me"] in x["peers"] and x["me"] in y["peers"] and (x, y))(A.vs(), B.vs()), 15)
    if not found:
        row["error"] = "15 秒内没互相发现"
        return row
    sa, sb = found
    for _ in range(sa["peers"].index(sb["me"]) + 1):
        A.key("down")
    A.key("ok")
    if not until(lambda: (B.vs() or {}).get("page") == INVITED, 6):
        row["error"] = "B 没收到邀请"
        return row
    B.key("ok")
    playing = until(lambda: (lambda x, y: x and y and x["page"] == PLAY and y["page"] == PLAY and (x, y))(A.vs(), B.vs()), 10)
    if not playing:
        row["error"] = "没开始"
        return row
    row["same"] = playing[0]["seed"] == playing[1]["seed"] and playing[0]["game"] == playing[1]["game"] == game
    low = [10 ** 9, 10 ** 9, 10 ** 9, 10 ** 9]
    t0 = time.time()
    while time.time() - t0 < 300:
        a, b = A.vs(), B.vs()
        if a and b:
            if a["page"] == PLAY:
                low[0] = min(low[0], a["heap"]); low[1] = min(low[1], a["largest"])
            if b["page"] == PLAY:
                low[2] = min(low[2], b["heap"]); low[3] = min(low[3], b["largest"])
            if a["page"] == RESULT and b["page"] == RESULT:
                break
            if a["page"] == NOTICE or b["page"] == NOTICE:
                row["error"] = f"中途提示 note A{a['note']} B{b['note']}"
                return row
        time.sleep(1)
    else:
        row["error"] = "300 秒内没出结果"
        return row
    time.sleep(1.2)
    a, b = until(A.vs, 10), until(B.vs, 10)
    if not (a and b):
        row["error"] = "结算后读不到状态"
        return row
    mirror = (a["outcome"], b["outcome"]) in ((WIN, LOSE), (LOSE, WIN), (DRAW, DRAW))
    scores = a["mine"][0] == b["theirs"][0] and b["mine"][0] == a["theirs"][0]
    row.update(ok=bool(mirror and scores and row["same"]), A=[a["mine"][0], a["outcome"]], B=[b["mine"][0], b["outcome"]],
               seconds=round(time.time() - t0), play_heap_low={"A": low[:2], "B": low[2:]},
               drop=[a["drop"], b["drop"]], fail=[a["fail"], b["fail"]])
    for bdg in (A, B):
        bdg.key("double_up")
    time.sleep(1.5)
    sa, sb = A.adv(), B.adv()
    row["kiosk_heap"] = [sa and sa["heap"], sb and sb["heap"]]
    return row


def run_test(port_a, port_b):
    A, B = Badge(port_a, "A"), Badge(port_b, "B")
    result = {"ports": [port_a, port_b], "games": []}
    names = {1: "赢", 2: "输", 3: "平"}
    try:
        log("\n等两块开机（约 10 秒）…")
        time.sleep(10)
        for b in (A, B):
            st = until(b.adv, 15, 1)
            if not st:
                raise SystemExit(f"[{b.label}] 串口没有回应")
            result[f"boot_{b.label}"] = {k: st.get(k) for k in ("heap", "largest")}
        for game in range(1, 9):
            log(f"\n=== {game} {GAMES[game]} ===")
            row = one_game(A, B, game)
            result["games"].append(row)
            if "error" in row:
                log("  出错：", row["error"])
                for b in (A, B):
                    b.key("double_up"); time.sleep(0.5)
                continue
            log(f"  A {row['A'][0]} 分（{names.get(row['A'][1])}） vs B {row['B'][0]} 分（{names.get(row['B'][1])}）",
                "一致" if row["ok"] else "不一致！", f"用时 {row['seconds']} 秒",
                f"对战中最低 heap/最大块 A {row['play_heap_low']['A']} B {row['play_heap_low']['B']}",
                f"回护照亭 heap {row['kiosk_heap']}")
        ok = sum(1 for r in result["games"] if r.get("ok"))
        result["summary"] = f"{ok}/8 一致"
        kh = [r["kiosk_heap"][0] for r in result["games"] if r.get("kiosk_heap") and r["kiosk_heap"][0]]
        result["kiosk_heap_drift_A"] = (kh[-1] - kh[0]) if len(kh) > 1 else None
    finally:
        A.close(); B.close()
        path = os.path.join(HERE, f"vs-all-{STAMP}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log("\n结果文件：", path)
        log(json.dumps({k: result.get(k) for k in ("summary", "kiosk_heap_drift_A")}, ensure_ascii=False))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        raise SystemExit(__doc__)
    for name, digest in SHA256.items():
        with open(os.path.join(HERE, name), "rb") as f:
            if hashlib.sha256(f.read()).hexdigest() != digest:
                raise SystemExit(f"{name} 校验失败，文件可能不完整")
    if "--test-only" not in flags:
        for port in args:
            flash(port)
    if "--flash-only" in flags or len(args) < 2:
        log("\n刷写完成。护照亭 → 双人对战 → 选游戏。")
        return
    run_test(args[0], args[1])


if __name__ == "__main__":
    main()
