# 灵伴 LINGBAN / Crystal Mouse EVT-A

**实际CAD与真实布线PCB数字原型已交接；全部制造文件NOT-FOR-FAB。** 从[COMPLETION.md](COMPLETION.md)查看精确产物、复现命令、实际测试与未验证门槛。

- 主控先传[架构与LB1 ASCII + CRC16串口协议](specs/architecture.md)、[官方核对引脚](specs/pin-map.md)给固件。
- [CAD](cad/README.md)：20件编辑源/STEP/STL，整机和爆炸STEP；底壳、透明上壳、原创独立晶堡/雪花、屏框与组件占位。
- [渲染](renders/README.md)：带概念标识的透明PNG、爆炸PNG、本地转台MP4与可复现Blender源。
- [PCB](pcb/README.md)：可编辑KiCad、实际511段走线/17过孔、BOM/PnP/网表/Gerber/钻孔，真实ERC/几何DRC/schematic-parity报告（均0）。
- [工程与制造](../docs/hardware/engineering-and-manufacturing.md)：99–899分档、299核心量产目标与单列DevKit样机成本、BOM批量/税/良率/NRE、七天样机、装配与验收。
- [验证](validation/README.md)；[工具安装与完整性](tools/README.md)；精简交付包在`delivery/`，不含tools/cache/本地状态。

OEM USB HID + 独立ESP32-S3开发板，双USB或外部Hub；电脑运行Agent。没有融合USB、硬件大模型、已打样/认证/量产或医疗/员工评分声明。主控负责Git、集成与发布；大体积局部工具/DMG/缓存不进交付包。

最终集成：LB1 ASCII+CRC16为唯一设备协议；GPIO/N8R8不变，隐私断SW3V3后灯/屏不显示privacy。49功能节点＋33明确NC节点与原理图完整网名一致，4个机械孔为board_only。既有CAD和pitch渲染hash不变，结果见`validation/integration/result.json`。
