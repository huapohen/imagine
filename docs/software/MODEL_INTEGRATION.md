# 本机临时模型接入

默认离线。`./software/start.sh --local-model-test` 才读取根目录 Git 忽略、当前用户持有且权限0600的 `.env`；不执行 shell，不读其他项目凭据。容器 Dockerfile 只复制软件源码与网页，不包含根 `.env`，网络监听模式禁止启用模型测试。此实现为临时本地验证，不是生产模型服务。

## 固定授权范围

- 第三方 WanAPI：`https://wanapi-dev.wanmol.com:29527/v1/responses`。
- 请求模型 `gpt-6-astra`、`reasoning: {effort: "medium"}`、`max_output_tokens: 1536`、`stream: true`、`store: false`。
- 经预检的直连 TLS，忽略环境代理、不接受重定向。每次子进程45秒硬期限、传输累计最多2MiB（SSE事件开销）、无自动重试。
- 共20次调用预留上限；`software/data/model-budget.sqlite3` 是跨服务重启、跨测试数据库共享的持久化账本，失败同样计次。不要删除账本重置预算。它是本机安全边界，不抵御能修改本机文件的用户。
- `.env` 支持 `LINGBAN_ENV=local-test` 及 `LINGBAN_MODEL_ENABLED/PROVIDER/BASE_URL/NAME/REASONING_EFFORT/API_KEY/MAX_CALLS/MAX_OUTPUT_TOKENS/TIMEOUT_SECONDS`。本文件不包含凭据或完整配置示例。

## 产品行为与权限

员工在「行动之前，等你点头」选择会议、阻塞或休息固定合成场景，勾选本次处理同意后生成草稿。只发送代码中的固定合成文字，不读取任务、姓名、企业结果、传感器或任何自由输入。企业与插件令牌均不能调用。该同意独立于业务结果分享，不改变已有授权或撤销语义。

`GET /api/model/status` 显示启用状态与调用预算；`POST /api/model/propose` 接受 `scenario`、`idempotency_key`、`synthetic_consent: true`，拒绝额外字段。重复幂等键不重复请求模型、不重复产生动作；不同场景复用同一键返回409。中途崩溃的预留不重放外部请求，返回409。

模型输出是未信任文本，仅接受JSON对象的title/body；严格限制160/2000字，禁止工具调用、拒绝包与未完成输出，允许完整JSON代码围栏。该网关在 `response.completed` 的 `output` 可能为空，因此收集 `response.output_item.done` / `response.output_text.done` 并等待 completed，拒绝失败流。模型只能创建pending动作，无法选择归属、权限、审批状态或外发渠道。前端使用HTML转义展示。批准仍走既有原子审批，仅写本地outbox；重复批准不重复写入，拒绝不产生outbox。

禁用、超额、超时、提供方错误或解析失败会使用固定离线草稿；界面明确提示降级。后台主动提醒继续运行确定性证据规则，模型不会自动消费提醒、更改专注策略或读取个人任务。输出可能包含事实错误，必须人工核对。

## 复现

```sh
cd software
python3 -m unittest discover -s tests -v
python3 -m lingban.live_model_test --local-only-synthetic-opt-in
```

实时脚本启动随机回环端口、内存合成数据库，以员工HTTP调用三场景，验证企业403、pending、重复请求无新调用和outbox为空；只有明确参数才会产生费用。脚本仅打印配置、用量、耗时、来源与断言结果，不打印模型正文、API Key或原始响应。每次运行消耗最多3次现有预算；剩余不足3次时在调用前退出。模型服务预算用尽则离线回退，不假称真实通过。

## 实际验证（2026-09-06）

本地软件58项自动测试通过；新增覆盖角色/同意、拒绝未知自由输入、跨用户隔离、模型不执行、幂等、预算持久化、超时无重试、错误脱敏、拒绝恶意/未完成输出、标准SSE与网关空终止output兼容。`node --check software/web/app.js` 通过。真实模型测试结果见下方记录。

兼容性诊断发现：chat/completions返回500 convert_request_failed；Responses必须使用列表input与stream=true；SSE终止包不一定聚合output。所有诊断均计入20次总预算，未降低模型或推理强度。第三方是否严格兑现模型别名和推理配置无法由客户端独立认证；只能证实发送配置及提供方响应。未完成生产部署、多用户配额、第三方保留策略认证或真实硬件验证。


最终三场景从真实HTTP入口通过，均 source=model、pending、重复幂等未增加调用、outbox为空：

| 合成场景 | 耗时 | input tokens | output tokens | total tokens |
| --- | ---: | ---: | ---: | ---: |
| 会议要点 | 37.60秒 | 109 | 872 | 981 |
| 阻塞推进 | 29.11秒 | 105 | 597 | 702 |
| 休息建议 | 11.37秒 | 109 | 188 | 297 |

最终成功三次共1980 tokens，输出均低于1536。含诊断总预留19/20次，剩余1次；不要再次运行三场景脚本消耗剩余配额。失败诊断未统一返回usage，因此不宣称1980是整个接入过程总消费，也无法由现有回执准确计算人民币费用。第三方原始响应和Key未写入报告或审计；合成草稿仅在测试内存数据库存在，测试结束已关闭。后续持续演示可用默认离线模式。


主控最终补充：新增退出模拟隐私时清除旧屏幕提示的回归后，全套59项通过；模型UI另有9项隔离浏览器检查通过，包含本次同意重置、默认离线、未同意不提交、不写outbox及移动宽度；没有新增模型调用。
