# 独立集成评审：灵伴 LINGBAN

评审日期：2026-09-06。范围为正在集成的数字原型；以下行号对应首次发现时的文件。软件、硬件、商业与演示仍由各自会话持续修改，本报告不是最终完成认证。高优先级发现已即时发送主控；修复后需回归，不能以本报告视为修复证据。

## 2026-09-06 最终回归状态

本轮 R1—R7 均已修复或按明确产品语义关闭；下面的折叠内容和旧口径表保留发现历史，不代表当前未修问题。

- **R1 已关闭**：全新内存 Store 首次 task/meeting 摄入成功；原 9 列/10 占位符错误消失。
- **R2 已关闭**：撤回后企业旧 A2A task 读取 404，同 messageId 重放重新计算 available=false；再次读取不再暴露旧缓存。
- **R3 按明确产品语义关闭**：主控决定按钮为“安静 10 分钟”，只暂停新通知，不承诺同证据到期重发。实测601秒后不重放同证据符合此决定；当前UI、HTTP示例和软件README均明确该语义，保留API名称snooze兼容。未发现当前操作文档承诺“稍后重新提醒”。
- **R4 已关闭**：非文本 file part 实际返回 -32005。
- **R6 已关闭**：RFQ 已明确离散共阳 RGB、GPIO4/5/6 PWM，与载板一致。
- **R5/R7 已关闭**：硬件架构、README/COMPLETION和制造说明已统一首发299灯＋触摸＋OLED、唯一LB1；旧LBP仅明确作为废弃稿。最终软件状态标识为 `LB1/1.0`；早期 `lingban.serial/1` 在协议文档中定义为LB1别名，不是第二种线缆协议。详情与固件修复证据见 `HARDWARE_REVIEW.md`。
- 插件权限较首次审查已有改进：现有专用令牌携带 plugin_id，由服务端强制绑定。实测只读插件令牌即使省略输入 plugin_id，写事件仍返回403；首次报告中“尚无插件专用令牌”的限制已失效。仍不可将 manifest-only 称为完整第三方代码沙箱。

<details>
<summary>首次发现与复现记录（历史；当前关闭状态见上文）</summary>

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

</details>

## 交付口径发现历史（已关闭）

|编号|实际冲突|收敛要求|
|---|---|---|
|R5|`hardware/specs/architecture.md:6` 写首发 499 元；`docs/product/DECISIONS.md`、商业计划与财务输入写 299 元核心版|统一首发 299 元含税零售目标；5 台工程样机成本单列，不将开发板样机成本当量产 BOM|
|R6|`docs/manufacturing-commercial/rfq-template.md:7` 写可寻址 RGB；硬件架构与 pin-map 写共阳离散 RGB 三路 PWM|RFQ 与工程 BOM/原理图保持同一选型|
|R7|`software/lingban/core.py:250` 写 `lingban.serial/1`；硬件架构与产品决策写 `LBP/0.1`|模拟状态和未来串口编解码明确区分；实际实现共享同一协议版本、帧字段与长度限制，不能只改版本字符串就声称互通|

## 原型可接受限制与真实数据/实物前门槛

- 权限检查：角色和 owner 查询在已阅核心路径中存在；审批有 owner 约束，只有 pending 可决定，批准写本地 outbox 且 action 唯一。未发现该路径会自动对外发送；此处的本地 outbox 是已声明的演示限制。
- 聚合：普通接口强制同组织、当前同意世代与至少 5 人；重新授权清空历史分享，未自动复活旧数据。这个门槛不能防止相邻实时查询差分推断；当前精确实时总和尚无固定统计窗口、差分保护或极端值抑制。商业计划已指出该要求，演示必须继续标合成数据，真实员工数据启用前另行验收。
- 数据生命周期：已阅核心代码尚无自动保留期限或个人全量导出/删除API；撤回业务分享不等同于删除个人任务、事件、审计或全部派生数据。插件已有专用令牌、服务端权限绑定，但 manifest-only 不构成第三方代码沙箱；完整员工令牌仍应只交给员工本人。原型不执行第三方代码，真实数据使用前需另验生命周期合同。
- 隐私开关：最终合同明确物理开关屏蔽外设，不自动改变电脑的主动提醒/专注计时器，不删除个人数据；暂停主机提醒由独立“安静10分钟”控制。最终核心模拟隐私态led=off，提示明确仅在电脑UI；固件的高阻/屏总线停止已由独立HAL测试验证。无真实硬件时不推断物理隔离或瞬时零反灌已获证明。
- GPIO/PCB：GPIO4–10、N8R8保留脚已对照官方文本；后续实际KiCad网表/PCB精确82针脚比较、ERC/DRC/parity均通过，见 `HARDWARE_REVIEW.md`。反灌、功耗和真实信号时序未验证。
- CAD：后续当前20件STEP有效、生成的完整相交报告为空；独立回读base/carrier/canopy与其他有效部件求交亦无>0.05mm³干涉，见硬件评审。没有执行公差链或实物装配验收。
- MCP/A2A：MCP 声明 2025-06-18 stdio tools 子集，A2A 声明 0.3.0 同步文本 JSON-RPC 子集；均明确未认证。已审初始化、工具路由、结构与错误路径；未跑官方客户端互操作认证。未覆盖官方完整协议不作为缺陷。

## 实际检查与复现边界

1. 阅读仓库 AGENTS.md；未读取原始 input/1.txt、任何 .env 或凭据；未用 Git、未付费、未发消息到外部。
2. 静态阅读 `software/lingban/{core,mcp,protocols,server}.py`，用 Python 标准库和内存 SQLite 复现 R1—R4；测试数据均为本次临时合成数据。
3. 阅读产品决策、商业计划/财务说明、RFQ、硬件架构与 pin-map，交叉检查首发售价、RGB 与 LBP 口径。
4. 财务脚本仅在内存替换输出函数后重算，不写商业目录；5 行 SKU economics、33 行 monthly、3 行 summary 均与现有 CSV 完全匹配，脚本内部现金勾稽通过。
5. 本文最初仅覆盖软件核心与文档；后续固件编译、HAL、LB1协议、PCB和CAD检查已在 `HARDWARE_REVIEW.md` 单列。未验证PPT/视频、真实USB设备、实物装配、部署或真实企业数据处理。进行中的文件缺失未列为缺陷。

复现核心导入方式：在项目根目录设置 `PYTHONDONTWRITEBYTECODE=1` 后运行 Python，将 `software` 加入 `sys.path`，导入 `lingban.core.Store` 和 `lingban.protocols.A2A`。所有逻辑复现使用 `Store()` 内存数据库；R3 使用可控 `clock=lambda: now[0]`。主控可按每项给出的输入建立永久回归测试。
