# 精灵管线（v0.1.0 开发增量）

基础编码器先以合成几何图验证；2026-10-25 Windows 已在此基础上接入用户选定的旅行服与复古护照 UI、共用地图/印章。人物由源像素 SVG 部件骨骼生成，原高清 NABO 和批准旅行服锁在 `game-art/adventure/art/reference/`、`art/design/round1/v2/`。新图的设备观感另做真机验收，不能沿用旧占位封面的实测结论。

## 当前 manifest 整包入口

```sh
python tools/build_adventure_assets.py --group travel --group ui --group static --verify-c
# 后续游戏独立检验，先保留交付包，不替换固件中的共用目录：
python tools/build_adventure_assets.py --group post --output private/game-art-c/post --verify-c
```

整包工具只读取 manifest 显式声明的 runtime 帧和 SHA256；不猜源目录、不把 256² master 自动当成显示帧。验证大小、锚点、二值 alpha、共享调色板和重复 ID 后，复用下面的行 RLE 编码。240×320 这类背景自动拆成每边≤256的片段，目录保留偏移。六套九宫格固定角、重复边/中心；数字目录包含真实 advance。先在暂存目录完成 Python 对拍和可选真实生成 C/生产解码器对拍，才更新自身所有权清单中的输出；预算失败保留旧包及手工文件。

默认共用包的 215 个资源/283 帧已通过生产 C 逐行检查（11,822 行，另九宫格 912 行）。打包报告 `firmware/main/generated/adv_assets_generated.json` 区分精确 RLE/表与 C3 目录结构估算：travel 129,224 B、static 74,329 B、UI 73,709 B，UI 小于 160 KiB。新游戏每包限 260 KiB，使用同样的独立 manifest 合同。不得据此改写用户设备旧分区；真实 factory 上限见 BUDGET。

`adv_ui_art.c` 根据目录的原生画布/锚点/fps 播放，未运行时缩放或镜像。欢迎动作与 1.4 秒延后的开机语音共用起点，地图采用六帧转身→八帧走路→六帧回正；增量与整屏在启动和动作边界对拍。`ag_sprite_tint` 只重着色非透明索引，供同一白色印章源显示铜/银/金。

## 输入与生成

底层 `generate_adv_sprites.py` 仍处理单个动画；总 manifest、原生尺寸和播放合同由上面的整包入口负责。直接使用底层工具时，准备同尺寸、已经缩到最终显示尺寸的 RGBA PNG，逐个按播放顺序传入。256×256 的制作画布应先由上游骨骼渲染器按目标角色高度和固定锚点导出目标帧，不能把画布高度当作角色高度。

```sh
python3 tools/generate_adv_sprites.py \
  --name travel_idle --output private/sprites/travel_idle \
  --background '#183040' \
  path/to/000.png path/to/001.png path/to/002.png
```

- 全动画共享最多 64 个索引：0 透明，1–63 不透明。RGB565 黑色可以是不透明色，不会被误当透明。
- 先转 RGB565。超过 63 种不透明色时，用 Pillow 的共享调色板量化，不抖动；颜色选择是有损的。Pillow 版本变化可能改变量化结果，同环境重复打包应一致。
- 半透明像素必须显式指定背景色，先在宿主机与该色混合；完全透明仍保持透明。不同世界的背景不同，不能把某个 matte 结果宣称适用于任意渐变背景。没有半透明时可省略 `--background`。
- 单帧每边 1–256 px，最多 65,535 帧；打包限制总像素不超过 16 Mi，较大的动画要拆分。
- 生成 `.h`、`.c`、`.json`。报告包括源文件 SHA256、索引帧 SHA256、调色板、关键帧索引、RLE 和索引表字节数。报告字节数不包含 C 结构体、链接器对齐和其他固件开销。
- 每次输出前，Python 解码所有帧并与**量化后的索引帧**逐字节比较；失败则不输出新的文件。原始 PNG 到调色板的颜色损失需另做美术验收。

## Flash 格式与渲染

`firmware/main/adv_sprite.h` 定义 `adv_sprite_t`：尺寸、帧数、调色板、每帧关键帧索引、逐行偏移和字节流。生成数组和描述符均为 `const`，由链接器放在只读数据区。每帧有 `height + 1` 个偏移，行流由 `(长度, 值)` 字节对构成，长度 1–255；256 像素长的同色行拆为 255 + 1。

值 0–63 写入索引，其中 0 **擦成透明**；64 从上一帧同一位置继承。关键帧不允许继承。差分不比完整帧更小时直接写关键帧；最多连续 7 个差分帧，随机访问只需从最近的关键帧回放最多 8 行流，不依赖调用者的播放顺序或此前帧。

`adv_sprite_row()` 在一个调用者提供的行缓冲里还原索引，检查帧、行、容量、关键帧链、数据范围、run 长度、索引和行宽。传入数组必须确实具有声明的长度；这不是接收外部任意指针的文件解析器。失败后行缓冲内容不保证有效，渲染器会丢弃该行。

```c
#include "travel_idle.h"
// x/y 为目标画布左上角；调用者根据自己的锚点计算。
ag_sprite(g, &travel_idle, frame, x, y);
```

`firmware/main/generated/*.c` 已加入 CMake 与宿主渲染构建，正式共用页面引用目录中的不可变素材。素材及其数组必须保持不可变，且至少存活到显示列表不再引用它们。渲染使用 256 字节的栈上索引行，复用现有 8 行 DMA 条带，不分配整帧、运行时堆或 IRAM，也不做镜像。帧号、位置、素材指针、染色和层叠顺序都参与脏区处理；透明像素露出下层。

## 验证

```sh
python3 -m unittest discover -s tests -p test_adv_sprites.py -v
python3 tools/run_tests.py
./build.sh /path/to/esp-idf-v6.0.2
```

基础阶段的 10 项宿主测试涵盖：超过 64 色的共享量化、显式 matte、透明黑色区分、全透明动画、256 像素长 run、跨关键帧乱序访问、透明擦除、生成 C 的可编译性和逐帧解码、坏数据拒绝、裁剪/移动/删除/素材切换、80 组随机层叠画面、改变绘制顺序，以及增量帧与整屏重画和像素参考的比较。后来已补染色、九宫格及整包/正式页面回归；当前 UI 截图由生产渲染测试重新生成，文字缺字仍由宿主门禁检查。

可选的原生内存检查（macOS Clang；其他编译器需支持相同 sanitizer）：

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -g \
  -Ifirmware/main firmware/main/adv_sprite.c tests/adv_host/adv_sprite_sanitize.c \
  -o /tmp/nabo-adv-sprite-sanitize
/tmp/nabo-adv-sprite-sanitize
```

检查已知关键帧/差分样本和 50,000 组确定性坏行流，含输出缓冲哨兵。它是独立补充检查，不代替完整宿主门禁，也不证明 ESP32-C3 的帧率、栈余量或真机表现。Windows 旧外壳基线已做真机冒烟；正式美术新候选须重新做设备验证，见 VALIDATION/HANDOFF 的对应哈希。
