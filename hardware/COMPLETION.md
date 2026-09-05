# 灵伴 LINGBAN / Crystal Mouse EVT-A — 完成交接

**交付状态：实际CAD + 实际布线PCB的数字工程原型；全部制造输出 NOT-FOR-FAB。** 完成日期2026-09-06。唯一首发为299元核心目标含税零售价（1000台情景，灯＋触摸＋OLED）；当前5台DevKit样机成本约863–1850元/合格台未税工程估算、待报价；108元是未来批量商业模型假设，499仅未来外观/服务套装。没有实物打样、板级通电、固件烧录、认证或量产完成声明。本会话只写hardware/与docs/hardware/，不做Git、不读取原始input/需求或.env、不联系厂家、不付费；主控负责集成。

## 本轮最终集成结果

- 唯一协议LB1 ASCII+CRC16，UART桥115200 8N1、N8R8和GPIO冻结；无每消息TTL/推送事件。隐私切SW3V3并高阻GPIO4–9，不显示privacy灯/屏；touch阈值0默认禁用，屏为状态图标。
- 修复已复现的86项parity差异：保留原理图局部标签，用完整`/3V3`等名称匹配PCB；33个明确NC单脚网按KiCad语义保留且无铜连接；H1–H4设`board_only/exclude_from_bom/exclude_from_pos_files`，不使用全局忽略或错误豁免。
- **KiCad9.0.7 schematic parity=0、几何DRC=0、未连接项=0、ERC=0**。完整网络名逐节点比较：49功能节点＋33明确NC节点，共82节点一致；36项选定/保留脚检查通过。
- CAD与pitch渲染118个既有文件hash均未改变，铜线/过孔/焊盘/板框几何hash未改变，既有CAD干涉仍为[]。本轮不重新生成几何、不重渲染产品图；仅刷新PCB检查、制造导出与PCB图。
- 交付ZIP重新生成，严格不含`tools/`、下载/缓存、`.env`、锁文件、KiCad本地状态或`.DS_Store`；源码S表达式辅助模块随PCB提供。包与逐文件hash在delivery/，包装审核见`package-audit.json`。

证据：`validation/integration/result.json`、`integration/parity-before.json`、`pcb-drc.json`、`pcb-geometric-drc.json`、`sch-erc.json`、`netlist-pinmap-check.json`。生成器用`--sync-existing`只修项目语义，铜线原样保留；之后从头生成也调用同一语义逻辑。

## 精确产物

