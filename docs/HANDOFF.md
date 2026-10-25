# 交接本

更新：2026-10-25 · 固件 v0.1.0（骨架）· 提交见 `git log`

**Mac 精灵管线历史增量见第 9 节。** Windows 接手已同步最新界面设计要求，并将构建配置版本统一为 `0.1.0`；设备验证及美术各轮进展将在后续章节记录。镜像仍须以 SHA256 识别。

## 1. 现在是什么状态

《NABO 的冒险之旅》合集的**骨架、11轮美术和共用界面已交付，正在逐款开发正式游戏**。最新程序状态见 `DEVELOPMENT_PROGRESS.md`，镜像和实测边界见 `VALIDATION.md`。

- 合集外壳完整：封面 → 竖向地图（9 个站点）→ 护照亭 / 护照 / 设置 → 盖章仪式 → 统一的游戏流程（标题、倒数、进行中、暂停、结束、结算）。
- 跳一跳、深潜是现成游戏，从地图进出，最佳成绩回传给外壳算印章。
- 小火车POST正式规则/美术已接入，173项宿主门禁通过。首版5d0f6d…真机自动送信/补给/结算及10轮进出通过，但约20fps未达目标；最新透明外缘/背景重复运算优化候选0cd108…已冻结、尚未刷写。萤火虫、登山、滑雪、热气球、太空仍跑**占位游戏**，不能算正式可玩完成。
- 共用页面已接入选定旅行服、地图/印章和复古护照美术。用户已对557607…镜像的加粗字体、新欢迎演出和30秒睡醒确认通过，原样冻结的已验收bin保留；新增玩法候选仍须各自实测。

## 2. 先读这些

| 文件 | 内容 |
|---|---|
| `AGENTS.md` | 维护约定（必须遵守） |
| `game-art/adventure/DESIGN.md` | 已实现的规则：站点、按键、印章、一局流程、游戏接口、存档、串口命令 |
| `game-art/adventure/GAMES.md` | 6 个新游戏的玩法和起始参数 |
| `game-art/adventure/UI_DESIGN.md` | 配色、字体、每个画面（截图由生产代码渲染）；第 7 节是界面视觉设计要求 |
| `game-art/adventure/ART_BRIEF.md` / `CODEX_PROMPTS.md` | 美术规格 / 按轮次的提示词 |
| `game-art/adventure/BUDGET.md` | Flash、内存预算 |
| nabo-passport-game skill | NABO 小游戏的通用流程（M0–M4、发布） |

## 3. 文件职责

