# LB1 串口协议 — 唯一现行合同

2026-09-06 主控裁决：使用已经实现的 **LB1 ASCII + CRC16**；旧 `LBP/0.1` NDJSON 草案废止，不提供兼容解析器。此协议不是 MCP/A2A 或 USB HID。软件标识 `lingban.serial/1` 对应线缆标识 `LB1`，并非另一个协议。本文对应 `firmware/include/protocol.hpp` 和 `software/lingban/serial_protocol.py`。

## 传输与帧

开发板 **USB-UART 桥**，UART0 RX44/TX43，115200 baud、8 data bits、no parity、1 stop bit，无流控。`ARDUINO_USB_CDC_ON_BOOT=0`，不把 Serial 重定向到 native USB。OEM 鼠标另接 USB，固件不改变 HID 底座。

```text
LB1|<seq>|<TYPE>|<payload>|<CRC16><LF>
```

- 整帧最多 **256 bytes，包含一个 LF**。只接受 ASCII；CRLF、无 LF、多个分隔段、非 ASCII 均不接受。
- seq 为 1..65535 十进制，无符号、无前导零；0 和 65536 不允许。
- TYPE 大小写敏感，编解码白名单只有 `HELLO SET GET PING CAPS STATE ACK ERR`。主机请求仅前四项；主机传入合法帧的 CAPS/STATE/ACK/ERR 返回 `ERR code=unsupported`。**没有 TOUCH/PRIVACY 类型、推送事件或 ttl_ms**。
- payload 可空，仅允许 `[A-Za-z0-9_=;,.-]*`。字段格式 `key=value;key=value`，key 非空、区分大小写，不允许重复 key、尾部分号或额外等号。各方法限制字段集合；没有 `rgb` 数组、任意颜色或每消息 TTL。
- CRC16-CCITT-FALSE：poly=0x1021、init=0xffff、refin=false、refout=false、xorout=0。覆盖 `LB1|seq|TYPE|payload` 的全部字节，不包含最后的 `|CRC16` 和 LF。CRC 固定 4 位**大写**十六进制。标准向量 ASCII `123456789 → 29B1`。
- CRC/版本前缀/类型词/seq/ASCII/长度/规范帧错误：**静默丢弃，不发送 ERR**，不能相信损坏帧的序号。完整但字段/方法参数无效：可信序号的 ERR，见下表。
- 实际串口解析超长时丢弃至 LF；未完成帧最后字节后 **1 秒**清理接收缓冲。这是分帧恢复，不是会话心跳或 TTL。

## 请求与响应

|请求|允许 payload|响应与说明|
|---|---|---|
|HELLO|`versions=1`；可另带 `session=0123456789abcdef`|CAPS：`version=1;led=0/1;touch=0/1;privacy=0/1;screen=0/1;simulated=0/1`。正式主机每次连接使用新 16 位小写 hex session；不带 session 仅兼容一次性自检|
|SET|非空，`led` / `text` 一个或两个字段|ACK `applied=1`。led 为 off/teal/amber/blue；text 为下述 UTF-8 hex。赋值只在握手有效、隐私关闭时接受；无任意执行或审批语义|
|GET|空|STATE：`link=online/offline;led=off/teal/amber/blue;privacy=0/1;touch=0/1;text=<utf8hex>`。未握手也能读安全 offline，不因此取得操作权限|
|PING|空|ACK：在线 `alive=1`；离线 `alive=0`。离线 PING 不建立握手|

CAPS 是已配置驱动能力，**不是板测报告**。`screen=1` 表示 SSD1306 候选配置存在，不能证明 0x3C 有设备或屏幕实际工作。EVT-A 默认 touch=0（阈值未标定），safe 四项能力均为 0。模拟器为 simulated=1；共享 golden fixture 使用 simulated=0 与四项能力为 1，以便跨语言字节比较。

`text` 的字段名保持原实现，不重命名为 text_utf8hex。编码为 **0..80 个 UTF-8 bytes → 0..160 个小写 hex 字符**，长度必须偶数。允许空文本。解码后必须是合法 Unicode 标量序列 U+0000..U+10FFFF，排除 U+D800..U+DFFF，拒绝过长 UTF-8、孤立 continuation、截断、多于 U+10FFFF 等。U+0000 等控制标量可以作为逻辑数据保留；不会执行控制字符或 shell 命令。主机桥裁切 80 bytes 时回退到完整 UTF-8 字符边界；设备不静默修复非法文本，返回 `code=text`，不部分更新 LED。当前屏幕只显示状态图标，逻辑文字可经 GET 查询，**没有中文字体渲染承诺**。

## 错误优先级与去重

先处理会话时间，再验证整帧。验证通过后顺序为：有效新 HELLO 会话重置 → 序号冲突/重试 → 字段语法 → 方法参数。SET 参数错误优先级：`handshake_required` → `privacy_active` → `fields` → `led` → `text`；任一错误均不赋值。

