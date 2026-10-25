# 开机表演 V2 / V2a 审阅包

当前冻结候选为 **V2a**，尚未声明用户验收、固件验收或 160KiB 预算通过。不要覆盖 `v2a/runtime/`、`v2a/masters/` 与当前独立清单；继续修正应另存 V2b。

- 独立清单：`../../boot-v2-manifest.json`，SHA256 `e02927badea6222ca97a014b5f9adaaa0090405524c33b6238df2083fef42c0e`。
- 带原声预览：`../../preview/boot-v2/welcome-v2a-production-ui-voice.mp4`，SHA256 `5eef23f2e28ceabfece21deb9a7d5202187291228fab1d961a7d870136536b0d`。
- 可点击离线对照：`../../preview/boot-v2/welcome-v2a-voice-preview.html`。
- 原尺寸接续对照：`../../preview/boot-v2/v2a-transition-comparison-1x.png`；前作并排：`previous-series-v1-v2a-1x.png`，同属该预览目录。

## 演出与播放合同

提包带蓄势 → 扶帽檐抬头 → 张掌挥手 → 掌心邀请 → 脚尖朝出发方向、点头回稳。34 个事件引用 32 张独立 PNG，12fps 时钟共 53 tick，即 4.416667s；整数毫秒表结束于 4417ms。运行画布 74×121、锚点 `(29,121)`，固定身体采样高 120px，额外 1px 为倾头包络。屏幕脚锚 `(120,266)`，没有整人入场平移或预览专用额外动作。

`v2a/presentation-timeline.h` 与清单时间表一致，34×4+16=152B。各姿态起始时刻、duration、独立帧索引均在清单和 `v2a/poses.json`。C 端应按这张表选帧，末姿态保持，不循环两遍。

显示文案原样 `NABO,陪你冒险`。已有 `audio/boot-welcome.wav` 不变，SHA256 `38b4eb8435d6a7915d17af2083a696acfa2660244be1bf7e65dc78251f0c468b`，原声在屏幕亮起后 1400ms 开始、4090.625ms 结束。MP4 的 H264/AAC 仅用于观看，PNG 与生产 C 对拍才是像素依据。

## 原像素来源

身份仍为唯一原图 `reference/nabo-idle-original.png` 的 NABO，衣服为用户已选 v2①轻便徒步。身体与衣服只读复用冻结 `art/rig` 的 hiker 像素。

离线表情使用项目原生 `reference/nabo-idle.png` 的三格整头（睁、半闭、闭），SHA256 `c63575691d15220e8d6fafdab911a10767a5fc1c13925992dbd10e3a5e93d3fa`。去除外连黑底和医生衣领后整头注册；没有拼接眼口片段、画新脸、镜像帽标。头与表情一起作小幅正交刚性旋转，BICUBIC 重采样会改变边缘 RGB，因此不声称旋转后逐像素无损。冻结 common 头文件没有修改。

张掌与半开掌只读复用已验收前作 `nabo-sound-lab/.../S-WELCOME.mp4` 的实际 3.65s 与 3.25s 原帧。视频 SHA256 `d950a0a1799683741466cce73b3a8208dd207ffd665c257c31fecca58d144002`。ROI、源帧 SHA、alpha 清理规则与手腕坐标见 `source/provenance.json`。只保留源手掌/相邻原描边；半开掌下方粉色袖口按 alpha 排除，没有带入耳机或原服装，没有重画手指。右袖被挎包遮挡的部分由同件衣服左袖独立镜像补齐；头、身体、帽子、文字均不镜像。

## 真实修订和失败

- `attempt1-master-contact.png` 留在预览目录，记录第一次黑底 flood-fill 失败，未作为成品。
- `attempt2/` 及其 `reviewed-v2/` 保留 29 事件前版与当时视频、清单、脚本。独立审核发现 0.833→1.0s 抬帽、1.333→1.417s 离帽开掌及 2.5s 邀请跳姿，且闭眼偏多。
- V2a 拆原 hold 增加 tick11 抬帽、tick15 离帽、tick17 半开至 tick18 张掌、tick29 邀请及 tick40 收掌桥接；肩胸轻跟随，删除 warm-blink。53 tick 与原声时刻不变。

## 验证边界与复现

`../../preview/boot-v2/qa-v2a.json`：32 图共 48 可见色、二值 alpha；34 个源画布均未在边界裁切，手腕局部袖口/手掌无像素空隙；全闭眼 3 tick、半闭眼 5 tick。已逐看原尺寸 contact、接续对照、前作并排和 UI 合成。连续 MP4 动态审核由主代理/交叉审核者进行；本代理的 file:// 浏览器播放被 URL 策略阻止，未绕过限制，不能据静态图声称已连续播放通过。

人物仍有固定中性嘴形和二维关节限制，不能宣称达到前作完整表情/形变能力。主代理/host 负责保持画质的无损压缩与最终 UI+开机总预算。预览目录旧 `packing-*.json` 的 27 帧结果属于前版 V2，不能用于声明当前 V2a 通过。

只读重渲染验证：运行 `game-art/adventure/tools/boot_v2_reproduce.py`。该脚本在本目录临时子目录重建源切片/rig，逐像素比较全部 34 个逻辑姿态、32 张独立图，结束移除临时副本，不覆盖冻结图或清单。结果在 `../../preview/boot-v2/repro-v2a.json`；本次完全一致。`v2a/source-snapshot/` 留存冻结生成脚本与清单。`boot_v2_build.py` 是生成工具，会写图和清单，冻结期间不要运行覆盖式构建。

未改固件、总 manifest、共享 common、POST、SKI 或原始前作资源；未接触设备。没有发起新的 Grok 或逐帧模型生成。
