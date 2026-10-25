# POST · 第 6 轮交付

状态：本轮人物、道具与宿主解码检查完成，等待用户美术与后续真机验收。未实现正式玩法，未写设备或固件生成目录。

正式入口为 `../../post-manifest.json`，其中 `animations` 与 `assets` 路径均相对 `art/`。两款都已制作，不需要用户先选一款才继续。

| 皮肤 | 内容 | 帧数 | 目标 |
| --- | --- | ---: | --- |
| post_a | 车窗待机、拉汽笛、甩信、被撞晃、送达欢呼 | 各 6 帧 | 半身 40px |
| post_b | 车窗待机、送达欢呼 | 各 6 帧 | 半身 40px |
| post_a | 结算欢呼 | 8 帧 | 全身 72px |

共 50 帧人物；12fps，只有待机循环。半身源锚 `(128,160)`，全身 `(128,224)`，正式源画布均为 256×256 RGBA。半身所有动作及两皮肤共用 36×40 运行画布、锚 `(22,40)`、同一缩放和调色板；全身为 49×72、锚 `(27,72)`。这是动作整体包络高度，不是每一帧独立裁到相同身高。

`frames/post/masters/` 保留高色原始渲染；`frames/post/<skin>/` 是正式 256²、64 色内、二值 alpha 交付；`frames/post/runtime/` 为明确给打包器使用的目标尺寸。预览和 GIF 没有混入运行帧目录。

A 是米白衬衫、海军蓝背带裤、短红领巾；B 是邮差短制服、皮质邮包。白 NABO 帽从未替换成列车员或邮差帽。新服装母版在 `games/post/source/`，用内置 imagegen 对实际原图作衣服编辑，A/B 各一次，prompt 与生成记录一并保存。没有逐帧 AI 生成。

运行角色只取新母版衣服，头、脸、帽、镜仍只读引用冻结的 `rig/common/front/` 源像素。共用头底缘夹带了旅行服领口，本包的局部 alpha mask 保留所有 y≤93 像素，并在 y94..100 保留 x121..137 的颈部，排除旧衣领；原共用源和所有保留 RGB 均未修改。没有镜像或新画表情。各部件为带原图切片的独立 SVG 包装、PNG 和显式 mask，骨骼合同见 `rig/post/rig.json`。

道具在规范目录 `games/post/`：96×88 火车头、4 帧车轮循环、车窗前景、车厢、六色信封、铁轨/枕木/组合直轨/岔口、可染色单白站台、羊、牛、煤堆、远山剪影。22 个原生资产都有可编辑 SVG；最大 9 个 RGBA 色（含透明）。轮子四状态同时保留独立静态引用与动画引用，打包报告据实计入两者。列车的司机胸口位置与合成顺序写在清单。

优先查看：

- `train-composition-contact.png`：两皮肤在车窗里的 240×320 原尺寸及 2× 组合。
- `post_a-*-contact.png` / `post_b-*-contact.png`：每帧原尺寸、3×，铁路实际底色与深底。
- `props-contact.png`：全部原生道具及 2×。
- `source-identity-review.png`：新衣母版与共用头组合；用于核对身份来源。
- `*-rail.gif` / `*-dark.gif`：12fps 近似时间的逐帧预览；`*-train-loop.gif` 用 12 帧对齐 6 帧人物和 4 帧车轮。

预览的铁路底色从当前 `adv_ui_map.c` WORLD[3] 读入并量化 RGB565。列车组合只检查美术比例与遮挡，未冒充实际游戏 UI 或真机截图。`first-*`、`repaired-pose-check`、`*-detail` 是自修审计图，不是正式运行资产。

在仓库根目录重建（Python + Pillow + NumPy）：

```powershell
& 'C:\Users\pc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' game-art/adventure/tools/post_build.py
& 'C:\Users\pc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' game-art/adventure/tools/post_verify.py
```

预览使用同工作区 Fortune 的 SourceHanSansCN-Medium.otf，来源 SHA 在 manifest。保留的 AI 母版是固定输入；重建不调用模型，也不需要网络。

生产 C 行解码校验只生成至指定独立目录：

```powershell
$env:CC='D:/nabo-passport-tools/w64devkit/bin/gcc.exe'
$env:PATH='D:\nabo-passport-tools\w64devkit\bin;'+$env:PATH
& 'C:\Users\pc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/build_adventure_assets.py --group post --output private/game-art-c/post --verify-c
```

结果与边界见 `QA.md`、`verification.json`、`packing-validation.json`、`reproducibility.json`。
