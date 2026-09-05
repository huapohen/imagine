# 最终交付验收矩阵

2026-09-06，主控集成。此版本可用于本地产品演示、项目/投资评审和深圳工厂技术讨论。制造状态保持 **NOT-FOR-FAB**；下表严格区分已执行的数字验证与尚无实物证据的项目。

|交付|实际验证与结果|证据|未验证边界|
|---|---|---|---|
|软件/权限|59项自动测试；服务端角色隔离、并发审批仅一次、撤销共享与A2A缓存、插件越权拒绝、规则提醒、持久化|`./software/test.sh`、`software/tests/`|生产部署、真实企业连接器、多用户负载|
|真实模型|WanAPI Responses，gpt-6-astra / medium；会议、阻塞、休息三个HTTP场景成功，均pending；重复幂等不增加调用，未批准outbox为空|[模型验收](../software/MODEL_INTEGRATION.md)|总预留19/20含诊断；成功三次1980 tokens并非全程用量；不能独立认证提供方模型别名或保留策略|
|员工/企业网页|隔离Chrome 152，14项场景回归+9项模型入口/离线回退/同意检查；桌面与390px移动布局，未见前端异常|[场景报告](browser/report.json)、[模型UI](browser/model-ui.json)、同目录截图|用户既有Chrome配置访问8765曾返回ERR_BLOCKED_BY_CLIENT，未关闭其保护；无实机硬件|
|固件/设备协议|LB1 Python/C++共用104行golden；独立75条CRC核验；Mock HAL隐私高阻、共阳反相、5秒离线、去抖/回绕；safe/EVT-A两目标实际编译|[固件](../../firmware/README.md)、[独立HAL源](hal_independent.cpp)、[硬件评审](HARDWARE_REVIEW.md)|未烧录、未接线、触摸阈值未标定、OLED为候选|
|CAD|20件有效STEP/BREP、20件水密STL；完整生成报告无>0.05mm³正体积干涉；独立STEP回读与关键部件求交通过|`hardware/validation/`、`hardware/cad/exports/`|OEM/器件仍有占位；壁厚、公差、人体工学、装配、止拉与强度须实测|
|KiCad|官方9.0.7 ERC0、几何DRC0、未连线0、schematic parity0；82个针脚精确网名一致，4个机械孔声明board-only|[独立复核](HARDWARE_REVIEW.md)、`hardware/validation/pcb-drc.json`|ESD料号/模块针序/电源峰值/反灌/EMC/DFM签字未完成|
|商业资料|16页BP PDF，财务CSV可重算；299核心目标、108批量估算、66.51贡献；500万元融资建议与60万元经营模型分开|[BP验收](../../pitch/business-plan/QA.md)、[商业复核](BUSINESS_RELEASE_REVIEW.md)|非报价、收入、融资或订单实绩；本次未验证真实留存与购买|
|路演|18页可编辑PPTX、PDF、离线HTML及讲稿；286段正文一致、中文渲染检查、HTML15项检查|[PPT验收](../../pitch/qa/QA-report.md)|未验证Microsoft PowerPoint/Google Slides原生编辑保存及放映机字体|
|AI影片|8条各15.000秒、2560×1440；合集120.000秒；中文旁白/字幕/概念标签；原片及来源哈希保留|[媒体验收](../../media/FINAL_REPORT.md)|生成形态与CAD存在差异，不能证明功能、实物或运动安全|
|软件录屏|28.000秒真实隔离浏览器录屏与同次验证定格截图；明确合成数据/设备模拟/离线规则|[录屏来源与QA](../../media/demo/README.md)|早期已通过规则界面快照，不展示新增模型按钮，不是硬件录像|
|资料服务|14项公开/私有路径验证；.env、.local、私有API账本、下载与工具目录均拒绝访问|[路由检查](portal-access.json)|仅回环服务，无公网部署|

## 交接后的下一步

按[工厂入口](../manufacturing-commercial/FACTORY_START_HERE.md)取得OEM/模块真实图纸和拆项报价，完成电子机械复核后再形成可下单版本。七天目标是五台样机；30天试销取决于器件到货、合规与小批验收。没有对外发送采购/投资消息，没有下单、开模、租GPU或生产发布。

## 安全与费用记录

临时模型`.env`为当前用户0600文件，Git忽略；镜像和工厂包不包含它。真实模型只处理固定合成文本，默认程序离线。本人同意、权限、审批和预算均由本地程序验证，模型文本不能触发外部执行。

八条MiniMax-H3生成API全部成功，120输出秒按官方刊例预占96元，低于用户100元上限；不是账户最终扣款证明。模型接入人民币成本未从不完整usage推算。没有额外付费生成、付费语音或GPU租赁。

源码、文档及审查证据存于私有仓库；大体积附件、哈希与恢复方法见[Release附件](../operations/RELEASE_ASSETS.md)。用户可以复现检查，也可以直接从本地资料中心打开已生成交付物。
