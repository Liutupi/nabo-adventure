# CLIMB 第8轮交付

入口：[review.html](review.html)、[真实1x场景](overview-1x.png)、[场景部件](static-contact.png)。

皮肤A为青灰登山服与背包，皮肤B为红色冲锋衣。两个服装master均实际调用内置imagegen编辑原始NABO身份图与已选轻便徒步设计板；生成头部不进入动画，动画头部和表情只读复用冻结common的front/left/right像素。左、右头部各有独立原始视角，没有镜像帽标。原图、prompt及SHA记录保留在`games/climb/masters/`。

共100帧、16条12fps动画：A左右抓壁待机6、换边6、蓄力4、跳6、滑落6、登顶8，另正面结算8；B左右待机6及正面结算8，其余动作显式沿用A。第二款继承动作穿A服装，不能标称已制作红衣全套。正式256RGBA、无损master与终尺寸runtime分别保存；固定足底根点(128,224)，游戏动作60px、结算72px。全部runtime都有显式canvas、anchor及逐帧SHA，不按帧重新裁切或居中。

SVG仅封装独立原像素部件，骨骼、裁片、source-only关节重叠和关键帧可编辑。源文件不改RGB。局部alpha遮罩去除common头部底部继承的旧旅行服领边，并在合成后去除衣物下方少量脱离主体的切片碎点；头脸帽子区域不会参与后一步清理。初稿膝部断缝已用源像素关节重叠修正。

场景为原生32px岩壁灰/冷/雪三组共6块；普通、碎裂、结冰三岩点，落石和水壶。雪堆直接引用冻结`map/tiles/mountain/snow-drift.png`及`map/tiles/ski/snow-mound.png`，与滑雪共享原文件及SHA，不再绘制另一份雪堆。静态源图形由`climb_scene.py`确定性绘制。

已逐张查看16条动画接触表（实际1x与3x最近邻、冷岩/雪地双背景），并查看240×320真实场景、结算和静态素材联系表。修正了72px接触表展示区域不足导致的脚底裁切；交付帧本身没有裁切。小尺寸保留原白帽、棕发、黑眼镜与脸部；帽上文字因60px总身高无法逐字阅读，不能把高倍预览当作1x文字可读性验收。

主代理另指出首轮场景岩点未对准手脚、角色悬空。已修正组合：每帧从实际骨骼变换后的手部轮廓和鞋底提取接触点，写入`rig.json`约定及manifest `contacts.per_frame`。`grip_contact`和`foot_contact`均在runtime canvas坐标，屏幕位置=`world_root + contact - runtime_anchor`；也保留formal坐标、两手/两脚各点、当前wall与support_state。0号待机帧A左手/左足为(7,21)/(18,62)，A右手/右足为(51,21)/(42,62)，根点保持不变。真实1x预览根点左(56,181)、右(184,181)，沿接触点摆放岩点上唇；踏点后端与岩壁连续。重新实看左右场景已能看到至少一手抓住岩点、一足踏在岩点。角色PNG无改动；manifest与C打包记录已同步重验。

`continuity.json`含18项正式帧与runtime端点逐像素相等验证。蓄力始于抓壁中性帧；跳从蓄力末帧开始并回到同侧抓壁；换边末帧等于对侧抓壁0；滑落回到同侧抓壁0；结算首末中性相同。登顶结束于相应侧向中性站姿，切正面结算前需由外壳显式转身或切页，不能直接当成循环。

真实打包与生产C逐帧逐行对拍见`packing-qa.json`：29资源、113帧、7,072行全部一致；RLE96,584B，表31,154B，C3描述符/目录估算2,563B，共130,301B。未超过单游戏260KiB；最终链接对齐/去重尚需ELF实测。这次仅临时目录编译对拍，没有向现有2MiB factory固件全嵌入，也没有设备/用户动画验收。

复现（仓库根目录，CC指向可用gcc）：

```powershell
$env:CC='D:\nabo-passport-tools\w64devkit\bin\gcc.exe'
python game-art/adventure/tools/climb_pipeline.py --verify-c
```

只读重验现有包可运行`climb_verify.py --verify-c`。每源文件均低于约400行。当前动作已经本地完成接续修正，无需向Grok委派片段。
