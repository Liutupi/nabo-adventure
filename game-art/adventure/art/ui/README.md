# 复古护照手账 UI 素材包（第 5 轮）

用户已选第 3 轮方向①。这里提供与该方向一致的原生像素部件、字标和分层封面；不修改固件界面，不代表新镜像或真机已经验收。`design/round3/` 原候选保留。

所有部件共用 `palette.json` 的 15 个可见颜色，透明索引另占一位；不包含人物独立调色板。中文用已验证的思源黑体 Medium，SHA256 与 `firmware/tools/collection-fonts.json` 一致；界面字号 12/16/18 px。数字图是用同一字体直接在最终像素画布栅格化的独立 20/36 px 高资产，没有把大图缩成小字。

`ui-manifest.json` 是本 UI 包的独立清单，不是全项目总清单。每项含 `name/path/size/palette`、透明标记、色数限制、SHA256、是否实际打包。`pack:false` 的大图/九宫格母版仅供编辑与审阅，不应重复装入固件。

- `cards/menu/`：normal / selected / disabled；12×12 四角。
- `cards/info/`：normal / current；12×12 四角。
- `cards/popup/normal/`：16×16 四角。
- 每组有九张独立图：`top-left/top/top-right/left/center/right/bottom-left/bottom/bottom-right.png`；边与中心按原像素平铺，四角不缩放。`atlas.png` 是可编辑母版，不重复打包。
- `bars/`：高 32 顶栏、高 30 底栏。`resources/`：高 10 的资源框、可平铺填充/低值填充和端帽、七种 16×16 图标。
- `passport/`：32×32、两色可平铺底纹，104×52 普通/当前格框与独立未解锁遮罩。
- `numbers/20/`、`numbers/36/`：0–9、m、+，含逐字 advance；每图不超过 8 色。
- `labels/`：新纪录、测试不记录、占位关卡，以及独立开机文案与出发按钮。
- `map/`：三态站点底座、正反脚印、16×16 锁和小章槽；`stamps/ink-pad.png` 为印泥底纹。
- `wordmarks/`：独立透明合集字标与八个游戏字标，各自不超过 16 色。动态成绩、提示和名字不烘焙进背景。

## 开机封面分层契约

完整制作时会提供 `cover-background.png`：没有 NABO、字标或按钮，只含海/镇/雪山/太空地图缩影；人物和字标另叠。底部 y=270..319 保持纯纸色留白。

NABO 单独放 `cover-character.png`（240×320 合成位置层）和 `cover-character-sprite.png`（实际小图）。已批准的旅行服像素直接采样，最终可使用 `welcome120` 的原像素及原锚点；没有重画头、脸、白帽或眼镜。人物与地图不烘焙在一起移动。

`cover-illustration.png` 是背景 + 独立字标 + 独立人物的静态效果参考。`preview/cover.png` 再叠“NABO,陪你冒险”和“按 OK 出发”，每层按清单位置合成必须逐像素相同。语音由主程序独立集成，不包含在此 UI 图像包里。

长 320 的背景按 `cover-background-top.png`（240×256）和 `cover-background-bottom.png`（240×64）提供实际打包片段，避免超出当前精灵单边 256 的限制。完整背景和完整参考图不重复打包。

## 复现与验证

在仓库根运行 `python game-art/adventure/tools/build_ui_assets.py`；制作中的地图未齐时可加 `--parts-only`。若指定正式 welcome120 帧，必须同时给 `--character <路径> --character-anchor <x> <y>`，保留其原像素和锚点，不进行二次缩放或量化。

再运行 `python game-art/adventure/tools/verify_ui_assets.py`。程序核对所有 PNG 的色数、尺寸、SHA、透明边界、九宫格两组目标尺寸与原角像素、封面图层重建。`preview/` 的单屏均为 240×320、1 倍像素，`screens-1x.png` 只是整屏拼接。

`ui-qa.json` 和清单预算使用逐行 RLE（计行表/调色板/小型头部并去重）的**明确估计**，不是 PNG 文件大小，也不是已经编入固件的最终字节数。实际 C/RLE 包大小由主任务打包后实测，必须 ≤160 KiB。预览、候选和无损母版不计入固件包。