| 文件 | 职责 |
|---|---|
| `game-art/adventure/prototype/adv_core.js` | **规则的标准答案**：外壳模型、占位游戏、设置子模型、mulberry32 |
| `game-art/adventure/prototype/index.html` + `adv_draw.js` | 浏览器原型（键盘 ↑ ↓ Enter；画面按固件版式画） |
| `tests/adv_golden/record_golden.js` | 用原型录对拍轨迹（`node tests/adv_golden/record_golden.js`） |
| `firmware/main/adv_model.c/.h` | 外壳状态机（无屏幕、声音、RTOS 依赖） |
| `firmware/main/adv_game.h` | 外壳 ↔ 游戏的接口 |
| `firmware/main/adv_stations.c/.h` | 9 个站点：名字、世界、门槛、占位标记、颜色、路径顺序 |
| `firmware/main/adv_demo.c/.h` | 占位游戏 |
| `firmware/main/adv_rng.h` | mulberry32（与原型一致） |
| `firmware/main/adv_gfx.c/.h`、`adv_shapes.c`、`adv_text.c/.h` | 直绘渲染器：显示列表 + 脏矩形 + 8 行条带（从牌桌渲染器分出来，去掉了牌、骰子、杯子） |
| `firmware/main/adv_sprite.c/.h` | Flash 精灵逐行 RLE 解码、关键帧 + 最多 7 个差分帧，供 `AG_SPRITE` 使用 |
| `tools/generate_adv_sprites.py` / `docs/SPRITES.md` | 最终尺寸 PNG → 共享 64 色 → 行 RLE → C 数组；逐帧核对和接入说明 |
| `firmware/main/adv_ui.c` | 面板输出、通用部件、封面、护照亭、设置、状态、页面分发 |
| `firmware/main/adv_ui_map.c` | 地图、护照、盖章 |
| `firmware/main/adv_ui_session.c` | 游戏标题、资源条、倒数、暂停、结束、结算、占位游戏画面 |
| `firmware/main/adv_ui_jump.c` | 跳一跳画面（原样搬自《游戏特辑》） |
| `firmware/main/adv_sound.c/.h` | 提示音与POST持续鸣笛合成（三角波，无采样） |
| `firmware/main/adv_post.c/.h`、`adv_ui_post.c` | POST纯整数60Hz规则与正式原尺寸美术组合 |
| `game-art/adventure/prototype/adv_post.js`、`adv_post_draw.js`、`post.html` | POST标准规则、浏览器画面和可玩调参入口 |
| `tests/post_golden/`、`tests/test_adv_post.py` | POST 30,000步JS/C逐步对拍、规则边界和变异检查 |
| `tools/smoke_post.py` | 测试模式串口实玩、进出压力检查，确认恢复正常模式后才通过 |
| `firmware/main/adv_main.c` | 入口：按键队列、60 Hz 步进、NVS、音频、旧游戏进出、串口诊断、深睡 |
| `firmware/main/collection_model.c` | 设置 / 状态子模型（沿用） |
| `firmware/main/nabo_dive*`、`nabo_jump*` | 深潜、跳一跳（未改） |
| `firmware/tools/generate_collection_fonts.py` | 从 `adv_*.c` 收集中文，生成 12/16/18 号字库 |
| `firmware/tools/verify_firmware.py` | 检查合并镜像的布局 |
| `firmware/tools/flash_candidate.py` | 只写 app 的保护式刷写（核对身份、备份、校验） |
| `tests/test_adv_model.py` | 4 条对拍轨迹（约 1.4 万步）+ 7 个故意改坏规则的变异体 |
| `tests/test_adv_renderer.py` | 渲染每个画面到 `docs/images/ui/`；每次输入后增量帧 = 整屏重画；无溢出 |
| `game-art/dive/` | 深潜的美术、骨骼、渲染脚本、网页原型（原样保留） |
| `docs/nabo-games-v1.0.0/` | 底座《游戏特辑》v1.0.0 的发布、验证和来源记录（历史） |

## 4. 怎么跑

```sh
python3 -m pip install -r requirements-dev.txt    # Pillow
python3 tools/run_tests.py                         # 宿主测试，不碰设备（macOS 用 cc，Windows 用 gcc）
node tests/adv_golden/record_golden.js             # 改了 adv_core.js 后重录
./build.sh ~/esp-idf-v6.0.2                        # macOS / Linux；Windows 用 build.ps1
```

浏览器原型：在仓库根目录起一个静态服务器（`python3 -m http.server 8768`），打开 `http://localhost:8768/game-art/adventure/prototype/`。

刷写（只写 app，保留 NVS 和其他分区）：

```sh
python firmware/tools/flash_candidate.py --app firmware/build-idf6/nabo-adventure.bin --sha256 <SHA256> --mode inspect
python firmware/tools/flash_candidate.py --app firmware/build-idf6/nabo-adventure.bin --sha256 <SHA256> --mode upgrade --expected-mac <工牌 MAC>
```

**先 inspect 再 upgrade**，并用 `--expected-mac` 锁定设备：同一个 USB 口上可能接着别的板子（用户的 Tab5 就出现过）。

## 5. 验证状态（v0.1.0）

以下保留初次交接的历史状态，Windows 实测增量与绑定镜像见第 10 节。

