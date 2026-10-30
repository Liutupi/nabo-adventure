# NABO 的冒险之旅 v0.2.0 安装说明

适用于 FoloToy AI Passport ESP32-C3 / 8MB。八款游戏离线运行，素材均嵌入应用，不需要另刷 assets.bin。

| 文件 | 用途 | 地址 |
|---|---|---|
| nabo-adventure-v0.2.0-full.bin | 首次完整安装，重置设置和成绩 | 0x0 |
| nabo-adventure-v0.2.0-app.bin | 兼容分区上的保留存档升级 | 0x10000 |
| nabo-adventure-v0.2.0.zip | 镜像、升级工具、说明、许可与校验和 | 解压后选择 |

应用SHA256：`e9fe81f6cd52f194d309638305cd9e41faaf074c2c076f815578fb34981e8afc`，与本次工牌串口回归的应用逐字节相同。发布没有重新编译应用。

## 首次完整安装

在 AI Passport 网页刷机工具中选择本地固件，使用 **full.bin，从0x0写入**。启动器和分区表复用 v0.1.0 已发布文件，应用为本次 e9fe81f6；合并后NVS/PHY空洞全部为FF，不含任何设备存档或配网数据。完整写入会重置原有设置和成绩。

安装后分区为NVS 0x9000、factory 0x10000（0x3f0000）、assets 0x400000、files 0x700000。应用升级的设备验证不等于空存档完整安装验收；后者尚未真机验证，因此本版标记为预览版。

首次安装使用应用默认设置：扬声器开启、音量70%、亮度80%、无操作300秒休眠。验证工牌保持静音，不代表首次安装默认静音；可在正常设置中关闭扬声器。状态页内置版本文字仍为v0.1.0，以发布标签和SHA识别本版。

## 保留存档升级

工牌退出游戏并保持唤醒，连接数据线；解压ZIP，在解压目录打开终端。安装工具依赖并枚举串口：

```powershell
python -m pip install esptool==5.5.0
python -m serial.tools.list_ports -v
python -m esptool --port COM口 read-mac
```

将下面的COM口和小写MAC替换为刚读到的实际设备值（macOS使用枚举到的 `/dev/cu.*`）：

```powershell
python tools/flash_candidate.py --mode upgrade --no-backup --port COM口 --expected-mac aa:bb:cc:dd:ee:ff --app nabo-adventure-v0.2.0-app.bin --sha256 e9fe81f6cd52f194d309638305cd9e41faaf074c2c076f815578fb34981e8afc
```

此方式不备份或读取旧应用，只核对ESP32-C3、8MB Flash、实际MAC、安全状态、分区MD5及边界；只写应用，逐字节读回应用和启动区/NVS/PHY。record/assets依靠写入/擦除范围保护，不宣称对它们逐字节回读。工具不会整片擦除或改写分区表。省略 `--no-backup` 可使用完整备份/保护区比较模式，备份并非升级的必要条件。

仅接受三种精确布局：本版开发分区、旧2MB应用+6MB资源，以及2MB应用+64KB record+剩余assets；两种旧布局均从0x200000起保护旧数据。未知/加密布局会拒绝写入。设备回执或可选备份留在本机 `private/device/`，不要上传。

升级保留设置、跳一跳/深潜等原记录；POST/CLIMB/SKY的V1记录保留，新V2使用不同分数键，旧章和解锁继承。不要用full.bin代替保留存档升级，也不要把app.bin从0x0刷入。

## 操作与预览范围

地图上/下移动，OK进入；前一站拿铜章解锁下一站，初始不会全部解锁。六款V2横屏、三键朝下：左/右控制，中键主动作；长按中键暂停，中键继续、左键重来；标题/暂停/结算双击右键回地图，进行中右键不会退出。各款具体操作见ZIP内 `GAME_CONTROLS.md`。

八款各十轮串口回归、暂停/返回、六款自然结算、内存、最新静音/NVS比较通过。实体三键手感、实际LCD读图/服装/卡片、满场景帧率、对局睡醒和音质仍待人工验证，B款选择未实现。新升级工具的布局/读回保护经过宿主检查；本轮设备升级使用等价分段校验流程。详细证据见 `VALIDATION.json`。

下载后按 `SHA256SUMS.txt` 校验，ZIP内部按 `contents.sha256` 校验；Windows可用 `Get-FileHash 文件名 -Algorithm SHA256`。源码MIT，NABO形象/美术权利另行保留，第三方许可随ZIP附带。本项目与FoloToy官方无隶属或背书关系。