|用途|路径|内容|
|---|---|---|
|冻结软硬件架构|`hardware/specs/architecture.md`|OEM USB HID + 独立ESP32-S3开发板，双USB/外部Hub，电脑运行Agent；LB1 ASCII + CRC16串口协议|
|官方核对引脚|`hardware/specs/pin-map.md`、`pin-map.json`|GPIO4/5/6/7/8/9/10对应J1.4/5/6/7/12/15/16；v1.1板载RGB38/初版48均避开；官方文本、DXF与原理图缓存在references/|
|参数化CAD源|`hardware/cad/parameters.json`、`build_cad.py`|mm单位，外壳/底板/光学孔/双出线槽/柱位与公差、屏框、原创云阶晶堡、六折雪花、定位底座及组件占位|
|CAD工程导出|`hardware/cad/exports/`|20件逐件STL + 20件逐件STEP；`lingban_assembly.step`整机装配；`lingban_exploded.step`爆炸装配。当前零件以parts.json为准，无旧插座重复件|
|pitch图片|`hardware/renders/lingban_hero.png`、`lingban_exploded.png`|1800×1500透明Cycles渲染，带“AI概念展示 / 数字工程原型 / 非实物”标识|
|动画与源|`hardware/renders/lingban_turntable_concept.mp4`、`lingban_hero.blend`、`lingban_exploded.blend`、`lingban_turntable.blend`、`render_scene.py`、`finish_media.py`|720×720、约5秒完整转台视频；120帧24fps可编辑旋转源，视频每4帧抽样。raw/frames只作中间产物|
|可编辑PCB工程|`hardware/pcb/NOT-FOR-FAB/lingban_carrier.kicad_pro`、`.kicad_sch`、`.kicad_pcb`|36×76×1.6mm两层载板，开发板双排插座，灯/触摸/屏/DPDT物理开关线束，底面阻容，自包含符号和封装库|
|真实走线图|`hardware/pcb/NOT-FOR-FAB/plots/pcb-routed.svg`、`pcb-routed.png`|由实际KiCad铜线/焊盘坐标导出，511段铜线、17过孔、35条连接树边；无未布线连接|
|网表/装配清单|`hardware/pcb/NOT-FOR-FAB/lingban_carrier.net`、`.xml`、`BOM.csv`、`PnP.csv`、`PnP-kicad.csv`|KiCad真实网表；底面SMD贴装坐标，D1标DNI；厂商须确认底视/顶视、原点与旋转|
|制造评审文件|`hardware/pcb/NOT-FOR-FAB/gerber-review-only/`|F/B铜、F/B阻焊、F/B丝印、底面锡膏、Edge.Cuts共8个Gerber；PTH/NPTH两份Excellon钻孔、钻孔图、gbrjob。不是下单包|
|工程/商业交接|`docs/hardware/engineering-and-manufacturing.md`|99/199/299/499/899电子机械差异、BOM批量/税/良率/NRE估算、7天样机计划、制造就绪矩阵、装配验收与工厂待确认尺寸|
|局部工具与校验|工作区`hardware/tools/README.md`（不随ZIP）、`hardware/requirements.lock`；`hardware/validation/tool-integrity.json`|CadQuery2.8.0、trimesh5.1.0、Blender4.5.3、KiCad9.0.7；官方哈希/应用签名验证；不依赖全局brew安装|
|精简交付包|`hardware/delivery/lingban_evt_a_review.zip`、`SHA256SUMS.txt`|供主控集成，不含tools目录、DMG、venv、缓存、挂载应用树、本地状态和视频逐帧中间文件|

## 可重复运行命令

在仓库根运行；工具挂载/重建步骤见hardware/tools/README.md。

```sh
python3 hardware/pcb/build_pcb.py --sync-existing
python3 hardware/pcb/finalize_project.py
python3 hardware/pcb/export_and_verify.py
hardware/tools/venv/bin/python hardware/pcb/render_board.py
hardware/tools/venv/bin/python hardware/validation/validate_artifacts.py
python3 hardware/validation/integration/check_integration.py
python3 hardware/package_delivery.py
```

`export_and_verify.py`调用真实KiCad，parity检查同时启用`--schematic-parity --exit-code-violations`，另导出独立几何DRC和ERC，失败非零退出。当前命令使用工作区既有工具；精简ZIP不附带tools，可用已安装的等版本工具或以hardware/requirements.lock重建局部Python环境。CAD尺寸参数不是全部独立约束求解器；更改壳宽/壳长会调整放样，但安装坐标、OEM接口与装饰仍须检查Python参数与干涉，不能只改一个数字直接制造。

## 实际验证

- OpenCascade：当前20件BREP均有效、均为一个实体；两两正体积干涉 >0.05mm³ 为0。见`validation/cad-brep.json`、`cad-intersections.json`。不意味着局部法向壁厚、公差、强度或实物手感已通过。
- 导出STL：20件均封闭、水密、法向一致、正体积、单连通实体，见`stl-mesh-check.json`、`artifact-check-summary.json`。
- KiCad9.0.7：**ERC 0违规；几何DRC 0违规、0未连接项；schematic parity 0**，未靠规则忽略/排除消除报告。见`sch-erc.json`、`pcb-drc.json`、`pcb-geometric-drc.json`与`kicad-command-results.json`。ERC对象是无源载板触点，不证明ESP/外部模块电气特性。
- 36项官方选定脚/保留脚核对通过；49功能焊盘及33个明确NC焊盘与KiCad导出原理图网表完整名称一致（不再去掉/前缀），NC均单脚且无铜连接。见`netlist-pinmap-check.json`。本轮已只读核对LB1软件/固件、N8R8 profile及GPIO；主控报告两目标编译和HAL测试通过，本会话不重复编译/烧录。
- Blender官方SHA256匹配，Blender/KiCad应用codesign严格验证退出0；KiCad DMG内部校验有效。Python以官方PyPI元数据生成hash锁并从实测可信镜像执行`--require-hashes --reinstall`成功。见工具完整性/安装日志。
- 渲染由本地Cycles执行；视频由ffmpeg编码、ffprobe检查，见`media-probe.json`。城堡窗发光、光导环与屏幕文案是视觉示意/合成数据。

