# 交接本




## 2026-10-26 14:44 SPACE V2「月面跳跳」G0/G1 已交，等用户试玩

- 概念、键位、数值：`game-art/adventure/SPACE_V2_CONCEPT.md`；试玩页 `prototype/space_v2.html`。只用现有太空 A 款素材，不需要 Grok。主引擎改为点按，长按中键暂停与 NIGHT/SKI 一致。
- **用户认可前 Codex 不要动 SPACE 的 C、素材或 V1。**

## 2026-10-26 14:27 SKI V2「雪崩速降」已接入固件（云端，未上机）

- 用户 14:27 试玩后回复“可以”。V2 替换 V1，只用现有滑雪 A 款素材 + 程序画的跳台/冰面/雪崩，不需要 Grok。设计、键位、文件、验证边界：**`game-art/adventure/SKI_DESIGN.md`**。
- 外壳：NIGHT 与 SKI 统一为“V2 横屏手势”（`adv_model.c`/`adv_core.js` 的 `v2()`）：中键开始/继续、长按中键暂停、左键在暂停页重来、游戏中上键不回地图、暂停页双击上回地图。门槛 300/1000/2500。
- 云端：263 项宿主检查通过；app 1,619,744 B，预算 PASS，扣 352 KiB 后余 51,424 B。
- **Codex 下一步（Windows，可与 NIGHT 一起做）**：`build.ps1` 重建 → 保护式升级 → `tools/smoke_night.py` 与 `tools/smoke_late_games.py`（SKI 段已改成 V2 手势；SKY/SPACE 不变）→ 记录两款帧率与 heap → 交给用户实玩。帧率明显低于 25fps 先报告再优化，不擅自改玩法数值。
- 下一款按 REDESIGN_V2：SPACE → SKY → CLIMB，同样先 G0/G1 给用户试玩；现有素材能做好就不交 Grok。

## 2026-10-26 13:46 NIGHT V2 已接入固件（云端，未上机）——Codex 从这里接手

- 用户 13:45 认可 V2 试玩（“这个设计比之前的好多了”），13:46 决定**本款现有素材够用就不交 Grok 做视频**。所以 NIGHT 跳过 G2，直接接入；V1 已被替换（git 历史可回退）。
- 设计、键位、平衡、文件清单与验证边界：**`game-art/adventure/NIGHT_DESIGN.md`**。键位：左按住慢走、右按住小跑、中点按挥罐/满能量双击放光/长按暂停；**游戏中任何上键手势不回地图，暂停页双击上键回地图**（`docs/GAME_CONTROLS.md` 末节）。
- 素材：NIGHT 只用共用 `travel/walk_right|sad|cheer`；V1 坐姿精灵不再打包（命令见 `tools/ADVENTURE_ASSETS.md`）。门槛改为 100/300/800。
- 云端：263 项宿主检查通过；IDF6.0.2 构建 app 1,612,048 B（比 ddd1f50d 小约 48 KB），预算 PASS，扣 352 KiB 后余 59,120 B。云端 SHA 不可刷。
- **Codex 下一步（Windows）**：拉取 → `build.ps1` 重建 → 保护式升级 → `python tools/smoke_night.py --port … --app … --sha256 … --receipt …`（新版：真实中键挥罐打完一局，再 10 轮“进场/右键跑/左键慢/长按中暂停/冻结/继续/再暂停/双击上回地图”，并确认游戏中双击上不退出）→ 记录帧率（整屏重画 + 逐像素压暗，最需要关注）、heap → 交给用户实玩挥罐手感与黑暗可读性。帧率若明显低于 25fps，先报告再优化（可把压暗改成按行跨度批处理），不要擅自改玩法数值。
- 其余四款（SKI → SPACE → SKY → CLIMB）仍按 REDESIGN_V2 走 G0/G1；容量方案仍未定，需要 Grok 动作的款在 G2 前必须问用户。

## 2026-10-26 13:22 用户反馈：萤火虫起五款重做（V2），先读这里

用户实玩 ddd1f50d 后反馈：从萤火虫开始游戏性不足甚至无聊（对比深潜）；美术/UI 不行，人物动作僵硬像贴片人；需要左右操作的必须横屏；动作交给 Grok；对 Codex 要求提高。规划与质量门见 **[REDESIGN_V2.md](REDESIGN_V2.md)**，Grok 动作总表见 `game-art/adventure/art/grok-handoff/V2-ACTIONS.md`。

现在的状态：

- 工牌与固件不变：仍是下方记录的 ddd1f50d 候选，八款 V1 可玩、可回退。
- **待用户拍板（REDESIGN_V2 第 7 节）**：横屏游戏的返回/暂停手势；容量方案（V2 动作需要几百 KB，当前只余约 10 KB）；V2 顺序（建议 NIGHT 先做样板）；V1 去留。
- 拍板前不要继续改 V1 五款；可以做的只有：为 NIGHT V2 写 G0 概念和浏览器原型（占位美术），不刷机、不接 C。

## 2026-10-26 Windows 恢复：当前记录优先于下方历史

用户已明确“同步github,继续任务”，睡前停止已解除。已快进同步 `claude/climb-cloud` 的8个提交，最新云端来源 `6453dfc`；新增 CLIMB / SKI / SKY / SPACE 正式引擎、A款美术和规则对拍，不能再称这四款为占位。所有后续验证继续静音，保存的扬声器关闭与300秒休眠保持。

当前 Windows 候选 **`ddd1f50dfeb8eafd207292bdd27fc9de8d120713bee3fd65f03b69c04c444e9e`**，app **1,661,056 B**，真实 factory 2,031,616 B，扣永久352KiB后余 **10,112 B**。265项宿主检查/114.377秒、IDF6.0.2构建及预算通过；保护式app-only升级与全片保护字节回读通过。回执 `private/device/20261026-121641-168475-receipt.json`。精确bin保留在 `private/candidates/<完整SHA>/`，不得用重建覆盖。

