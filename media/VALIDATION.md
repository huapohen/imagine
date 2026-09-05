# 实际验证 · 2026-09-06

- 动态读取macOS系统代理并测试端口与目标请求；官方文档直连200约0.380秒、系统代理200约0.571秒，选择直连。明细 `network-check.json`。
- 官方文档指南、创建、查询、列表、按量计费、OpenAPI JSON均HTTPS下载成功。`sources.json`保存URL、抓取时间、本地SHA-256。SHA不是官方签名。
- `python3 video_client.py plan`：8条、每条12.00元、总96.00元；0次网络/付费请求。
- `python3 -m unittest discover -s …/media -p test_video_client.py`：8项全部通过。模拟网络，无真实API。覆盖精确规格价格、未知价格拒绝、额外付费媒体拒绝、免费首帧、请求前预占、超时不自动重提、8条/预算上限、task_id保存、失败预算保留、未授权路由拒绝。
- 客户端与两个制作脚本 `py_compile` 通过。
- 本机ffmpeg 9.0.1、ffprobe、Pillow可用；ffmpeg不含drawtext/subtitles，采用Pillow中文透明PNG叠加。
- 本机实际创建10秒640×360纯色测试夹具+5秒静图，装配输出 `verification/assembly_test_15s.mp4`。ffprobe：15.000秒、640×360、H.264。抽取第12秒画面并目视确认中文标签可读：`verification/label_check.png`。这是技术夹具，不是产品视频、不是2K生成结果。
- 装配脚本保留原分辨率，明确记录源时长/类型/哈希和静态尾帧；不会将10秒片声称原生15秒。

尚未验证：真实API Key权限/余额、真实生成任务及等待时长、实际输出2K像素尺寸/质量、CDN下载响应、真实软件屏幕录制及macOS权限、真实硬件。研究代理未提交任何付费任务、未寻找或读取凭据。最终生成与账单属于主控制器后续执行，不能把本验证报告当作已完成生成证明。
