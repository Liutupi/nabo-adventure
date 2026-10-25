# SPACE 第11轮交付

入口：[review.html](review.html)、[四屏真实1x](overview-1x.png)、[着陆器分层1x](lander-layers-1x.png)、[静态部件](static-contact.png)。

两款服装master实际使用内置imagegen编辑原始NABO与已选轻便徒步板，prompt、原PNG、SHA及生成记录在`games/space/masters/`。A为米白/灰蓝宇航服与青色胸前模块；B为白金色宇航服。生成的脸、帽、玻璃全部不进入动画：运行头脸只读复用已冻结common独立front/left/right源像素，当前动作采用正面视角，不镜像帽标。服装RGB采样原master，部件由SVG封装像素和骨骼关键帧变换，不逐帧调用模型。

共58帧、9条12fps动画：A舱内待机6、喷气4、着陆6、硬着陆8、插旗8、结算欢呼8=40；B轻量舱内待机6、喷气4、结算8=18，其余三动作显式沿用A，不能把继承动作标称白金全套。正式256RGBA固定足底根点(128,224)；游戏56px（包含球罩）、结算72px。一次对齐每视角源鞋底后，全动画不重新居中。runtime游戏canvas57×57/anchor(29,56)，结算73×73/anchor(37,72)，额外1px是固定画布余量。

球罩独立分为背部轮廓和前部高光，不填充玻璃面、不引入整片半透明色。正式设备轮廓宽4px，缩到56px后约1px，避免初稿细线缩小后断成零散点。全部alpha为0/255；两个设备图层与原头部opaque源像素交集为0，白帽、眼镜、脸不会被玻璃涂色遮盖。最终每个动画≤64色，透明索引0。不同动画同皮肤共享formal palette，runtime按皮肤+尺寸共享palette。

静态包9项：着陆器back/front两层均96×96；3块32×32月面；96×24着陆台、16×24燃料罐、32×28小行星、16×28旅行旗。全部由可编辑`space_scene.py`原生1x图形产生，≤16色。无星点或火焰素材；这两类留给引擎。

着陆器的本地坐标合同在manifest `lander`：anchor(48,92)，脚底接触点(9,92)/(86,92)，主喷口(48,90)、方向(0,1)，侧喷口(9,65)/(86,65)；crew根点(48,70)。按back → crew → front顺序合成，不再次缩放crew。前面板有意遮住舱内人物下肢，头脸完整可见。真实1x落地示例将脚底edge放在屏幕y278、着陆台上沿y278，保证无悬空。插旗示例直接站在月面y286，不把人放进着陆台前板。

插旗是明确的独立道具层：`animations[].attachments.flag`逐帧给出runtime top_left、visible、phase和层次。0–1号收纳不可见，2–5跟随右手套；5号先触地并保持握持，6号才松手；5–7号旗的位置固定。其后宿主接续预览保留独立world旗、人物回待机；游戏外壳仍须接入同一合同。`contacts.per_frame`包含左右手套源/终尺寸坐标，`flag_lifecycle`明确握点(2,10)、触地5、松手6与世界坐标锁存时机。世界位置公式为`world_root + runtime_point - runtime_anchor`。因此PNG保留可复用的身体动作，旗不是烘焙在人物上的纹理。

最终9张全帧接触表均已实际查看（夜空与月面、1x+3x），并查看4张240×320场景、静态表和着陆器分层；无帽标镜像、脚底裁切、领口断缝。56px总身高下帽标只能辨识蓝色标记，不能承诺逐字读出NABO；1x和高倍预览分别展示，不能混用验收。

`continuity.json`含14项检查：A着陆/硬着陆/插旗身体首末等于idle0（正式/runtime均逐像素相同）；两皮肤结算首末相同；idle0与喷气相位0相同；旗帜落地末三帧保持位置且底点等于根点；4个握持帧均通过独立手套原像素遮罩检查。喷气为循环，离开动作应回到相位0或由外壳安排过渡，不能任意截断后声称无跳变。

真实生成C与生产`adv_sprite.c`/`adv_ninepatch.c`宿主对拍：18资源、67帧、3,954行全一致。RLE60,054B+表17,470B+目录/描述符估算1,539B=79,063B，低于260KiB单游戏预算。最终链接对齐/去重需ELF实测；本次仅临时目录C对拍，未全嵌入旧2MiB factory，也未做设备/用户视觉验收。

跨包独立审核实看发现首版4→5号旗从(44,20)跳到(44,28)，单帧8px落地。已改右臂真实姿态，先随手下降、触地再释放，没有只改附件坐标。修后可见旗最大相邻位移8.000→4.243px，最大竖直步长8→3px；右手套最大步长4.472→4.243px。2–5号旗握点与源手套遮罩和正式runtime不透明像素全为0px间隙；5号底点恰为固定根点56，之后旗不再跟手移动。失败原图、原清单和原C报告保存在private质量审核目录。`flag-contact-qa.json`保存逐帧值和前后清单SHA；`flag-ground-contact.png`展示全部8帧56px与3x；`plant-flag-persist.gif`/contact实际展示idle→插旗→idle且world旗不消失。头脸和头盔源文件未改、原中性端点保持。`reproducibility.json`记录完整重建+C对拍全部输出逐字节一致。

复现（仓库根目录，CC为可用gcc）：

```powershell
$env:CC='D:\nabo-passport-tools\w64devkit\bin\gcc.exe'
python game-art/adventure/tools/space_pipeline.py --verify-c
```

只读复核用`space_verify.py --verify-c`。脚本均小于约400行，没有更改共享头脸、固件、其他轮次素材或主manifest。当前接续可本地修妥，无Grok委派。