|ERR code|含义|
|---|---|
|sequence_conflict|最近缓存中同 seq 对应另一帧；不替换旧缓存、不续命|
|fields|重复/缺失/未知字段、字段语法错误、GET/PING 非空 payload；ttl_ms 在此明确拒绝|
|version|HELLO versions 不是 1、session 非 16 位小写 hex 或存在未知字段|
|handshake_required|SET 在未握手/已离线状态到达|
|privacy_active|SET 在物理隐私启用时到达，包括试图远程解除隐私|
|led / text|对应值无效|
|unsupported|合法线缆响应类型被作为请求传入|

设备缓存**最近 16 个不同 seq，FIFO**，包括方法级错误响应。相同 seq 同帧重试不延长 FIFO 窗口，SET 返回原响应且不再次应用；同 seq 不同帧返回 sequence_conflict。**GET/PING 重试重新生成当前状态**并在已在线时刷新心跳，避免旧 touch/privacy 被缓存读回。重复 HELLO/SET 不刷新心跳。超过窗口不保证永久去重；SET 是状态赋值。

新合法 session nonce 清空缓存和灯/屏/触摸逻辑状态并建立新握手。物理隐私状态改变时清空缓存与灯/屏/触摸状态，保留会话心跳；旧 SET 不会在隐私中通过缓存重放。会话超时清空 ready、session、全部缓存和输出状态。

## 5 秒离线合同（不是 TTL）

HELLO 成功时建立基准时间；此后**有效且无参数的 GET/PING**（包括同帧重试）刷新在线心跳。SET、坏 CRC、非法参数、未知类型、序号冲突以及缓存 HELLO 都不能保活。主机桥正常每秒循环 GET，建议其他控制器最多每 2 秒心跳。

距最后有效心跳 **>=5000 ms**，固件主循环调用 poll，即使完全没有 UART 字节也执行：

1. ready=false、清 session/cache，灯逻辑 off、text 为空、touch=false；保留物理 privacy 真值。
2. 如果外设电源仍允许，发送屏幕 Display OFF，然后卸载 PWM、Wire.end 并释放外设引脚为 INPUT；停止后续刷新。若已物理隐私断电，跳过任何屏幕/PWM写操作，直接高阻。
3. GET 返回 `link=offline`、空灯屏安全状态，PING 返回 alive=0，SET 返回 handshake_required。
4. 恢复必须 HELLO；桥在 GET 读到 offline 时发新 nonce 重握手。真实设备拔除造成 I/O 错误时桥退出，重新接入需显式重启，不扫描设备。

固件 uint32 millis 差值支持计数回绕。Python 模拟器使用单调时钟，receive 自动 poll，测试/嵌入使用者可显式 poll；模拟器对象不另起计时线程。**没有每消息 ttl_ms，不能把 5 秒会话 watchdog 描述为命令 TTL。**

## 物理隐私与电气安全

GPIO10 外部 10k 接常供 3V3，开关允许时接 GND；HIGH/断线/未配置=隐私。开关另一极切断 SW3V3。固件首次初始化任何外设前读取隐私。进入隐私在检测到高电平时立即 detach PWM、Wire.end，GPIO4/5/6/7/8/9 INPUT（不启用内部上拉），清输出，停止触摸及屏刷新。允许 LOW 连续稳定 40ms 且握手 online 才恢复外设。

共阳 RGB 经 470Ω 到 GPIO4/5/6 灌电流：亮度 b=0..255 对应 duty=255−b，off=255/高电平；初始化先预装 off duty 与 HIGH 再 attach。隐私时 LED 供电被切，**不点亮“隐私灯”**；隐私指示由 UI 和开关本体提供。主机 Web 原有 `led=privacy` 是合成 UI 标签，不是线缆 LED 枚举，也不表示物理 LED 亮着。

隐私开关不是主机数据总线隔离器：它屏蔽外设，不删除电脑任务，也不自动改变主机专注计时器。原型没有外发执行器，审批始终仅写本地 outbox，触摸不会自动批准。高阻时序通过 mock HAL 验证；实际开关触点错时、I2C在途事务延迟、GPIO复用、反灌电流仍须板测，软件不能保证物理开关瞬间零延迟。

## Golden vectors 与复现

唯一机器可读 fixture：[serial-golden-vectors.tsv](serial-golden-vectors.tsv)，**104 行**，两种实现直接读取同一冻结文件，不在测试时生成期望。帧和响应按 hex 存储（含 LF）；`-` 表示无响应。RESET/PRIVACY/TOUCH/POLL 是**测试驱动指令，不是线缆类型**。列为 name、operation、milliseconds、input_hex_or_control、expected_hex。fixture 的 CRC 用 Python stdlib `binascii.crc_hqx` 独立计算，手工按本文指定状态和预期；维护工具在 `software/scripts/write_golden_vectors.py`，不导入被测协议。

```sh
./firmware/test.sh
./software/test-integration.sh
# 单独逐字节复核同一 fixture：
./firmware/build/protocol_test --golden docs/software/serial-golden-vectors.tsv
```

覆盖：有效 CRC、损坏、256-byte 边界、seq 界限、格式错误、UTF-8 字节范围、字段错误优先级、16 项窗口、旧状态缓存、nonce 重连、隐私、GET/PING保活、恰好5秒超时、SET/错误帧不保活。C++ controller mock 另测 GPIO/Wire/PWM时序和 millis 回绕。上述检查均不构成真实串口、灯光、屏幕或烧录验证。
