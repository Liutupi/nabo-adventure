# 宣传封面生成记录

使用内置 image_gen；新绘宣传画，不改固件素材。权威身份参考为项目`nabo-idle-original.png`，服装参考为已批准的`boot/v3/nabo-hero-start.png`，版式参考为声音实验室社区v0.2.0-preview.1封面。保留白帽、蓝色未镜像帽标、棕发、圆黑眼镜、灰蓝眼睛和青绿色徒步装。

首轮提示：制作一张3:4竖版NABO冒险系列社区封面；参考声音实验室的午夜紫黑底、专业粗字、青色和暖金强调。主角占中央/右侧60%，大而有亲和力，采用已批准的徒步外套和斜挎旅行包，邀请观者出发。环境从深海和铁路过渡到远山、月球与太空，路线连贯、克制、不堆贴纸。文字为“NABO / AI PASSPORT”“NABO”“冒险之旅”“从深海，到月球。”“8款离线游戏 · 冒险护照”“NABO，陪你冒险”“v0.1.0 · 预览版”“AI宣传插画 · 非实机画面”。不加设备硬件，不称实拍，不改人物身份。

定向修改提示（最终）：只修正标题排版，四个汉字“冒险之旅”必须完整可见，不能被帽子或头发遮住。把该行缩到左侧约x50–435的安全区，保留粗字、青色“冒险”和金色“之旅”。人物、帽标、风景、路线、配色和其他文字全部保持原样，仍为3:4整张封面。

首轮因标题末字与帽子重叠未采用；修正版作为01-cover.png。其余四张是代码生成的SVG/HTML新排版，嵌入原样生产C截图；并非AI重画游戏界面或实物摄影。

## 最终一次实际调用提示词

```text
Make a narrowly targeted typography correction to this finished portrait poster. The four Chinese title characters '冒险之旅' must be entirely visible, with no character hidden behind NABO's white cap or hair. Reduce this single title line's font size/width enough to fit in the left clear area, approximately x=50 to x=435, keeping it very heavy/bold, turquoise '冒险' and gold '之旅', with all four characters intact. Keep the title in the same general area below the large white NABO heading. Preserve absolutely everything else: character face, cap and NABO logo, original artwork, landscape, route, colors, all other text, footer, composition and 3:4 aspect ratio. Do not change the character, do not add anything. Deliver the complete corrected poster.
```
