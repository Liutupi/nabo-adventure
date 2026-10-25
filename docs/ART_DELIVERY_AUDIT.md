# 六游戏美术交付独立审计

核对日期：2026-10-25。依据 `AGENTS.md`、`game-art/adventure/CODEX_PROMPTS.md` 第6–11轮、`ART_BRIEF.md` 3.0/3.2/6–8节、`GAMES.md` 第1–6节，以及六包实际清单、PNG、rig、来源记录和交付文档。

**结论：未发现动作/皮肤/静态清单的必需项缺件。** 共64个人物动作、398张人物正式帧及对应398张高色master、6个动态道具动作30帧、77个静态引用。运行动画/静态合计505个逻辑帧引用、499个不同PNG路径；复用雪块和静态/动画共用车轮未重复声称独立制作。NIGHT/SKY集中预览及hitbox空间说明已补齐。此结论只表示美术交付覆盖；**六个新游戏正式玩法仍未完成，用户美术/设备验收及最新编码预算均未因此通过。**

## 当前清单身份

| 包 | SHA256 | 人物动作/帧 | 动态道具动作/帧 | 静态引用 |
| --- | --- | ---: | ---: | ---: |
| POST | `42464721aae43aa0c7dc2aba7b55b4f6b4966f8ef61b2ecc23bcbce5a764636f` | 8 / 50 | 2 / 10 | 22 |
| NIGHT | `d9d5b35ec4702fa5fd739b5224d1d5c0b933b72c5d272ade1f9c3a8e6679a0bb` | 14 / 84 | 1 / 4 | 10 |
| CLIMB | `d2eecac332e1f45e02bdba1591f5ef1474562cbc11978a7cf2c49b94e8cc3b71` | 16 / 100 | 0 / 0 | 13 |
| SKI | `ce917671979911b3aa2d645ab99a30bd605677497a4cb5e13649a51ab35c84fb` | 9 / 56 | 0 / 0 | 12 |
| SKY | `abfbc0ffd9e3e97e61295911ea5c65b3c65f988bcc2af9021247590b07b3ee98` | 8 / 50 | 3 / 16 | 11 |
| SPACE | `168d04124ab06e8d7e181a41c51e3eec91ba3e9f7dd5911fa8690a25e96fe789` | 9 / 58 | 0 / 0 | 9 |

路径均为 `game-art/adventure/art/<id>-manifest.json`。本轮未改这六份清单、正式/运行PNG、rig或生成工具。

提交前核对1168个主集合独立文件（13清单/音频、794PNG共804引用、11个PROOF、350正式C/H）的Git索引与工作树原字节一致；扩展125个JSON中的1616个当前SHA绑定文件也一致。10条旧SHA保留历史制作记录，不冒充当前源码：旧boot尝试4条、产图时UI布局4条、SKI当时POST工具2条。艺术脚本与源文件按字节保存；当前生产证明以最新包工具/生成C哈希及候选冻结源为准。

## 动作、皮肤与静态逐项覆盖

| 包 | A必需动作（实际帧数） | B实际范围 | 场景/动态道具覆盖 |
| --- | --- | --- | --- |
| POST | idle/whistle/throw/hit/delivered各6；全身settlement_cheer8 | idle6、delivered6，均40px半身 | 96×88火车头/前景、车轮4循环、汽笛绳6；车厢、六色信封、32×32铁轨/枕木/直轨、岔口、单白可染色站台、羊、牛、煤堆、远山齐全 |
| NIGHT | 坐姿idle8、左右挪各4、抓6、举罐6、哈欠6、结算cheer8 | 同A全套，超过第二款轻量最低范围 | 草4、树影4均32×32；飞蛾4帧16×16；空罐19×37、独立发光mask32×32齐全 |
| CLIMB | 左/右各idle6、换边6、蓄力4、跳6、滑落6、登顶8；正面结算8 | 左右idle各6、结算8；其它动作显式继承A | 灰/冷/雪三组岩壁各2块32×32；普通/碎裂/结冰岩点、落石、水壶；2件共享雪图引用齐全 |
| SKI | 直滑6、左/右倾各4、跳6、摔倒8、终点6、结算8 | 直滑6、结算8；其余用A | 两块独立雪板、杖、大小松树、红蓝旗门、雪包、可可屋、终点拱门；4件冻结雪素材引用齐全 |
| SKY | idle/heat/vent/hit各6、接邮票4、全身结算8 | idle6、结算8；其它明确用A | 独立96×96球体、吊篮前64×28/后64×10、燃烧器、云4块32×32、雷云、邮票；鸟4帧24×20、heat/vent绳层各6及idle绳齐全 |
| SPACE | idle6、喷气4、着陆6、硬着陆8、插旗8、结算8 | idle6、喷气4、结算8；其余明确继承A | 着陆器back/front各96×96、着陆台96×24、月面3块32×32、燃料罐、小行星、独立旗；主/侧喷口、脚底接触点及旗携带/触地/释放合同齐全 |