| 项目 | 状态 |
|---|---|
| 宿主测试 64 项 | ✅ 全过（macOS，cc） |
| ESP-IDF 6.0.2 构建、合并镜像、布局检查 | ✅ app 1,158,976 B，SHA256 `ba99d31e…090e7`，分区剩 72% |
| 浏览器原型 | ✅ 能加载、按键响应、无控制台错误 |
| **真机** | ❌ **没刷过**。按键手感、声音、深潜和跳一跳进出、10 轮进出的内存、深睡唤醒都没验证 |

## 6. 待办（按顺序）

| # | 任务 | 完成标准 |
|---|---|---|
| 1 | **基线真机冒烟已完成**，后续镜像另测 | Windows 候选 app `71cc1f6b…fdb32` 已保护式升级；页面、各十轮进出、三键、声音、临时 30 秒休眠和上键唤醒已查。后续新开机音画及 UI 镜像不得沿用此结果，见第 10 节 |
| 2 | 全部11轮美术技术交付完成；字体/欢迎V2a待新候选真机 | 用户已选旅行服v2①及界面①复古护照；六游戏独立C包、完整索引与跨人审阅已补齐。新版字体/欢迎经160项门禁，设备尚未升级，详见ART_PROGRESS/ART_DELIVERY_AUDIT |
| 3 | 精灵和界面管线已接正式共用包 | 行 RLE、runtime manifest/锚点/fps、32 色共享 UI、六套九宫格、大数字、真实 C 解码对拍与生产页面渲染通过；新候选设备验收见第 10 节 |
| 4 | 小火车 POST（M0–M4） | 原型里做出玩法、调参（`GAMES.md` 第 1 节）→ 录对拍 → `adv_post.c` + `draw` → H 横向模式 → 站点 3 `placeholder = false` |
| 5 | 地图硬件竖向滚动 | 走一站时镜头平滑滚动，60 fps（参考深潜 `nabo_dive_render.c`） |
| 6 | 服装系统 | 银章解锁第二款；标题页可切换；存 `adv_skin_<id>` |
| 7 | 其余 5 个游戏 | 萤火虫 → 登山 → 滑雪 → 热气球 → 太空，同第 4 项流程 |
| 8 | 结局 | 8 枚金章后太空站的“回家”（`GAMES.md` 第 7 节） |
| 9 | 可选：压缩跳一跳素材 | 见 `BUDGET.md` 第 3 节 |

## 7. 注意事项

- **不要把渲染代码放进 IRAM**：深潜试过，开机 abort 循环。
- C3 没有浮点单元：新代码一律整数 / 定点（深潜沿用的浮点代码不动）。
- 改规则一定先改 `adv_core.js`，重录轨迹，再改 C；`test_adv_model.py` 会逐步比对。
- 新增中文界面文字后重新生成字库（`firmware/tools/generate_collection_fonts.py`，需要 `lv_font_conv` 1.5.3 和 SourceHanSansCN-Medium.otf，SHA256 记在 `firmware/tools/collection-fonts.json`）。宿主测试会抓缺字。
- 脚本测试真机时先 `>adv.test=1`，否则会写入假成绩。
- 游戏进行中上键是游戏键，只有长按上能暂停；不要在对局中加双击上返回。
- NABO 的帽标不能镜像，朝左、朝右动作各做一套。
- 不要提交 `private/`、设备备份、NVS、串口原始日志。
- 在 macOS 外接卷（非 APFS）上工作会产生 `._*` 文件，会弄坏 ESP-IDF 组件哈希和 `.git` 包索引：在 APFS 磁盘上构建，或者构建前 `find . -name '._*' -delete`。

## 8. 给 Codex 的开场白（可直接复制）

> 这是 NABO 的冒险之旅合集固件（ESP32-C3 AI Passport 工牌，独立离线版）。先读 `AGENTS.md`、`docs/HANDOFF.md`、`game-art/adventure/DESIGN.md`，并按 nabo-passport-game skill 的流程工作。现在的状态和待办在 HANDOFF 第 5、6 节。今天做待办第 __ 项。改规则先改 `game-art/adventure/prototype/adv_core.js` 并重录 `tests/adv_golden`；每次改完跑 `python3 tools/run_tests.py` 和 `./build.sh`，把结果（测试数、app 大小、SHA256）写回 HANDOFF。

