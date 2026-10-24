# 交接本

更新：2026-10-25 · 固件 v0.1.0（骨架）· 提交见 `git log`

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
| 3 | 精灵管线 | `tools/generate_adv_sprites.py`（64 色、行 RLE、关键帧 + 差分，打包后逐帧比对）；`adv_gfx` 实现 `AG_SPRITE`；地图换上 NABO 走路和地标 |
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
