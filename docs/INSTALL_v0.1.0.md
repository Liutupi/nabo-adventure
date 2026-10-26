# NABO 的冒险之旅 v0.1.0 安装说明

这是首个公开预览固件，适用于 FoloToy AI Passport 的 ESP32-C3 / 8MB 型号。固件离线运行，八款游戏素材均嵌入应用，无需另刷 assets.bin。

## 下载哪个文件

| 文件 | 用途 | 写入地址 |
|---|---|---|
| nabo-adventure-v0.1.0-full.bin | 首次完整安装；会重置设置和游戏成绩 | 0x0 |
| nabo-adventure-v0.1.0-app.bin | 已有兼容底座、需要保留设置和成绩的升级 | 0x10000 |
| nabo-adventure-v0.1.0.zip | 以上镜像、分拆启动文件、保护式升级工具、校验和、操作说明及许可 | 解压后按下面选择 |

应用版 SHA256：`8897cd9e790bac8ec8812f83582f278145da85b4a835a6584e643211acdc3bf8`。它与本次工牌上通过自动检查的应用逐字节相同，版本发布没有重新编译替换。

## 首次安装

在 AI Passport 网页刷机工具选择本地固件时，使用 **full.bin**，从 **0x0** 完整写入。新布局为 nvs 0x9000、factory 0x10000（0x3f0000）、assets 0x400000、files 0x700000。完整镜像在 NVS/PHY 空洞处是 FF，不包含任何人的存档或配网数据；写入会清除原设置和成绩。

完整安装镜像的启动器、分区、偏移、FF填充和应用字节已检查，**空存档首次安装尚未做真机验收**；本轮真机验证使用保留旧分区的应用升级。因此本版标为预览版。

## 保留数据升级

保持工牌唤醒、接好数据线，退出游戏，解压ZIP并在该目录打开终端。需要 Python 和 esptool 5.5.0：

```powershell
python -m pip install esptool==5.5.0
python -m serial.tools.list_ports -v
python -m esptool --port COM口 read-mac
```

将下面的COM口和小写MAC替换为刚读到的真实设备值：

```powershell
python tools/flash_candidate.py --mode upgrade --port COM口 --expected-mac aa:bb:cc:dd:ee:ff --app nabo-adventure-v0.1.0-app.bin --sha256 8897cd9e790bac8ec8812f83582f278145da85b4a835a6584e643211acdc3bf8
```

工具只接受经过识别的两种兼容布局：旧factory 0x10000..0x200000 / assets 0x200000，或上述开发分区。它先核对芯片、8MB容量、MAC、安全状态和分区，私下备份并校验整片Flash，再只写应用并回读所有保护字节。旧布局的NVS、启动器、PHY和0x200000以后的旧资源均保留。遇到未知布局会拒绝写入。

备份和回执只会写到本机 `private/device/`，不要上传。应用版不能当作从0x0安装的完整镜像；保留数据升级不要用完整镜像或擦除Flash。

## 操作与验证范围

地图上/下移动、OK进入。前一站拿铜章后解锁下一站；初始进度不会全部解锁。

萤火虫之夜、雪崩速降、火箭登月 V2 顺时针横拿、三键朝下：左右键控制移动，中键主动作，长按中键暂停；暂停中键继续、左键重来；标题/暂停/结算页双击右键回地图。游戏中右键移动不会退出。其他游戏见ZIP内 GAME_CONTROLS.md。

本应用通过279项宿主检查、三款V2串口流程/十轮进出、火箭自动成功登月、旧跳一跳/深潜与热气球兼容检查、开机73帧与内存释放、存档比对；用户确认临时30秒设置页熄屏和上键唤醒。详细范围见 VALIDATION.json。

三款实体手感/画面阅读、本轮声音、逐款对局中休眠仍待验；POST/CLIMB没有在这份镜像上重跑串口整局。热气球/登山当前仍是V1，新V2正在规划；B款换装选择尚未完成。验证工牌保持静音，不代表首次安装默认静音。

## 校验和许可

GitHub资产按同页 SHA256SUMS.txt 校验；ZIP内部文件按 contents.sha256 校验。Windows可用 `Get-FileHash 文件名 -Algorithm SHA256`。

源码MIT；NABO形象和美术不随MIT授权。许可及第三方声明随ZIP附带。本项目与FoloToy官方无隶属或背书关系。
