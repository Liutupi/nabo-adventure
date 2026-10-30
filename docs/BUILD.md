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

Windows及macOS/Linux构建脚本均运行`tools/check_adventure_budget.py`：真实旧factory2,031,616B。2026-10-26用户已批准替代旧352KiB规则：SKY/CLIMB各72KiB净新增额度、64KiB长期修复额；配置见`firmware/tools/adventure-budget.json`，两款未接V2前均为reserved。开机V3+全UI224KiB，旧RLE档160KiB。构建目录的4MB开发布局检查不能替代此检查。只刷冻结app，保留旧6MB资源、NVS、当前成绩和静音设置。


睡前恢复点：直接用`firmware/checkpoints/2026-10-26/`内原样bin和SHA；99是已验收NIGHT操作的回退点，82是当前未最终验收的Grok候选。不要为恢复重新构建，也不要把宿主12fps目标GIF当成设备已达12fps。

## 2026-10-30 V2 隔离构建

本轮在 macOS 的 APFS 副本工作，已有 `build-idf6/sdkconfig` 仍是较早的编译配置，本候选未沿用该配置；新候选用 `build-v2-20261030` 和同目录新 `sdkconfig` 从 tracked defaults 构建。已核对 `CONFIG_COMPILER_OPTIMIZATION_SIZE=y`、`CONFIG_COMPILER_OPTIMIZATION_ASSERTIONS_SILENT=y`，main 保持 `-O2`。按原流程运行 `idf.py build`、`merge-bin`、`verify_firmware.py` 和 `check_adventure_budget.py`，路径参数指向新构建目录。交接中 Windows `build.ps1` 的本地重建步骤，在本机以同版本 IDF 的 build/merge/verify/budget 命令等价执行；不使用旧云端二进制。当前 macOS 候选 e9fe81f6 已按用户明确要求刷入；307项宿主、预算/布局、应用读回及八款串口回归通过。实际工牌多一个record分区，按完整实测边界做app-only写入；没有使用会强制全片备份的旧安装器模式，也没有冒充全保护区回读。最终静音/NVS与正常模式已核对，实体手感和睡醒仍待用户。

共用横屏标题另有 `collection_font_26.c`，只包含六款标题、暂停字形和 ASCII；12/16/18 px 字库继续覆盖所有 UI。`generate_collection_fonts.py` 一并复现四份字库。气球三张机械件由 `python3 tools/prepare_sky_v2.py` 原色最近邻缩至 2/3，NABO 帧不变。完整素材打包命令仍见 `tools/ADVENTURE_ASSETS.md`；跨平台 manifest 路径支持 Windows 分隔符并维持范围检查。更新美术索引时可用 `catalog_adventure_art.py --game-proof-root <新逐款证明目录>` 保留旧冻结证据。


## v0.2.0 发布包复现

应用必须逐字节等于已上机e9fe81f6，不重编译替换。准备三镜像目录：应用取已校验冻结输出，bootloader/partition-table从v0.1.0公开ZIP复用，flash_args沿用0x0/0x8000/0x10000；合并并运行verify_firmware。打包器核对固定应用SHA、八款设备验证和旧组件SHA，只加入白名单说明/工具/许可，不读取设备。

```sh
python3 tools/package_release.py --build <三镜像目录> --output release-v0.2.0 --idf <ESP-IDF-6.0.2目录> --source-commit 1309753751a71d8be571fc298fa0bf3fb3c52a95
python3 tools/verify_release.py release-v0.2.0
```

发布来源、7个资产校验和与公开下载回执见 `docs/releases/v0.2.0/` 和 `validation/release-v0.2.0.json`。源提交与v0.2.0标签一致；发布之后的交接/回执提交不改固件运行时输入。
