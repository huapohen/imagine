# EVT-A 冻结引脚表（已对照官方 v1.1 文档逐脚核对）

ESP32-S3-DevKitC-1，N8R8，2×22排针，2.54mm节距。必须逐脚对照官方表；禁止用 ESP32 普通款 pinout。避开启动绑带GPIO0/3/45/46，USB19/20，UART43/44，板载RGB38（v1.1）/48（初版），以及N8R8保留GPIO35/36/37。

|信号|GPIO|方向|电平/约束|
|---|---:|---|---|
|RGB_R|4|PWM sink|3.3V，串470Ω，低亮|
|RGB_G|5|PWM sink|3.3V，串470Ω|
|RGB_B|6|PWM sink|3.3V，串470Ω|
|TOUCH|7|touch input|3.3V，1k串联，ESD；调校后启用|
|I2C_SDA|8|open drain|3.3V，4.7k到外设电源；隐私态高阻|
|I2C_SCL|9|open drain|3.3V，4.7k到外设电源；100kHz起步|
|PRIVACY_ALLOW_N|10|input|外10k上拉到常供3V3；开关允许态接GND；高/断线=隐私|

屏幕候选 0.96in SSD1306 128×64 I2C 模组，首版连接器约定GND/VCC/SCL/SDA，不假定市售模块排列一致。禁止5V模块上拉进入GPIO。物理DPDT开关一极外设3V3通断，另一极允许态GPIO10接地。固件进入隐私立即将RGB/I2C/TOUCH变高阻，防止GPIO反灌断电外设；反灌仍须板测。

官方来源：https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html ，缓存 references/esp32-official-text.txt。所选GPIO4/5/6/7/8/9/10分别为官方J1的4/5/6/7/12/15/16脚；J1-1/2=3V3，J1-22=GND；J3-1/21/22=GND。实物排针宽度与脚1方向仍需量测。不得投板。

机读接口见 `pin-map.json`。额外官方尺寸证据 `references/devkit-dimensions.dxf` 提取到62.74mm、25.40mm、2.54mm、1.27mm、8.00mm文字；排间22.86=25.40−2×1.27。CAD开发板与载板定位按该几何假设对应，但到货仍需确认绘图基准和公差。v1.1板载RGB=GPIO38（官方明确），初版=GPIO48，均保留不用。

注意：`PRIVACY_ALLOW_N`是硬件说明名，PCB网络缩写为`PRIVACY_N`，都是GPIO10、高/断线=隐私，低=允许。本轮已只读核对固件实现；主控报告safe/EVT-A两目标编译和mock HAL测试通过。本硬件会话未重复编译或烧录，不冒称板测。

## 已实装 profile 与设备合同

唯一设备协议为 **LB1 ASCII + CRC16**，以 `docs/software/serial-protocol.md` 为准；UART桥115200 8N1，UART0 RX44/TX43，native CDC关闭。GPIO43/44由开发板USB-UART桥使用，载板不再接它们。

`firmware/platformio.ini`的esp32s3_evt_a：8MB flash、qio、qio_opi、opi PSRAM、BOARD_HAS_PSRAM、ARDUINO_USB_CDC_ON_BOOT=0；GPIO4/5/6/7/8/9/10与上表逐项一致，屏地址固定候选0x3C。LB_TOUCH_THRESHOLD=0，触摸采集默认禁用，CAPS touch=0；有电极不等于已标定。safe所有引脚/屏地址默认-1，能力为0。

共阳灯PWM duty=255−亮度，off=255/HIGH；先预装off再attach。隐私切SW3V3后灯/屏不显示privacy；GPIO4–9全部INPUT且不启用内部上拉。LOW稳定40ms且online才恢复。离线>=5秒会清状态并释放外设；已断电不再向屏/PWM写入。逻辑text可经GET读取，当前屏只画状态图标，不承诺渲染任意文字。实现来源为firmware/include/board_config.hpp、controller.hpp及software/lingban/serial_protocol.py；不自行变更引脚/协议。