## 9. 2026-10-25 Mac 接手：精灵管线基础支持（未真机验收）

### 范围和接手状态

- 独立克隆，基线 `9735f34f019116f21b806195fd90842cf2bb7a64`；初始 `main...origin/main` 干净。最近三次提交依次为 `9735f34`（交接与设计）、`fd91001`（冒险骨架）、`43d5497`（旧合集发布）。开发分支 `codex/sprite-pipeline`，具体提交用 `git log -1` 确认。
- 已读 `AGENTS.md`、本交接本、`README.md`、`docs/BUILD.md`、`docs/VALIDATION.md`、`DESIGN.md`、`ART_BRIEF.md`、`BUDGET.md`，并核对实际渲染、测试和构建代码。未修改其他 NABO 项目或本机 Codex memories。
- 仓库没有 `.agents/skills`；已检查本机通用 `passport-develop`、`passport-build`，其中 IDF 5.5.3 和目录约定不适用于本仓库。未找到文档所指的 `nabo-passport-game`，没有声称执行该技能；实际按本仓库 IDF 6.0.2、宿主门禁和维护约定推进。
- 第 1 项真机冒烟和第 2 项用户选造型仍待完成。此次明确授权先做第 3 项不依赖美术的编码、解码和渲染支持；不替换正式 NABO 美术、不推进整套六游戏。
- 初次交接回写时 Mac 环境断连，恢复后已核对：原 11 个改动完整，交接记录未写入，没有发现额外工作区改动。本节补齐该记录。用户后续授权提交到 GitHub 独立分支，未授权合并 main、强推、固件 release 或刷机。

### 完成内容

- `tools/generate_adv_sprites.py`：最终尺寸 RGBA PNG → 全动画共享最多 63 种不透明 RGB565 色 + 透明索引 0 → 逐行 RLE → C 数组和哈希报告。半透明要求显式背景色；关键帧与差分自适应选择，最多 7 个连续差分，打包后逐帧比较量化后的索引帧。
- `adv_sprite.c/.h`：随机访问逐行还原、元数据和坏流检查；`AG_SPRITE` 使用 256 字节栈上行缓冲和既有 DMA 条带，不分配整帧或堆，不使用浮点、IRAM 或镜像。
- 回归测试先复现、再修复重叠绘制操作换序时未标记脏区的问题。覆盖透明擦除、裁剪、移动、删除、素材切换和层叠顺序。
- 新增 10 项合成图测试和独立 ASan/UBSan 检查。CLI 测试使用当前 Python 的 `sys.executable`，避免 Windows 上没有 `python3` 别名时子进程失败；Windows 门禁尚未在该系统执行。
- 没有修改玩法规则，故原型与 golden 未动；没有增加界面文字或修改页面版式，字库未变，完整门禁重新生成的既有 UI 截图与基线一致。
- 管线格式、生成命令、C 接入方式和限制见 [SPRITES.md](SPRITES.md)。当前没有正式素材，固件不嵌入合成测试图；构建大小不包含未来美术数据。

### 实际验证与镜像身份

| 类别 | 结果 |
|---|---|
| 基线代码测试 | `python3 tools/run_tests.py`，64/64 通过 |
| 基线构建 | IDF 6.0.2 build / merge-bin / 布局检查通过；app 1,158,976 B；SHA256 `8194915a0eca8caa7cb8fdce59b5b662f8bb5563cc097442df38423ea7445bbc5` |
| 最终代码测试 | 完整宿主门禁 74/74 通过，既有 64 项 + 新增 10 项；宿主 C 用 `-Wall -Wextra -Werror` |
| 原生内存检查 | macOS Clang ASan + UBSan，已知关键帧/差分及 50,000 组确定性坏行流通过，退出码 0，无 sanitizer 报告 |
| 最终构建复核 | IDF 6.0.2 build / merge-bin / 布局检查 PASS；app 1,159,600 B（较基线 +624 B），分区 4,128,768 B，剩余 2,969,168 B |
| app SHA256 | `6318a43430a2eb55e8b0d842ff5b662f8bb5563cc097442df38423ea7445bbc5` |
| 合并镜像 | 1,225,136 B；SHA256 `6a179e4425d9979f1bf1d392172a7ee864162e545a2e0b6c142b562bff909b25` |
| 真机 | **未刷写、未验收**；按键、声音、10 轮进出内存、深睡唤醒、帧率和栈余量都未验证 |

