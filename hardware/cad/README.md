# 参数化机械 EVT-A

编辑 `parameters.json`（mm）与 `build_cad.py`，运行 `hardware/tools/venv/bin/python hardware/cad/build_cad.py`。`exports/`包含每件STEP/STL和整机STEP；`parts.json`列明零件、占位、包围盒和实体有效性。参数并非所有尺寸的唯一来源：放样截面、安装坐标、装饰几何及公差须同时编辑Python源；这是可编辑工程，不是已锁定模具模型。

制造件包括底壳、透明上壳、左右按钮盖、独立晶堡、独立雪花、屏框和城堡定位底座。其余名称带placeholder或标为placeholder的实体仅组件包络。OEM按钮杠杆/滚轮支架/光学镜片安装高度、开关真实固定结构、线缆止拉和屏模组孔位尚未完成，需实际模块图纸后ECO。

实际检查在`../validation/cad-brep.json`及`cad-intersections.json`；不是实物装配通过。STL检查另外记录 watertight/winding；透明壳双层放样名义壁厚非完整等厚认证。工程与装配约束见`../../docs/hardware/engineering-and-manufacturing.md`。
