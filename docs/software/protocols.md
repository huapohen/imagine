# 协议支持范围与版本

本原型未通过 MCP 或 A2A 官方认证/互通测试。HTTP REST 接口不被称作 MCP/A2A；真实协议适配入口分别是 stdio 与 `/a2a` JSON-RPC。

## MCP 2025-06-18

```sh
cd software
LINGBAN_TOKEN='启动终端员工令牌' python3 -m lingban.mcp
```

每行 UTF-8 JSON-RPC 2.0，不使用旧式 Content-Length framing。stdout 仅 JSON-RPC，诊断走 stderr。单行最大 32 KiB，溢出后丢弃至换行再恢复解析。

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"local-demo","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"tasks_list","arguments":{}}}
```

实现 initialize 版本协商、notifications/initialized、ping、tools/list、tools/call。客户端若不支持服务端返回版本，应依官方协议断开。未初始化调用 tools 返回 -32002；未知方法 -32601；未知工具或参数错误 -32602；解析错误 -32700；请求格式错误 -32600；通知没有响应。工具内部权限或业务错误返回 CallToolResult `isError: true` 与文本内容。

工具：tasks_list、events_ingest、action_propose、enterprise_summary。转发至本地 HTTP 服务复用鉴权与员工/企业权限；只接受 localhost 或 127.0.0.1 URL，禁用代理和重定向，避免令牌被转发至外网。无 approval 自动执行工具。员工令牌调用 enterprise_summary 返回业务权限错误。

未覆盖：resources、prompts、sampling、elicitation、roots、subscriptions、cancellation、进度、分页游标、listChanged 推送、HTTP transport、OAuth、官方 SDK 端到端互通。任务列表当前只返回最近 100 条，本地演示限制。

## A2A 0.3.0 JSON-RPC

Agent Card: `GET /.well-known/agent-card.json`。protocolVersion=0.3.0；preferredTransport=JSONRPC；URL 指向 `/a2a`；声明 HTTP Bearer；streaming/pushNotifications/stateTransitionHistory 均 false。

`POST /a2a` 实现 `message/send`、`tasks/get`。只接受用户 text parts，新建同步任务；configuration.blocking 必须 true（缺省 true），acceptedOutputModes 需含 text/plain。messageId 按身份幂等，同一 ID 改内容拒绝。状态 submitted → working → completed 在一个同步事务内执行，分别写审计；持久化终态与文本 artifact。传入文本仅请求本地固定摘要，不解释为任意执行指令。

Task、Message、TaskStatus、Artifact 和 AgentCard 的字段使用官方 0.3.0 schema 命名。tasks/get 按身份隔离，支持 historyLength 0..100。他人/不存在任务都返回 -32001；不支持的 file/data 或输出 MIME 类型 -32005；未知方法 -32601；无效参数 -32602；解析错误 -32700。HTTP 身份失败在 JSON-RPC 执行前返回 401/403。

未覆盖：message/stream、tasks/cancel、tasks/resubscribe、pushNotification 配置、SSE、异步 blocking=false、多轮 taskId/contextId continuation、文件/数据 part、扩展 metadata、gRPC、HTTP+JSON binding、签名 AgentCard、扩展卡和 OAuth。同步终态可通过 tasks/get 查询；不声称客户端能观察中间瞬时状态。

企业 A2A 只能取得合规聚合，且撤销分享会清除相关历史摘要缓存。没有任意 agent URL 调用或外部 A2A 发送。

## 官方参考来源

使用动态系统代理在官方 GitHub 版本标签 URL 下载了两个只读 schema 参考文件。HTTPS 验证开启，以下 SHA-256 为本次下载的本地复核值，非另行发布的官方签名或校验清单。

- `https://raw.githubusercontent.com/a2aproject/A2A/v0.3.0/specification/json/a2a.json`
  - `software/reference/a2a-v0.3.0.json`
  - SHA-256 `97d6e2435336836cd1d41dffacf83a1a97902b62b826ef14ec5704db85c95f17`
- `https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/2025-06-18/schema/2025-06-18/schema.ts`
  - `software/reference/mcp-2025-06-18.ts`
  - SHA-256 `0838332b90a9188c09fecddcaced2cd2d626126925d181bef8fc4785884706cf`

测试中的 schema 检查覆盖使用对象的必需字段和常量，不冒充完整 JSON Schema 校验器。可独立复核下载文件：

```sh
shasum -a 256 software/reference/a2a-v0.3.0.json software/reference/mcp-2025-06-18.ts
```
