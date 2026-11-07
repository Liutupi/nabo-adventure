# NABO 的冒险之旅 v0.3.0 安装说明

适用于 FoloToy AI Passport ESP32-C3 / 8MB。八款游戏全部可以**双人对战**：两块工牌通过 ESP-NOW 直连，不需要路由器、配网或手机。

| 文件 | 用途 | 地址 |
|---|---|---|
| nabo-adventure-v0.3.0-full.bin | 首次完整安装，重置设置和成绩 | 0x0 |
| nabo-adventure-v0.3.0-app.bin | 已是新分区布局的工牌：保留存档升级 | 0x10000 |
| nabo-adventure-v0.3.0.zip | 镜像、分区表、两种升级工具、说明、许可与校验和 | 解压后选择 |

应用 SHA256：`91b850dd1654c456d9ccd609e7a09017274bdba5fa395f51d9604a4c26970827`（2,267,040 B），与两块工牌双机实测的应用逐字节相同，发布时没有重新编译。

**v0.3.0 应用比旧 2MB 应用分区大。** 只能装在 factory 为 0x3f0000 的新布局上（v0.2.0 完整镜像装出的就是这个布局）。旧布局（2MB 应用 + 6MB 资源）请看下面第三种方式。

## 一、首次完整安装

在 AI Passport 网页刷机工具里选本地固件，用 **full.bin，从 0x0 写入**。启动器和分区表与 v0.1.0/v0.2.0 公开文件逐字节相同，NVS/PHY 空洞全为 FF，不含任何设备存档。**会重置设置和成绩。**

## 二、新布局上保留存档升级（v0.2.0 完整安装过的工牌）

工牌退出游戏并保持唤醒，连接数据线，在解压目录里：

```powershell
python -m pip install esptool==5.5.0
python -m esptool --port COM口 read-mac
python tools/flash_candidate.py --mode upgrade --no-backup --port COM口 --expected-mac aa:bb:cc:dd:ee:ff --app nabo-adventure-v0.3.0-app.bin --sha256 91b850dd1654c456d9ccd609e7a09017274bdba5fa395f51d9604a4c26970827
```

工具核对芯片、8MB、MAC 和分区布局后只写应用并逐字节读回；旧 2MB 布局会被拒绝（装不下），这时改用第三种方式。

## 三、旧布局切换到新布局并保留存档

适用于从 v0.1.0 起一直只升级应用、还是旧 2MB 布局的工牌。工具先整片备份 8MB（大小不对就停下），再只写 0x8000 分区表和 0x10000 应用；**不写启动器，不碰 0x9000 的 NVS**，设置和成绩保留：

```powershell
python tools/install_keep_saves.py --port COM口 --expected-mac aa:bb:cc:dd:ee:ff --app nabo-adventure-v0.3.0-app.bin --sha256 91b850dd1654c456d9ccd609e7a09017274bdba5fa395f51d9604a4c26970827 --partition-table partition-table.bin
```

备份存在 `private/device/`，不要上传。万一开不了机：`python -m esptool --port COM口 write-flash 0x0 备份文件.bin` 原样恢复。旧 assets 区会被新应用覆盖；以后换回小智等其他 NABO 固件，请整片重刷那个固件。

## 怎么对战

护照亭 → **双人对战** → 选游戏 → 大厅。两块都进大厅就能互相看到（显示 NABO-xxxx）；一方按 OK 邀请，另一方 OK 接受，倒数 3 秒同时开始。只有一块时可以选“和 NABO 练习”。具体按键见 ZIP 内 `GAME_CONTROLS.md`。

## 验证范围（预览版）

宿主 322 项检查通过。两块工牌实测：跳一跳 5 局双方比分全部一致、零丢包、中途退出 0.1 秒内被识别、开关对战 10 次内存零漂移，并已真人对玩；八款自动对战中跳一跳、深潜、小火车、萤火虫、登山、滑雪、热气球七款双方结果一致。**火箭登月对战还没有真机测过**，横屏六款的真人对战手感、对局中睡醒、空白工牌从 0x0 完整安装本镜像也未验收。详见 `VALIDATION.json`。

下载后按 `SHA256SUMS.txt` 校验，ZIP 内部按 `contents.sha256` 校验。源码 MIT，NABO 形象/美术权利另行保留，第三方许可随 ZIP 附带。本项目与 FoloToy 官方无隶属或背书关系。
