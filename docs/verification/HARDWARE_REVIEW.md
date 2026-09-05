# 独立硬件与协议集成评审

日期：2026-09-06。对象：`hardware/pcb/NOT-FOR-FAB` 数字工程原型、当前 CAD、固件与主机串口代码。评审期间各包持续修改，以下为本轮实际读取/执行的快照；未将实物未验证或正常在制列为缺陷。保留 NOT-FOR-FAB 状态，不授权投板。

## 2026-09-06 最终再复核状态（以此表覆盖下方早期快照）

本轮已发现的代码、电气网表一致性与交付口径问题均已关闭；没有剩余必须修改源码的阻断。制造文件仍为 NOT-FOR-FAB，原因是实物验证门槛尚未完成。

|项目|最新独立证据|状态|
|---|---|---|
|共阳 RGB 反相|真实 Controller 输出 OFF=255，teal=[255,195,217]；独立 Mock HAL 测试通过|代码级关闭，未通电验证|
|隐私高阻/I2C 停止|启动先读 GPIO10；隐私进入 detach PWM、Wire.end、GPIO4..9 INPUT；期间不刷屏；允许稳定 40ms 后才重启|代码级关闭，未测物理反灌瞬态|
|5秒通信失效|独立测试精确 5000ms、恢复握手、millis uint32 回绕；失效关灯/清文本/断外设驱动|代码级关闭|
|固件配置/端口|safe 全部交互禁用；独立 EVT-A GPIO4..10、触摸阈值0、OLED候选0x3C、CDC_ON_BOOT=0、UART0 RX44/TX43；N8R8 qio_opi/8MB|两个配置独立编译通过|
|LB1 实现|Python 编码 HELLO/SET/GET → C++ → Python 解码 CAPS/ACK/STATE，含 session nonce；C++/Python各执行104行冻结golden，75条期望响应CRC另经stdlib独立核验|已通过原生互通|
|硬件协议/299售价文件|architecture、hardware README/COMPLETION、docs/hardware 已统一LB1和299灯＋触摸＋OLED核心目标；499仅未来套装，5台DevKit成本863–1850单列，旧LBP仅出现在废弃声明|口径冲突关闭|
|KiCad parity|硬件修复后独立官方 CLI full parity：0几何错误、0未连线、**0 parity**；再次导出XML，82个SCH针脚与PCB精确网名完全一致|原86项已关闭|
|CAD|最新完整生成报告为 `[]`；独立回读20个实际导出STEP全部有效，base/carrier/canopy分别与所有其他当前部件求交，无>0.05mm³正体积干涉|已有几何证据，未做公差/实物装配验收|
|硬件专用ZIP|02:25更新的145条manifest与磁盘、ZIP逐SHA一致；ZIP CRC、SHA256SUMS均通过，关键LB1/299文档和PCB为最新|包内一致性通过；完整软硬件交付范围见下文|

独立 HAL 测试交付源码为 [hal_independent.cpp](hal_independent.cpp)，没有复用构建者测试。覆盖启动隐私、safe 配置、允许去抖、共阳 OFF/颜色、隐私停止、禁用触摸、通信失效/重连、PWM准备期间隐私突变和计时回绕；全部通过。另编译运行构建者 protocol/controller 测试，也通过。测试源码不包含本机绝对路径、凭据或二进制。

在项目根目录复现（仅 C++11 编译器，输出位于忽略的本地目录）：

```sh
mkdir -p .local/review
c++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/include \
  docs/verification/hal_independent.cpp -o .local/review/hal_independent
.local/review/hal_independent
```

STEP 回读证据 `.local/review/final-step-check.json` 使用当前 `parts.json` 有效清单，不导入 exports 中的旧迭代部件；没有重跑或修改硬件生成源。

