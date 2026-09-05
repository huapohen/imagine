# 最终集成修复证据

范围：硬件文档同步LB1/299核心SKU；修正KiCad局部标签、明确NC与板上专用机械孔语义。没有改GPIO、固件、CAD或产品渲染。

- `parity-before.json`：本轮真实复现82条net_conflict＋4条extra_footprint，共86条；旧普通DRC=0不代表parity=0。
- `baseline.json`：修复前118个CAD/渲染文件hash及PCB几何规范化hash（只排除网络名/属性/path等元数据）。
- `result.json`：修复后真实parity/几何DRC/ERC均0、未连接0；118文件及铜线/焊盘/板框几何不变；CAD既有干涉[]；只读软件/固件/商业源hash与GPIO/N8R8/LB1检查。
- `../netlist-pinmap-check.json`：49功能＋33明确NC，共82节点，用完整局部网名逐项对照。NC必须单脚且没有segment/via，不能再用strip('/')掩盖差异。

复现：运行COMPLETION.md中的元数据同步→封装库→KiCad导出检查→PCB图→网表检查→`python3 hardware/validation/integration/check_integration.py`→打包。`check_integration.py`只读软件/固件，不运行其测试、不写其目录；主控报告的两目标编译和HAL通过单独归因，非硬件板测。

产品图继续使用原始hash，供已授权H3 image reference；不重新生成。机械/电气实体仍待工程师与实物验证，NOT-FOR-FAB不变。今后需要实物ECO时另建明确基准，不能绕过本次冻结检查。
