# 灵伴 LINGBAN · 最终视频报告

核验时间：2026-09-05T18:06:21.358758+00:00。**8条成片及2分钟合集全部完成**。

[播放2分钟合集](final/LINGBAN_8_concepts_2min.mp4) · [8款总览图](qa/ALL_8_CONCEPTS.jpg) · [合集来源记录](final/LINGBAN_8_concepts_2min.provenance.json)

## API状态与预算

八个既有MiniMax-H3任务全部经API确认`succeeded`，每项用量15输出秒、0输入视频秒；01/02各1张首帧参考图，03–08无图输入。确认输出总计120秒。仅轮询和下载既有任务，未重提、未付费重做。

**本地预占96.00元，用户上限100.00元，未预占额度4.00元。** 按已抓取官方2K刊例价0.80元/秒，120秒对应96.00元；各任务≤5张图免费。此为预算账本与官方刊例价核算，不是账户账单结算凭证。未查询账单、余额、发票或退款，不声称账户已最终扣款96元；4元也不是账户实际余额。无收费视频参考或Context-IR，无付费语音。

[官方能力/价格核验](API_CAPABILITIES.md) · [公开来源及快照哈希](sources.json) · [脱敏API状态与成片规格](qa/final_specs_status.json)

## 成片

全部单片：**15.000秒、2560×1440、24fps、H.264**，音轨AAC / 48kHz / 单声道。原片全部为2560×1440、24fps、实际15.084秒，带AAC / 32kHz / 双声道及MiniMax AIGC元数据；后期保留原像素尺寸，仅裁至15秒，没有放大、静图补时或付费补拍。

所有片常驻「AI概念演示 · 非已生产实机」及「外观与功能待工程验证 / 屏幕内容为合成示意」，附中文旁白、字幕。旁白使用本机已有Tingting，通过系统say本地合成；保留原声10%线性增益混入。

| 片段 | API | 实测LUFS / dBTP | 检查与来源 |
|---|---|---|---|
| [01 晶鼠 · 透明城堡产品 Hero](final/01_crystal_mouse_focus.mp4) | succeeded | -16.00 / -1.50 | [4帧联系表](qa/01_crystal_mouse_focus_contact.jpg) · [来源/后期](final/01_crystal_mouse_focus.provenance.json) · [音量](qa/01_crystal_mouse_focus_loudness.json) |
| [02 晶鼠 · 由人批准的办公搭档](final/02_crystal_mouse_workday.mp4) | succeeded | -16.09 / -1.51 | [4帧联系表](qa/02_crystal_mouse_workday_contact.jpg) · [来源/后期](final/02_crystal_mouse_workday.provenance.json) · [音量](qa/02_crystal_mouse_workday_loudness.json) |
| [03 键盘边栏 · 专注节奏](final/03_keyboard_sidecar.mp4) | succeeded | -16.06 / -1.50 | [4帧联系表](qa/03_keyboard_sidecar_contact.jpg) · [来源/后期](final/03_keyboard_sidecar.provenance.json) · [音量](qa/03_keyboard_sidecar_loudness.json) |
| [04 桌面晶球 · 私人待办入口](final/04_desktop_orb.mp4) | succeeded | -16.27 / -1.50 | [4帧联系表](qa/04_desktop_orb_contact.jpg) · [来源/后期](final/04_desktop_orb.provenance.json) · [音量](qa/04_desktop_orb_loudness.json) |
| [05 显示器挂件 · 看得见的静音](final/05_monitor_charm.mp4) | succeeded | -16.04 / -1.51 | [4帧联系表](qa/05_monitor_charm_contact.jpg) · [来源/后期](final/05_monitor_charm.provenance.json) · [音量](qa/05_monitor_charm_loudness.json) |
| [06 会议 Puck · 明确共享的会议结果](final/06_meeting_puck.mp4) | succeeded | -16.17 / -1.51 | [4帧联系表](qa/06_meeting_puck_contact.jpg) · [来源/后期](final/06_meeting_puck.provenance.json) · [音量](qa/06_meeting_puck_loudness.json) |
| [07 桌垫模块 · 温和休息建议](final/07_deskmat_module.mp4) | succeeded | -15.89 / -1.51 | [4帧联系表](qa/07_deskmat_module_contact.jpg) · [来源/后期](final/07_deskmat_module.provenance.json) · [音量](qa/07_deskmat_module_loudness.json) |
| [08 机器人扩展 · 由人确认的小任务](final/08_robot_extension.mp4) | succeeded | -16.40 / -1.50 | [4帧联系表](qa/08_robot_extension_contact.jpg) · [来源/后期](final/08_robot_extension.provenance.json) · [音量](qa/08_robot_extension_loudness.json) |

合集按01–08顺序，视频与音频均从0.000开始、长120.000秒，容器精确120.000秒，2560×1440。拼接时修正AAC预滚时间戳，仅重编码音频去除21ms容器尾差，视频不二次编码。 [原片元数据脱敏记录](qa/source_metadata.json) · [合集音量](qa/compilation_loudness.json)

## 目视检查与边界

已实际查看8条各1/5/9/13秒的联系表，共32帧。中文标签和字幕可读、未裁切；主要物体可辨识，透明/晶体城堡风格贯穿。检查是抽帧和客观音量测量，不冒称完整逐帧验收或人工听音。

- 01/02以参考CAD起镜，随后转为写实鼠标；外壳、内部城堡与线缆形态有生成变化，并非严格CAD尺寸一致。只作外观/交互概念。
- 06会议人数与原始六人分镜不完全一致，圆盘演绎成透明圆顶摆件；不作为真实同意记录或会议系统验证。
- 07桌垫模块未证明夹持结构可实现；健康叙事仅休息建议、明确不作医疗判断。
- 08机器人路线靠近桌边，急停/安全距离没有工程验证；不得据此承诺运动安全。
- 生成屏幕存在合成文字/图形，旁白中的提醒、审批与共享均是叙事设想，不证明软件与硬件已联调。

原片保持不变，保留原提供方AIGC元数据。后期重编码不冒称原始数字签名仍绑定成片；来源哈希与成片哈希独立记录。企业内容禁止解读为隐蔽监控或个人情绪/生理评分。

## 复现

从项目根运行 `python3 media/final/produce.py`；脚本只做本地后期，完成项可跳过，不访问API、凭据或预算账本。八条齐全时制作合集。公开报告不包含Key、原始凭据输入、私有账本下载URL或认证响应全文。
