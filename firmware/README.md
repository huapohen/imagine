# 灵伴 ESP32-S3 固件 — safe / EVT-A

工程数字原型，NOT-FOR-FAB。电脑承载 Agent，成熟 USB HID 鼠标底座独立；ESP32-S3 只负责灯光、触摸、隐私开关、可选状态屏与 LB1 串口。无录音摄像、医疗推断或外发。

## 实际构建与测试

```sh
./firmware/test.sh
./software/test-integration.sh
# 已有隔离缓存，构建两个目标，无需安装或网络探测：
PLATFORMIO_CORE_DIR="$PWD/firmware/.platformio" PLATFORMIO_SETTING_ENABLE_TELEMETRY=No \
  firmware/tools/venv/bin/python -m platformio run -d firmware
```

本轮两个目标实际编译 SUCCESS：

|目标|RAM|Flash|物理配置|
|---|---:|---:|---|
|esp32s3_safe|19,964 B / 327,680 B|328,405 B / 3,342,336 B|全部交互引脚和屏地址 -1，缺省隐私，外设不启用|
|esp32s3_evt_a|19,964 B / 327,680 B|332,461 B / 3,342,336 B|GPIO与硬件pin-map对齐，触摸阈值未标定，仍禁用|

产物 `.pio/build/<目标>/firmware.bin` / `.elf`，日志 `build/integration-build.log`。`test.sh` 用 C++11、-Wall/-Wextra/-Werror 编译实际固件共用的协议核心和 Controller 模板。包含104行共用golden以及GPIO/Wire/PWM时序mock，软件完整回归结果见 [COMPLETION](../software/COMPLETION.md)。**这些不是烧录、板测、USB枚举、反灌或触摸校准证明。**

## 板型与端口

PlatformIO Core 6.1.18，espressif32 6.9.0，Arduino ESP32 2.0.17。注册表 `esp32-s3-devkitc-1` 默认描述 N8/no PSRAM，因此两个profile显式覆盖 **N8R8：8MB QIO flash、OPI PSRAM、memory_type=qio_opi、BOARD_HAS_PSRAM**。没有宣称通用板默认配置就是N8R8；实际板标签、PSRAM自检待实物验证。

`ARDUINO_USB_CDC_ON_BOOT=0`。注册表的 `ARDUINO_USB_MODE=1` 仅选择芯片USB模式，**不会自动启用CDC**；本实现的 `Serial` 是 UART0，代码显式 RX44/TX43、115200/SERIAL_8N1。使用开发板 **USB-UART桥连接器**，不是nativeUSB连接器；烧录端口也须硬件人员明确选择，固件会话未运行upload。OEM鼠标另有USB线，载板不并接VBUS。

## EVT-A 针脚与共阳电气合同

|宏|GPIO / 默认值|用途|
|---|---|---|
|LB_PIN_LED_R/G/B|4 / 5 / 6|SW3V3共阳RGB，各经470Ω至GPIO灌电流|
|LB_PIN_TOUCH|7|电极输入；阈值0时不调用touchRead|
|LB_PIN_SDA/SCL|8 / 9|100kHz I2C，外部4.7k上拉到SW3V3|
|LB_PIN_PRIVACY|10|外部10k上拉常供3V3；LOW允许，HIGH/断线隐私|
|LB_SCREEN_ADDRESS|0x3C|SSD1306 128×64候选地址，不等于已探测成功|
|LB_TOUCH_THRESHOLD|0|未实测，禁用触摸采集|

共阳LED亮度b对应8-bit duty=255−b；**off=255/HIGH**，不能写0。恢复时先准备PWM通道off，再预装GPIO HIGH，再attach。当前低亮颜色逻辑为teal=(0,60,38)、amber=(70,30,0)、blue=(0,18,70)，均是占空亮度，不是已实测电流。470Ω限制峰值，LED具体Vf/电流仍需板测。

## 隐私与断线时序

共用控制器 `include/controller.hpp` 是实际固件和mock唯一外设启停策略：

