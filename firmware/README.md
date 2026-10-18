# NABO 游戏特辑固件

入口为 `main/collection_main.c`，其余说明和验证边界见仓库根目录 README.md 与 docs/VALIDATION.md。

构建：ESP-IDF 6.0.2，运行根目录 build.ps1。候选输出位于 build-idf6/；这些文件不代表已完成真机验收，不可据此直接发布。

BSP 源自深潜独立版/FoloToy 官方，保留引脚和许可。IDF 6 适配仅涉及明确驱动依赖、包含顺序及构建约束。