以上是提交前 Mac 工作区构建的身份，不承诺其他路径、时间或编译环境重建得到相同 SHA256。镜像及匹配 ELF/MAP 保留在 Mac 的 `firmware/build-idf6/`；日志和完整哈希清单保留在忽略目录 `private/validation/`，不进入 Git。源码推送不包含固件、设备日志、NVS、备份或凭据，也不是正式固件发布。

### Windows 接手注意

1. Windows 会话继续主线；此分支基于 `9735f34`，取回后先比较当前主线差异。重点合并点为 `adv_gfx.c/.h`、`firmware/main/CMakeLists.txt` 和 `tests/test_adv_renderer.py`，不要覆盖 Windows 已有工作。
2. 新文件包括 `adv_sprite.c/.h`、打包器、`tests/test_adv_sprites.py` 和两个宿主 C 文件。已有测试只新增解码源文件；没有改站点、按键、音频、NVS 或分区。
3. 通过 `python tools/run_tests.py`（或可用的 `python3`）和仓库 `build.ps1` 重新验证 Windows 环境；依赖 Python 3、Pillow、Node 和可用的宿主 C/C++ 编译器。可选 sanitizer 指令记录的是 macOS 检查。
4. 输入 PNG 必须已在最终画布尺寸；总 manifest、骨骼输出缩放和锚点、帧率/循环调度尚未实现。获批美术到位后再接地图；合成图不代表正式美术批准或颜色质量验收。
5. 真机仍按第 6 节第 1 项执行，须有工牌和刷写授权。发布前还需统一文档/界面 `v0.1.0` 与继承的固件配置版本 `1.0.0`；本轮不改版本或发布固件。

## 10. Windows 主线继续：2026-10-25（进行中）

已克隆到 `D:\AI PASSPORT XIAOZHI\nabo-adventure`，本地分支 `codex/adventure-device-smoke`。主线更新至 `63d19d8`，并将 `8da163a` 的精灵管线整合到工作区，保留新 UI 要求；当前工作尚未提交或推送。

用户目标为按顺序完成全部轮次。Claude 新增 UI 风格板和整包后，原 9 轮为 11 轮。用户已选 **v2①轻便徒步** 与 **①复古护照手账**。最新逐项状态见 [ART_PROGRESS.md](ART_PROGRESS.md)。开机另须有 NABO 出场并说 `NABO,陪你冒险`。在能保证质量时 Codex 自行完成；只有具体动作经反复修正仍不良才请 Grok 补片，先写本地任务并告知用户路径，入口 `../GROK_HANDOFF.md`，当前没有 Grok 生成任务。

### 身份依据与制作边界

第一轮曾误用旧深潜重绘头部，用户明确拒绝，旧三款已撤回。真正原始全身图已原样放入 `art/reference/nabo-idle-original.png`（均相对 `game-art/adventure/`），来源/SHA256 在同目录 `source.json`。第 1 轮 v2 是基于此原图的换装编辑；之后使用用户选定①，禁止再用旧 SVG 头替代。当前 SVG 骨骼明确为原像素切片包装，既保留 masters，也交付每动画共享 64 色正式帧；不是重新手绘的矢量身份。

### 已冻结并上机的外壳基线