POST B无72px结算不列为缺件：第6轮明确“post_b只做车窗待机和送达欢呼”，另做72px全身结算限定post_a；ART_BRIEF3.2最后一条也规定游戏另做的72px结算穿第一款。其它轻量B不能被描述为已制作全部A动作的第二套服装。

全部白NABO帽保留。POST列车员、SKY飞行主题采用衣服/围巾及配件表达，不能按旧字面提示替换身份白帽。SKI母版为斜后上方身体、共用独立3/4头回望，护目镜位于帽侧/眉上；SPACE透明罩不遮盖原白帽、脸和镜框。来源母版/prompt/生成记录、原像素SVG部件与rig均存在；未逐帧调用模型。

## 实际PNG尺寸与颜色复核

已实际打开并核对全部398张正式人物PNG、398张master、428张运行动画PNG和77个静态引用：SHA、数组长度、画布与清单一致；正式人物均256×256 RGBA，源根点为全身(128,224)、半身(128,160)。正式/运行人物每动画合并≤64 RGBA色（含透明），运行alpha为0/255；静态均符合各自色限，最高10 RGBA色。masters保留高色，不能把量化后素材称作原RGB无损。

| 包 | 实际runtime画布 | 实际runtime锚 | 尺寸说明 |
| --- | --- | --- | --- |
| POST | 半身36×40；A结算49×72 | (22,40)；(27,72) | 半身alpha高40；结算逐姿态占70–71，固定72画布 |
| NIGHT | 56组A54×56/B53×56；72组A56×72/B52×72 | 56组(20,56)；72组A(23,72)/B(21,72) | 抓/举倾身后alpha高52–56，仍同组固定裁切 |
| CLIMB | 60组60×65；72组72×78 | (30,62)；(36,75) | 60px是固定身体参考采样比例；动作alpha实际60–62，额外画布为包络，非逐帧改身高 |
| SKI | 56组63×68；72组45×72 | (32,60)；(30,72) | 56/208本体比例；雪板/杖使中立alpha高62，倒地约38；不能将68解释为本体高 |
| SKY | 半身43×40；结算51×72 | (22,40)；(27,72) | 实际半身alpha高40、结算72 |
| SPACE | 56组57×57；72组73×73 | (29,56)；(37,72) | 罩内本体/球罩alpha高56/72，1px固定余量 |

CLIMB两件与SKI四件共享雪引用逐项匹配冻结`shared-static-manifest.json`的原路径/SHA；没有复制改画另一个版本。尺寸比较使用实际PNG，不拿放大联系表代替目标尺寸。

## 文档、可审阅入口与已补证据

六包都有独立manifest、服装来源/生成记录、rig/原像素SVG、制作脚本、QA或README、动作联系表/GIF及生产C记录。POST驾驶窗/固定绳端、CLIMB手脚岩点、SKI V2倾倒触雪、SPACE旗触地释放等修正均有失败与修后证据，不能沿用旧版失败图说明当前成品。

