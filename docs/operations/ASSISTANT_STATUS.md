# 助手监督状态 / README

本任务按 gpt-6-astra / low 会话配置执行。已读仓库 AGENTS.md。仅交付本文件、`scripts/supervise.py` 与 `.local/assistant-supervisor/` 本任务状态；未修改 session_runner.py，未进行 Git、UI、外联、付费操作，未读取原始需求、env 或密钥。

## 实际检查与运行

2026-09-06 启动后台监督 PID **47112**，PID 文件 `.local/assistant-supervisor/pid`。每 60 秒本地检查，默认最多 10 小时；不需要 LLM 长驻轮询。运行记录为 `status.json`，退出记录为 `lifecycle.json`；以 PID 文件及实际进程为准，历史退出记录不代表新进程退出。

首次检查：assistant / hardware / pitch / software 均为 running、attempt=1；主控心跳 `at=2026-09-06T00:51:54.349654+08:00`、`state=working`，thread_id 与真实主控 `01a0725c-ccf9-7192-8446-f23b0f6d55e3` 一致。本次限定日志尾部未见结构化错误、429、断网或退出事件；并非完整历史无错误的保证。没有发送真实恢复消息。

## 监督范围与恢复合同

- 只读取 `.local/sessions/*.status.json`、对应同名 `.jsonl` 最后 64 KiB，以及 `.local/root-heartbeat.json`。日志只分类顶层 CLI `error`、`turn.failed`、`thread.failed`、`process.exited`、`session.exited` 事件；忽略提示词、工具输出及普通文本中的错误字样，不保存原文。计数是滚动尾部计数，不是累计。
- 会话状态记录 state / attempt / exit_code；子会话故障只观察。session_runner 已有 CLI 重试，监督器不启动、恢复或终止其他会话。
- 主控心跳 at 必须是带时区 ISO 时间，thread_id 必须匹配真实 ID；过期阈值默认 600 秒。缺失、损坏、未来时间或 ID 不符均不触发恢复。
- 还必须由同一主控心跳或同 ID 状态提供：state 为 failed/error/crashed/exited/disconnected/rate_limited，`recovery_required: true`，非空稳定 `failure_id`，以及不早于心跳、不晚于当前时间的带时区 `failed_at`。同一故障不得反复生成新 ID。主控任一 running/working/waiting/ui_wait/waiting_ui/waiting_for_input/retrying/completed/stopped 状态否决恢复。
- 当前心跳没有这些故障字段，因此当前仅观察。单纯心跳超时、正常长任务、UI 等待、子会话退出、普通错误日志，都不足以恢复主控。不以运行时长判死，不强制重启。
- 条件满足才执行官方 `codex queue --thread 01a0725c-ccf9-7192-8446-f23b0f6d55e3 --message 继续`。故障哈希在调用前持久化，每个故障至多调用一次；失败或超时也不重试该故障，跨故障至少退避 30 分钟。CLI 超时 30 秒。队列接受不等于主控已恢复。锁防止重复监督进程；保留 ledger.json 才能维持跨启动去重。

## 复现与停止

从仓库根目录运行：

```sh
python3 scripts/supervise.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 .local/assistant-supervisor/test_supervise.py
python3 scripts/supervise.py --once
python3 scripts/supervise.py --hours 10
```

`--once` 仅观察，不排队；已有监督进程时锁会拒绝第二实例。后台进程已启动，不需重复启动。随时停止：

```sh
touch .local/assistant-supervisor/STOP
```

也可核实 PID 后发送 SIGTERM。STOP 每秒检查；若正在调用 queue，等待该调用退出或最多 30 秒超时。后续手动重新启动前只删除本任务 STOP 文件，保留 ledger；最长运行由单调时钟限制，退出清除 PID 文件。

实际验证：合成测试通过 14 项判定/去重断言；独立临时合成状态、mock subprocess 验证官方命令参数、跨运行故障去重、30 分钟退避、STOP、短期限退出、结构化日志过滤。测试零真实 queue 调用。官方 `codex queue --help` 已验证命令存在。生产快照成功，后台存活检查见本任务状态。未验证真实故障恢复、长达 10 小时连续运行、网络断开后队列送达或重新联网恢复。

## 权限与账户待办

Ghostty CUA 已明确拒绝该 app：监督器不会绕过，也无法自动授予权限或输入密码。账户剩余 2% 时进行一次正常重置是用户要求，但目前没有证据证实该控件存在。待主控通过 Chrome 核查余额和正规重置机制；仅正规可用重置才可执行。本任务没有执行重置、购买或切换账号，也无法从这些本地状态监控余额。

监督器能在本机进程仍运行时观察已落盘状态；不能保证断网时 LLM 继续工作，不能修复网络、绕过权限、确认未落盘故障或保证主控写心跳。电脑睡眠/关机、磁盘故障、队列不可用会影响监督与恢复。故障证据不足时保持不操作。