开机原片、73帧、人物大小、全部采样像素及原WAV不变。按16行比较两份YCbCr引用图，只重画确有变化的行带；慢I帧后逐帧补交，不跨过未显示的动作。当前真机 **73帧全部提交、跳过0帧，末帧选择时钟6008ms，选择间隔约11.984fps**；短窗普通draw计数约17.20fps含重复/无像素更新，不再用它冒充动作帧率。这里的末帧时间是合成前选择时钟，**不是光学测得的屏幕帧率**。正常封面10次进出稳定：封面heap92,768/largest36,864，地图heap267,528/largest114,688。设置页睡醒已由用户确认，新开机外观仍待用户验收。

**八游戏自动检查已通过。** 旧四游戏整局/各10轮加暖机/POST练习通过；静音后CLIMB到50米、自然结束、10轮加暖机、暂停冻结与返回通过；SKI/SKY/SPACE各10轮加暖机、移动不误退、暂停冻结、自然结束通过。SPACE串口自然坠落至燃料耗尽，成功着陆/插旗仍须实体验证。静音后POST短窗中位26.170fps、NIGHT28.443fps；新增三款各一个初始3秒窗口31.75/42.34/56.41fps，不代表最满场景。最终24,576B NVS与新静音基线逐字节一致，真实132/5888/POST8/NIGHT51和22枚章保留。新开机实际合成截图76,800像素与生产末帧逐像素相同。

**设置页30秒睡醒通过：用户随后明确确认“约30秒熄屏，上键能恢复”。** 180秒自动观察窗曾只见USB离线，原报告保持不改；用户确认与后续串口证据单独记录。唤醒后USB恢复同一工牌，正常保存模式test=0、owner=0，原成绩和22枚章不变，已见正常地图。保存的300秒及speaker=0已在睡前读回；用户醒后正在自由切页，因此没有再次复位或读NVS打断操作。游戏进行中的休眠未逐款复测。新开机观感与新四款实体手感/读图仍待用户，不称全M4或正式发布。B选择与容量方案、SKI/SKY/SPACE可玩浏览器页面、八金章回家与地图硬件滚动未完成。各关独立A款已接入，B源素材保留而默认不嵌入bin。精确候选和SHA在`firmware/checkpoints/2026-10-26-windows/`，此前99和82检查点保留。

源码、精确候选与记录已推送main/开发分支，检查点标签`checkpoint-2026-10-26-windows`绑定`8d2b9d2`；已从GitHub重新下载bin、交接本与验证JSON逐字节核对。睡眠观测及操作速查另以文档续记提交；原候选bin不重建。现由用户自由试玩新四款，优先核对CLIMB点按/蓄力与读图；按键速查见`GAME_CONTROLS.md`。自动按键已全部结束，不打断真人对局；以后续测先核对当前页面、最新进度和实际静音状态。

**静音核对纠正：** 本次首次升级前NVS实际为speaker=1，与睡前speaker=0不同；开测前错误依赖旧记录，首轮旧四游戏检查不能称“静音验收”。12:28已通过正常设置关闭扬声器，并读回/重启确认speaker=0、sleep=300；除speaker外全部用户设置及成绩键与升级前一致。新静音基线为`private/quiet-baseline-ddd1f50d.json/.bin`，SHA256 `1969121c5fb0c91fbc188fd9ef18ddb747ef9de0e9e1e3aebb975d7670f16280`。后续NVS应与此新基线比，不能把主动静音当存档损坏，更不能恢复旧speaker=1备份。CLIMB曾测试到50米后为纠正静音而中断，未写入真实11米；恢复正常模式后已从静音基线重新测试。以后必须读回实际设置再开测，不只信历史交接。

验证入口：`private/tests-boot-no-skip.log`、`private/build-boot-no-skip.log`、`private/probe-boot-no-skip.log`、`private/device-suite-ddd1f50d-run.log`、`private/climb-smoke-ddd1f50d-muted.log`、`private/late-games-ddd1f50d-muted.log`。CLIMB首次脚本入口失败已恢复正常模式；原因是模式切换后的吞键位未通过原始按下/松开清除，已补齐三键边沿后再测。新增 `tools/smoke_late_games.py` 验证三款生命周期/自然结束；`double_down` 串口键已补齐以验证SPACE暂停，测试工具也必须在正常封面/地图、无真人对局时才接管。串口测试不能代替实体按键、读图、配色与手感。

补充：八游戏的Windows渲染编译改GCC参数文件，避免WinError206。三个字库在Windows重新生成，C文件逐字节一致。C资产证明已按新解码器重新核验，594份生产C/H字节不变；冻结目录旧报告保留，更新后的报告在生产generated与 `private/asset-proof-boot-no-skip/`，不需要为报告更新重建bin。

## 2026-10-26 云端续作（二）：SKI / SKY / SPACE 正式玩法，八站全部有正式游戏（未上机）

用户随后要求“把还没做完的游戏一起做了”。同一分支 `claude/climb-cloud` 上继续，**仍然没有刷写、没有任何真机结果**。

| 项目 | 结果 |
|---|---|
| 规则 | [LATE_GAMES_DESIGN.md](../game-art/adventure/LATE_GAMES_DESIGN.md)；三款各自 JS 原型、只看屏幕的平衡策略、JS/C 逐步对拍与规则变异 |
| 按键 | 上键要按住移动的 NIGHT/SKI/SPACE 只认两次短点上回地图；暂停：NIGHT 长按下、SKI 长按 OK、SPACE 两次短点下、其余长按上。外壳轨迹 `late_games` 用真实按键把三款各打到铜章，并验证“长按移动 + 一次短点”不触发双击 |
| 画面 | 三款竖屏正式 A 款动作与道具；42 张生产 C 截图；SPACE 着陆器不能旋转，横向改为侧推 |
| 容量 | **B 款（银章第二套服装）素材留在仓库，默认不打包**（`--include-b-skins` 才打包），省 77 KB；IDF 组件改 `-Os` + 断言不带文字（main 仍 -O2）。app 1,660,192 B，扣 352 KiB 保留额后余 10,976 B |
| 门禁 | 263 项宿主测试通过；既有页面逐像素不变；云端构建 + 预算检查 PASS |

需要用户决定：B 款换装系统真正实现时，八款的 B 款共约 118 KB，按现在余量装不下，只能动用保留额、继续找无损空间，或只给部分游戏做 B 款。

