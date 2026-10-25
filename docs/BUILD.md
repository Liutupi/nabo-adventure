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

Windows 上建议显式指定同一套宿主工具链，避免 PATH 中的其他工具改变 gcc 子进程搜索路径：

```powershell
$env:Path = '<w64devkit>\bin;' + $env:Path
$env:CC = '<w64devkit>\bin\gcc.exe'
$env:CXX = '<w64devkit>\bin\g++.exe'
python tools/run_tests.py
```

宿主 Python 需装 Pillow；ESP-IDF 虚拟环境用于构建、esptool 和串口，不必同时承担美术和宿主渲染依赖。

设备自动冒烟在保护式 app 升级、回读通过后执行：

```powershell
python tools/smoke_adventure.py --port <COM口> --app <已回读app.bin> --sha256 <小写SHA256> --receipt <private内刷写凭据.json>
```

它检查测试模式、外壳页面、跳一跳/深潜各十轮进出及内存，原始日志与详细状态只保存在 `private/smoke/`。结束后保持测试模式，应重启再开始正常游玩；实体按键、声音和深睡唤醒仍需实际检查。

在 macOS 外接卷（非 APFS）上构建会生成 `._*` 文件，弄坏 ESP-IDF 组件哈希：放在 APFS 磁盘上构建，或者先 `find . -name '._*' -delete`。
