# 软件会话完成记录

本轮集成修复完成时间：2026-09-06 02:12（Asia/Shanghai）。只修改 `software/`、`firmware/`、`docs/software/`，未操作 Git。未读取原始需求文件、.env、已有密钥或 `../active_agent`；无外联消息、付费模型、付费视频、厂商联系或系统全局修改。

## 本轮主控集成修复

已读 HARDWARE_REVIEW / REVIEW_FINDINGS 与实际 pin-map，修复共阳LED active-low PWM、隐私断电高阻及首次初始化时序。新增共用 Controller mock HAL 验证和 N8R8 / USB-UART 的 EVT-A profile；保留全-1 safe profile。LB1 为唯一现行协议，104行冻结golden由Python/C++共用，GET/PING连续5秒失效清握手与输出，返回安全offline；没有ttl_ms。

前轮R1任务初次INSERT和R2撤销A2A缓存修复保留，新增R2同messageId重放三个派生字段回归。A2A内容类型错误按官方0.3.0改为-32005。snooze沿用UI“安静10分钟”，明确不承诺同证据到期再通知。

请主控按 [INTEGRATION_NOTES](../docs/software/INTEGRATION_NOTES.md) 协调硬件旧文档；软件会话未越界修改硬件目录。未启动持久业务服务，临时HTTP测试服务已由测试退出清理，启动与最终推送交还主控。

## 运行

从仓库根目录：

```sh
./software/start.sh
```

Python 3.9+，stdlib 零运行依赖 + SQLite，默认 `127.0.0.1:8765`。打开终端显示的员工/企业角色链接。令牌在启动时生成并轮换，仅存哈希；链接不写入文档。合成演示数据自动初始化，撤销状态跨重启保留。

```sh
./software/test-integration.sh
# 本轮复用仓库内缓存，实际构建 safe 和 EVT-A 两个目标：
PLATFORMIO_CORE_DIR="$PWD/firmware/.platformio" PLATFORMIO_SETTING_ENABLE_TELEMETRY=No \
  firmware/tools/venv/bin/python -m platformio run -d firmware
```

## 已交付

- 暖白、墨蓝、青绿的中文响应式 Web 工作台，原创透明城堡晶鼠 SVG；员工/企业角色由服务端令牌强制区分。界面全局标注 DEMO / 合成数据，硬件模拟与命名待检索说明明确。
- 事件摄入和按员工隔离的幂等键、SQLite 任务记忆、后台 worker、证据版本解释、冷却、专注静默、非医疗休息计时器与提醒反馈。
- 人工动作审批和审计；并发批准最多写一次本地 outbox，拒绝无 outbox，没有对外发送器。
- 明确授权 + 明确提交业务结果；企业只见本组织至少 5 人聚合。撤销删除共享行及企业 A2A 历史聚合缓存，重新授权不复活旧数据。
- manifest 权限校验及专用插件令牌；省略 plugin_id 也不能越权。插件无任意代码执行，不能审批、授权或解除隐私开关。
- 模拟灯光、触摸、隐私开关、小屏逻辑状态；有真实 POSIX 串口桥、协议模拟器、CRC、版本/会话协商、16项FIFO重试窗口、严格UTF-8 hex、5秒offline和隐私高阻控制。
- MCP 2025-06-18 stdio JSON-RPC：initialize、initialized、ping、tools/list、tools/call 与错误。
- A2A 0.3.0：Agent Card、message/send、tasks/get、同步任务生命周期与持久化。正式方法与字段，支持子集，未认证。
- 一键场景：会议将近、项目阻塞、专注与休息、撤销企业分享。
- 启动脚本、Dockerfile、HTTP 示例、部署边界、官方版本化 schema 参考及许可、ESP32-S3 PlatformIO 固件和硬件无关 C++ 自检。

## 实际验证结果

