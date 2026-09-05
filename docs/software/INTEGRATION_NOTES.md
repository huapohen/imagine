# 主控集成修复记录

日期：2026-09-06。已阅读 `docs/verification/HARDWARE_REVIEW.md`、`REVIEW_FINDINGS.md`、`hardware/specs/architecture.md`、`pin-map.md` 及主控独立浏览器 report.json。只修改 software/firmware/docs/software，不操作 Git，不付费、不外发、未读取凭据或原始需求。

## 已修复与接口合同

|评审项|本轮实现|验证|
|---|---|---|
|P1 共阳 RGB 输出反相|GPIO4/5/6 sink，off=HIGH/255；attach 前预装255，亮度反相|共用控制器 mock 验证 prepare→HIGH→attach 和各通道 duty；两个 PlatformIO 目标实际编译|
|P1 隐私断电反灌风险|首次隐私读取早于外设初始化；检测 HIGH 立刻 detach PWM / Wire.end / 六个外设引脚 INPUT；不向断电屏幕写隐私画面、不点断电隐私灯；LOW稳定40ms且online后恢复|实际固件调用的同一 Controller 模板经 mock HAL 核对顺序、恢复、抖动、中途掉电与无屏ACK；不等于反灌板测|
|协议冲突|LB1 ASCII+CRC16 唯一；增加精确规范、104行Python/C++共用golden、GET/PING5秒失效、安全offline；无ttl_ms|双方逐字节通过同一fixture；mock验证超时断开外设|
|板/USB配置|safe全-1；EVT-A GPIO4/5/6、7、8/9、10和0x3C；N8R8内存覆盖；Serial UART0 RX44/TX43，CDC_ON_BOOT=0，115200|两个目标实际编译；触摸阈值0禁用；未实际枚举USB或使用串口|
|R1 初次任务INSERT|保持已有9列修复，未改业务实现|全新Store/seed、事件与幂等原有测试继续通过|
|R2 撤销后A2A历史泄漏|保持已有缓存删除修复；新增同messageId重放、三个派生字段均重新受聚合门槛控制的回归|旧tasks/get不可读，重放artifacts/history/status.message全部available=false|
|R3 snooze口径|沿用已修UI“安静10分钟”，明确不承诺同证据到期再通知|新增同证据601秒后不重发、新证据正常提醒回归|
|R4 A2A错误码|当前源仍为-32003，本轮改为官方0.3.0的-32005|直接从官方schema常量复核file/data/不支持输出MIME错误|

## 请主控协调的文档边界

本轮初读快照中，`hardware/specs/architecture.md` 仍含旧 LBP/0.1 NDJSON、512-byte/uint32、ttl_ms、RGB数组及首发499元文字。主控已指定硬件会话更新；软件会话不越界改 hardware。本文及 `docs/software/serial-protocol.md` 是本轮实现合同，主控最终应确认硬件/产品文档不再将旧协议视为现行方案。

`pin-map.md` 的 GPIO、共阳/470Ω、SW3V3断电与高阻约束已在 EVT-A 对齐。保留 NOT-FOR-FAB，不能据编译解除硬件门槛。KiCad parity、CAD相交、售价口径属于硬件/主控范围，不由本次软件修复证明关闭。

CAPS.screen=1 只代表候选驱动已配置，不证明实际显示器存在。若0x3C无ACK，控制器结束Wire并释放I2C，引脚仍需实物核对。触摸阈值没有实测，不启用；N8R8 PSRAM按官方内存配置编译，未做内存实测。

物理隐私不等于暂停电脑Agent：外设禁用、触摸不批准任何动作；电脑仍可保存个人任务和生成提醒，本原型所有审批只写本地outbox、无自动外发。若产品希望物理开关也暂停主机提醒，需主控单独定义用户可见合同，不能宣称硬断电能切断电脑数据处理。

## 浏览器验收的两种证据

主控提供的 `docs/verification/browser/report.json`：隔离 headless Chrome **152.0.7977.66**，14/14检查通过、errors=[]，包括实际HTTP会议/阻塞/审批/专注/撤销链路、移动端无横向溢出及无前端异常。该验证由主控完成，本轮只读取证据，未重复运行浏览器。

用户现有 Chrome profile 打开本地地址仍 `ERR_BLOCKED_BY_CLIENT`，保护未关闭。应写“独立浏览器验证通过；用户Chrome打开受阻”，不能写成视觉完全未验证或用户浏览器已修复。本轮未改变前端页面实现。

完整实际命令与结果见 `software/COMPLETION.md`。服务启动和最终推送交还主控。

## 并行改动隔离

收尾观察到主控正在加入 `software/lingban/model.py`、`live_model_test.py`、`tests/test_model.py` 及README模型入口；本会话不修改这些文件、不读取其配置、不执行真实模型或会读.env的测试。新增 `software/test-integration.sh` 固定只运行 core/HTTP/protocols 三个回归模块和固件mock/golden，避免无意包含并行工作。本文的48项结果只覆盖该范围，不冒充主控的全仓最终验收。观察时README新链接 `docs/software/MODEL_INTEGRATION.md` 尚未落盘，交由主控完成，不删除其在制链接。