上机顺序同下方 CLIMB 段：Windows 重建 → inspect/upgrade → 四款旧游戏回归（精灵格式、编译参数都变了）→ 逐款实玩 CLIMB/SKI/SKY/SPACE（手感、帧率、10 轮进出、睡醒）。`>adv.open=ski|sky|space` 测试模式直达；三款还没有串口冒烟脚本。

## 2026-10-26 云端续作：登山 CLIMB 正式玩法（分支 `claude/climb-cloud`，未上机）

用户在睡前封存后明确要求“继续在云端优化”。云端没有工牌，所以先做不依赖实体的部分：**CLIMB 正式玩法 M0–M3 + 两项无损容量优化**。开机帧率收尾和四游戏真机回归仍需工牌，顺序上留给下次有设备时。工牌上仍是 82efd1ef，本分支**没有刷写、没有任何真机结果**。

| 项目 | 结果 |
|---|---|
| 规则 | [CLIMB_DESIGN.md](../game-art/adventure/CLIMB_DESIGN.md)；点 OK 换边上 1 米，按住 OK 蓄力松开同侧跳 2/3 米；碎石/结冰/落石/水壶；可达性保证与 0–4 米新手阶梯 |
| 原型 | `prototype/adv_climb.js` + 可玩 `climb.html`（无头 Chromium 实际按键试过） |
| 平衡 | `node tests/climb_policy.js`，200 种子：盲点/盲跳拿不到铜；熟练约 70% 银、约 7% 金 |
| C 对拍 | `adv_climb.c` 与 JS 7 条轨迹逐步一致（含金章 306 米、冰面、碎石、落石、重开）；外壳 `climb_round` 轨迹；12 项边界 + 6 个规则变异 |
| 画面 | `adv_ui_climb.c` 竖屏、镜头锁手、正式 A 款动作；16 张生产 C 截图 `docs/images/ui/climb-*.png`；增量 = 整屏、无溢出 |
| 容量 | 精灵行表 uint16（-37,232 B）+ 相同帧只存一次 adv-row-rle-v4（-40,064 B），全部旧页面逐像素不变；接入 CLIMB 后 app 1,629,088 B，**扣 352 KiB 保留额后余 42,080 B** |
| 字库 | 三个 collection 字库新增 25 字；12 px 源字体哈希与记录一致，16/18 px 用 Google Fonts 2022 `NotoSansSC-Bold.otf`，先证明它对原 306 字逐字节重现旧文件 |
| 门禁 | 241 项宿主测试通过；云端 IDF 6.0.2 构建 + `check_adventure_budget.py` PASS |

**云端构建不等于 Windows 构建**：组件注册表在云端不可达，五个托管组件按锁定版本从 GitHub 取源码，`IDF_COMPONENT_MANAGER=0` 构建；基线 82efd1ef 源码在云端构建出的 app 大小与清单完全相同（1,592,848 B），SHA256 因构建路径不同而不同。**要上机必须在 Windows 用 `build.ps1` 重新构建并按原流程 inspect → upgrade**，不要拿云端二进制刷写。

下次有工牌时：

1. Windows 取回本分支（或合并后的 main），`python tools/run_tests.py` 与 `build.ps1`；确认 app 余量与本节一致量级。
2. 保护式升级后先跑既有四游戏回归（新精灵格式影响全部画面解码：宿主已逐像素证明，真机仍要看）；再 `python tools/smoke_climb.py`（云端写成，**从未运行**，先读代码再用）。
3. 用户实玩 CLIMB：点按/蓄力 12 帧界线的手感、帧率（整屏滚动，没有用 ST7789 硬件滚动）、落石可读性、10 轮进出与睡醒。
4. 之后回到上次封存的开机 12fps 收尾和 SKI → SKY → SPACE。B 款（红色冲锋衣）素材已随包嵌入但未接线。

## 2026-10-26 睡前封存：下次先读

用户要求固定目前成果、上传GitHub并写好交接本后停工。今晚不继续开发、不安排自动续跑、不再请用户操作工牌；等用户明确“继续”再恢复。

**2026-10-26 睡前封存，停止新增开发。** 当前工牌为`82efd1efdda558a598fa0058e8f9e419eb571d761856e9c98c96b9a05ba5f236`：app1,592,848B，225项/101.481秒宿主检查和构建通过；app-only升级、全片保护回读、正常模式10次封面进出、76,800像素合成截图及24,576B NVS一致性通过。NIGHT51分、22枚章保留，扬声器关闭，保存的休眠仍300秒。**开机短窗实测约9.84fps，未达到12fps目标；新封面实体观感、本镜像睡醒及整套四游戏真机回归未完成，不得写成全验收。** 已另外原样收录99e71e9f玩法回退点。二进制和SHA清单位于`firmware/checkpoints/2026-10-26/`，机器记录见`validation/v0.1.0-boot-v3-82efd1ef.json`。Git检查点为`checkpoint-2026-10-26`，开发分支`codex/adventure-device-smoke`；本次上传采用非强制快进方式更新main。

| 已确定 | 边界 |
|---|---|
| 跳一跳/深潜/POST | 既有正式玩法；POST5a精确镜像曾整局/按键/声音/30秒睡醒通过 |
| NIGHT99e71e9f |211项检查、完整静音自动套件、用户按住移动/中键暂停/两短点上返回均通过；99自己的睡醒未重测 |
| 当前BOOT-V3-01/82efd1ef | Grok原片已接入，225项检查和有限真机检查通过；9.84fps仍低于12，外观/睡醒/整套四游戏回归待验 |
| 其余内容 | CLIMB/SKI/SKY/SPACE仍占位；银章B款切换未接，不能说游戏全做完 |

下次按此顺序：

