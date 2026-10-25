# 生产 UI · typography v2

这是在已选复古护照方向上的第二版生产素材。上一版完整保存在899d275检查点；`design/round3/`与`design/refinement-v2/`原审阅稿保留。本次只改UI图像及其生成工具，未改手写固件、共享人物/游戏包或设备。尚待主任务真实C打包与渲染接入，不把Pillow组合图称为设备截图。

先看`preview/core-3-1x.png`（封面、真实纵向站点布局、护照）和`preview/all-13-1x.png`；13张单页均240×320，已逐张实际检查。另有`preview/nine-slice/contact.png`，展示6种状态各48×32/240×120两种尺寸，四角原像素与内部无缝平铺检查通过。

保留奶白纸色、海军蓝和邮戳红，去掉多重土黄细框、格子底纹和无意义编号。选中菜单/当前信息卡/当前护照格为海军蓝实底+4px红侧条；所有动态标题、分数、提示在选中状态必须用奶白`#fffaf0`。普通字`#203849`，次要字`#60707a`。真实共享部件14可见色，完整声明调色板16可见色（含字体边缘备用色），透明另占一位，低于32色。

中文16/18标题使用核对过的静态Noto Sans SC Bold700，12正文为原SourceHanSansCN-Medium500；固定英文品牌/20与36高数字用Montserrat Bold700。`fonts/sources.json`保留原文件路径、SHA、full name、版本、字重、OFL和fsType；`fonts/bold16-subset.txt`/`bold18-subset.txt`供root生成4bpp C子集。字体文件本身未复制或转换分发，完整许可文本在`licenses/`。当前`adv_text.c`固定4bpp，不把未实现的2bpp当作生产方案。

`wordmarks/collection.png`是220×90透明字标：38px NABO、12px字距ADVENTURE、26px完整“NABO 的冒险之旅”，无字旅行旗；4色。8个游戏字标200×80，26px粗中文+14pxMontserrat英文，不超过16色。静态标签文字单独PNG；动态名字、最佳、未解锁等由程序字库写。

现有137项API路径保持，六组九宫格命名不变：menu normal/selected/disabled、info normal/current四角12×12；popup normal四角16×16；边与中心8px平铺。`atlas.png`仅编辑、pack=false。顶栏32、底栏30、资源条10；护照格仍104×52；数字仍20/36高、0–9/m/+和advance；三标签≤100×24；锁≤16、脚印≤10、底座48×40、印泥64。

护照`locked-mask.png`现在只有锁图形，不再烘焙深色“未解锁”横条；程序需按状态在相对(8,30)写未解锁，选中时用奶白。格框不重复烘焙章槽，程序只画实际章，避免二重圆点。

封面严格分层：`cover-background.png`没有人物、标题、文案或按钮，海/小镇/雪山/太空为原生UI缩影；底部270..320纯纸色。实际打包背景top240×256/bottom240×64，offset(0,0)/(0,256)。独立字标放(10,12)；原样welcome000的人物根点(120,266)，不重画、不缩放、不重新量化；caption(10,270)，208×34按钮(16,284)。完整背景/人物位置层/静态合成均pack=false，只有背景分片、字标和标签进入UI包。`verify_ui_assets.py`核对所有层重建逐像素一致；封面含NABO56色，低于64。

接入合同在`integration-tokens.json`。地图预览按实际adv_path位置：小火车在上、跳一跳居中、护照亭在下，节点间112px，左右交替，世界地面是程序预览渐变而非新增背景素材。保留生产camera/traveler、9世界上下关系和上下键，不能把预览的可见节点写死成地图。当前/邻站卡112×52，title Bold16墨迹相对(8,8)、次行Medium12相对(8,30)，成绩右对齐x104，选中一律奶白。护照建议格位x12/124、y70/124/178/232。所有其他页面的动态文字位置、字体、颜色、对齐和数字位置还写在`preview/*.layout.json`；这里的坐标是墨迹左上，不是C基线。C基线应由实际生成字形box_h/ofs_y推导并经真实渲染核验。

Python使用生产同格式adv-row-rle-v1逐项量测（不按相同SHA去重藏掉重复数组）：RLE36,008B+表14,310B+C3目录/描述符估算11,791B=62,109B。加当前welcome47,730B为109,839B，低于163,840B，角色没有挪到travel组后不计。可给替换启动角色的额度为101,731B；新boot-v2必须替换旧welcome成本重测，不能沿用本数字。主任务最终还需真实C解码/整包RLE和ELF测量；动态C字库继续单列app，不重复扣UI图像预算。

复现：

```powershell
python game-art/adventure/tools/build_ui_assets.py --character game-art/adventure/art/frames/travel/runtime/welcome/000.png --character-anchor 31 120
python game-art/adventure/tools/verify_ui_assets.py
```

`ui-manifest.json`逐项记录name/path/size/palette/SHA/color_limit/pack；`ui-qa.json`为像素/结构宿主结果。`row_rle_estimate_bytes_deduplicated`仅保留旧的粗略历史估算字段，预算应使用`actual_static_estimate_c3`及`ui_plus_current_boot_estimate`，不把PNG大小或Python解码等同生产C通过。
