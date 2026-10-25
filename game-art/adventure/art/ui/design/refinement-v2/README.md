# Typography refinement v2 · 审阅提案

查看 `screens-1x.png`（三页各240×320）、`before-after-1x.png`（上原稿、下v2），以及单页 `cover.png` / `map.png` / `passport.png`。3x图只是最近邻放大，原始1x PNG为尺寸判断依据。当前尚未写入生产UI或获得用户定稿确认。

保留已选复古护照的海军蓝、米白和邮戳红，改以奶白留白为主。去掉多重土黄细框、密集纸边和格子底纹；当前卡用海军蓝实底和4px红色侧条，所有动态选中文字、数字、辅助文字均用奶白 `#fffaf0`，普通文字 `#203849`，次要文字冷灰 `#60707a`。人物仍直接使用冻结旅行服PNG，无缩放、无重绘头脸、无重新量化。

封面品牌是38px Montserrat Bold `NABO` + 12px有字距的 `ADVENTURE`，中文完整标题 `NABO 的冒险之旅` 为26px真粗体，实测墨迹210×26。独立纸底字标220×88（≤220×90）、4色；去掉无产品含义的红色“01”，改成无字旅行旗。封面全部共56色（含原样NABO），共享UI共19色。CTA 16px粗体，34px实底按钮，实际字形墨迹上下均留8px。

中文来自本机原始静态 `Noto Sans SC Bold`，字重700、版本2.002：

`C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf`

SHA256 `d1961be1161ea1be08496c920862d06ea5c23a757628f4fd69368de1d9f51bed`。

已读取原字体name/OS2表核对full name、Adobe版权、内嵌SIL OFL1.1、fsType0、静态700；没有用安装的non-release可变字体，也没有用日文字形版思源字体替代简体中文。本轮仅读取该原文件渲染预览，没有转换或复制系统字体文件分发。核验边界是本地文件元数据与SHA，不宣称它已经和某个官方发行包逐字节比对。

英文为现有LVGL依赖带的 `Montserrat Bold` v8.000、700：

`D:/AI PASSPORT XIAOZHI/table-undercover/repo/xiaozhi-esp32/managed_components/lvgl__lvgl/tests/src/test_files/fonts/Montserrat-Bold.ttf`

SHA256 `06a0e623bbaf4a0237f1d605affa269f9e431ff50c7143dcbb47b815edaba9bd`。正文12px保留已核验 `SourceHanSansCN-Medium.otf`、500、SHA `a94e558a2fe972bee4f46bce0843abff37063fd68c33f1e7d9058f6f09432b01`。完整路径、full name、版本、嵌入许可在 `fonts.json`；完整OFL许可文本在 `licenses/`；所需粗字子集为 `bold16-subset.txt` 和 `bold18-subset.txt`。

层级为：封面中文26、地图大站名24、护照页标题22、顶栏/当前卡18、卡片站名/按钮16、提示12。文本原生1x由真实字体光栅化，没有描边伪粗体，没有放大默认像素字。预览边缘为三个覆盖值；生产动态字库继续4bpp，因为当前 `adv_text.c` 固定读取4bpp，不用未经实现的2bpp节省作为预算承诺。

地图页是**字体、色彩、当前卡/邻站卡的版式示意**，其中12分/1枚印章是示例数据，不代表当前真机NVS。它不取代真实9世界纵向地图。接入时必须保留 `adv_path[]`、世界顺序、112px站距、node_x左右交替、camera/traveler平移/转身和上下键行为；示例中两个节点不能变成生产固定节点。真实世界渐变、地标和滚动继续由现有引擎画。

`layout-tokens.json` 给出可直接映射原地图站点卡的合同：卡片x沿用 `node_x<120 ? node_x+25 : node_x-137`；y=`node_y-26`；112×52；标题Bold16墨迹左上相对(8,8)，次行Medium12相对(8,30)，右侧成绩对齐相对x104。52px高为真实16/12字形保留至少8px边距，不能沿用40px卡高再塞粗字。标题baseline应由实际生成C字形 `ink_top + box_h + ofs_y` 求得并跑真实渲染，不把Pillow字号当C基线。顶栏仍32、底栏30；地图世界名用12px，避免18px长标题挤到右侧章数。

预算口径在 `qa.json`：旧UI73,709B + 当前启动NABO47,730B =121,439B；角色没有挪到travel分组后隐去。新字标实际RLE4,966B + 表368B + C3描述符估算32B =5,366B。保守保留旧字标/数字不扣减，再加新20/36数字4bpp估计5,476B，UI与启动角色合计估计132,281B，仍低于163,840B；最终需要真实全包C生成/ELF核量。若新4秒表演替换当前welcome，必须重新核总量，不能继续沿用47,730B。

通用动态字体单列app基线105,053B：本提案保留Medium，新增当前三页所需Bold16/18有界子集，4bpp位图与描述符/索引保守估计增加6,115B，合集字体估计111,168B。它没有重复计入UI精灵160KiB。若扩充字符或整套Medium替换为Bold，必须对实际生成C差额和最终app另行核量；不嵌入整份OTF/TTF，不在运行期分配字库或整屏帧缓冲。

复现：在仓库根目录运行 `python game-art/adventure/tools/ui_refine_v2.py`。所有输出限定本目录，只有 `ui_refine_v2*.py` 为新增源码，冻结生产UI、其他美术包、固件均未改。
