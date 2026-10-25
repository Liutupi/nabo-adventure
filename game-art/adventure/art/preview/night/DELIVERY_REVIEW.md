# NIGHT 集中审阅入口

本页补齐可查看证据，不改变素材或玩法状态。全部图像按原 PNG **1×像素**合成，没有缩放、重画、改色或新生成角色。

- [静态及动态道具全表](delivery-static-dynamic-1x.png)：10 个静态引用，加 4 个道具动画帧，实际 640×448。
- [四幅完整场景](delivery-scenes-1x.png)：960×344；每幅实际画面240×320，顶上24px仅是图外审阅标签。
- 单幅完整场景：[0](delivery-scene-00-1x.png)、[1](delivery-scene-01-1x.png)、[2](delivery-scene-02-1x.png)、[3](delivery-scene-03-1x.png)。
- 原人物动作：[全部动作](all-actions-overview.png)，来源与制作/验收边界见[QA](QA.md)。
- 元数据空间：[hitbox制作坐标说明](../../HITBOX_CONVENTIONS.md)，不同空间的值不能直接混用。

底色来自当前 `firmware/main/adv_ui_map.c` WORLD[4]：RGB(24, 48, 60)。NIGHT新图只做既有草/树影/飞蛾/罐层/角色alpha拼接，白色发光层保持原mask色；其强度/着色仍由引擎负责。SKY场景直接从已交热绳、放气绳和接邮票场景裁出完整240×320像素，另加入既有B场景；没有重画绳端或改变接合。

清单SHA256：`d9d5b35ec4702fa5fd739b5224d1d5c0b933b72c5d272ade1f9c3a8e6679a0bb`。静态/动画/原母版/rig/脚本前后全量源SHA未变，详情见[补充QA](delivery-evidence-qa.json)。复现脚本私有保留在 `private/art-delivery-audit/build_preview_evidence.py`，不进固件。

这些是宿主美术组合，尚未实现正式游戏逻辑、碰撞、资源/成绩或实机显示验收。