1. 先核对设备、当前app和正常模式/新成绩；继续保留静音，不擅自打开扬声器。
2. 收尾开机流畅度。初版11171578约6.11fps，行缓存baf301f1约8.25fps，当前双缓冲82efd1ef约9.84fps；源图、动作、73帧和采样像素不变。可评估只解码动态上部/人物、下部字标静态绘制以减少CPU，但必须先测容量与画质，不能直接删帧或缩小NABO。80MHz屏时钟和板级引脚未改。
3. 完成新候选的四游戏各10轮、NVS新基线比对，用户有空后再做新封面观感与可见30秒睡醒；当前没有这些验收结果。中途若用户玩出新纪录，另取新基线，不能恢复旧51分/旧章备份。
4. 开机收尾后，按CLIMB→SKI→SKY→SPACE开发正式玩法及B选择系统。服装/界面已选，不要重问；不委派新的Grok片段。

恢复用本次收录的精确app，不重建已验收文件。两份bin均为app-only，禁止刷合并镜像或改旧6MB资源区。最新私有回执`private/device/20261026-004856-227976-receipt.json`；原始备份、NVS和日志只在本机private。当前225项日志`private/tests-video-pipeline-full.log`，设备探针`private/boot-v3-device-probe.json`，NVS比对`private/nvs-boot-v3-82efd1ef-handoff.json`。静音宿主GIF是12fps目标示意，不能当作实机9.84fps的录像。


以下保留初始交接与开发过程；状态以最上方2026-10-26睡前封存为准。

初始更新：2026-10-25 · 固件 v0.1.0（骨架）· 提交见 `git log`

**Mac 精灵管线历史增量见第 9 节。** Windows 接手已同步最新界面设计要求，并将构建配置版本统一为 `0.1.0`；设备验证及美术各轮进展将在后续章节记录。镜像仍须以 SHA256 识别。

## 1. 现在是什么状态

**2026-10-26 睡前封存，停止新增开发。** 当前工牌为`82efd1efdda558a598fa0058e8f9e419eb571d761856e9c98c96b9a05ba5f236`：app1,592,848B，225项/101.481秒宿主检查和构建通过；app-only升级、全片保护回读、正常模式10次封面进出、76,800像素合成截图及24,576B NVS一致性通过。NIGHT51分、22枚章保留，扬声器关闭，保存的休眠仍300秒。**开机短窗实测约9.84fps，未达到12fps目标；新封面实体观感、本镜像睡醒及整套四游戏真机回归未完成，不得写成全验收。** 已另外原样收录99e71e9f玩法回退点。二进制和SHA清单位于`firmware/checkpoints/2026-10-26/`，机器记录见`validation/v0.1.0-boot-v3-82efd1ef.json`。Git检查点为`checkpoint-2026-10-26`，开发分支`codex/adventure-device-smoke`；本次上传采用非强制快进方式更新main。

《NABO 的冒险之旅》合集的**骨架、11轮美术和共用界面已交付，正在逐款开发正式游戏**。最新程序状态见 `DEVELOPMENT_PROGRESS.md`，镜像和实测边界见 `VALIDATION.md`。

**99e71e9f已验收玩法基线：NIGHT正式横屏玩法、自动回归和用户按键验收通过；本镜像休眠尚未重测。** 211项/95.627秒宿主检查通过，app1,655,184B，真实factory余376,432B，扣352KiB保留额后余15,984B。横拿后三键朝下：按住左OK/右UP连续移动，中DOWN短点举罐、长按暂停；只有两次短点UP回地图，移动按压不计入退出。完整自动套件在静音下通过，NIGHT/POST及两款旧游戏各10轮加暖机，地图heap255,316和largest114,688稳定；24,576字节NVS与关闭扬声器后的新基线相同。用户确认移动不误退、长按中键暂停及双击返回都正常。最新真实进度132/5888/POST8/NIGHT51，22枚章；不得覆盖为早期纪录。扬声器按用户要求保持关闭，未做本轮听感验收。

Grok的BOOT-V3-01已接入当前82efd1ef，性能及验收边界见最上方封存段。99玩法回退点和旧5a验收镜像均原样保留。B换装及CLIMB/SKI/SKY/SPACE正式玩法待开发。

- 合集外壳完整：封面 → 竖向地图（9 个站点）→ 护照亭 / 护照 / 设置 → 盖章仪式 → 统一的游戏流程（标题、倒数、进行中、暂停、结束、结算）。
- 跳一跳、深潜是现成游戏，从地图进出，最佳成绩回传给外壳算印章。
- 小火车POST正式规则/美术已接入并验收；NIGHT正式横屏追光和睡衣A款已接入，99e71e9f自动回归及用户按键实测通过。登山、滑雪、热气球、太空仍跑**占位游戏**。
- 共用页面已接入选定旅行服、地图/印章和复古护照美术。用户已对557607…镜像的加粗字体、新欢迎演出和30秒睡醒确认通过，原样冻结的已验收bin保留；新增玩法候选仍须各自实测。

## 2. 先读这些

| 文件 | 内容 |
|---|---|
| `AGENTS.md` | 维护约定（必须遵守） |
| `GAME_CONTROLS.md` / `COSTUME_INTEGRATION.md` | 用户最新统一返回操作与各关独立服装要求；素材/已接入/待接线边界 |
| `game-art/adventure/DESIGN.md` | 已实现的规则：站点、按键、印章、一局流程、游戏接口、存档、串口命令 |
| `game-art/adventure/GAMES.md` | 6 个新游戏的玩法和起始参数 |
| `game-art/adventure/UI_DESIGN.md` | 配色、字体、每个画面（截图由生产代码渲染）；第 7 节是界面视觉设计要求 |
| `game-art/adventure/ART_BRIEF.md` / `CODEX_PROMPTS.md` | 美术规格 / 按轮次的提示词 |
| `game-art/adventure/BUDGET.md` | Flash、内存预算 |
| nabo-passport-game skill | NABO 小游戏的通用流程（M0–M4、发布） |

## 3. 文件职责

