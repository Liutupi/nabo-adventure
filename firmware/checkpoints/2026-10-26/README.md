# 2026-10-26 睡前检查点

这不是正式发行。只收录从已冻结目录原样复制的app，未重新构建；不含NVS、整片备份、旧资源或凭据。

| 文件 | 用途 |
|---|---|
| `nabo-adventure-night-99e71e9f.bin` | 已由用户确认夜林按住左右不误退、中键长按暂停、双短点上返回的玩法回退点；旧开机设计，99镜像睡醒未重测 |
| `nabo-adventure-boot-v3-82efd1ef-candidate.bin` | 当前工牌的新Grok开机候选；225项宿主检查、保护回读、10轮封面生命周期和76,800像素核对通过；实测约9.84fps，仍低于12fps目标，实体观感/新镜像睡醒/整套游戏回归待验 |

使用`manifest.json`/`SHA256SUMS.txt`核对文件，重枚举实际工牌和MAC，再用`firmware/tools/flash_candidate.py --app <所选bin> --sha256 <完整SHA> --mode upgrade --port <实际端口> --expected-mac <实际MAC>`做保护式升级。**只写0x10000的app；不能刷0x0、合并镜像、分区表、旧资源或执行erase。**不能用本次新构建替换回退点的精确文件。

当前静音设置保存在用户工牌NVS中，二进制不携带设置或成绩。升级须保留NVS。完整进度和次日顺序见[交接本](../../../docs/HANDOFF.md)。
