"""旁听两块工牌的真人对战：记录每块的对战事件（翻页、谁掉下去、胜负），不按任何键。

用法：python vs_watch.py COM12 COM11
两人照常手动对战几局，结束后在命令行按 Ctrl+C。结果写到 vs-watch-<时间>.log 和 .json。
"""
import datetime
import json
import os
import sys
import threading
import time

import serial

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
PAGES = ["大厅", "等待", "被邀请", "倒数", "对战中", "结算", "提示"]
OUT = {0: "-", 1: "赢", 2: "输", 3: "平"}
events = []
lock = threading.Lock()
log = open(os.path.join(HERE, f"vs-watch-{STAMP}.log"), "w", encoding="utf-8")
t0 = time.time()


def watch(port, label, stop):
    ser = serial.Serial(port, 115200, timeout=0.1)
    buf, last_poll = b"", 0.0
    while not stop.is_set():
        if time.time() - last_poll > 2:
            ser.write(b">vs.status\n")
            last_poll = time.time()
        buf += ser.read(512)
        while b"\n" in buf:
            raw, buf = buf.split(b"\n", 1)
            text = raw.decode("utf-8", "replace").strip()
            t = round(time.time() - t0, 2)
            with lock:
                log.write(f"{t:8.2f} [{label}] {text}\n")
                log.flush()
            at = text.find("@vsev ")
            if at >= 0:
                try:
                    e = json.loads(text[at + 6:])
                except ValueError:
                    continue
                e.update(t=t, badge=label)
                with lock:
                    events.append(e)
                print(f"{t:8.2f}s  {label}  {PAGES[e['page']] if e['page'] < len(PAGES) else e['page']:<4}"
                      f"  我 {e['mine'][0]:>3}{'(掉)' if e['mine'][1] else '    '}"
                      f"  对手 {e['theirs'][0]:>3}{'(掉)' if e['theirs'][1] else '    '}"
                      f"  结果 {OUT.get(e['outcome'], e['outcome'])}", flush=True)
    ser.close()


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    stop = threading.Event()
    threads = [threading.Thread(target=watch, args=(p, l, stop), daemon=True) for p, l in zip(sys.argv[1:], "AB")]
    for th in threads:
        th.start()
    print("开始旁听。两人进入双人对战照常玩，结束后按 Ctrl+C。")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    stop.set()
    for th in threads:
        th.join(timeout=2)
    path = os.path.join(HERE, f"vs-watch-{STAMP}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=1)
    print("\n已保存：", path)


if __name__ == "__main__":
    main()
