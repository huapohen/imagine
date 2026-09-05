# 灵伴 LINGBAN / Imagine

透明晶鼠中的原创微型城堡，与电脑上的主动办公伙伴。当前交付是**可运行软件、固件与数字工程原型、商业与路演资料、AI概念影片**；实物样机、认证与量产尚待验证。

## 打开交付

- [本地资料中心](http://127.0.0.1:8766/)：产品图、全部文档、概念影片与评审资料。
- [16页商业计划PDF](pitch/business-plan/lingban-business-plan.pdf) · [商业计划源文](docs/business/business-plan.md)
- [18页可编辑PPTX](pitch/deliverables/final-20260906/lingban-vc-deck.pptx) · [PDF](pitch/deliverables/final-20260906/lingban-vc-deck.pdf) · [离线HTML](pitch/deliverables/final-20260906/lingban-vc-deck.html)
- [3分钟与8分钟逐字稿](docs/business/pitch-scripts.md) · [60个投资人问题](docs/business/investor-qa-60.md)
- [软件启动说明](software/README.md) · [模型接入与真实测试](docs/software/MODEL_INTEGRATION.md) · [固件](firmware/README.md)
- [CAD/PCB工程交接](hardware/COMPLETION.md) · [工厂RFQ](docs/manufacturing-commercial/rfq-template.md) · [独立硬件评审](docs/verification/HARDWARE_REVIEW.md)
- [八条影片与制作验证](media/FINAL_REPORT.md) · [私有GitHub仓库](https://github.com/huapohen/imagine)

## 本地运行

Python 3.9+，软件服务仅使用标准库：

```sh
./software/start.sh
```

按终端显示的员工/企业链接进入。角色令牌是访问凭据，只保存在页面内存；不要把带令牌的链接放进报告。所有默认演示数据均为合成数据，审批结果只进入本地outbox。

本次交付已在8765启动默认离线服务。当前角色链接记录在权限0600、Git忽略且资料服务不提供访问的`.local/demo-server.log`；可在本机终端查看。用户既有Chrome配置曾拦截该端口，未关闭浏览器保护；隔离浏览器验收已通过，录屏可直接查看。

另开终端运行资料中心：

```sh
python3 scripts/serve_workspace.py
```

临时模型测试使用根目录已被Git忽略的`.env`，须按[模型说明](docs/software/MODEL_INTEGRATION.md)显式开启。默认模型为`gpt-6-astra`、推理强度`medium`；模型负责合成场景草稿，本地权限、本人确认和调用预算保持有效。临时配置不进入镜像、交付压缩包或生产环境。

## 验证与交付边界

[最终验收矩阵](docs/verification/RELEASE_READINESS.md)记录自动化、浏览器、协议、固件编译、CAD、KiCad与视频的实际证据及未验证项。

299元是1000台情景下核心版的目标售价；108元制造成本和66.51元单位贡献是模型估算。五台EVT样机的开发板、透明件和装配成本单独计算。融资500万元是建议方案，60万元精简经营模型单独列示，没有收入或融资实绩假设。

企业只获得本人明确分享的业务结果与至少五人的聚合。人数阈值不代表匿名化；不做秘密采集、键盘记录、情绪/生理员工评分或自动雇佣决策。

EVT-A采用OEM USB HID鼠标总成与独立ESP32-S3交互模块、两路USB连接，电脑承担AI。设备唯一线协议是LB1 ASCII + CRC16；MCP 2025-06-18与A2A 0.3.0是本地实现子集。固件可编译、数字检查通过都不能替代实际通电、ESD/EMC、人体工学和工厂DFM签字；制造文件保持**NOT-FOR-FAB**。

大体积影片和制造ZIP通过私有GitHub Release附件分发，源码、财务、文档和精确哈希清单保留在Git。仅克隆仓库时，按[附件清单](docs/operations/RELEASE_ASSETS.md)恢复媒体。没有联系厂家/投资人、租GPU或额外购买工具。
