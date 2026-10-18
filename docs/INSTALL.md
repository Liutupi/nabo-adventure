# 安装 v1.0.0

适用 FoloToy AI Passport ESP32-C3 / 8MB。深潜、牌桌三玩法、优化跳一跳和设置均可离线使用，无需配网或激活。

## 已有 NABO 定制分区：保留数据升级

下载并解压ZIP。使用Python3.11和esptool5.5.0，核实设备自己的串口、MAC及实际分区，不要照抄另一块工牌的身份。

```powershell
python -m pip install esptool==5.5.0
python flash_candidate.py --app nabo-games.bin --sha256 e83a1bb216392c3cb67e5ab08af2a354bed2f2a3f44080ecdd2a7f6291acf390 --mode inspect
python flash_candidate.py --app nabo-games.bin --sha256 e83a1bb216392c3cb67e5ab08af2a354bed2f2a3f44080ecdd2a7f6291acf390 --mode upgrade --port YOUR_COM_PORT --expected-mac your:device:mac:address
```

第二条只检查文件。第三条需要替换为设备身份；工具核对芯片、8MB、安全状态及完整分区，先备份并验证，仅写应用0x10000，再读回应用并核验所有保留区。备份保存到本机private/device，不要上传。

## 首次完整安装

使用 nabo-game-collection-v1.0.0-full.bin，从0x0刷入。包含公开启动器、分区表和已验收应用。完整安装会覆盖 NVS 中的设置和成绩；需要保留数据时使用上述应用升级。

本次验收采用应用升级，未对空NVS做首次完整安装实机测试。完整包输入、偏移、填充区和应用字节已静态核验。所有素材均在应用中，不需要单独刷assets.bin。

## 校验与操作

逐个对照SHA256SUMS.txt校验下载文件。应用应为2,581,856字节。首页上/下选择、OK进入；深潜与设置长按上返回；牌桌对局长按OK两秒暂停并返回封面，再长按上回首页；跳一跳按住OK蓄力、松开起跳，上返回，下切换角色。