| 文件 | 职责 |
|---|---|
| `game-art/adventure/prototype/adv_core.js` | **规则的标准答案**：外壳模型、占位游戏、设置子模型、mulberry32 |
| `game-art/adventure/prototype/index.html` + `adv_draw.js` | 浏览器原型（键盘 ↑ ↓ Enter；画面按固件版式画） |
| `tests/adv_golden/record_golden.js` | 用原型录对拍轨迹（`node tests/adv_golden/record_golden.js`） |
| `firmware/main/adv_model.c/.h` | 外壳状态机（无屏幕、声音、RTOS 依赖） |
| `firmware/main/adv_game.h` | 外壳 ↔ 游戏的接口 |
| `firmware/main/adv_stations.c/.h` | 9 个站点：名字、世界、门槛、占位标记、颜色、路径顺序 |
| `firmware/main/adv_demo.c/.h` | 占位游戏 |
| `firmware/main/adv_rng.h` | mulberry32（与原型一致） |
| `firmware/main/adv_gfx.c/.h`、`adv_shapes.c`、`adv_text.c/.h` | 直绘渲染器：显示列表 + 脏矩形 + 8 行条带（从牌桌渲染器分出来，去掉了牌、骰子、杯子） |
| `firmware/main/adv_sprite.c/.h` | Flash 精灵逐行 RLE 解码、关键帧 + 最多 7 个差分帧，供 `AG_SPRITE` 使用 |
| `tools/generate_adv_sprites.py` / `docs/SPRITES.md` | 最终尺寸 PNG → 共享 64 色 → 行 RLE → C 数组；逐帧核对和接入说明 |
| `firmware/main/adv_ui.c` | 面板输出、通用部件、封面、护照亭、设置、状态、页面分发 |
| `firmware/main/adv_ui_map.c` | 地图、护照、盖章 |
| `firmware/main/adv_ui_session.c` | 游戏标题、资源条、倒数、暂停、结束、结算、占位游戏画面 |
| `firmware/main/adv_ui_jump.c` | 跳一跳画面（原样搬自《游戏特辑》） |
| `firmware/main/adv_sound.c/.h` | 提示音与POST持续鸣笛合成（三角波，无采样） |
| `firmware/main/adv_post.c/.h`、`adv_ui_post.c` | POST纯整数60Hz规则与正式原尺寸美术组合 |
| `game-art/adventure/prototype/adv_post.js`、`adv_post_draw.js`、`post.html` | POST标准规则、浏览器画面和可玩调参入口 |
| `tests/post_golden/`、`tests/test_adv_post.py` | POST 30,000步JS/C逐步对拍、规则边界和变异检查 |
| `tools/smoke_post.py` | 测试模式串口实玩、进出压力检查，确认恢复正常模式后才通过 |
| `firmware/main/adv_main.c` | 入口：按键队列、60 Hz 步进、NVS、音频、旧游戏进出、串口诊断、深睡 |
| `firmware/main/collection_model.c` | 设置 / 状态子模型（沿用） |
| `firmware/main/nabo_dive*`、`nabo_jump*` | 深潜、跳一跳（未改） |
| `firmware/tools/generate_collection_fonts.py` | 从 `adv_*.c` 收集中文，生成 12/16/18 号字库 |
| `firmware/tools/verify_firmware.py` | 检查合并镜像的布局 |
| `firmware/tools/flash_candidate.py` | 只写 app 的保护式刷写（核对身份、备份、校验） |
| `tests/test_adv_model.py` | 4 条对拍轨迹（约 1.4 万步）+ 7 个故意改坏规则的变异体 |
| `tests/test_adv_renderer.py` | 渲染每个画面到 `docs/images/ui/`；每次输入后增量帧 = 整屏重画；无溢出 |
| `game-art/dive/` | 深潜的美术、骨骼、渲染脚本、网页原型（原样保留） |
| `docs/nabo-games-v1.0.0/` | 底座《游戏特辑》v1.0.0 的发布、验证和来源记录（历史） |

## 4. 怎么跑

```sh
python3 -m pip install -r requirements-dev.txt    # Pillow
python3 tools/run_tests.py                         # 宿主测试，不碰设备（macOS 用 cc，Windows 用 gcc）
node tests/adv_golden/record_golden.js             # 改了 adv_core.js 后重录
./build.sh ~/esp-idf-v6.0.2                        # macOS / Linux；Windows 用 build.ps1
```

浏览器原型：在仓库根目录起一个静态服务器（`python3 -m http.server 8768`），打开 `http://localhost:8768/game-art/adventure/prototype/`。

刷写（只写 app，保留 NVS 和其他分区）：

```sh
python firmware/tools/flash_candidate.py --app firmware/build-idf6/nabo-adventure.bin --sha256 <SHA256> --mode inspect
python firmware/tools/flash_candidate.py --app firmware/build-idf6/nabo-adventure.bin --sha256 <SHA256> --mode upgrade --expected-mac <工牌 MAC>
```

**先 inspect 再 upgrade**，并用 `--expected-mac` 锁定设备：同一个 USB 口上可能接着别的板子（用户的 Tab5 就出现过）。

## 5. 验证状态（v0.1.0）

以下保留初次交接的历史状态，Windows 实测增量与绑定镜像见第 10 节。

| 项目 | 状态 |
|---|---|
| 宿主测试 64 项 | ✅ 全过（macOS，cc） |
| ESP-IDF 6.0.2 构建、合并镜像、布局检查 | ✅ app 1,158,976 B，SHA256 `ba99d31e…090e7`，分区剩 72% |
| 浏览器原型 | ✅ 能加载、按键响应、无控制台错误 |
| **真机** | ❌ **没刷过**。按键手感、声音、深潜和跳一跳进出、10 轮进出的内存、深睡唤醒都没验证 |

## 6. 初始交接待办（历史；当前以上方睡前封存为准）

