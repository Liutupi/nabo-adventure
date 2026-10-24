# 构建

ESP-IDF 6.0.2、ESP32-C3、8MB Flash；LVGL 9.5.0 及依赖由 firmware/dependencies.lock 锁定。Windows 执行根目录 build.ps1。

构建生成应用、启动器、分区表与合并镜像，并运行布局检查。源码包含生成后的字体和半身像，不要求重跑生成器。需要重新转换半身像时，使用 Pillow 13 运行 firmware/tools/generate_collection_portrait.py；原始帧来源和摘要见 art/nabo-white-coat-idle.json。

重建输出只作为新候选，不能替换v1.0.0已验收的发布字节。公开完整安装包复用与验收设备相同的已发布启动器；它与新 SDK 生成的启动器分别记录。