## 工程师/厂商确认后才能推进的点

1. **制造状态不提升到fab-candidate**：D1为未冻结封装的ESD DNI占位；RGB、OLED、DPDT及插座未全部冻结MPN/供应商图纸。需要真实TVS方案、线束脚序、装配方向和DFM审核。
2. **电气未实测**：开发板稳压器/USB能力、启动与无线峰值、满白屏/满亮、隐私断电反灌、触摸阈值/ESD、温升。初版默认USB-UART且关闭Wi-Fi/BLE；通用500mA端口不能按1A电源使用。
3. **隐私边界明确**：机械DPDT切屏/灯电源并给GPIO状态，断线默认隐私；不硬断USB、触摸线路或主机Agent。实装HAL detach PWM/Wire.end并将GPIO4–9置INPUT，无内部上拉；SW3V3断电后不显示privacy灯/屏，只由UI/开关本体指示。触摸默认阈值0、禁用采集，屏仅状态图标；没有音视频、生理诊断、员工评分或秘密采集。
4. **机械需实物ECO**：OEM外形/固定孔/镜片到桌面高度/光学中心、按钮杠杆与滚轮结构；屏模块厚度/孔位和屏框防脱卡扣；装饰底座防脱；隐私开关固定孔与实际止拉件；铜螺母/底脚/螺钉/透明料收缩和后处理。当前名义126×80×54，实际曲面可能超调，完整包络见`assembly-envelope.json`。
5. **RF净空未完成整机验证**：PCB有禁铜区，但附近金属紧固件/铜螺母仍需移位或改非金属，按实际模块天线参考布局复审；不宣称无线/EMC验证通过。
6. **下阶段是7天样机**：到货、工程师签字、电气上电与机械验收均是门槛；30天试销受法规/认证/小批量验收限制。没有厂商报价，所有成本明确批量、税、良率和NRE假设；VC/退出估值不属于本次硬件事实。

specs/已与实装LB1/GPIO同步，继续使用hash未变的带标识PNG/MP4供pitch，最后将NOT-FOR-FAB工程交给电子/机械工程师审核。不要把hardware/downloads、tools/venv、uv-cache、mount-*加入Git或对外包。

## 本轮影响文件

- 接口与商业：`hardware/specs/architecture.md`、`pin-map.md`、`pin-map.json`；`hardware/README.md`、本文件；`docs/hardware/README.md`、`engineering-and-manufacturing.md`。
- PCB语义与复现：`hardware/pcb/build_pcb.py`、新增`semantic_sync.py`与本地`sexpr.py`、`finalize_project.py`、`export_and_verify.py`、`render_board.py`、PCB README；NOT-FOR-FAB中的PCB/原理图、库、BOM、导出网表/制造文件/PCB图已刷新。铜线几何未改，原项目规则未加忽略项。
- 验证与交付：`hardware/validation/validate_artifacts.py`、README、`integration/`和当前检查报告；`hardware/package_delivery.py`、用于无工具环境交付的`hardware/requirements.lock`、delivery/ZIP/manifest/SHA/audit。CAD与产品PNG/MP4/Blender源均未修改；软件、固件及商业主文只读。