| # | 任务 | 完成标准 |
|---|---|---|
| 1 | **基线真机冒烟已完成**，后续镜像另测 | Windows 候选 app `71cc1f6b…fdb32` 已保护式升级；页面、各十轮进出、三键、声音、临时 30 秒休眠和上键唤醒已查。后续新开机音画及 UI 镜像不得沿用此结果，见第 10 节 |
| 2 | 全部11轮美术技术交付完成；字体/欢迎V2a待新候选真机 | 用户已选旅行服v2①及界面①复古护照；六游戏独立C包、完整索引与跨人审阅已补齐。新版字体/欢迎经160项门禁，设备尚未升级，详见ART_PROGRESS/ART_DELIVERY_AUDIT |
| 3 | 精灵和界面管线已接正式共用包 | 行 RLE、runtime manifest/锚点/fps、32 色共享 UI、六套九宫格、大数字、真实 C 解码对拍与生产页面渲染通过；新候选设备验收见第 10 节 |
| 4 | 小火车 POST（M0–M4） | 原型里做出玩法、调参（`GAMES.md` 第 1 节）→ 录对拍 → `adv_post.c` + `draw` → H 横向模式 → 站点 3 `placeholder = false` |
| 5 | 地图硬件竖向滚动 | 走一站时镜头平滑滚动，60 fps（参考深潜 `nabo_dive_render.c`） |
| 6 | 服装系统 | 银章解锁第二款；标题页可切换；存 `adv_skin_<id>` |
| 7 | 其余 5 个游戏 | 萤火虫 → 登山 → 滑雪 → 热气球 → 太空，同第 4 项流程 |
| 8 | 结局 | 8 枚金章后太空站的“回家”（`GAMES.md` 第 7 节） |
| 9 | 可选：压缩跳一跳素材 | 见 `BUDGET.md` 第 3 节 |

## 7. 注意事项

- **不要把渲染代码放进 IRAM**：深潜试过，开机 abort 循环。
- C3 没有浮点单元：新代码一律整数 / 定点（深潜沿用的浮点代码不动）。
- 改规则一定先改 `adv_core.js`，重录轨迹，再改 C；`test_adv_model.py` 会逐步比对。
- 新增中文界面文字后重新生成字库（`firmware/tools/generate_collection_fonts.py`，需要 `lv_font_conv` 1.5.3 和 SourceHanSansCN-Medium.otf，SHA256 记在 `firmware/tools/collection-fonts.json`）。宿主测试会抓缺字。
- 脚本测试真机时先 `>adv.test=1`，否则会写入假成绩。
- 所有游戏两次短点上键回地图；NIGHT按住左右移动不计入退出，长按中DOWN暂停，其余游戏保留各自暂停操作。
- NABO 的帽标不能镜像，朝左、朝右动作各做一套。
- 不要提交 `private/`、设备备份、NVS、串口原始日志。
- 在 macOS 外接卷（非 APFS）上工作会产生 `._*` 文件，会弄坏 ESP-IDF 组件哈希和 `.git` 包索引：在 APFS 磁盘上构建，或者构建前 `find . -name '._*' -delete`。

## 8. 给 Codex 的开场白（可直接复制）

> 这是 NABO 的冒险之旅合集固件（ESP32-C3 AI Passport 工牌，独立离线版）。先读 `AGENTS.md`、`docs/HANDOFF.md`、`game-art/adventure/DESIGN.md`，并按 nabo-passport-game skill 的流程工作。现在的状态和待办在 HANDOFF 第 5、6 节。今天做待办第 __ 项。改规则先改 `game-art/adventure/prototype/adv_core.js` 并重录 `tests/adv_golden`；每次改完跑 `python3 tools/run_tests.py` 和 `./build.sh`，把结果（测试数、app 大小、SHA256）写回 HANDOFF。

## 9. 2026-10-25 Mac 接手：精灵管线基础支持（未真机验收）

### 范围和接手状态

- 独立克隆，基线 `9735f34f019116f21b806195fd90842cf2bb7a64`；初始 `main...origin/main` 干净。最近三次提交依次为 `9735f34`（交接与设计）、`fd91001`（冒险骨架）、`43d5497`（旧合集发布）。开发分支 `codex/sprite-pipeline`，具体提交用 `git log -1` 确认。
- 已读 `AGENTS.md`、本交接本、`README.md`、`docs/BUILD.md`、`docs/VALIDATION.md`、`DESIGN.md`、`ART_BRIEF.md`、`BUDGET.md`，并核对实际渲染、测试和构建代码。未修改其他 NABO 项目或本机 Codex memories。
- 仓库没有 `.agents/skills`；已检查本机通用 `passport-develop`、`passport-build`，其中 IDF 5.5.3 和目录约定不适用于本仓库。未找到文档所指的 `nabo-passport-game`，没有声称执行该技能；实际按本仓库 IDF 6.0.2、宿主门禁和维护约定推进。
- 第 1 项真机冒烟和第 2 项用户选造型仍待完成。此次明确授权先做第 3 项不依赖美术的编码、解码和渲染支持；不替换正式 NABO 美术、不推进整套六游戏。
- 初次交接回写时 Mac 环境断连，恢复后已核对：原 11 个改动完整，交接记录未写入，没有发现额外工作区改动。本节补齐该记录。用户后续授权提交到 GitHub 独立分支，未授权合并 main、强推、固件 release 或刷机。

### 完成内容

- `tools/generate_adv_sprites.py`：最终尺寸 RGBA PNG → 全动画共享最多 63 种不透明 RGB565 色 + 透明索引 0 → 逐行 RLE → C 数组和哈希报告。半透明要求显式背景色；关键帧与差分自适应选择，最多 7 个连续差分，打包后逐帧比较量化后的索引帧。
- `adv_sprite.c/.h`：随机访问逐行还原、元数据和坏流检查；`AG_SPRITE` 使用 256 字节栈上行缓冲和既有 DMA 条带，不分配整帧或堆，不使用浮点、IRAM 或镜像。
- 回归测试先复现、再修复重叠绘制操作换序时未标记脏区的问题。覆盖透明擦除、裁剪、移动、删除、素材切换和层叠顺序。
- 新增 10 项合成图测试和独立 ASan/UBSan 检查。CLI 测试使用当前 Python 的 `sys.executable`，避免 Windows 上没有 `python3` 别名时子进程失败；Windows 门禁尚未在该系统执行。
- 没有修改玩法规则，故原型与 golden 未动；没有增加界面文字或修改页面版式，字库未变，完整门禁重新生成的既有 UI 截图与基线一致。
- 管线格式、生成命令、C 接入方式和限制见 [SPRITES.md](SPRITES.md)。当前没有正式素材，固件不嵌入合成测试图；构建大小不包含未来美术数据。

### 实际验证与镜像身份

