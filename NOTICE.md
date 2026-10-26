# 素材与许可

- **代码**（`firmware/` 下除精灵图数据与字体以外的源码、`game-art/*/prototype/` 网页原型与脚本、`game-art/*/tools/`、`tools/`、`tests/`）：MIT，见 [LICENSE](LICENSE)。`firmware/main/adv_gfx.c`、`adv_shapes.c`、`adv_text.c` 由 NABO 牌桌渲染器改写，另见 [LICENSE.Table](LICENSE.Table)；跳一跳代码见 [LICENSE.Jump](LICENSE.Jump)。
- **NABO 形象与美术**：`game-art/dive/` 下的 `frames/`、`rig/` 中的 SVG 部件、`design/` 中的造型图、`prototype/assets/` 中由帧生成的图集，`firmware/main/nabo_dive_sprites.c`、`jump_sprites.bin`、`collection_portrait.c`、`art/nabo-white-coat-idle.rle`，以及今后 `game-art/adventure/art/` 下的所有角色、场景、印章美术。NABO 角色归项目拥有者所有，造型与动作帧由项目拥有者使用 Codex 为本项目绘制。**不随 MIT 授权**；转载、再分发或用于其他项目前请先取得许可。
- `docs/images/ui/` 的截图由本仓库代码渲染，包含 NABO 半身像，同样不随 MIT 授权。`docs/images/cover-white-coat.png` 为使用相同角色参考制作的宣传插画。
- 网页原型从 Google Fonts 加载 Archivo Black、Noto Sans SC、Space Mono（均为 OFL 1.1），仓库中不包含字体文件。
- `firmware/components/bsp/` 来自 FoloToy 官方 ai-passport 项目（MIT，见 `firmware/LICENSE.FoloToy`）；`firmware/main/` 中的位图字体由思源黑体 Source Han Sans、Archivo Black、Space Mono 生成（均为 OFL 1.1，许可证随附）。

本项目是 NABO 独立社区固件，与 FoloToy 官方无隶属或背书关系。

## v0.1.0 二进制随附声明

- 开机V3使用项目拥有者提供的Grok生成原片，并经项目工具处理；角色身份仍以项目原始参考为准。此演出与其他NABO美术均不随代码MIT授权。
- PL_MPEG解码器来自Dominic Szablewski / phoboslab，MIT；保留的源码及上游记录在`firmware/main/third_party/pl_mpeg/`，发布ZIP附同一份文件。
- ESP-IDF 6.0.2为Apache-2.0，LVGL 9.5.0及项目所用Espressif托管组件的许可证随ZIP附带；固件所用Source Han Sans、Noto Sans SC Bold、Archivo Black和Space Mono字体的OFL声明一并保留。