硬件专用ZIP的独立核对证据为 `.local/review/final-package-check.json`，145条manifest与包中内容全部匹配，未包含 `.env`、`.local`、工具虚拟环境或下载目录。该专包未包含权威 `docs/software/serial-protocol.md` 与 `serial-golden-vectors.tsv`。主控已确认总集成 `scripts/package_factory.py` 负责配套完整协议/向量、固件src/include/test、本独立HAL源码与报告、RFQ/验收资料；完整工程交接应使用总集成包。总包的最终生成、打包检查与发布由主控收尾，本评审不把尚未执行的总包发布写作已验证。

共享协议向量已分别用 C++ runner 和 Python Simulator 独立重放 **104 行**，全部通过；75 条带线缆帧的期望响应另外用 Python 标准库 `binascii.crc_hqx(...,0xffff)` 核验 CRC。可复现命令：

```sh
c++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/include \
  firmware/test/protocol_test.cpp -o .local/review/protocol_final
.local/review/protocol_final --golden docs/software/serial-golden-vectors.tsv
```

编译使用现有缓存 PlatformIO/ESP32 工具链，无下载；输出目录 `.local/review/pio-build`，日志 `independent-pio-build.log`：safe 和 EVT-A 均 SUCCESS。safe RAM 19,964B、Flash 328,405B；EVT-A RAM 19,964B、Flash 332,461B。**编译、Mock HAL 与原生协议通过不等于烧录或实物验证。**

<details>
<summary>首次发现记录（历史快照；已修固件问题不作为当前阻断）</summary>

1. **P1：固件输出模式与载板电气合同不一致。** 当前 `firmware/src/main.cpp:36-41` 用 active-high PWM，`firmware/include/board_config.hpp` 也明确写 active-high；载板为 SW3V3 共阳 RGB，GPIO 经 470Ω 灌电流。启用实际引脚后，`off` 对应三路 0 占空比，即持续拉低、实际全亮；颜色和亮度反相。必须为共阳反相输出。默认全部引脚 -1 使此问题暂未施加到实物，不能据此将错误的 EVT 配置交给接线人员。
2. **P1：隐私态未停止外设 GPIO/I2C 驱动。** 当前 `firmware/src/main.cpp:57` 仅更新逻辑状态；`:71-72` 继续 PWM 与定期 Wire 刷屏，`:48-50` 在首次读取物理隐私输入前已初始化外设。载板切断 SW3V3 后，这不满足 pin-map 要求的 RGB/I2C/TOUCH 高阻，并可能经数据线给断电外设反灌。应先采样隐私，再按允许态启用；隐私激活时立即停止/卸载 PWM、结束 Wire 并将交互引脚设高阻；恢复允许需明确重初始化。主控已通知软件会话修复，**本轮尚未获得修复后硬件适配代码回归结果**。
3. **协议合同冲突必须收敛。** 已实现的 Python/C++ 都是 `LB1|seq|TYPE|payload|CRC16`，ASCII、256-byte 上限、序号 1..65535；`hardware/specs/architecture.md:14-26` 当时仍为 LBP/0.1 NDJSON、512-byte、uint32、RGB/TTL 字段。二者不可互解。主控已裁决 LB1 为唯一现行协议并通知硬件更新；收尾需全仓消除将 NDJSON 视为现行协议的声明。`firmware/platformio.ini` 当前还启用 USB CDC，而硬件架构约定 USB-UART 桥，主控已通知用独立 EVT 配置统一端口。
4. **P2：KiCad 原理图/PCB 实际网名不一致。** 独立开启 `--schematic-parity` 得到 86 条：82 条 net_conflict、4 条 extra_footprint。49 个有效连接的拓扑逐脚一致；冲突主要为 SCH 局部标签 `/3V3` 与 PCB `3V3` 的根路径名称，以及 SCH 的 33 个 `unconnected-*` 与 PCB 空网。4 个安装孔没有 SCH 元件。必须统一网名/NC 与机械孔策略，或精确记录认可的 board-only 孔项，不能以普通 DRC=0 宣称 parity=0。这不是已证实的电气短接或 GPIO 接错。

上述 P1 与协议冲突已即时发送主控。旧协议中的 5 秒离线/TTL 承诺也需处理：当前 `main.cpp:70` 仅在半帧超时时清输入缓存，完整会话断线不清 ready/灯/屏状态；采用 LB1 后应实现有效帧心跳失效回安全态，或明确不再宣称尚未实现的能力。

