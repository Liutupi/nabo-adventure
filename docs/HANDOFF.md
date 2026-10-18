# v1.0.0 交接

应用已通过用户实机验收，SHA256 为 `e83a1bb216392c3cb67e5ab08af2a354bed2f2a3f44080ecdd2a7f6291acf390`。复制同一份构建输出发布，禁止用后续重编镜像代替。

| 文件 | 职责 |
| --- | --- |
| firmware/main/collection_main.c | 输入、页面与音频生命周期、设置、串口诊断、深睡 |
| firmware/main/collection_model.c | 菜单、设置预览、保存与取消 |
| firmware/main/collection_ui.c | 首页、设置、状态、跳一跳显示 |
| firmware/main/collection_portrait.c | 已有白大褂半身像的 RGB565 转换数据 |
| firmware/main/nabo_dive* | 来源深潜模块，游戏逻辑与画面未改 |
| firmware/main/nabo_table* | 牌桌三玩法及渲染 |
| firmware/main/nabo_jump* | 进阶跳一跳、连续蓄力、迷你及一人位平台 |
| firmware/tools/flash_candidate.py | 身份、分区、备份、应用升级与保留区验证 |

游戏资源均嵌入应用，不需要 assets.bin。保留数据升级只写0x10000；完整镜像从0x0写入会覆盖 NVS。启动器和分区表复用已发布且与验收设备一致的 v1.6.0 公开文件，未从设备备份提取发布文件。

本独立仓库不继承旧 Git 历史；firmware树与验收构建输入一致，见 source-provenance.json。来源项目的 firmware/README.md 保留原说明，本合集构建与安装以根目录 README 和 docs/BUILD.md、docs/INSTALL.md 为准。原始设备日志、备份和构建目录不在公开仓库或附件中。
