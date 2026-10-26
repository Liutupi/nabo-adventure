# NABO 的冒险之旅

FoloToy AI Passport（ESP32-C3 / 8 MB）上的 NABO 游戏合集，独立离线固件：开机进入一张竖向冒险地图，从深海一路到太空，8 个游戏站点，每个游戏三枚印章，盖满一本冒险护照。不需要配网、激活或小智服务。

**首个公开预览固件 v0.1.0：** [GitHub 下载](https://github.com/Liutupi/nabo-adventure/releases/tag/v0.1.0) · [安装说明](docs/INSTALL_v0.1.0.md) · [发布说明](docs/RELEASE_v0.1.0.md)。首次安装选full.bin（重置设置与成绩）；保留数据选app.bin并使用保护式升级工具。发布应用与已上机8897cd9e逐字节一致，完整安装路径尚未真机验收。

> **开发中。** 八款正式游戏引擎及各关[独立主题服装A款](docs/COSTUME_INTEGRATION.md)已接入，正在逐项真机验收。POST与NIGHT已有先前精确镜像的用户验收；CLIMB/SKI/SKY/SPACE为新接入玩法，不能沿用旧镜像的验收。银章B款选择系统尚未完成。见[开发进度](docs/DEVELOPMENT_PROGRESS.md)与[验证记录](docs/VALIDATION.md)。

| 封面 | 地图 | 护照 | 盖章 | 游戏标题 | 结算 |
|---|---|---|---|---|---|
| ![](docs/images/ui/cover.png) | ![](docs/images/ui/map-town.png) | ![](docs/images/ui/passport.png) | ![](docs/images/ui/stamp-bronze.png) | ![](docs/images/ui/title.png) | ![](docs/images/ui/result.png) |

**2026-10-26 Windows续作：** 同步Claude四款正式玩法，265项宿主检查与构建通过；新Grok开机真机已提交全部73帧、跳过0帧，帧选择时序约11.98fps。八游戏静音回归及实体验收状态见[交接本](docs/HANDOFF.md)。[此前睡前回退点](firmware/checkpoints/2026-10-26/)保留；[静音宿主预览](docs/images/ui/boot-v3-silent.gif)不是实机录像。

**V2续作：** 萤火虫之夜、雪崩速降、火箭登月已接入工牌；8897cd9e通过279项宿主检查与保护式升级，火箭三个短窗28.1–28.8fps、夜林四个短窗28.7–29.9fps（draw计数，非光学或最满场景保证）。三款自动检查、火箭自动成功登月及用户确认设置页睡醒通过，实体游戏手感/读图仍待验；精确镜像与结果见[最新交接](docs/HANDOFF.md)。火箭完整29张图保留；热气球/登山各72KiB净新增预算及64KiB修复空间已锁住，美术复用见[后续计划](docs/V2_ART_AND_CAPACITY_PLAN.md)。

截图由生产C代码在宿主机渲染；共用页面、POST与NIGHT使用正式美术。宿主截图不能代替实体操作、声音和帧率验收。

## 站点

| 站 | 世界 | 游戏 | 状态 |
|---|---|---|---|
| 护照亭 | 小镇 | 冒险护照、设置 | ✅ |
| 1 | 小镇 | 跳一跳：按住蓄力、松开起跳 | ✅ 现成 |
| 2 | 深海 | 深潜：变向、俯冲、氧气 | ✅ 现成 |
| 3 | 铁路平原 | 小火车送信：选轨、卸信、鸣笛 | ✅ 核心玩法真机通过；B换装待接 |
| 4 | 夜林 | 萤火虫之夜V2：夜路挥罐、补光、小跑、放光 | V2已接入；当前候选验证见交接本 |
| 5 | 雪山 | 登山：点 OK 换边、按住蓄力跳、躲落石 | 已构建上机；自动与实体验收见交接本 |
| 6 | 雪坡 | 雪崩速降V2：横屏转弯、连过旗门、跳台转体 | V2已接入；当前候选验证见交接本 |
| 7 | 云端 | 热气球：按住加热、躲鸟群雷云 | 已构建上机；自动与实体验收见交接本 |
| 8 | 太空 | 火箭登月V2：点火、分离、奔月、反推着陆 | V2已接入；当前候选验证见交接本 |

上一站拿到铜章，下一站解锁。

## 操作

- 地图：上 / 下 沿路线走，OK 进入，长按 OK 打开护照，长按上回封面。
- NIGHT/SKI/SPACE V2顺时针横拿、三键朝下：左/右移动，中键主动作，长按中键暂停；暂停中键继续、左键重来。**标题、暂停、结算页双击右键回地图**；游戏中右键手势不退出，避免连续移动误退。
- 其他游戏仍双击上键回地图，单击和长按上键不会退出。POST长按上键暂停，深潜单击上键暂停/继续。完整操作见[按键表](docs/GAME_CONTROLS.md)。
- 跳一跳、深潜保留原来的操作（见 [DESIGN.md](game-art/adventure/DESIGN.md) 第 3 节）。

## 开发

| 文档 | 内容 |
|---|---|
| [docs/HANDOFF.md](docs/HANDOFF.md) | 现状、文件职责、待办、注意事项 |
| [game-art/adventure/DESIGN.md](game-art/adventure/DESIGN.md) | 已实现的规则 |
| [game-art/adventure/GAMES.md](game-art/adventure/GAMES.md) | 6 个新游戏的玩法 |
| [game-art/adventure/UI_DESIGN.md](game-art/adventure/UI_DESIGN.md) | 界面设计 |
| [game-art/adventure/ART_BRIEF.md](game-art/adventure/ART_BRIEF.md) | 美术规格 |
| [game-art/adventure/CODEX_PROMPTS.md](game-art/adventure/CODEX_PROMPTS.md) | 美术提示词（按轮次） |
| [game-art/adventure/BUDGET.md](game-art/adventure/BUDGET.md) | 空间与内存预算 |
| [docs/BUILD.md](docs/BUILD.md) / [docs/VALIDATION.md](docs/VALIDATION.md) | 构建 / 验证记录 |
| [docs/SPRITES.md](docs/SPRITES.md) | 精灵打包、逐行解码、正式共用/POST美术与回归 |
| [docs/DEVELOPMENT_PROGRESS.md](docs/DEVELOPMENT_PROGRESS.md) | 正式玩法M0–M4进度与待验收项目 |
| [game-art/adventure/POST_DESIGN.md](game-art/adventure/POST_DESIGN.md) | POST输入、规则和资源/岔路边界 |

```sh
python3 tools/run_tests.py          # 宿主测试（不碰设备）
./build.sh ~/esp-idf-v6.0.2         # 构建、合并、布局检查
```

浏览器原型：`python3 -m http.server`，打开 `game-art/adventure/prototype/`。
小火车直接试玩：打开 `game-art/adventure/prototype/post.html`；正式默认与固件均为整数60Hz。普通进度仍需深潜铜章，串口测试入口仅在测试模式临时直达POST，不伪造成绩或永久解锁。

## 来源

从 [Liutupi/nabo-games](https://github.com/Liutupi/nabo-games)（《NABO 游戏特辑》v1.0.0）分出，去掉了牌桌；底座的发布与验证记录在 `docs/nabo-games-v1.0.0/`。深潜的美术与骨骼在 `game-art/dive/`。

仓库开发布局为app `0x10000`（0x3f0000）、assets `0x400000`、files `0x700000`。**用户工牌实际保留旧布局，factory只有2,031,616B，assets从0x200000开始；升级必须读取真实布局并按旧上限保护。** 本固件只写app，不改分区、不读写旧资源区，见BUDGET及保护式安装器。

## 许可

代码 MIT；NABO 形象和美术素材不随 MIT 授权。详见 [NOTICE.md](NOTICE.md)。本项目与 FoloToy 官方无隶属或背书关系。
