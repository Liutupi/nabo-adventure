"""Switch an AI Passport to the 4 MB-factory layout and install an app, keeping saves.

For badges still on a legacy 2 MB-factory layout (app-only upgrades from v0.1.0), whose factory
partition is too small for the wireless v0.3.0 app. Writes exactly two regions: the partition
table at 0x8000 and the app at 0x10000. The bootloader (0x0) and NVS (0x9000, settings/scores)
are never written; nothing is erased beyond the sectors esptool rewrites for those two images.
A full 8 MB backup is read first and checked for size before anything is written; restore it
with `esptool write-flash 0x0 <backup>` if needed. The old assets area is overwritten by the
larger app (other NABO firmwares need a full reflash anyway).

Use the ESP-IDF Python environment (esptool 5.x, pyserial):
    python tools/install_keep_saves.py --port COM12 --app nabo-adventure-v0.3.0-app.bin \\
        --sha256 <app sha256> --partition-table partition-table.bin
"""
import argparse
import datetime
import hashlib
import os
import subprocess
import sys

PT_SHA = "feb7ea496adb63179bf197f87431e6c8ddade47ce0228c1e671ef01421effc0c"   # factory 0x10000+0x3f0000
FLASH = 0x800000
APP_MAX = 0x3F0000


def esptool(port, *args):
    cmd = [sys.executable, "-m", "esptool", "--chip", "esp32c3", "--port", port, *args]
    print(">>", " ".join(cmd), flush=True)
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode:
        print(out.stdout[-3000:], out.stderr[-3000:])
        raise SystemExit("esptool failed; stopped")
    return out.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True)
    ap.add_argument("--app", required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--partition-table", required=True)
    ap.add_argument("--expected-mac", help="lower-case aa:bb:cc:dd:ee:ff; refuse any other badge")
    ap.add_argument("--backup-dir", default="private/device")
    a = ap.parse_args()
    app = open(a.app, "rb").read()
    pt = open(a.partition_table, "rb").read()
    if hashlib.sha256(app).hexdigest() != a.sha256.lower():
        raise SystemExit("app SHA256 mismatch; stopped")
    if hashlib.sha256(pt).hexdigest() != PT_SHA:
        raise SystemExit("unexpected partition table; stopped")
    if len(app) > APP_MAX:
        raise SystemExit("app larger than the factory partition; stopped")
    info = esptool(a.port, "flash-id")
    mac = next((l.split()[-1].lower() for l in info.splitlines() if l.strip().startswith("MAC")), "")
    if "ESP32-C3" not in info or "8MB" not in info:
        raise SystemExit("not an ESP32-C3 with 8 MB flash; stopped")
    if a.expected_mac and mac != a.expected_mac.lower():
        raise SystemExit(f"MAC {mac} != expected {a.expected_mac}; stopped")
    os.makedirs(a.backup_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(a.backup_dir, f"backup-{mac.replace(':', '')}-{stamp}.bin")
    print(f"1/2 full 8 MB backup -> {backup}")
    esptool(a.port, "--baud", "921600", "read-flash", "0", hex(FLASH), backup)
    if os.path.getsize(backup) != FLASH:
        raise SystemExit("backup size wrong; nothing written")
    print("2/2 partition table 0x8000 + app 0x10000 (bootloader and NVS untouched)")
    out = esptool(a.port, "--baud", "921600", "write-flash", "--flash-mode", "keep", "--flash-freq", "keep",
                  "--flash-size", "keep", "0x8000", a.partition_table, "0x10000", a.app)
    verified = sum("verified" in l for l in out.splitlines())
    if verified != 2:
        raise SystemExit(f"only {verified}/2 images verified; restore the backup if the badge does not boot")
    print("Done: both images verified. Saves in NVS were not touched. Keep the backup private.")


if __name__ == "__main__":
    main()
