# 社区 v0.1.0 图文材料

用户要求在AI Passport玩法社区发布，封面与既有NABO系列对齐，并重写玩法说明。已提交到账号土皮的条目1662、修订3808，随后审核通过，**已公开发布**：[社区详情](https://ai-passport.folotoy.cn/plays/1662/?v=3808-2)。提交与公开状态以`submission-status.json`为准。

## 图片顺序

1. `01-cover.png`：内置image_gen新生成的宣传主视觉，NABO身份与已批准旅行服保持，采用声音实验室系列的深色底、粗字、青金配色。图中标明AI宣传插画/非实机画面。
2. `02-passport.jpg`：地图、护照、八站名称和铜银金印章。
3. `03-night-ski.jpg`：萤火虫与雪崩速降的操作和结束条件。
4. `04-rocket.jpg`：点火、飞行、地月转移与着陆。
5. `05-controls.jpg`：横拿三键映射，补充跳一跳、深潜、小火车。

图片均3:4。详情图1080×1440、浏览器按画布边界导出JPEG；原固件画面未AI重绘，含演示数据并在图上标注。文字使用Noto Sans SC Bold和Space Mono，许可证附assets目录；画面来源和哈希见`graphics-manifest.json`，安全边界检查见`layout-validation.json`。

## 文案与固件

- [COPY_ZH.md](COPY_ZH.md)：介绍、每款目标/操作/结束条件、解锁门槛、安装和更新说明。
- [PROMPTS.md](PROMPTS.md)：封面工具、参考与最终提示词记录。
- [GitHub v0.1.0](https://github.com/Liutupi/nabo-adventure/releases/tag/v0.1.0)：本次上传使用其中的完整镜像，1,881,520B，SHA256 `2bca7adda06ea0b0e1cc3f4959781583983172c0b6163c2b1768c117e4b979d0`。应用部分原样为8897cd9e。
- 完整安装会清除原设置/成绩，首次完整安装尚未真机验收。需要保留数据请用GitHub保护式应用升级，不为本次社区提交重建或修改固件。

图文生成没有操作用户工牌，也不改变GitHub既有Release或标签。社区提交后须从实际保存页面重新下载图片/固件核对，并分别记录已提交、审核中、已公开。

## 已保存内容核对

五张服务端WebP均为900×1200，顺序及外观与本地五图相符；网页保存的标题、介绍、完整使用方法和更新日志逐项比对通过。社区固件从本修订实际保存的href重新下载，1,881,520字节，与GitHub完整镜像逐字节相同；查看`image-validation.json`和`firmware-validation.json`。固件采用创作者认证下载核对，匿名固件下载暂未独立测试；公开页面及“安装最新版”入口已实际打开核实。

`submitted-review.jpg`保留最初审核中凭据，`published.jpg`为公开页面凭据。无需重复新建项目或撤回已提交内容，也不要调用旧项目的记录脚本覆盖历史结果。
