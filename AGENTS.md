# 维护约定

这是《NABO 的冒险之旅》独立离线游戏合集，不是小智固件。先读 `docs/HANDOFF.md` 和 `game-art/adventure/DESIGN.md`，按 nabo-passport-game skill 的流程工作。

- 规则以 `game-art/adventure/prototype/adv_core.js` 为准：先改原型，重录 `tests/adv_golden`（`node tests/adv_golden/record_golden.js`），再改 C，跑 `python3 tools/run_tests.py`。
- NABO 的脸、眼镜、发型、白帽和帽标不能改，只能换衣服；帽标不能左右镜像。唯一身份依据是 `game-art/adventure/art/reference/nabo-idle-original.png`（1254 原始高清全身图，SHA256 见同目录记录），必须先实际查看。旧 `game-art/dive/rig` 是另一份重绘稿，不能当成本项目的身份依据；用户已拒绝据此制作的第 1 轮初稿。写美术提示词时只称“NABO”，并附经核对的原图锁定身份，不凭模型记忆重画。
- 页面切换、游戏释放与音频读写由 `adv_main.c` 的同一把锁串行化，禁止释放游戏状态时仍有 PCM 消费者。
- 不启动 Wi-Fi、蓝牙、小智、语音服务或麦克风。所有素材嵌入 app，不读写 assets / files 分区，不改分区表和板级引脚。
- 设置和成绩使用 NVS 命名空间 `nabo_ui`；不改已有键（`jump_best`、`dive_best` 等），新键用 `adv_` 前缀。不得用擦除 NVS 掩盖初始化错误。
- 整数运算；不把代码放进 IRAM；每个源文件尽量不超过约 400 行。
- 修改 UI 后重新生成字库并跑渲染测试（截图会更新到 `docs/images/ui/`）；改输入、音频、休眠或页面切换需实机验证。
- 构建和宿主测试不能代替实体按键、声音和唤醒验收。正式发布须绑定已验收镜像的 SHA256。
- `private/`、凭据、设备备份、NVS 和原始设备日志不得提交或上传。保留全部第三方许可。
- 2026-10-25 用户补充：在能保证质量时由 Codex 自行完成；只有具体动作反复修正仍衔接不好，才请 Grok 补片。需要 Grok 时先写本地明确任务并告知用户绝对路径，入口见 `GROK_HANDOFF.md`。当前没有正在委派的 Grok 片段。
- 开机须有已选 NABO 形象出场，并配合说原文 `NABO,陪你冒险`；沿用前作“阳光小男孩”音色与可跳过、离开即停播的生命周期。不要用未经批准的新形象或新音色替换。
