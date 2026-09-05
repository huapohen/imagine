# ESP32-S3 交互载板 EVT-A

`NOT-FOR-FAB/lingban_carrier.kicad_pro` 为可编辑工程；同目录包含原理图、实际双面走线PCB、自包含符号/封装库。36×76×1.6mm，2层1oz假设，0.25mm线宽，0.65/0.30mm过孔。所有输出仅工程评审用。

本载板只含插座、限流/上拉阻容、屏/LED/触摸/物理开关线束接口；ESP32-S3、RGB灯、屏幕与DPDT是外部器件。原理图所有引脚是无源载板触点，ERC只证明本载板连接规则；不证明ESP电气配置或外接器件正确。D1为DNI ESD占位，量产必须冻结真实TVS并更改封装/复验。

复现：仓库根运行 `python3 hardware/pcb/build_pcb.py --sync-existing`、`python3 hardware/pcb/finalize_project.py`、`python3 hardware/pcb/export_and_verify.py`。最后一条真实调用KiCad9.0.7，强制--schematic-parity及--exit-code-violations，同时记录独立几何DRC、ERC并导出制造文件。`gerber-review-only/`不是下单包；禁止仅因DRC/ERC通过即生产。

官方pinout/协议见`../specs/`；供电、线束、装配、成本与未验证项见`../../docs/hardware/engineering-and-manufacturing.md`。PCB顶面箭头方向尚需丝印完善，按J1/J3官方脚1及方形焊盘识别。PnP.csv为设计清单，PnP-kicad.csv为KiCad导出坐标；优先后者并由贴片厂核对底面旋转、原点和DNI。

`build_pcb.py --sync-existing`与`semantic_sync.py`只统一局部标签的完整网名、明确NC单脚网、符号path和机械孔board_only属性，不改铜线坐标。普通全量生成也会调用同一逻辑，未新增忽略规则。H1–H4的exclude_from_bom/pos是真实板上专用机械语义；采购BOM不列机械孔。49功能节点、33个无铜NC节点共82项与KiCad导出网表逐项匹配，检查不删除/前缀。

`sexpr.py`随本目录交付；工具环境不进入ZIP。设备接口只使用LB1；USB-UART115200、GPIO4–10及N8R8按已实装配置冻结，见specs/。
