# 灵伴 LINGBAN 视频交付

本地后期完成 **8/8** 条。更新时间：2026-09-05T18:06:21.430414+00:00。

全部成片来自MiniMax-H3原生2560×1440、请求15秒的AI概念片；原片实际约15.08秒，后期裁为精确15秒，无放大、无补静帧。不得作为已量产/已验证实机证据。

统一常驻中文标签「AI概念演示 · 非已生产实机」，中文旁白及字幕由macOS已有婷婷声线本地合成，不下载、不调用付费语音；原片环境音以0.10增益混入，成片测量音量见qa/*_loudness.json。源AI生成标记保留于未修改原片，重编码成片不冒称原始签名仍有效。

| 成片 | 时长/尺寸 | QA |
|---|---|---|
| [ 晶鼠 · 透明城堡产品 Hero ](final/01_crystal_mouse_focus.mp4) | 15秒 / 2560×1440 | [联系表](qa/01_crystal_mouse_focus_contact.jpg)、[来源记录](final/01_crystal_mouse_focus.provenance.json) |
| [ 晶鼠 · 由人批准的办公搭档 ](final/02_crystal_mouse_workday.mp4) | 15秒 / 2560×1440 | [联系表](qa/02_crystal_mouse_workday_contact.jpg)、[来源记录](final/02_crystal_mouse_workday.provenance.json) |
| [ 键盘边栏 · 专注节奏 ](final/03_keyboard_sidecar.mp4) | 15秒 / 2560×1440 | [联系表](qa/03_keyboard_sidecar_contact.jpg)、[来源记录](final/03_keyboard_sidecar.provenance.json) |
| [ 桌面晶球 · 私人待办入口 ](final/04_desktop_orb.mp4) | 15秒 / 2560×1440 | [联系表](qa/04_desktop_orb_contact.jpg)、[来源记录](final/04_desktop_orb.provenance.json) |
| [ 显示器挂件 · 看得见的静音 ](final/05_monitor_charm.mp4) | 15秒 / 2560×1440 | [联系表](qa/05_monitor_charm_contact.jpg)、[来源记录](final/05_monitor_charm.provenance.json) |
| [ 会议 Puck · 明确共享的会议结果 ](final/06_meeting_puck.mp4) | 15秒 / 2560×1440 | [联系表](qa/06_meeting_puck_contact.jpg)、[来源记录](final/06_meeting_puck.provenance.json) |
| [ 桌垫模块 · 温和休息建议 ](final/07_deskmat_module.mp4) | 15秒 / 2560×1440 | [联系表](qa/07_deskmat_module_contact.jpg)、[来源记录](final/07_deskmat_module.provenance.json) |
| [ 机器人扩展 · 由人确认的小任务 ](final/08_robot_extension.mp4) | 15秒 / 2560×1440 | [联系表](qa/08_robot_extension_contact.jpg)、[来源记录](final/08_robot_extension.provenance.json) |

[按01–08排序的2分钟合集](final/LINGBAN_8_concepts_2min.mp4)

复现：`python3 media/final/produce.py`（从项目根运行，处理已下载且尚未成片的全部视频，八条齐备后自动合并）；单条 `--id 03_keyboard_sidecar`；最多监看30分钟 `--watch-seconds 1800`。此脚本只读requests与generated，不接触API/Key/账本，不能付费重做。

字幕语义仅为概念叙事，屏幕数据为合成示意；健康仅休息/舒适度建议。原片动作或几何可能存在生成误差，抽帧不等同于真实硬件或功能验证。
