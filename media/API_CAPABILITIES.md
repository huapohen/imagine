# MiniMax 视频接口核验 · 2026-09-06

已通过 HTTPS 实际抓取官方文档；来源、时间和本地快照 SHA-256 见 `sources.json`。SHA-256 仅用于快照一致性，不冒称官方签名。未调用付费 API、未读取或寻找任何凭据。

## 可直接满足用户规格

- 模型精确值：`MiniMax-H3`，不是 H3-Max，也不是旧 Hailuo 模型。
- 原生输出支持 `2K`；时长支持 4–15 的整数秒，**原生15秒可用**。
- 创建：`POST https://api.minimax.cn/v2/video_generation`。
- 查询：`GET https://api.minimax.cn/v2/query/video_generation/{task_id}`。
- 成功：`task.status=succeeded`，`task.content.url` 是限时下载地址；最近7天内可查询，过期下载地址可重新查询。
- 纯文本使用 `content:[{"type":"text","text":"…"}]`，`ratio:"16:9"` 必填且不能adaptive。提示词≤7000字符。
- 首尾帧可用 `image_url` + `role:first_frame/last_frame`；I2V省略ratio，以参考图片比例为准。

## 预算

官方 `pricing-paygo.md`「视频」：H3 2K **0.80元/秒**，H3 768P 0.50元/秒。H3-Max 480P 0.33元/秒、768P 0.50元/秒，但**不支持2K**。H3图片≤5张免费，超过部分0.20元/张；音频输入免费，视频参考2K按0.80元/秒另计。Context-IR按token额外计费。

本方案：**8条 × 15秒 × 0.80元 = 96元**，授权总上限100元，剩余4元不足重做一条15秒片。最便宜的原规格候选就是H3 / 2K / 15秒、纯文本或一张首帧图，无视频参考、无Context-IR。先提交透明鼠标2条（24元），合格后继续其余6条（72元）；不自动重试付费创建请求。失败/网络不确定请求保留预算占用，核实账单前不释放。

没有官方证据证明当前价格时必须拒绝提交；不能靠自定单价绕过。`video_client.py`仅支持已核验的H3纯文本或≤5张免费图片请求，并校验本地价格证据SHA-256、预算100元和最多8次提交。账本为本工作批次预算，不代表账户余额、税务发票或并发其他应用支出。账户权限及实际余额仍未验证。

## 主控制器接口

```sh
cd /Users/lwblx/huapohen/agent/execute/enterprise_work/imagine/media
python3 video_client.py plan --requests requests.json
# 主控制器从安全来源设置 MINIMAX_API_KEY，不写命令历史/产物。
python3 video_client.py submit --requests requests.json --id 01_crystal_mouse_focus --budget-cny 100
python3 video_client.py poll --id 01_crystal_mouse_focus
# poll每次只做一次请求，至少间隔10秒；成功后download。
python3 video_client.py download --id 01_crystal_mouse_focus
```

客户端默认账本 `video_ledger.json`，响应中只保留task_id/status/usage/限时下载地址，绝不打印Key、原始错误body或下载URL。提交前在磁盘保留摘要及预算预占。若创建超时，禁止盲目重试；使用 `list` 查询最近任务，人工核对后 `attach --id … --task-id …` 恢复。所有付费创建由主控制器执行。

## 质量与真实性

`storyboards.md`有8条15秒镜头、旁白与prompt。每条由后期烧录常驻「AI概念演示 · 非已生产实机」，末尾说明「功能/外观待工程验证」。不要让模型绘制中文界面或关键标签；后期叠加。健康仅舒适度/休息建议；企业展示合成数据、明确分享与≥5人聚合，禁止秘密监控。分辨率和时长必须用ffprobe验收，不能将插帧/放大当作原生2K。

原生15秒生成是首选。若质量不足，`assemble_concept.py`可把授权生成的6/10秒片源与CAD图/真实软件录屏组合成15秒，必须记录片源实际长度；这种剪辑不等同于原生15秒AI生成，不能虚报。由于本轮96元预算无足够余量，任何重新生成应先核实账单及剩余额度。
