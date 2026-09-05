# 灵伴 LINGBAN / Crystal Mouse — EVT-A 冻结接口

工程数字原型，未打样、未板测、未认证。日期2026-09-06。主控集成；所有尺寸mm。原创「云阶晶堡」。本轮同步已实装的协议和固件配置，不改变GPIO、CAD几何或pitch渲染。

## 唯一首发与硬件边界

- **299元是1000台情景的核心版目标含税零售价，功能为灯＋触摸＋OLED。** 首轮只验证这一核心硬件；108元批量直接成本是未来商业模型假设，非当前开发板样机报价。5台DevKit工程样机成本单列、待报价。499元仅未来外观/服务套装，不是第二个首发版本。完整分档和敏感性见docs/hardware/engineering-and-manufacturing.md。
- 成熟有线USB HID鼠标OEM总成＋独立ESP32-S3-DevKitC-1 N8R8开发板＋交互载板，电脑运行Agent。A线为OEM鼠标，B线固定使用开发板**USB-UART桥**：UART0 RX44/TX43、115200 8N1、无流控；`ARDUINO_USB_CDC_ON_BOOT=0`。可接外部供电Hub；不融合USB、不并接VBUS、不改OEM HID。
- 载板接3V3/GND与GPIO4/5/6低电流共阳RGB、GPIO7触摸、GPIO8/9 I2C、GPIO10物理隐私。GPIO和N8R8设置以已实装的`firmware/platformio.ini`、`include/board_config.hpp`及`include/controller.hpp`为准，见本目录pin-map.md/json。
- 3V3来自开发板稳压器；载板外设预算<=60mA，5V电源按1A能力预留验证。500mA端口不得按1A使用，实耗、启动峰值和热耗未测；首版关闭Wi-Fi/BLE。
- 物理DPDT一极切断灯/屏SW3V3，另一极在允许态将GPIO10接GND；外10k上拉常供3V3。HIGH/断线/未配置=隐私。隐私时外设断电，**不显示隐私灯，也不在屏上显示privacy**；指示由主机UI和开关本体提供。
- 固件先读取隐私再初始化外设。进入隐私时detach PWM、Wire.end，GPIO4/5/6/7/8/9改INPUT、不启用内部上拉，清灯/屏/触摸逻辑状态。允许LOW连续40ms且已握手online才恢复。共阳RGB的PWM duty=255−亮度，off=255/HIGH，初始化先预装off。
- 隐私开关不硬断触摸线路、USB或主机Agent，不删除电脑任务、不自动改变主机专注计时器。无音视频/医疗传感器、无员工评分；审批仍由主机执行授权流程，触摸不隐式批准。
- OEM原主控、镜片、光学高度、滚轮和按键沿用成熟总成，CAD包络不等于任意OEM能装入。壳体和电气仍需工程师及实物审查。

## 唯一设备协议：LB1 ASCII + CRC16

**权威规范：`docs/software/serial-protocol.md`**；`firmware/serial-protocol.md`指向同一合同。软件标识`lingban.serial/1`对应线缆`LB1`，非MCP/A2A。旧LBP/0.1 NDJSON草案已废弃，无兼容解析器。下表只是硬件交接摘要，不定义第二套协议。

```text
LB1|<seq>|<TYPE>|<payload>|<CRC16><LF>
```

|项目|冻结值/行为|
|---|---|
|帧|ASCII，最多256 bytes（含单个LF），不接受CRLF；seq=1..65535十进制、无前导零|
|CRC|CRC16-CCITT-FALSE，poly=0x1021、init=0xffff、无反射/xorout=0；覆盖最后CRC分隔符之前全部字节；4位大写hex；123456789→29B1|
|握手|HELLO `versions=1;session=<16位小写hex>`；每次连接新nonce，返回CAPS；无session仅一次性自检兼容|
|状态赋值|SET只允许`led=off/teal/amber/blue`和/或`text=<0..80 UTF-8 bytes的小写hex>`，非空字段集合；无任意RGB数组、无每消息TTL；ACK applied=1不代表电脑审批执行完成|
|读取/心跳|GET/PING payload为空；GET→STATE，PING→ACK alive=0/1。正式桥每秒GET，其他控制器最多每2秒GET/PING|
|5秒离线|距最后有效心跳>=5000ms，poll清会话/缓存/输出。仅合法空GET/PING（含同帧重试）刷新心跳；SET、错误帧、序号冲突、缓存HELLO不保活。恢复需HELLO|
|离线电气|仍有外设电源时先Display OFF再卸载PWM/Wire并高阻；若已物理隐私断电，跳过所有屏/PWM写操作，直接高阻|
|重试|最近16个seq FIFO；同seq异帧sequence_conflict；SET重试不重复应用，GET/PING重试返回当前状态|
|错误|坏CRC/帧/ASCII/类型词/seq静默丢弃；合法帧的方法/字段错误才返回可信seq的ERR；无ttl_ms、TOUCH/PRIVACY推送类型|
|能力|EVT-A配置led=1、privacy=1、screen=1，**touch=0**（阈值0未标定）；safe四项为0。CAPS描述配置而非板测|
|屏幕|SSD1306候选0x3C；当前HAL显示状态图标。text为逻辑数据，GET可读取，无任意文字/中文字体已实装承诺|
|隐私状态|STATE privacy=1、led=off、touch=0、text为空；SET被拒绝。主机UI的`led=privacy`是合成标签，不是线缆枚举或物理灯光|

未完成帧1秒清接收缓冲仅用于分帧恢复，不是命令TTL或5秒会话watchdog。黄金向量为`docs/software/serial-golden-vectors.tsv`，RESET/PRIVACY/TOUCH/POLL是测试驱动命令，不是线缆消息。本轮只读核对实现；主控报告两目标编译及HAL隐私/共阳/断联测试通过，不替代烧录和实际串口/反灌/屏幕验证。

## 机械与制造边界

名义126×80×54，已验证的CAD/STEP及pitch渲染本轮保持不变。偏大展示样机，人体工学未验证。壁厚、间隙、柱位、双USB槽、光学孔等见CAD参数与工程交接；OEM真实尺寸、屏/LED/开关料号、反灌、ESD、天线净空和止拉须到货复审。即使ERC/DRC/parity清零，制造文件仍为NOT-FOR-FAB。
