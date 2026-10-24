# 构建

ESP-IDF 6.0.2，目标 ESP32-C3，8 MB Flash；LVGL 9.5.0 等依赖由 `firmware/dependencies.lock` 锁定（首次构建会联网下载到 `firmware/managed_components/`）。

| 系统 | 命令 |
|---|---|
| macOS / Linux | `./build.sh ~/esp-idf-v6.0.2` |
| Windows | `./build.ps1`（默认 `C:\Espressif\esp-idf-v6.0.2`，可传 `-IdfPath`） |

两者都会：构建 → `merge-bin` 生成 `firmware/build-idf6/nabo-adventure-merged.bin` → `firmware/tools/verify_firmware.py` 检查镜像布局。

输出：

| 文件 | 用途 |
|---|---|
| `firmware/build-idf6/nabo-adventure.bin` | 应用，升级时只写 `0x10000` |
| `firmware/build-idf6/nabo-adventure-merged.bin` | 完整镜像，从 `0x0` 写入（会覆盖 NVS） |

源码里已经包含生成好的字库和半身像，构建不需要重跑生成器。新增中文界面文字后：

```sh
python3 firmware/tools/generate_collection_fonts.py \
  --converter <lv_font_conv 1.5.3 的 lv_font_conv.js> \
  --font <SourceHanSansCN-Medium.otf>
```

宿主测试：`python3 -m pip install -r requirements-dev.txt`，然后 `python3 tools/run_tests.py`（需要 C 编译器：macOS 自带 cc，Windows 用 MinGW gcc）。

在 macOS 外接卷（非 APFS）上构建会生成 `._*` 文件，弄坏 ESP-IDF 组件哈希：放在 APFS 磁盘上构建，或者先 `find . -name '._*' -delete`。
