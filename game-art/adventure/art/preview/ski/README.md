# SKI · 第 9 轮

入口：`../../ski-manifest.json`，路径均相对 `art/`。状态为宿主制作与解码验证完成；等待用户美术验收及后续真机、玩法集成。

| 皮肤 | 动作 | 帧数 | NABO 本体目标 |
| --- | --- | ---: | --- |
| ski_a | 直滑、左倾、右倾、跳、摔倒、过终点 | 6 / 4 / 4 / 6 / 8 / 6 | 56px |
| ski_a | 结算欢呼 | 8 | 72px |
| ski_b | 直滑、结算欢呼 | 6 / 8 | 56px / 72px |

共 9 片段、56 人物帧，12fps。仅直滑循环。左右倾四帧从中立进入倾斜，输入持续时保持末帧，松键倒放回中立再接直滑；不要硬切回直滑。其他非循环片段首末为相同姿态。终点仍持杖，避免首帧道具突然消失；结算页另用不带雪板和雪杖的欢呼。

角色源画布为256×256 RGBA，固定锚`(128,224)`。本体56px按208px参考身高统一缩放；雪板、雪杖与起跳留白额外占空间。V2只扩原包络下缘1px，运行画布为 **63×68，锚`(32,60)`**，横向与上缘注册保持V1。这不是把本体缩成68px；没有逐帧裁切或变身高。72px组仍 **45×72，锚`(30,72)`**。各尺寸组两皮肤和全部相关动作共用同一裁切、缩放及调色板。

两次内置 imagegen 分别制作了 A/B **真实斜后上方背身**衣服母版：A 为带兜帽、肩背色条的滑雪服；B 为彩色毛线套装和围巾。生成母版的头不进入人物运行层，脸、帽、镜、发仍读取冻结的独立 `common/left`，作回望姿态。A 仅额外提取生成稿的帽侧护目镜作为配件，不遮原眼镜、眼睛或正面帽标；B 保持原白帽。没有镜像角色，也没有把正面躯干称为背视。

`games/ski/source/`保存原母版、prompt、生成记录；`rig/ski/`保存切片PNG/SVG、mask、采样、支点与接触坐标。服装归一化后，共用头保持原身份比例；局部alpha排衣领只排除旧旅行服领口，保留source RGB不变。所有y≤93头像素保留，y94..100仅留原颈部暖色像素。非fall仍只整数平移；fall按原整块头/表情/帽/镜作正行列式刚性旋转，不镜像、不非均匀拉伸、不画新脸。旋转重采样与调色损失分别量化记录，不能宣称旋转后的每个RGB仍原样。

双靴与对应雪板绑定、手套/杖按握点绑定并逐帧验证实际alpha重叠。两板分别绘制，没有镜像NABO。独立复看确认V1摔倒只是蹲低滑行后，V2改为0/12/36/62/62/36/12/0°整身倾倒，双膝折起、远板上翘25°，右手在雪板外侧触雪，停两帧后撑起回中立。原微笑保留。其余8片段48张高色master逐字节不变，72px两组16张runtime也不变；新的共享56px调色板/画布已全量回验。

12 个静态引用包括两块雪板、雪杖、大松树、红蓝旗门、热可可小屋、终点拱门，以及直接引用冻结共享包的雪堆、雪包、小松树和冰晶。共享雪素材保留相同路径与 SHA，未复制或改画，也不改 CLIMB 的目录。新静态图形均有可编辑 SVG，目标尺寸原生绘制；最大 8 个 RGBA 色。

查看入口：

- `identity-and-body-view.png`：原始形象、已选旅行服源，以及两套背身衣服配共用头。
- `slope-composition-contact.png`：A/B 的 240×320 原生组合及 2×；只是美术遮挡与比例预览，没有冒充实际游戏 UI。
- `ski_*-contact.png`：全部动作每帧 1× 和 3×，实际雪坡 RGB565 底色与深底。
- `props-contact.png`：12 个道具/共享引用及 2×。
- `fall-v2-slope-all8.png`、`fall-v2-snow-contact-detail.png`：全部原生摔落坡场与实际手/雪接触裁切。
- `fall-v2-slope-continuity.gif`：直滑→摔落/触雪→回稳的真实目标尺寸接续。
- `*-snow.gif` / `*-dark.gif`：12fps 的 GIF 近似时序；运行时间以 manifest 精确 12fps 为准。

`first-*`、`repaired-*`、`*-inspection`、`*-detail` 为真实自修审计；只使用清单中的正式帧。

仓库根目录重建（固定保存的母版，不调用模型）：

```powershell
& 'C:\Users\pc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' game-art/adventure/tools/ski_build.py
& 'C:\Users\pc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' game-art/adventure/tools/ski_verify.py
```

完整重建和真实C验证用`ski_pipeline.py`；两次字节复现用`ski_reproduce.py`。V2生产C为68帧/4372行、估118715B；327个输出经完整管线及C对拍重建逐字节一致。具体转角、手位移、0px触雪、原帧不漂移与重采样误差见`fall-repair.json`。

需要 Pillow、NumPy 与同工作区 Fortune 的 SourceHanSansCN-Medium.otf。字体、原图、母版、共享包和脚本来源 SHA 在独立清单。

生产 C 校验仅输出独立目录：

```powershell
$env:CC='D:/nabo-passport-tools/w64devkit/bin/gcc.exe'
$env:PATH='D:\nabo-passport-tools\w64devkit\bin;'+$env:PATH
& 'C:\Users\pc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/build_adventure_assets.py --group ski --output private/game-art-c/ski --verify-c
```

详见 `QA.md`、`verification.json`、`packing-validation.json`、`reproducibility.json`。本轮没有写设备、固件生成目录、主 manifest 或共享 rig。