</details>

## 针脚、网络与电源核对结果

用实际挂载的 **KiCad 9.0.7 CLI** 导出 SCH 的 XML 网表，另行解析 PCB 的每个 footprint/pad-net；没有仅依赖路由脚本或 DRC 摘要。首次49个有效连接节点/14个网络在规范化根路径后拓扑一致；**修复后再次独立导出，全部82个SCH针脚（含NC）与PCB精确网名直接比较，零错配，不再去掉根路径**。PCB 86 个焊盘中的额外4个是明确的board-only安装孔 H1–H4。

|功能|实际连接|判定|
|---|---|---|
|常供 3V3|J1-1/2、C1-1、R7-1、J7-2|与开发板官方针序一致|
|GND|J1-22、J3-1/21/22，以及屏/触摸/电容/开关回路|与官方针序一致|
|红/绿/蓝|J1-4/5/6 → R1/R2/R3 470Ω → J5-2/3/4|GPIO4/5/6 正确，共阳 J5-1 接 SW3V3|
|触摸|J1-7(GPIO7) → R4 1k → J6-1 ELECTRODE；D1 预留到 GND|拓扑一致，D1 是明确 DNI 的待选件|
|屏|J1-12(GPIO8) SDA、J1-15(GPIO9) SCL；R5/R6 4.7k 上拉到 SW3V3；J4=GND/VCC/SCL/SDA|正确，没有将上拉接常供 3V3|
|隐私|J1-16(GPIO10) ↔ R7 10k 常供 3V3 ↔ J7-4；J7-5=GND|高/断线为隐私，与 fail-closed 文档一致|
|双极外置开关|J7-1=SW3V3 common、2=3V3 allow、3=NC；4=PRIVACY_N common、5=GND allow、6=NC|按已写的外置线束约定允许态两极同时闭合；无开关具体料号，仍需实物触点/线束核对|

缓存官方文本 `hardware/specs/references/esp32-official-text.txt` 的 J1/J3 表与上述接用针脚一致。22×2 排针节距 2.54 mm；两排 x=6.57/29.43，中心距 22.86 mm。未用 J1-21 的 5V，未占用 N8R8 的 GPIO35/36/37、启动绑带或 USB/UART 保留脚。

LED 峰值不能只凭低 PWM 占空比声称达标，串阻才约束峰值。以常见红 LED Vf≈1.8 V 举例，(3.3−1.8)/470≈3.2 mA；绿色/蓝色电流取决于真实 Vf。当前 470Ω 共阳方案没有发现必然过流，但 LED 具体料号与 Vf 未定，“每路峰值 ≤5 mA”仍须按最坏电源/电阻/LED 参数复核，不能算已板测。

触摸 D1 在 SCH 标 dnp、BOM 标 DNI，当前实板设计不具有已选定/已装配的 ESD 防护。该限制已写入工程资料，作为 NOT-FOR-FAB 候选可接受；接触放电、漏电/寄生电容和触摸阈值必须在器件选型后验收。

## KiCad 实际检查

- 本轮独立执行 ERC：**0 violations**。
- 本轮独立执行 DRC，含 all-track-errors、severity-all：**0 几何/间距 violations、0 unconnected items**。
- 修复后同一命令加 schematic-parity、severity-all：**0 parity issues**；原86项已关闭，没有把4个安装孔误作缺失电气元件。
- 所有符号为被动连接器/无源器件，ERC=0 不会检测 MCU 固件方向、共阳反相或断电反灌。
- PCB 0..36 × 0..76 mm，厚 1.6 mm；实际有 511 段铜线、17 个过孔，不是仅飞线。天线区存在实际双层 keepout：x=7..29、y=0..8，禁止 tracks/vias/pads/copperpour；当前铜线端点最低 y=10 mm，没有看到进入该区域的线路。keepout 不证明射频性能，开发板版本/天线位置/外壳金属距离仍须实物核对。

