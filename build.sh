#!/usr/bin/env bash
# Build, merge and verify the firmware on macOS / Linux. Usage: ./build.sh [path-to-esp-idf-v6.0.2]
set -euo pipefail
IDF=${1:-${IDF_PATH:-$HOME/esp-idf-v6.0.2}}
# shellcheck disable=SC1091
source "$IDF/export.sh" >/dev/null
cd "$(dirname "$0")/firmware"
idf.py -B build-idf6 -DSDKCONFIG=build-idf6/sdkconfig -DIDF_TARGET=esp32c3 build
idf.py -B build-idf6 merge-bin -o nabo-adventure-merged.bin
python tools/verify_firmware.py build-idf6
python ../tools/check_adventure_budget.py build-idf6