| 类别 | 结果 |
|---|---|
| 基线代码测试 | `python3 tools/run_tests.py`，64/64 通过 |
| 基线构建 | IDF 6.0.2 build / merge-bin / 布局检查通过；app 1,158,976 B；SHA256 `8194915a0eca8caa7cb8fdce59b5b662f8bb5563cc097442df38423ea7445bbc5` |
| 最终代码测试 | 完整宿主门禁 74/74 通过，既有 64 项 + 新增 10 项；宿主 C 用 `-Wall -Wextra -Werror` |
| 原生内存检查 | macOS Clang ASan + UBSan，已知关键帧/差分及 50,000 组确定性坏行流通过，退出码 0，无 sanitizer 报告 |
| 最终构建复核 | IDF 6.0.2 build / merge-bin / 布局检查 PASS；app 1,159,600 B（较基线 +624 B），分区 4,128,768 B，剩余 2,969,168 B |
| app SHA256 | `6318a43430a2eb55e8b0d842ff5b662f8bb5563cc097442df38423ea7445bbc5` |
| 合并镜像 | 1,225,136 B；SHA256 `6a179e4425d9979f1bf1d392172a7ee864162e545a2e0b6c142b562bff909b25` |
| 真机 | **未刷写、未验收**；按键、声音、10 轮进出内存、深睡唤醒、帧率和栈余量都未验证 |

以上是提交前 Mac 工作区构建的身份，不承诺其他路径、时间或编译环境重建得到相同 SHA256。镜像及匹配 ELF/MAP 保留在 Mac 的 `firmware/build-idf6/`；日志和完整哈希清单保留在忽略目录 `private/validation/`，不进入 Git。源码推送不包含固件、设备日志、NVS、备份或凭据，也不是正式固件发布。

### Windows 接手注意

1. Windows 会话继续主线；此分支基于 `9735f34`，取回后先比较当前主线差异。重点合并点为 `adv_gfx.c/.h`、`firmware/main/CMakeLists.txt` 和 `tests/test_adv_renderer.py`，不要覆盖 Windows 已有工作。
2. 新文件包括 `adv_sprite.c/.h`、打包器、`tests/test_adv_sprites.py` 和两个宿主 C 文件。已有测试只新增解码源文件；没有改站点、按键、音频、NVS 或分区。
3. 通过 `python tools/run_tests.py`（或可用的 `python3`）和仓库 `build.ps1` 重新验证 Windows 环境；依赖 Python 3、Pillow、Node 和可用的宿主 C/C++ 编译器。可选 sanitizer 指令记录的是 macOS 检查。
4. 输入 PNG 必须已在最终画布尺寸；总 manifest、骨骼输出缩放和锚点、帧率/循环调度尚未实现。获批美术到位后再接地图；合成图不代表正式美术批准或颜色质量验收。
5. 真机仍按第 6 节第 1 项执行，须有工牌和刷写授权。发布前还需统一文档/界面 `v0.1.0` 与继承的固件配置版本 `1.0.0`；本轮不改版本或发布固件。

## 10. Windows 主线继续：2026-10-25（进行中）

已克隆到 `D:\AI PASSPORT XIAOZHI\nabo-adventure`，本地分支 `codex/adventure-device-smoke`。主线更新至 `63d19d8`，并将 `8da163a` 的精灵管线整合到工作区，保留新 UI 要求；当前工作尚未提交或推送。

用户目标为按顺序完成全部轮次。Claude 新增 UI 风格板和整包后，原 9 轮为 11 轮。用户已选 **v2①轻便徒步** 与 **①复古护照手账**。最新逐项状态见 [ART_PROGRESS.md](ART_PROGRESS.md)。开机另须有 NABO 出场并说 `NABO,陪你冒险`。在能保证质量时 Codex 自行完成；只有具体动作经反复修正仍不良才请 Grok 补片，先写本地任务并告知用户路径，入口 `../GROK_HANDOFF.md`，当前没有 Grok 生成任务。

### 身份依据与制作边界

第一轮曾误用旧深潜重绘头部，用户明确拒绝，旧三款已撤回。真正原始全身图已原样放入 `art/reference/nabo-idle-original.png`（均相对 `game-art/adventure/`），来源/SHA256 在同目录 `source.json`。第 1 轮 v2 是基于此原图的换装编辑；之后使用用户选定①，禁止再用旧 SVG 头替代。当前 SVG 骨骼明确为原像素切片包装，既保留 masters，也交付每动画共享 64 色正式帧；不是重新手绘的矢量身份。

### 已冻结并上机的外壳基线

- app 1,160,608 B；SHA256 `71cc1f6b2eca742cdb11b5e861694e7a43e5bdf3ce8e1da689f3ca32b66fdb32`；IDF 6.0.2，配置版本已统一 `0.1.0`。
- 工牌 MAC 尾号 `a9:58`。真实分区为 `legacy_2m_app_6m_assets`：factory `0x10000..0x200000`，assets `0x200000..0x800000`。首次严格布局检查拒绝且没有写入；随后只增加这个精确白名单，按真实 factory 大小与扇区界限复核，保持全备份和全部保护区回读。实际分区表未改。
- 刷写后 app 和所有受保护字节一致；NVS 在自动游戏测试后再次读回，24,576 B 与升级前完全一致。原日志、备份、回执和冻结 app/ELF/MAP 只留 `private/`。
- 页面导航、跳一跳和深潜各十轮串口进出通过；第一轮地图 heap：跳一跳 259,052 B 不变，深潜 258,964 B 不变，largest 均 114,688 B。额外一轮同样稳定。
- 用户确认显示、三键和声音正常；原休眠为 300 秒，在测试保护下临时设 30 秒后，用户确认约 30 秒熄屏、上键唤醒回封面。临时设置未落盘。设备只确认到该镜像；后续音画/UI 不能据此直接验收。

### 程序增量与当前继续点

`adv_persist.c/.h` 统一保护外壳、跳一跳、深潜、教程和设置的测试写入；跳一跳成绩成功后去重；退出测试先停游戏，再重载真实存档。`>adv.open=jump|dive` 仅测试模式的地图可用，不造分数。深潜停止超时不再释放仍存活缓冲。

