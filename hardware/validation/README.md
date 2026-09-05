# 实际验证记录

- `cad-brep.json` / `cad-intersections.json`：实际OpenCascade实体有效性、逐件包围盒/体积与两两正体积干涉；阈值0.05mm³。不代表公差链、壁厚或实物装配测试。
- `stl-mesh-check.json`：导出的STL经trimesh检查封闭、水密、法向、正体积、连通组件。复现 `hardware/tools/venv/bin/python hardware/validation/validate_artifacts.py`。
- `pcb-drc.json` / `sch-erc.json`：KiCad9.0.7真实检查，parity命令带`--schematic-parity --exit-code-violations`，独立几何报告为`pcb-geometric-drc.json`；报告没有靠排除/忽略规则抹掉错误。`kicad-command-results.json`记录真实导出退出码。
- `netlist-pinmap-check.json`：独立官方引脚预期对实际KiCad XML网表；49功能＋33明确NC焊盘用完整网名逐项对照原理图网表，不去掉/前缀，且NC必须单脚无铜。检查避开5V、USB、UART、绑带与PSRAM脚。
- `routing-summary.json`：自编双层网格路由器统计；路由器宣称成功不能替代KiCad DRC，须结合正式报告。
- `media-probe.json`：ffprobe真实MP4编码/分辨率/时长。PNG/视频均概念演示，无实物照片。
- `network-probes.json` / `mirror-probes.json` / `tool-integrity.json`：下载线路与完整性。工具日志里首次下载失败/旧迭代失败保留审计，不代表最终产物失败。

未进行任何电气通电、固件烧录、示波器峰值、热、ESD、RF、HID装配性能、按钮寿命、人体工学、认证或厂家DFM验证。完整已测/未测边界见COMPLETION与docs/hardware。

本轮整合证据在`integration/`：before报告复现86项parity差异；result报告为0，并核对118个既有CAD/渲染文件hash和PCB几何不变、GPIO/N8R8/LB1与只读实装来源一致。主控报告两目标固件编译与HAL隐私/共阳/断联通过；本轮没有重复编译、烧录或实物测试。

交付包清单采用明确格式白名单，不含tools、cache、.env、KiCad本地状态和临时锁；`delivery/package-audit.json`记录ZIP完整性、条目与manifest哈希核对。
