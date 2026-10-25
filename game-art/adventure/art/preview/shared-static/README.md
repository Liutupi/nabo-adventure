# 第 4 轮：复古护照手账共用静态美术

状态：代理完成原生尺寸、背景与联系表检查；等待用户美术验收，尚未代表真机效果验收。

入口：`../../shared-static-manifest.json`（清单内路径均相对 `art/`）。主美术总清单由主代理管理，本包未改动它。

交付包括 9 世界各 6 个逻辑图块（32×32）、9 个地标（96×96）、8 个游戏印章和护照亭徽记（96×96）、7 个资源图标（16×16）。雪坡的 `snow-drift` 引用雪山同一资产，所以共有 54 个逻辑图块、53 个图块文件、78 个独立资产。

每个 PNG 都有同名可编辑 SVG，SVG 的分组对应结构、轮廓和细节。PNG 为直接在目标像素网格绘制的交付基准；SVG 的几何便于编辑，修改几何后应修改对应 Python 绘图源并重建，避免不同 SVG 渲染器的描边取整改变像素。没有将大图缩成图标，没有抖动、柔化、渐变或半透明边缘。

所有图形为本轮原生绘图；配色直接读取用户选定的 `ui/design/round3/01-passport/palette.json`。印章仅使用纯白 `#FFFFFF` 与透明，外圈没有文字，供引擎染色和排外圈字。字体只用于预览说明，不进入资产。没有绘制或改动 NABO 形象，也没有引用已撤回的旧深潜人物 SVG。

地图与地标的背景来自当前 `firmware/main/adv_ui_map.c` 的 `WORLD` 数组，先按固件 RGB565 量化再显示；深色 UI 背景与铜印色来自 `adv_ui_internal.h`。护照亭目前按固件路径索引使用港口底色，未擅自改成小镇。背景、调色板、绘图源和字体的 SHA 均在清单 provenance 中。

联系表均含 1× 原始尺寸和整数倍放大：

- `tiles-contact.png`：全部 54 个逻辑图块，实际世界底色。
- `landmarks-contact.png`：9 个地标，实际世界底色。
- `stamps-contact.png` / `stamps-world-contact.png`：原白线深底，以及实际世界底色的引擎铜色模拟。
- `icons-contact.png` / `icons-world-contact.png`：7 个原尺寸图标及 6× 放大。
- `repeat-seams-contact.png`：9 个声明可平铺图块的 3×3 重复。

每件另有原尺寸实际背景预览；图块位于 `tile/`，地标 `landmark/`，印章 `stamp/`，资源 `icon/`，重复图块 `repeats/`。单资产路径与对应背景可从清单 `previews` 查找。

从仓库根目录运行：

```powershell
& 'C:\Users\pc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' game-art/adventure/tools/build_shared_static.py
```

依赖 Python 与 Pillow。默认预览字体为同工作区 `nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf`，脚本会核验 SHA；换位置时以 `--font` 指向相同字节的字体。脚本只写本包获准的资产、预览与独立清单，不生成固件代码。各源文件均小于 400 行。

详见 `QA.md`、`validation.json` 与 `reproducibility.json`。源文件改变后应重新执行视觉检查，不能仅沿用本轮记录。
