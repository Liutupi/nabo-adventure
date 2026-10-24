# NABO 游戏特辑 v1.0.0

一块工牌，三大游戏入口、五种玩法。保留 NABO 和设置，去掉小智语音及联网服务，开机即可离线玩。

![NABO 游戏特辑](https://raw.githubusercontent.com/Liutupi/nabo-games/v1.0.0/docs/images/cover-white-coat.png)

- **深潜 DIVE**：换向、俯冲、氧气和深度纪录。
- **NABO 牌桌**：21点、大话骰支持2–4人；谁是卧底支持3–8人，264组词。
- **NABO 跳一跳**：连续蓄力、渐进难度、迷你平台；约20次成功落地后随机出现咖啡杯、电脑、音箱、黑胶等一人位平台。
- **设置**：音量、亮度、扬声器、自动休眠、电量与设备状态。首页使用原有白大褂 NABO 半身像。

![牌桌三种玩法实机渲染](https://raw.githubusercontent.com/Liutupi/nabo-games/v1.0.0/docs/images/table-three-games-device.png)

## 下载与安装

- ZIP：安装文件、校验清单、安装说明和许可。
- `nabo-game-collection-v1.0.0-full.bin`：首次完整安装，从`0x0`刷入。完整安装会覆盖NVS中的设置、成绩等数据。
- `nabo-games.bin`：保留数据升级使用的已验收应用，只写`0x10000`。请先确认设备身份、兼容分区并备份，使用ZIP中的受保护升级工具。
- 所有游戏素材均嵌入应用，不需要单独刷`assets.bin`。

详细操作见[安装说明](https://github.com/Liutupi/nabo-games/blob/v1.0.0/docs/INSTALL.md)。

## 验证

80项宿主测试、最终5项渲染复核通过；实机完成牌桌结算、5/8人卧底、跳一跳一人位平台和10轮游戏进出检查。用户已确认五种玩法、实体按键、音效、设置、长按退出与自动休眠后按键唤醒均正常。

应用2,581,856字节，SHA256：

```text
e83a1bb216392c3cb67e5ab08af2a354bed2f2a3f44080ecdd2a7f6291acf390
```

发布使用同一份已验收应用，不重新编译。启动器、分区表复用与验收设备一致的公开版本。此次采用保留数据的应用升级，未对空NVS进行首次完整安装实机测试；完整包输入、偏移、填充区与应用字节已静态核验。详见[验证记录](https://github.com/Liutupi/nabo-games/blob/v1.0.0/docs/VALIDATION.md)。

源码MIT；NABO形象和美术不随MIT授权，见NOTICE。本项目为独立社区固件，与FoloToy官方无隶属或背书关系。
