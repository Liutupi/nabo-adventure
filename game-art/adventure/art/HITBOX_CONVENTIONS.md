# 六游戏 hitbox 制作坐标说明

2026-10-25，适用于[交付审计](../../../docs/ART_DELIVERY_AUDIT.md)列出的六份清单 SHA。本次只补文档，未修改冻结清单、PNG、rig 或打包器。**这些数值是制作参考框，六个正式碰撞玩法尚未实现，不能把不同空间的数组直接混用，也不能当作已调好的碰撞判定。**

## 已有字段的空间、格式和边界

下表导出脚本均位于 `game-art/adventure/tools/`；以当前清单每条动画的值为准，示例不是全包共用常量。

| 清单 | `animations[].hitbox` | 原值来源与单位 | right/bottom 约定 |
| --- | --- | --- | --- |
| `post-manifest.json` | **源256画布 LTRB** `[left,top,right,bottom]` | `post_build.py:union` 对该动作全部高色 master 的 alpha≥128 取并集；源像素，动作各不相同，例如 idle `[83,15,174,160]` | `max(x)+1,max(y)+1`，左/上含、右/下不含，矩形 `[l,r)×[t,b)` |
| `night-manifest.json` | **runtime画布 XYWH** `[x,y,width,height]` | `night_pipeline.py` 将源参考矩形 `(95,144,66,80)` 的原点和宽高分别按该皮肤/尺寸组 nominal scale 四舍五入；56px例 `[9,29,22,27]` | 使用整数像素边界；`right=x+width,bottom=y+height`，右/下不含；**不是**源256坐标 |
| `climb-manifest.json` | **源256画布 LTRB** `[42,16,214,224]` | `climb_export.py` 固定制作参考常量，不是逐帧 alpha 框；源像素 | 本补充将其明确解释为半开边界 `[42,214)×[16,224)`。原导出器只有常量、没有碰撞消费者，未曾验证含边碰撞行为 |
| `ski-manifest.json` | **源256画布 LTRB** | `ski_build.py:union` 对单动作全部 master 的 alpha≥128 取并集；源像素，含雪板、雪杖/倒地动作包络，例如 straight `[22,15,240,249]` | 与 POST 相同，右/下是最大占用像素+1，不含 |
| `sky-manifest.json` | **runtime画布 XYWH** | `sky_pipeline.py` 将源参考矩形 `(104,102,50,58)` 的原点和宽高分别按尺寸组 nominal scale 四舍五入；40px例 `[15,24,14,16]` | 与 NIGHT 相同，右/下为 x+w/y+h，不含；这只是人物上身参考，不含气球/吊篮 |
| `space-manifest.json` | **源256画布 LTRB** `[75,5,183,225]` | `space_export.py` 固定制作参考常量，源像素；并非着陆器碰撞框 | 本补充将其明确解释为半开边界 `[75,183)×[5,225)`；原脚本未实现碰撞边界规则 |

宽高必须由 LTRB 的差求出；不能把 LTRB 最后两项当宽高。反之，NIGHT/SKY 的最后两项不能直接当 right/bottom。道具动画没有人物 hitbox，静态 `size/anchor` 也不等同于碰撞框。

## 源256 → runtime 使用的现有字段

`C=(cx,cy,cr,cb)` 均为 Pillow 半开裁切框；`W,H=animations[].runtime_canvas`。每条动画读取自己的字段，不跨皮肤或40/56/60/72px组复用别组裁切。

