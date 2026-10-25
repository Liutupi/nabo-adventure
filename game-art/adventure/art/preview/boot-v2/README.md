# 欢迎V2a

用户否定了已上机V1的整体平移入场。当前V2a使用已选徒步装，按提包→扶帽→挥手→邀请→收手→中性制作；固定脚锚，原生表情与既有张掌素材来源见 `../../boot/v2/source/provenance.json`。这是一份已通过技术验证、仍待用户实体观感确认的候选，不宣称口型同步。

- 当前唯一角色清单：`../../boot-v2-manifest.json`，SHA256 `e02927badea6222ca97a014b5f9adaaa0090405524c33b6238df2083fef42c0e`。
- 实际固件选择：`../../boot/selection.json`；32张74×121物理帧，34曝光，4.417秒。物理帧重排只服务压缩，生产时间表逆映射，逻辑画面与时长逐项不变。
- 当前完整音画：[welcome-v2a-production-ui-voice.mp4](welcome-v2a-production-ui-voice.mp4)。语音保持用户确认正常的原WAV，1.4秒开始、4.090625秒结束。
- 目标尺寸帧表：[v2a-120px-contact.png](v2a-120px-contact.png)；过渡修正：[v2a-transition-comparison-1x.png](v2a-transition-comparison-1x.png)。
- 当前生产包证明：[packing-production-v2a.json](packing-production-v2a.json)；源像素/透明/裁切与接缝：[qa-v2a.json](qa-v2a.json)；原源重建：[repro-v2a.json](repro-v2a.json)。

实际生产包UI57,244B，开机演员含时间表102,381B，合计159,625B/163,840B。新literal行流与最优key分块保持旧v1兼容、32B描述符和最多7delta；全部原PNG/RGBA、曝光顺序与时长不变。生产C逐行比较与4,424个时间点边界检查通过，不能据此推断工牌帧率或用户已接受。

`packing-validation.json`、`packing-optimal-keys.json`、`packing-intern-ui.json`及不带a的MP4保留先前V2尝试，来源和字节数不代表当前V2a。`art/boot/v2/presentation-timeline.h`服务预览原序；固件使用 `tools/generate_boot_presentation.py` 从选择文件生成的 `firmware/main/generated/adv_boot_presentation.h`，不要手抄物理序号。

后续557607镜像已上机，用户对新字体/欢迎确认“都正常”，本次30秒熄屏/上键恢复也通过。上方“待确认”及包快照status记录生成时状态；当前验收以docs/VALIDATION.md最新节为准。当前不需要Grok补片，入口继续待命。
