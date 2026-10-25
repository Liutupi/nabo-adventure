# 交接本

更新：2026-10-25 · 固件 v0.1.0（骨架）· 提交见 `git log`

**Mac 精灵管线增量见第 9 节。** 文档和界面为 v0.1.0，构建配置元数据仍沿用底座的 `1.0.0`；本轮未改版本配置，请以提交和镜像 SHA256 识别。

## 1. 现在是什么状态

《NABO 的冒险之旅》合集的**骨架已经能编译、宿主测试全过，但还没上过真机**。

- 合集外壳完整：封面 → 竖向地图（9 个站点）→ 护照亭 / 护照 / 设置 → 盖章仪式 → 统一的游戏流程（标题、倒数、进行中、暂停、结束、结算）。
- 跳一跳、深潜是现成游戏，从地图进出，最佳成绩回传给外壳算印章。
- 其余 6 站（小火车、萤火虫、登山、滑雪、热气球、太空）跑同一个**占位游戏**，门槛临时 3 / 6 / 10，用来验证整条流程。
- 画面全是形状和文字占位，没有新的 NABO 美术。美术规格和 Codex 提示词已写好。

## 2. 先读这些

| 文件 | 内容 |
|---|---|
| `AGENTS.md` | 维护约定（必须遵守） |
| `game-art/adventure/DESIGN.md` | 已实现的规则：站点、按键、印章、一局流程、游戏接口、存档、串口命令 |
| `game-art/adventure/GAMES.md` | 6 个新游戏的玩法和起始参数 |
| `game-art/adventure/UI_DESIGN.md` | 配色、字体、每个画面（截图由生产代码渲染） |
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
| `firmware/main/adv_sound.c/.h` | 提示音合成（三角波，无采样） |
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

| 项目 | 状态 |
|---|---|
| 宿主测试 64 项 | ✅ 全过（macOS，cc） |
| ESP-IDF 6.0.2 构建、合并镜像、布局检查 | ✅ app 1,158,976 B，SHA256 `ba99d31e…090e7`，分区剩 72% |
| 浏览器原型 | ✅ 能加载、按键响应、无控制台错误 |
| **真机** | ❌ **没刷过**。按键手感、声音、深潜和跳一跳进出、10 轮进出的内存、深睡唤醒都没验证 |

## 6. 待办（按顺序）

| # | 任务 | 完成标准 |
|---|---|---|
| 1 | **真机冒烟**（要用户的工牌） | 刷 app → 封面、地图、护照亭、设置能走通；跳一跳和深潜进出各 10 次不重启；`>adv.status` 记录地图 / 游戏中 / 回地图的 `heap`、`largest`，10 轮不下降；声音不爆音；深睡后按键能唤醒 |
| 2 | 美术第 1–3 轮（Codex） | 按 `CODEX_PROMPTS.md`；第 1 轮由用户选造型 |
| 3 | 精灵管线（基础支持完成，正式美术接入待做） | 编码、解码、`AG_SPRITE` 及合成图回归已完成；仍需批准的 NABO 动画和地标、总 manifest/锚点/播放调度，再接入地图，详见第 9 节 |
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
