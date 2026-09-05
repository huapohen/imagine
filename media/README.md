# 灵伴视频研究与制作

官方核验见 `API_CAPABILITIES.md`，完整出处与快照哈希见 `sources.json`。本目录研究代理未读取原始需求/凭据、未调用付费生成。8条原生H3/2K/15秒方案刊例价96元。创建与账单由主控制器负责。

## 复现

```sh
cd /Users/lwblx/huapohen/agent/execute/enterprise_work/imagine/media
python3 video_client.py plan
python3 -m unittest test_video_client.py
# 原生15秒片烧录标签；保留提供方原始尺寸，不将上采样冒称原生2K。
python3 assemble_concept.py --video generated/01_crystal_mouse_focus.mp4 --output edited/01_crystal_mouse_focus.mp4 --title '灵伴晶鼠 · 掌心城堡'
# 可选：真人录制的旁白（voiceover_zh在requests.json），覆盖生成音频。
# 添加 --voiceover narration.wav
# 已有6/10秒AI片源 + CAD静图 = 后期15秒，自动记录provenance而非冒称原生15秒。
python3 assemble_concept.py --video source10s.mp4 --still ../hardware/renders/mouse.png --output edited/composite.mp4
# macOS真实软件屏幕录制；先选中本地演示窗口、全屏，仅显示合成数据。
python3 record_screen.py --list
python3 record_screen.py --screen-index 1 --seconds 15 --output recordings/software-demo.mp4
python3 assemble_concept.py --video recordings/software-demo.mp4 --software-recording --output edited/software-demo.mp4 --title '灵伴本地软件 · 合成数据'
```

屏幕索引必须从本机实时列表取得，示例1不是固定设备。录屏不录麦克风，macOS可能要求系统屏幕录制权限；未授权时不能声称完成录屏。`assemble_concept.py`依赖已有Pillow和ffmpeg/ffprobe，用透明PNG烧录中文，避免当前ffmpeg缺少drawtext/subtitles的问题。默认静音，可添加自有旁白，不下载未经授权配乐。

## 提交与恢复

`MINIMAX_API_KEY`只从环境变量读，不保存在请求/账本或日志。`submit --budget-cny 100 --id …`每次仅提交一条。先将首帧图片以data URL或HTTPS加入对应payload.content（role=first_frame），去掉ratio；参考图免费总数不得超过5。始终保留原始requests和CAD来源。

账本在请求前预占12元；提交后保存task_id；每ID禁止再次提交。网络超时也不释放预占。若task_id未落盘，`list`查看最近任务，与时间/模型/时长/分辨率人工核对，确认身份后`attach`；不可猜测。最近任务窗口7天。失败和取消未核实退款前仍占预算。`poll`只查询一次，不内置等待。`download`只向查询返回的已核验官方CDN域名发送无凭据下载，未知CDN先核验官方文档，不把Key发往CDN。

## 验证与局限

见 `VALIDATION.md`。H3接口/价格为2026-09-06公开文档快照，并非真实账户权限或余额验证。官方未给出输出2K的固定宽高像素表，应保留生成原始分辨率并用ffprobe记录，不强行声称2560×1440。下载SHA-256只能证明本地文件一致性，不能替代提供方签名。没有真实硬件、功能工程验证、医疗测量或量产证明。