- POST：[README/QA](../game-art/adventure/art/preview/post/README.md)、`train-composition-contact.png`、`whistle-cab-contact.png`、`props-contact.png`。
- NIGHT：[集中入口](../game-art/adventure/art/preview/night/DELIVERY_REVIEW.md)、原`QA.md`与`all-actions-overview.png`。
- CLIMB：[README/review](../game-art/adventure/art/preview/climb/README.md)、`overview-1x.png`、`static-contact.png`。
- SKI：[README/QA](../game-art/adventure/art/preview/ski/README.md)、`fall-v2-slope-all8.png`、`props-contact.png`。
- SKY：[集中入口](../game-art/adventure/art/preview/sky/DELIVERY_REVIEW.md)、原`QA.md`及绳端连续场景。
- SPACE：[README/review](../game-art/adventure/art/preview/space/README.md)、`overview-1x.png`、`static-contact.png`、`flag-ground-contact.png`。

本次独立实看了上述六包代表组合、NIGHT/SKY全部动作总表，以及POST/CLIMB/SKI/SPACE静态表。发现NIGHT/SKY缺集中静态/动态道具入口后，按追加授权补齐以下原尺寸预览并逐张查看；不把代表图检查冒充每段连续播放或用户审美验收：

| 路径（相对 `game-art/adventure/art/preview/`） | 实际尺寸/覆盖 |
| --- | --- |
| `night/delivery-static-dynamic-1x.png` | 640×448，10静态+4飞蛾，原像素1× |
| `sky/delivery-static-dynamic-1x.png` | 960×720，11静态+4鸟+heat/vent绳各6，原像素1× |
| 两包各`delivery-scenes-1x.png` | 各960×344，四幅240×320，额外24px仅图外标签 |
| 两包各`delivery-scene-00/01/02/03-1x.png` | 单张各240×320 |

NIGHT使用当前WORLD[4] RGB(24,48,60)，SKY使用WORLD[7] RGB(140,200,250)。NIGHT只alpha拼接既有草/树影/飞蛾/罐层/人物；SKY从现有热绳、放气绳、接邮票场景裁出完整240×320像素并保留B场景，没有重画/缩放源。两包710个源文件、清单、rig、母版及相关原脚本前后全SHA相同，16个新增交付文件重复构建字节一致。公开摘要在各`delivery-evidence-qa.json`；私有复现脚本/全量锁定与复现证明保留于`private/art-delivery-audit/`。

原`hitbox`存在源256 LTRB与runtime XYWH两种空间，已新增[HITBOX_CONVENTIONS.md](../game-art/adventure/art/HITBOX_CONVENTIONS.md)逐包定义单位、右下边界、crop/scale/anchor来源和可执行转换；不改冻结清单消除误读。框仍是制作参考；正式碰撞须按最终runtime-alpha、道具几何与玩法重新定，不可跨空间直接消费原值。

## 最新编码证明与剩余范围

- 独立库存审计结束后，root已用最终 `adv-row-rle-v2` 对全部六包重新执行生产C证明：POST82帧/4188行/69,264B、NIGHT98/5349/162,387B、CLIMB113/7072/110,730B、SKI68/4372/98,768B、SKY77/3438/52,304B、SPACE67/3954/65,912B，均低于260KiB。每包 `packing-validation.json` 已刷新，完整绑定11个工具/解码源码及生成C/头文件SHA；索引只接受当前报告，旧工具漂移的历史证据不再冒充最新验证。
- 共用UI/旅行服/静态包为299帧/13,780行+九宫格912行；全量索引362资源/804帧、42,153行通过。UI含开机演员/时间表159,625B/160KiB。完整宿主160项及IDF6.0.2构建通过，候选app1,533,920B且符合旧factory上限；**六包尚未嵌入这份共用候选**，最终正式玩法合包的ELF、运行内存/帧率仍需后续实现与设备验证。
- 六个正式玩法的原型、确定性轨迹、C实现、碰撞/状态机、皮肤解锁/继承、资源与成绩、场景滚动、附件生命周期和真实按键/声音/休眠验收仍属程序后续工作。本轮美术库存完整不代表正式玩法完成。