- app 1,160,608 B；SHA256 `71cc1f6b2eca742cdb11b5e861694e7a43e5bdf3ce8e1da689f3ca32b66fdb32`；IDF 6.0.2，配置版本已统一 `0.1.0`。
- 工牌 MAC 尾号 `a9:58`。真实分区为 `legacy_2m_app_6m_assets`：factory `0x10000..0x200000`，assets `0x200000..0x800000`。首次严格布局检查拒绝且没有写入；随后只增加这个精确白名单，按真实 factory 大小与扇区界限复核，保持全备份和全部保护区回读。实际分区表未改。
- 刷写后 app 和所有受保护字节一致；NVS 在自动游戏测试后再次读回，24,576 B 与升级前完全一致。原日志、备份、回执和冻结 app/ELF/MAP 只留 `private/`。
- 页面导航、跳一跳和深潜各十轮串口进出通过；第一轮地图 heap：跳一跳 259,052 B 不变，深潜 258,964 B 不变，largest 均 114,688 B。额外一轮同样稳定。
- 用户确认显示、三键和声音正常；原休眠为 300 秒，在测试保护下临时设 30 秒后，用户确认约 30 秒熄屏、上键唤醒回封面。临时设置未落盘。设备只确认到该镜像；后续音画/UI 不能据此直接验收。

### 程序增量与当前继续点

`adv_persist.c/.h` 统一保护外壳、跳一跳、深潜、教程和设置的测试写入；跳一跳成绩成功后去重；退出测试先停游戏，再重载真实存档。`>adv.open=jump|dive` 仅测试模式的地图可用，不造分数。深潜停止超时不再释放仍存活缓冲。

休眠实测发现底座继承的 codec 关闭后重复停 I2S 告警，已使用公开 `i2s_channel_get_info/is_enabled` 修复；真正错误继续报告。`adv_boot.c/.h` 已用真实 WAV 全部 43,050 个样本对拍，开机语音延后 1,400 ms 一次播放，离开封面/测试重置/休眠立即停播，共用 audio lock；音频为原系列“阳光小男孩”。`AG_NINEPATCH` 已支持单个显示操作的固定角和重复边/中心，最小/最大卡、移动、裁剪、增量 = 整屏回归通过。

最新中间构建 app 1,248,384 B，完整宿主门禁 **115 项通过**；新增开机音频和 I2S 修复尚未上机，当前等第 4–5 轮正式角色/静态包/UI 资产接入再生成候选。六个新游戏的正式规则仍未实现，不把美术或占位关卡当成正式游戏。

### 正式共用包上机（第 1–5 轮）

app **1,514,528 B**，SHA256 **`6667fa0215dc75a02ddbcad93d53bc5b76aba1e797bd9cf42344b81d45578b3e`**，精确 app/ELF/MAP/sdkconfig/素材清单与源哈希已冻结 `private/candidates/<sha>/`。构建及旧 factory 离线容量检查通过，实际尚余 517,088 B；没有改分区或写资源区。已完成本候选的保护式升级/全片回读及自动冒烟；实体声画和唤醒待本轮用户确认，不沿用基线 `71cc…` 的实体认可。

最终完整宿主门禁 128 项通过，含生产渲染 9 项、包器 10 项及锁定地标压暗/透明回归。共用真实 C 包 215 资源/283 帧，11,822 行及九宫格 912 行逐像素核对。RLE/表/目录估算分别 travel 129,224 B、static 74,329 B、UI 73,709 B，详细 ELF 符号及真实预览检查见 VALIDATION。封面为分层原生资源+120px旅行服 NABO，1.4秒后播 `NABO,陪你冒险`；离开页面取消声音。地图为12fps动作与软件镜头插值，60fps硬件滚动仍是待办。

新游戏美术按第 6–11 轮继续，独立包先 `--group post|night|climb|ski|sky|space --output private/game-art-c/<id> --verify-c` 校验，每包≤260KiB；暂不把全部未实现游戏素材嵌进旧2MB factory。用户要求能保证质量时由 Codex 完成；只有真实动作经反复自修仍不顺时才写具体本地 Grok 任务并告知路径。当前 `GROK_HANDOFF.md` 仍待命。