最终独立证据：`.local/review/final-netlist.xml`、`final-drc.json`、`final-erc.json`。初次 `independent-drc.json` 的86项只保留作修复历史。命令使用项目内挂载的 `hardware/tools/mount-kicad/KiCad/KiCad.app/Contents/MacOS/kicad-cli`，没有安装/下载工具或修改系统设置。ERC/DRC 配置目录限定 `.local/review`。

安装同版本 KiCad 后，从项目根目录复现全量 parity 检查（可将 `kicad-cli` 替换为本机官方工具路径）：

```sh
kicad-cli pcb drc --schematic-parity --all-track-errors --severity-all \
  --exit-code-violations --format json -o .local/review/final-drc.json \
  hardware/pcb/NOT-FOR-FAB/lingban_carrier.kicad_pcb
kicad-cli sch erc --severity-all --exit-code-violations --format json \
  -o .local/review/final-erc.json hardware/pcb/NOT-FOR-FAB/lingban_carrier.kicad_sch
```

## CAD 与载板实物占位

当前 `hardware/cad/build_cad.py:52-57` 的载板为 36×76×1.6 mm，与实际 PCB Edge.Cuts 相同。CAD 坐标关系可对齐为 x_CAD=x_PCB−28、y_CAD=40−y_PCB；PCB 四孔 (3,3)/(33,3)/(3,71)/(33,71) 对应 CAD x=−25/5、y=37/−31，孔径均 2.5 mm。排母 x=−21.43/1.43、长 55.88 mm，与双排 22 脚及 22.86 mm 排距一致。

CAD 的板底 z=12 mm、板顶 13.6 mm、排母高 9 mm、开发板底 z=23 mm 已留出堆叠关系；但板底 SMD 元件、连接器壳体/插头/线束、焊点高度尚无完整实体包络，不能把“载板矩形没有相交”写为完整装配净空验证。开发板和 OEM 仍是明确的待实测占位。

评审中相交报告持续更新：开始见排母与屏框/屏占位相交，后续已消失；本轮最后读取 `hardware/validation/cad-intersections.json` 尚列 canopy↔castle_socket_sled 2.564 mm³。硬件会话仍在修，此项记为**在制、未做最终关闭**，不把此前已消失的中间问题列作当前缺陷。最终应检查最新 assembly 与有效 parts 清单；exports 中存在以前迭代的不同排母坐标文件，不能逐个导入整个目录当作最终装配。

## 协议实际运行与上一轮 P1 回归

本轮把现有 `firmware/test/protocol_test.cpp` 编译至 `.local/review/protocol_test`，未修改源码。原生 C++ 测试通过 CRC16-CCITT-FALSE 标准向量、帧界限、握手、默认隐私、幂等/冲突、字段验证。再用 Python 的真实 `encode` 生成 HELLO/SET/GET 喂给 C++ `--echo`，Python `decode` 成功读取 CAPS/ACK/STATE。**这证明 LB1 编解码跨语言一致，不证明 Arduino GPIO、USB、OLED 或真实串口通信。**

- 前轮 R1 已关闭：全新内存 Store 首次 `task.upsert` 与 `meeting.upsert` 都成功，不再出现 9 列/10 占位符错误。
- 前轮 R2 已关闭：5 人企业 A2A 摘要后撤回 1 人，旧 `tasks/get` 返回 404，同 `messageId` 重放重新计算 `available=false`；旧 artifacts/history/status.message 不再经该路径读回。
- 本轮没有再次审计全部前轮 P2 或新增加的全部软件 API，不能将上述两项通过扩大为全软件验收。

## 可接受限制

无真实样机、板级功耗/ESD/反灌/射频/人机工程验证，属于明确的数字原型边界。safe 配置引脚禁用、EVT-A 触摸阈值待标定、D1 DNI、双 USB、未完成中文屏幕字体均可在准确标识下接受。共阳 PWM 与隐私高阻已完成代码修复和独立 Mock HAL 回归；生产输出继续保持 NOT-FOR-FAB，直到工程复核与实测门槛完成。
