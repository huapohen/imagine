# HTTP 示例（本机合成演示）

先执行 `./software/start.sh`。把启动终端员工或企业链接中 `#token=` 后的值显式填入下列变量。不要将令牌或带令牌链接提交到 Git；以下占位值不是实际凭据。所有命令在仓库根目录运行。

```sh
EMPLOYEE_TOKEN='员工令牌占位'
ENTERPRISE_TOKEN='企业令牌占位'
BASE='http://127.0.0.1:8765'
curl "$BASE/api/me" -H "Authorization: Bearer $EMPLOYEE_TOKEN"
curl "$BASE/api/state" -H "Authorization: Bearer $EMPLOYEE_TOKEN"
```

摄入事件（同键重放不会创建第二条，改变同键内容返回 409）：

```sh
curl "$BASE/api/events" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"idempotency_key":"example-blocked-1","type":"task.upsert","payload":{"id":"board-review","title":"合成任务：等待主板接口核对","state":"blocked","project":"晶鼠试点"}}
JSON
```

不需要手动调用 tick；worker 每秒自动判断。`meeting.upsert` 同样接受 id/title/state/due_at/project，其中 due_at 为 UTC Unix 秒。`focus.set` payload 为 `{"until":0,"cooldown_seconds":300}`，until=0 结束专注，未来时间开启安静期（最多 24 小时）。`break.due` payload 只接受 due_at。

```sh
curl "$BASE/api/scenarios" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"meeting"}'
# 其他场景名：blocked / focus / resume / revoke
curl "$BASE/api/alerts/feedback" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"id":"提醒ID","feedback":"useful"}'
# feedback: useful / dismissed / snooze（安静 10 分钟，不承诺同证据到期再通知）
```

动作提案与批准，使用提案响应中的 id：

```sh
curl "$BASE/api/actions" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"title":"合成会议要点","body":"仅在本地保存：核对主板接口和城堡空间"}'
curl "$BASE/api/actions/decide" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"id":"动作ID","decision":"approve"}'
# decision=reject 不生成 outbox。相同决定可安全重放，终态不可翻转。
```

授权、明确分享、撤销及企业聚合：

```sh
curl "$BASE/api/consent" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"enabled":true}'
curl "$BASE/api/share" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"completed":2,"blocked":1}'
curl "$BASE/api/enterprise/summary" -H "Authorization: Bearer $ENTERPRISE_TOKEN"
curl "$BASE/api/consent" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"enabled":false}'
# 初始仅 5 位合成分享者，撤销一位后企业结果 available=false。
curl "$BASE/api/enterprise/summary" -H "Authorization: Bearer $ENTERPRISE_TOKEN"
# 下列越权访问必须 403：
curl -i "$BASE/api/state" -H "Authorization: Bearer $ENTERPRISE_TOKEN"
```

插件 manifest 与受限令牌：

```sh
curl "$BASE/api/plugins" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"id":"demo-calendar","name":"合成日历插件","version":"1.0.0","permissions":["events:write","tasks:read"],"event_types":["meeting.upsert"]}
JSON
curl "$BASE/api/plugins/token" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"id":"demo-calendar"}'
PLUGIN_TOKEN='插件接口响应令牌占位'
curl "$BASE/api/plugins/demo-calendar/tasks" -H "Authorization: Bearer $PLUGIN_TOKEN"
# 插件令牌访问 /api/state、审批、consent、A2A 等必须 403。
```

模拟设备（员工主令牌）：

```sh
curl "$BASE/api/hardware" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"led":"teal","screen":"会议将在十分钟后开始","touch":true}'
curl "$BASE/api/hardware" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"privacy":true}'
# 隐私启用后 led=privacy、touch=false；插件不能解除隐私。
```

A2A 正式 JSON-RPC：

```sh
curl "$BASE/.well-known/agent-card.json"
curl "$BASE/a2a" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @- <<'JSON'
{"jsonrpc":"2.0","id":"send-1","method":"message/send","params":{"message":{"kind":"message","role":"user","messageId":"example-a2a-1","parts":[{"kind":"text","text":"给我一份合成任务摘要"}]},"configuration":{"blocking":true,"acceptedOutputModes":["text/plain"]}}}
JSON
curl "$BASE/a2a" -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":"get-1","method":"tasks/get","params":{"id":"返回的task id","historyLength":2}}'
```

主要状态码：400 输入无效，401 令牌无效，403 权限/Origin/Host 拒绝，404 不存在或非本人对象，409 幂等/审批冲突，411 缺少长度，413 超过 32 KiB，415 非 JSON。A2A 方法执行错误使用 JSON-RPC error，见协议文档。