1. 启动先配置/读取GPIO10，再将RGB/I2C/TOUCH全部INPUT，不给未判定电源状态的外设初始化。
2. 物理允许LOW连续稳定40ms，且LB1握手online后，才初始化PWM和屏。屏初始保持Display OFF，写入新图标后才点亮。
3. 检测HIGH立即detach PWM、Wire.end，将4/5/6/7/8/9设INPUT（无内部上拉），清灯/屏/触摸逻辑状态；停止屏刷新。**此分支不发送OLED指令、不强亮LED**，因为SW3V3已经切断。隐私指示靠UI/开关本体。
4. 允许态需重新稳定40ms才能恢复外设；不会恢复隐私前缓存的灯屏指令。
5. 无有效GET/PING心跳>=5秒，清ready/session/cache/灯屏状态；电源仍允许时先OLED Display OFF再释放外设。隐私断电时不发送这个命令。重新HELLO才能恢复online；没有每消息TTL。

主循环每轮及每串口字节检查控制器，串口单轮最多64字节；I2C每个事务前读物理状态、事务timeout=5ms。高电平在正在执行的事务期间变化时，在下一次检查返回后释放外设。这是软件检测时序，**不保证DPDT触点切换瞬间零反灌**；开关两极错时、GPIO复用、在途I2C与实测漏电仍是NOT-FOR-FAB门槛。

无OLED ACK时Wire.end并释放I2C，不持续刷不存在的屏。屏幕仅绘制状态图标，不含中文字体；UTF-8逻辑文本只在串口STATE查询。CAPS声明配置能力，不冒充实物探测报告。

## 触摸启用指南（本轮未启用）

保持threshold=0直至hardware核对电极、串1k、ESD器件DNI/选型、地与外壳，使用合成操作验证干燥/潮湿、接触/不接触噪声分布。不要采用网络示例的未标定固定阈值。经实物审定阈值后，在单独的本地测试profile显式加 `-DLB_TOUCH_THRESHOLD=<实测阈值>`；S3逻辑为touchRead>阈值、稳定40ms才变更布尔状态。

然后必须实测隐私切换时GPIO7输入复用/漏电/触摸硬件是否完全停止、允许恢复是否正确、串口是否始终屏蔽隐私态touch。现有mock不能证明芯片触摸外设的电气状态。触摸只做非敏感本地交互，不能变成情绪/生理信息、医疗判断或审批捷径。

## 串口桥与协议

唯一 [LB1精确规范](../docs/software/serial-protocol.md) 和 [104行golden](../docs/software/serial-golden-vectors.tsv)。无NDJSON、无ttl_ms、无TOUCH/PRIVACY线缆类型。

```sh
cd software
python3 -m lingban.serial_protocol --self-test
LINGBAN_TOKEN='员工本地令牌占位' python3 -m lingban.serial_protocol --once
# 已确认硬件后显式给出设备；本轮未运行：
LINGBAN_TOKEN='员工本地令牌占位' python3 -m lingban.serial_protocol --device /dev/已确认USB_UART
```

桥默认模拟器，不扫描设备。POSIX stdlib termios/select配置115200/8N1；同帧最多重试3次，每次1秒。GET检测offline后新nonce重握手；设备物理拔除造成错误时退出，明确重启后重新打开。关闭时恢复该设备的termios，不改系统全局配置。

## 隔离工具链来源

本轮复用已有 `firmware/tools/venv`、`.platformio` 和 `.pio` 缓存，未下载或安装新依赖。首轮工具来自实测后的可信PyPI镜像和已验证动态系统代理的PlatformIO官方包，包管理器完整性检查开启。`tools-lock.txt` 记录Python依赖；缓存数GiB，均在firmware目录并由.gitignore排除。

新环境需按AGENTS.md先短测源/代理/可信镜像，再建局部venv安装platformio==6.1.18；`build_local.py` 为需网络探测的首次构建辅助脚本，已有缓存优先上面的命令。禁止把构建成功当成允许投板、烧录、认证或量产的依据。
