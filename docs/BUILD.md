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

若复用睡前的旧`build-idf6/sdkconfig`，它会优先于新defaults；需先保存旧配置并确认当前选择为`CONFIG_COMPILER_OPTIMIZATION_SIZE=y`、`CONFIG_COMPILER_OPTIMIZATION_ASSERTIONS_SILENT=y`。main仍由CMake最后追加`-O2`。本次Windows已切换并验证；不要把修改本机构建配置当成修改设备NVS，也不要擦除设备来解决构建预算问题。

```sh
python3 firmware/tools/generate_collection_fonts.py \
  --converter <lv_font_conv 1.5.3 的 lv_font_conv.js> \
  --font <SourceHanSansCN-Medium.otf>
```

字体来源：12 px 为 SourceHanSansCN-Medium.otf（adobe-fonts/source-han-sans release 分支 `SubsetOTF/CN/`，SHA256 与 `collection-fonts.json` 一致）；16/18 px 用 google/fonts 提交 `111c44387` 之前的 `ofl/notosanssc/NotoSansSC-Bold.otf`（SHA256 `5ed69f3e…`），它对此前 306 字逐字节重现旧的 16/18 px 输出，与 Windows 记录的 `Noto Sans SC Bold (TrueType).otf` 字形一致。加 `--heading-font` 传入。

云端（无组件注册表）只能测大小：五个托管组件按 `dependencies.lock` 版本从 GitHub 取源码，`IDF_COMPONENT_MANAGER=0`、`EXTRA_COMPONENT_DIRS` 构建，app 大小与 Windows 一致但 SHA 不同，不可刷写。

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


## Grok开机V3与真实旧布局容量

选定素材在`game-art/adventure/art/boot/selection.json`。重现素材用`tools/prepare_boot_video.py --ffmpeg <FFmpeg7.1绝对路径> --output <空候选目录>`；已有输入和原片保留。激活选择后先运行`tools/generate_boot_video.py`、`tools/generate_boot_presentation.py`，再重建主/六游戏C证明并更新索引。两个旧字库用`tools/subset_legacy_fonts.py`从保留原C字形数据复现，不重新栅格化字形。

Windows及macOS/Linux构建脚本均运行`tools/check_adventure_budget.py`：真实旧factory2,031,616B，永久余量352KiB；开机V3+全UI224KiB，旧RLE档160KiB。构建目录的4MB开发布局检查不能替代此检查。只刷冻结app，保留旧6MB资源、NVS、当前成绩和静音设置。


睡前恢复点：直接用`firmware/checkpoints/2026-10-26/`内原样bin和SHA；99是已验收NIGHT操作的回退点，82是当前未最终验收的Grok候选。不要为恢复重新构建，也不要把宿主12fps目标GIF当成设备已达12fps。
