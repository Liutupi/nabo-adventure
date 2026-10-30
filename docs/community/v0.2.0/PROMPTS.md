# v0.2.0 封面与详情来源

封面沿用此前已获认可的NABO宣传插画。使用内置image_gen编辑，唯一请求为把左下角“v0.1.0 · 预览版”改成“v0.2.0 · 预览版”，保持人物、帽标、场景、其余文案和3:4构图。工具明确完成后复制最终PNG到本目录，实际打开上传文件，核对NABO身份、版本和“AI宣传插画 · 非实机画面”标注。仅作目视一致性确认，不宣称全图逐像素不变。

四张详情由原有 `tools/prepare_community.py` 的HTML/SVG组件排版，读取当前 `docs/images/ui/` 的生产C宿主截图，使用相同Noto Sans SC Bold / Space Mono字体。字体和许可复用 `../v0.1.0/assets/`，没有用AI重绘游戏截图；图上均标注含演示数据。最终JPEG已逐张打开确认，无加载占位、裁切或未完成任务画面。

源截图与文件SHA见 `graphics-manifest.json`；最终上传图的尺寸/哈希/目视记录见 `image-validation.json`。更新材料与v0.1.0目录分开保存，不覆盖历史发布凭据。