休眠实测发现底座继承的 codec 关闭后重复停 I2S 告警，已使用公开 `i2s_channel_get_info/is_enabled` 修复；真正错误继续报告。`adv_boot.c/.h` 已用真实 WAV 全部 43,050 个样本对拍，开机语音延后 1,400 ms 一次播放，离开封面/测试重置/休眠立即停播，共用 audio lock；音频为原系列“阳光小男孩”。`AG_NINEPATCH` 已支持单个显示操作的固定角和重复边/中心，最小/最大卡、移动、裁剪、增量 = 整屏回归通过。

最新中间构建 app 1,248,384 B，完整宿主门禁 **115 项通过**；新增开机音频和 I2S 修复尚未上机，当前等第 4–5 轮正式角色/静态包/UI 资产接入再生成候选。六个新游戏的正式规则仍未实现，不把美术或占位关卡当成正式游戏。

### 正式共用包上机（第 1–5 轮）

app **1,514,528 B**，SHA256 **`6667fa0215dc75a02ddbcad93d53bc5b76aba1e797bd9cf42344b81d45578b3e`**，精确 app/ELF/MAP/sdkconfig/素材清单与源哈希已冻结 `private/candidates/<sha>/`。构建及旧 factory 离线容量检查通过，实际尚余 517,088 B；没有改分区或写资源区。已完成本候选的保护式升级/全片回读及自动冒烟；实体声画和唤醒待本轮用户确认，不沿用基线 `71cc…` 的实体认可。

最终完整宿主门禁 128 项通过，含生产渲染 9 项、包器 10 项及锁定地标压暗/透明回归。共用真实 C 包 215 资源/283 帧，11,822 行及九宫格 912 行逐像素核对。RLE/表/目录估算分别 travel 129,224 B、static 74,329 B、UI 73,709 B，详细 ELF 符号及真实预览检查见 VALIDATION。封面为分层原生资源+120px旅行服 NABO，1.4秒后播 `NABO,陪你冒险`；离开页面取消声音。地图为12fps动作与软件镜头插值，60fps硬件滚动仍是待办。

新游戏美术按第 6–11 轮继续，独立包先 `--group post|night|climb|ski|sky|space --output private/game-art-c/<id> --verify-c` 校验，每包≤260KiB；暂不把全部未实现游戏素材嵌进旧2MB factory。用户要求能保证质量时由 Codex 完成；只有真实动作经反复自修仍不顺时才写具体本地 Grok 任务并告知路径。当前 `GROK_HANDOFF.md` 仍待命。

## 11. 当前继续点：字体与欢迎V2a

用户确认 `6667fa…` 的语音清楚，但否定开机只有平移、缺乏灵动感，并指出整体字体单薄/陈旧。因此已完成新一轮视觉修正，旧视觉不能按接受处理：

- 标题16/18px改Noto Sans SC Bold、正文12px用Source Han Sans CN Medium，品牌/大数字用Montserrat Bold；深蓝选中卡+奶白字、留白/对齐、银章文字对比、封面CTA、超大纪录和锁图标均重新检查，13页实际C图通过。细节见 `UI_REFINEMENT.md`。
- 欢迎V2a为32张物理帧/34曝光/4.417秒，提包→扶帽→挥手→邀请→收手，固定脚锚(120,266)，不再整人平移；保留原WAV与1.4秒延迟。选择入口 `art/boot/selection.json` 锁定e02927ba…清单；源头脸/帽标不镜像。预览和当前证明见 `art/preview/boot-v2/README.md`。
- literal行流+最优key分块兼容旧v1，descriptor32B和最多7delta不变。物理帧排序通过时间表逆映射，34曝光画面/时长不变；实际生产C的4,424个时间点通过。UI与开机演员/时间表合计159,625 B/160KiB，完整计费。
- **六游戏美术全部独立交付**：合计64个人物动作/398人物帧，静态/动态道具另计；全11轮索引362资源/804帧，生产C42,153行+九宫格912行通过，所有六包<260KiB。审计见 `ART_DELIVERY_AUDIT.md`，各包有1x预览和打包证明。正式6游戏代码仍是占位，不宣称玩法已做完。

新候选 **`557607a2f468fed67f5e52adae2f008dd7b44fd5b9d52d94d16c72bb0fa97604`**，app **1,533,920 B**，真实旧factory余497,696 B；**160项宿主门禁**与Windows IDF6.0.2构建通过。app/ELF/MAP/配置、当前字体/生成头及源哈希私有冻结在对应候选目录，**已保护式app-only升级及全片回读通过**；两旧游戏各10轮+暖机无持续内存下降，NVS24,576字节与本次刷前完全相同。新封面76,800像素与宿主一致，地图/护照已实看，详细heap/回执见VALIDATION。

下一步：新镜像已重启到正常模式并重播开机，等用户实际看字体/动作；本候选也已做可见30秒临时设置，观察USB掉线并重启回封面/test0，等这一次实体熄屏/上键回答。现有99分/3章/seen7已逐字节保留，后续仍不能恢复旧0分NVS。用户已补充确认上一候选第二次可见30秒测试“约30秒熄屏，上键能恢复”，记6667fa…实体通过；首次亮屏反馈保留。Grok仍待命，只有具体动作自修后依然不顺才写独立任务并通知用户绝对路径。

## 557607 本镜像用户确认与范围

用户已对本镜像新字体/欢迎回答“都正常”，并对这一次30秒测试确认“约30秒熄屏，上键能恢复”。本镜像已保护式app升级、全片保护字节回读、两旧游戏各10轮冒烟；99分/3章存档24,576字节与本次刷前备份相同，当前恢复正常模式/test0，原持久休眠300秒未改。上述此前“待答/未上机”保留当时检查阶段，当前实体字体/欢迎和30秒睡醒记为通过；精确已验收bin按原SHA冻结，不能用新构建替换。

**11轮完成的是美术和共用界面/演出交付。正式可玩的游戏只有跳一跳和深潜。小火车、萤火虫、登山、滑雪、热气球、太空的美术及独立C包已齐，正式玩法仍待开发，即使解锁也还是占位关卡。** 用户已询问此范围，后续必须按“美术交付/正式可玩”分别汇报。程序后续从HANDOFF待办小火车POST的原型/规则对拍/C实现/横屏/素材整合/真机验证开始，其余五款依次实施。