## 11. 当前继续点：字体与欢迎V2a

用户确认 `6667fa…` 的语音清楚，但否定开机只有平移、缺乏灵动感，并指出整体字体单薄/陈旧。因此已完成新一轮视觉修正，旧视觉不能按接受处理：

- 标题16/18px改Noto Sans SC Bold、正文12px用Source Han Sans CN Medium，品牌/大数字用Montserrat Bold；深蓝选中卡+奶白字、留白/对齐、银章文字对比、封面CTA、超大纪录和锁图标均重新检查，13页实际C图通过。细节见 `UI_REFINEMENT.md`。
- 欢迎V2a为32张物理帧/34曝光/4.417秒，提包→扶帽→挥手→邀请→收手，固定脚锚(120,266)，不再整人平移；保留原WAV与1.4秒延迟。选择入口 `art/boot/selection.json` 锁定e02927ba…清单；源头脸/帽标不镜像。预览和当前证明见 `art/preview/boot-v2/README.md`。
- literal行流+最优key分块兼容旧v1，descriptor32B和最多7delta不变。物理帧排序通过时间表逆映射，34曝光画面/时长不变；实际生产C的4,424个时间点通过。UI与开机演员/时间表合计159,625 B/160KiB，完整计费。
- **六游戏美术全部独立交付**：合计64个人物动作/398人物帧，静态/动态道具另计；全11轮索引362资源/804帧，生产C42,153行+九宫格912行通过，所有六包<260KiB。审计见 `ART_DELIVERY_AUDIT.md`，各包有1x预览和打包证明。正式6游戏代码仍是占位，不宣称玩法已做完。

新候选 **`557607a2f468fed67f5e52adae2f008dd7b44fd5b9d52d94d16c72bb0fa97604`**，app **1,533,920 B**，真实旧factory余497,696 B；**160项宿主门禁**与Windows IDF6.0.2构建通过。app/ELF/MAP/配置、当前字体/生成头及源哈希私有冻结在对应候选目录，**已保护式app-only升级及全片回读通过**；两旧游戏各10轮+暖机无持续内存下降，NVS24,576字节与本次刷前完全相同。新封面76,800像素与宿主一致，地图/护照已实看，详细heap/回执见VALIDATION。

下一步：新镜像已重启到正常模式并重播开机，等用户实际看字体/动作；本候选也已做可见30秒临时设置，观察USB掉线并重启回封面/test0，等这一次实体熄屏/上键回答。现有99分/3章/seen7已逐字节保留，后续仍不能恢复旧0分NVS。用户已补充确认上一候选第二次可见30秒测试“约30秒熄屏，上键能恢复”，记6667fa…实体通过；首次亮屏反馈保留。Grok仍待命，只有具体动作自修后依然不顺才写独立任务并通知用户绝对路径。

## 557607 本镜像用户确认与范围

用户已对本镜像新字体/欢迎回答“都正常”，并对这一次30秒测试确认“约30秒熄屏，上键能恢复”。本镜像已保护式app升级、全片保护字节回读、两旧游戏各10轮冒烟；99分/3章存档24,576字节与本次刷前备份相同，当前恢复正常模式/test0，原持久休眠300秒未改。上述此前“待答/未上机”保留当时检查阶段，当前实体字体/欢迎和30秒睡醒记为通过；精确已验收bin按原SHA冻结，不能用新构建替换。

**11轮完成的是美术和共用界面/演出交付。正式可玩的游戏只有跳一跳和深潜。小火车、萤火虫、登山、滑雪、热气球、太空的美术及独立C包已齐，正式玩法仍待开发，即使解锁也还是占位关卡。** 用户已询问此范围，后续必须按“美术交付/正式可玩”分别汇报。程序后续从HANDOFF待办小火车POST的原型/规则对拍/C实现/横屏/素材整合/真机验证开始，其余五款依次实施。
