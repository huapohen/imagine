# 独立集成评审：灵伴 LINGBAN

评审日期：2026-09-06。范围为正在集成的数字原型；以下行号对应首次发现时的文件。软件、硬件、商业与演示仍由各自会话持续修改，本报告不是最终完成认证。高优先级发现已即时发送主控；修复后需回归，不能以本报告视为修复证据。

## 必须修复的已复现问题

### R1 / P1：首次任务摄入阻断，连带 seed 无法完成

- 位置：`software/lingban/core.py:56,127`。
- `tasks` 表有 9 列；INSERT 使用 10 个占位符，实际提供 9 个值。
- 实际结果：首次 `task.upsert` 抛出 `sqlite3.OperationalError: table tasks has 9 columns but 10 values were supplied`；`meeting.upsert` 共用此路径；`seed()` 同样依赖首次任务创建。
- 回归：全新内存 Store 建员工，摄入一个 task/meeting；确认首次成功、相同幂等键重放成功、更新版本成功，并在全新数据库启动服务器。

### R2 / P1：企业 A2A 历史缓存绕过分享撤回

- 位置：`software/lingban/protocols.py:58-61,73-78,85-87`；撤回逻辑 `software/lingban/core.py:199-208`。
- A2A 将企业聚合保存到 task 的 artifacts、history 和 status.message。撤回只删除 `shared`，不使这些派生缓存失效。
- 实际复现：5 名员工分别明确分享 completed=10、blocked=1；企业发 `message/send` 得到 50/5。撤回一名后普通企业接口正确返回 `available=false`，但旧 task 的 `tasks/get` 以及同一 `messageId` 重放仍返回 `available=true, completed=50, blocked=5`。
- 修复要求：企业 A2A 派生内容必须受当前授权/统计世代约束；撤回后所有再次读取与幂等重放都应失效或重算，并覆盖三个内容字段。已经由外部接收者保存的副本不能保证追回，应明确此边界。

### R3 / P2：稍后提醒永不重发

- 位置：`software/lingban/core.py:159,173`。
- `snooze` 只设置十分钟 `focus_until`；到期后仍被相同 `fingerprint` 的永久去重阻止。
- 实际复现：内存 fixture 插入阻塞任务，首次 tick=1；反馈 snooze；时钟前进 601 秒；tick=0，提醒总数仍为 1。为继续独立检查，此复现仅在内存直接插入 fixture 绕过 R1，没有修改产品源码。
- 回归：同一未解决任务在稍后期限后准确重提醒一次；无反馈时仍保持去重；任务已解决时不重提醒。

### R4 / P2：A2A 不支持内容类型返回错误代码不符所声明版本

- 位置：`software/lingban/protocols.py:37`；参考 `software/reference/a2a-v0.3.0.json` 的 `ContentTypeNotSupportedError`。
- 非文本 part 实际返回 `-32003`。A2A 0.3.0 规定内容类型不支持为 `-32005`，`-32003` 表示 push notification 不支持。
- 回归：file/data 输入及不支持的输出 MIME 返回 `-32005`；不存在 task 保持 `-32001`。

## 必须统一的交付口径

|编号|实际冲突|收敛要求|
|---|---|---|
|R5|`hardware/specs/architecture.md:6` 写首发 499 元；`docs/product/DECISIONS.md`、商业计划与财务输入写 299 元核心版|统一首发 299 元含税零售目标；5 台工程样机成本单列，不将开发板样机成本当量产 BOM|
|R6|`docs/manufacturing-commercial/rfq-template.md:7` 写可寻址 RGB；硬件架构与 pin-map 写共阳离散 RGB 三路 PWM|RFQ 与工程 BOM/原理图保持同一选型|
|R7|`software/lingban/core.py:250` 写 `lingban.serial/1`；硬件架构与产品决策写 `LBP/0.1`|模拟状态和未来串口编解码明确区分；实际实现共享同一协议版本、帧字段与长度限制，不能只改版本字符串就声称互通|

## 原型可接受限制与真实数据/实物前门槛

- 权限检查：角色和 owner 查询在已阅核心路径中存在；审批有 owner 约束，只有 pending 可决定，批准写本地 outbox 且 action 唯一。未发现该路径会自动对外发送；此处的本地 outbox 是已声明的演示限制。
- 聚合：普通接口强制同组织、当前同意世代与至少 5 人；重新授权清空历史分享，未自动复活旧数据。这个门槛不能防止相邻实时查询差分推断；当前精确实时总和尚无固定统计窗口、差分保护或极端值抑制。商业计划已指出该要求，演示必须继续标合成数据，真实员工数据启用前另行验收。
- 数据生命周期：已阅代码尚无保留期限、个人全量导出/删除、插件专用令牌与独立沙箱。manifest-only 并不构成第三方代码权限隔离；若插件拥有员工完整令牌，省略 `plugin_id` 即回到员工权限。当前不执行第三方代码的明确限制可以接受；不可宣传为已隔离的插件运行环境。撤回业务分享不等同于删除个人任务、事件、审计或全部派生数据。
- 隐私开关：实际模拟 `privacy=true` 后，新增阻塞任务仍会产生主机 alert，仅硬件状态被覆盖为隐私显示。架构写“主机必须同步停止自动执行”，产品写可关闭主动提醒；应定义隐私/暂停分别覆盖哪些主机行为并测试。无真实硬件时不推断物理开关已失效。
- GPIO：已将 GPIO4/5/6 RGB、7 touch、8/9 I2C、10 privacy 与缓存官方文本比较，均为可用 GPIO；N8R8 的 35/36/37 避让一致。官方文本也说明板载 RGB 初版为 GPIO48、v1.1 为 GPIO38；当前分配未使用两者。PCB 尚在制，本次没有验证连接器脚号、焊盘、电气网络、反灌、功耗或信号时序。
- CAD：已看到 BRep 与相交报告，但 CAD 仍在调整；没有将中间相交清单视为最终结构缺陷，也没有执行最终装配验收。
- MCP/A2A：MCP 声明 2025-06-18 stdio tools 子集，A2A 声明 0.3.0 同步文本 JSON-RPC 子集；均明确未认证。已审初始化、工具路由、结构与错误路径；未跑官方客户端互操作认证。未覆盖官方完整协议不作为缺陷。

## 实际检查与复现边界

1. 阅读仓库 AGENTS.md；未读取原始 input/1.txt、任何 .env 或凭据；未用 Git、未付费、未发消息到外部。
2. 静态阅读 `software/lingban/{core,mcp,protocols,server}.py`，用 Python 标准库和内存 SQLite 复现 R1—R4；测试数据均为本次临时合成数据。
3. 阅读产品决策、商业计划/财务说明、RFQ、硬件架构与 pin-map，交叉检查首发售价、RGB 与 LBP 口径。
4. 财务脚本仅在内存替换输出函数后重算，不写商业目录；5 行 SKU economics、33 行 monthly、3 行 summary 均与现有 CSV 完全匹配，脚本内部现金勾稽通过。
5. 未验证最终 UI、PPT/视频、固件、PCB、CAD 装配、真实 USB 设备、部署或真实企业数据处理。进行中的文件缺失未列为缺陷。

复现核心导入方式：在项目根目录设置 `PYTHONDONTWRITEBYTECODE=1` 后运行 Python，将 `software` 加入 `sys.path`，导入 `lingban.core.Store` 和 `lingban.protocols.A2A`。所有逻辑复现使用 `Store()` 内存数据库；R3 使用可控 `clock=lambda: now[0]`。主控可按每项给出的输入建立永久回归测试。
