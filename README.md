# NABO 的冒险之旅

FoloToy AI Passport（ESP32-C3 / 8 MB）上的 NABO 游戏合集，独立离线固件：开机进入一张竖向冒险地图，从深海一路到太空，8 个游戏站点，每个游戏三枚印章，盖满一本冒险护照。不需要配网、激活或小智服务。

> **开发中。** 外壳、跳一跳和深潜的基线已完成用户工牌冒烟：页面、三键、声音、各十轮进出及临时 30 秒休眠/上键唤醒；具体镜像与边界见 [验证记录](docs/VALIDATION.md)。其余 6 站仍为占位关卡。新的旅行服、地图、手账界面与“NABO,陪你冒险”开机演出按 [11 轮清单](docs/ART_PROGRESS.md) 制作、集成中，不能把基线验证沿用到后续镜像。

| 封面 | 地图 | 护照 | 盖章 | 游戏标题 | 结算 |
|---|---|---|---|---|---|
| ![](docs/images/ui/cover.png) | ![](docs/images/ui/map-town.png) | ![](docs/images/ui/passport.png) | ![](docs/images/ui/stamp-bronze.png) | ![](docs/images/ui/title.png) | ![](docs/images/ui/result.png) |

截图由生产 C 代码在宿主机渲染，画面中的图形是占位版式。

## 站点

| 站 | 世界 | 游戏 | 状态 |
|---|---|---|---|
| 护照亭 | 小镇 | 冒险护照、设置 | ✅ |
| 1 | 小镇 | 跳一跳：按住蓄力、松开起跳 | ✅ 现成 |
| 2 | 深海 | 深潜：变向、俯冲、氧气 | ✅ 现成 |
| 3 | 铁路平原 | 小火车送信：选轨、卸信、鸣笛 | 占位 |
| 4 | 夜林 | 萤火虫：挪动、举罐抓萤火虫 | 占位 |
| 5 | 雪山 | 登山：换边、蓄力跳、躲落石 | 占位 |
| 6 | 雪坡 | 滑雪：转弯、过旗门 | 占位 |
| 7 | 云端 | 热气球：加热上升、躲鸟群 | 占位 |
| 8 | 太空 | 太空着陆：喷气、倾斜、平稳落地 | 占位 |

上一站拿到铜章，下一站解锁。

## 操作

- 地图：上 / 下 沿路线走，OK 进入，长按 OK 打开护照，长按上回封面。
- 新游戏（统一流程）：OK 开始；进行中长按上暂停；暂停里 OK 继续、下 重来、长按上回地图。
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
| [docs/SPRITES.md](docs/SPRITES.md) | 精灵打包、逐行解码和合成图回归；正式美术未接入 |

```sh
python3 tools/run_tests.py          # 宿主测试（不碰设备）
./build.sh ~/esp-idf-v6.0.2         # 构建、合并、布局检查
```

浏览器原型：`python3 -m http.server`，打开 `game-art/adventure/prototype/`。

## 来源

从 [Liutupi/nabo-games](https://github.com/Liutupi/nabo-games)（《NABO 游戏特辑》v1.0.0）分出，去掉了牌桌；底座的发布与验证记录在 `docs/nabo-games-v1.0.0/`。深潜的美术与骨骼在 `game-art/dive/`。

分区边界与 NABO 定制版一致：app `0x10000`（0x3f0000），assets `0x400000`，files `0x700000`。本固件只写 app，不读写 assets / files。

## 许可

代码 MIT；NABO 形象和美术素材不随 MIT 授权。详见 [NOTICE.md](NOTICE.md)。本项目与 FoloToy 官方无隶属或背书关系。