| 检查 | 实际结果 |
| --- | --- |
| 启动与HTTP | 前轮一键启动成功；本轮测试实际启动本地临时HTTP服务完成协议/鉴权/审批链路，未留下持久服务 |
| `./software/test-integration.sh` | **48 项本轮固定范围 unittest 全部通过**，本轮 2.208 秒；包含真实 HTTP、worker、并发审批、MCP 子进程和模拟串口桥 |
| `./firmware/test.sh` | C++11 + `-Wall -Wextra -Werror` 编译并执行共享协议核心、104行冻结golden和实际Controller的mock HAL，PASS |
| Python 串口自检 | CRC、握手、去重和隐私优先，PASS |
| Python/C++ 交叉验证 | 同一104行fixture逐字节通过，含5秒边界、UTF-8/CRC错误、FIFO和隐私；mock含millis回绕与硬件调用顺序 |
| `node --check software/web/app.js` | PASS |
| `python3 -m compileall -q software/lingban` | PASS |
| PlatformIO safe | **SUCCESS**，RAM 19,964 B，Flash 328,405 B，binary 328,768 B |
| PlatformIO EVT-A | **SUCCESS**，RAM 19,964 B，Flash 332,461 B，binary 332,832 B；两个目标构建总计5.713秒 |
| 独立浏览器验证 | 主控隔离headless Chrome 152.0.7977.66，**14/14链路通过**、errors=[]；本轮读取 `docs/verification/browser/report.json` 与截图证据，不重复宣称自行运行 |
| 用户现有Chrome | 仍 `ERR_BLOCKED_BY_CLIENT`，未关闭保护；与独立浏览器已通过须区分 |
| Docker build/run | 未验证：本机 Docker daemon 未运行；未启动或修改系统服务 |
| 实际硬件 | 未接设备、未烧录、未板级验证，不声称打样或认证完成 |

本轮测试明细 `software/test-output/integration-tests.txt`；固件构建日志 `firmware/build/integration-build.log`。这两个目录及数据库、工具缓存列入各自 .gitignore。

两个固件的大小与SHA-256、测试数量和证据来源见 [INTEGRATION_RESULTS.json](../docs/software/INTEGRATION_RESULTS.json)。

固定范围为 `test_core.py`、`test_http.py`、`test_protocols.py`，`test-integration.sh` 不发现或执行并行新增的 `test_model.py`，不读 .env。原有 `test.sh` 仍由主控用于全仓集成测试。

覆盖项目：幂等与键冲突、状态相同不重提醒、证据变化与冷却、专注及解除、阻塞解决、会议时间窗口、后台自动触发、反馈归属、16 次并发批准仅 1 次落箱、拒绝与终态不可翻转、员工/企业/组织隔离、>=5 门槛、撤销清数据与历史摘要、重新授权不恢复、隐私输入拒绝、插件白名单和专用令牌越权、Host/Origin/令牌/体积/路径边界、MCP 握手/通知/错误/真实 stdio、A2A 生命周期/归属/类型错误、串口 CRC/重试/字段/隐私/会话/跨语言交叉验证、持久化和非回环绑定显式门槛。

## 接口与文档入口

- [运行说明](README.md)
- [架构、授权与撤销](../docs/software/README.md)
- [HTTP 示例](../docs/software/http-examples.md)
- [MCP / A2A 版本、能力和未覆盖项](../docs/software/protocols.md)
- [部署与 Docker 边界](../docs/software/deployment.md)
- [固件、配置与复现](../firmware/README.md)
- [LB1精确规范](../docs/software/serial-protocol.md) 与 [104行共用golden](../docs/software/serial-golden-vectors.tsv)

HTTP：`/api/me`、`/api/state`、`/api/events`、`/api/alerts/feedback`、`/api/actions`、`/api/actions/decide`、`/api/consent`、`/api/share`、`/api/enterprise/summary`、`/api/plugins`、`/api/plugins/token`、`/api/plugins/{id}/tasks`、`/api/hardware`、`/api/scenarios`、`/.well-known/agent-card.json`、`/a2a`、`/health`。

## 未验证与交付边界

本地合成演示，不是公网多租户生产系统。未做 TLS/SSO、限流配额、加密备份、法证级删除、差分隐私、官方协议 SDK 互通或认证。>=5 并不防止所有持续观察推断；撤销不能取回用户已看见的数据。任务列表最近 100 条，提醒/动作 UI 最近 8 条。本轮只修改离线规则与板级/协议边界，不实现或调用模型。并行主控正在加入的可选模型适配由其独立验收；不覆盖其文件、不读取配置或调用付费接口。

safe目标全部交互引脚-1，EVT-A目标按pin-map设GPIO4/5/6 LED、7 touch、8/9 I2C、10 privacy和屏地址候选0x3C。两个目标均显式N8R8内存配置、UART0 USB-UART 115200，CDC关闭。触摸阈值0未标定，禁用采集；无隐私开关时默认禁用交互。可选 SSD1306 只渲染状态图标，不具备中文字体。USB HID底座独立。共阳LED反相与隐私高阻软件时序通过mock；实际LED电流、断电反灌、开关两极触点错时、PSRAM、触摸复用/ESD、屏地址、UART桥枚举都仍须实物验收。保留NOT-FOR-FAB，不把编译与mock当作板测。