| 包 | 裁切框 C | nominal scale s | 画面锚 |
| --- | --- | --- | --- |
| POST | `runtime_quantization.source_bbox` | `runtime_quantization.scale` | `runtime_anchor`；源 `anchor` 为半身(128,160)/全身(128,224) |
| NIGHT | `runtime_quantization.global_source_bbox` | `runtime_quantization.scale` | `runtime_anchor`，源(128,224)；hitbox已在runtime，不再缩一次 |
| CLIMB | `runtime_palette.source_crop`，现 `[24,8,232,232]` | `runtime_palette.scale`，60/208 或72/208 | `runtime_anchor`，源(128,224) |
| SKI | `runtime_quantization.source_bbox`；56px现 `[10,2,243,255]`，72px另读自身组 | `runtime_quantization.scale`；56/208，72px按自身包络 | `runtime_anchor`，源(128,224)；gear包络不是本体身高 |
| SKY | `runtime_quantization.geometry.bbox` | `runtime_quantization.geometry.scale` | `runtime_anchor`；半身源(128,160)/全身(128,224)；hitbox已在runtime |
| SPACE | `runtime_palette.source_crop`，现 `[16,4,240,228]` | `runtime_palette.scale`，56/220 或72/220 | `runtime_anchor`，源(128,224) |

已有附件/接触点的制作映射使用 `round((x-cx)*s), round((y-cy)*s)`，`round` 为生成脚本的 Python ties-to-even。对应的 `contacts`、`runtime_hand_contacts`、`runtime_jar_opening` 已经是 runtime 坐标，不应再次转换。**实际合成一律使用清单明确给出的 `runtime_anchor`，不要用浮点重算的锚替换它。**

由于输出 W/H 分别取整，PNG实际采样比例为 `sx=W/(cr-cx)`、`sy=H/(cb-cy)`，可能与 nominal s 有细微差异。若只需将源参考框保守映射到目标画布，可离线执行：

```python
from math import floor, ceil

def source_ltrb_to_runtime(box, crop, canvas):
    l, t, r, b = box
    cx, cy, cr, cb = crop
    w, h = canvas
    sx, sy = w / (cr - cx), h / (cb - cy)
    return [max(0, min(w, floor((l-cx)*sx))),
            max(0, min(h, floor((t-cy)*sy))),
            max(0, min(w, ceil((r-cx)*sx))),
            max(0, min(h, ceil((b-cy)*sy)))]

def runtime_xywh_to_ltrb(box):
    x, y, w, h = box
    return [x, y, x+w, y+h]
```

这是**框边界转换**，不保证等于 LANCZOS采样/alpha阈值后的实际轮廓。点像素中心的精确采样网格映射是 `((x+0.5-cx)*sx-0.5, (y+0.5-cy)*sy-0.5)`，也不应拿它替代已交的整数附件握点。若正式玩法需要逐像素轮廓，以最终 PNG 的二值 alpha 或专门的玩法碰撞形状重新定。

runtime框放到屏幕/世界坐标时，统一对四边加 `world_root - runtime_anchor`；先源→runtime、再加世界平移。禁止把源256的 left/top直接加屏幕根点。

## 正式玩法接入边界

- POST应为车体、轨道、信封/车站定碰撞，不应拿40px司机包络代替整辆火车。现有 `events` 仅定义甩信释放/抓绳帧。
- NIGHT抓取应使用相应动作的 `runtime_jar_opening` 和玩法捕获范围，人物躯干参考框不表示瓶口。
- CLIMB岩点支撑用 `contacts.per_frame.grip_contact/foot_contact`；固定人物参考框不保证包含每帧伸出的手脚，也不是抓点判定。
- SKI动作并集包含雪板和杖且跨帧扩大，正式受击范围/过门范围应分别设计，不直接用整个并集。
- SKY人物框不含96px球体和吊篮，气球撞鸟/雷云需要独立几何；heat/vent绳层与同名人物动作同步。
- SPACE着陆判定应采用 `lander.landing_feet`（本地底边 y92）、倾斜和速度；人物hitbox不是着陆器。旗的携带/触地/释放使用 `attachments.flag`/`flag_lifecycle`，不靠人物参考框猜测。

上述字段和坐标变换现在均有可执行解释，未补写任何冻结资产。最终玩法碰撞形状、阈值、状态转移、C/原型对拍与设备验收仍待后续实现。
