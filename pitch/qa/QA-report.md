# 最终内容同步验收

发布版本：`final-20260906`。日期：2026-09-06。本次仅同步内容和素材，沿用18页版式。唯一发布目录是 `pitch/deliverables/final-20260906/`；旧release移至`.build/archived-deliverables/`。

## 本轮同步内容

- 第5页重新导入最新 `hardware/renders/hero_raw.png`，保留产品主体和概念示意脚注。封面继续采用原创SVG并明确标注“原创产品概念示意”。未把几何检查或概念渲染称为实物验证。
- 第6页根据软件完成记录、协议文档及源码更新为 **MCP 2025-06-18 stdio JSON-RPC tools子集**、**A2A 0.3.0 JSON-RPC同步文本任务子集**。实际支持方法、已有测试覆盖、主要未覆盖项在页面展示，全部限制在讲稿列明。没有官方SDK端到端互通或认证声明。
- 同页明确本稿验收范围是电脑端本地规则Agent，批准只写本地outbox，没有外部发送器。软件完成记录已说明主控正在加入可选模型适配，由其独立验收，本稿不验证模型实现或调用。LB1待实机验证，未接设备或验证硬件连通。
- 第16页及讲稿对齐BP第11节，500万元为本方案建议，非用户指定金额，用途200/100/60/80/60万元。60万元独立运营模型继续采用NRE12万元、月固定5.5万元，基准10个月期末60494.30元（6.05万元），累计亏损29.02万元。不推算500万元跑道。
- 重新生成逐页讲稿、HTML内置讲稿与PDF文字正文deck-content.md，更新source-manifest.json和素材哈希。没有修改商业源或`pitch/business-plan/`。

## 本轮实际验证

| 检查 | 结果 | 证据 |
|---|---|---|
| 完整构建 | `./pitch/build.sh final-20260906-r5`实际成功 | .build/final-20260906-r5/ |
| PPTX结构和回读 | 18页，18份notes，Artifact Tool回读通过 | validation.json |
| 原生可编辑元素 | 原生文字、6张原生表格、原生架构图 | validation.json及PPTX XML |
| 布局与字体策略 | 零finding、零warning，Hiragino Sans GB策略通过 | validation.json |
| 融资金额 | 原生表格显式金额合约：200+100+60+80+60=500 | validation.json |
| 比例与单位贡献 | 40+20+12+16+12=100%；299-108-46.36-33.13-45=66.51元 | content-qa.json |
| 全稿重渲染 | bundled LibreOffice生成18页PDF，Poppler输出18张1600×900 PNG | .build/final-20260906-r5/render/ |
| PPTX/PDF文字 | 286段文字在对应PDF页找到，零缺失，字体资源均嵌入 | content-qa.json |
| 原文/讲稿/HTML | 18页notes与构建原文相符，HTML内置讲稿与来源逐页一致 | sync-qa.json |
| HTML显示图 | 18张嵌入图与最终PNG字节完全相同 | sync-qa.json |
| 构建源码 | 本次实际运行的build.mjs与src/build.mjs字节相同 | sync-qa.json |
| 视觉检查 | 第5、6、16页全尺寸目检通过，全稿缩略图检查通过；已修正第6页LB1文字换行 | visual-review.json；contact-sheet.jpg |
| 未改变页 | 其余15页与此前逐页验收版本像素完全相同 | visual-review.json |
| HTML实际浏览器 | Chrome 152.0.7977.77隔离headless，既有脚本15项检查通过 | html-qa.json |
| HTML实际打印 | 打印媒体显示18页，实际打印PDF页数18 | .build/final-20260906-r5/html-print-check.pdf |
| 来源清单 | 本次构建后复核清单，无源文件漂移；硬件原图副本与源文件哈希一致 | source-manifest.json；sync-qa.json；assets/manifest.json |

15项HTML检查覆盖：18张图片加载、初始页、左右方向键、Home/End、下一页按钮、讲稿展示、Esc关闭讲稿、全屏进入及退出、打印全页显示、移动端无水平溢出、零外部网络请求及零JS错误。用户已有Chrome profile对8765本地软件演示的拦截，不影响本次隔离浏览器中的离线file://HTML；本次未访问8765，也未绕过该拦截。

## 软件事实的证据边界

本任务实际读取并交叉核对了：

- `software/COMPLETION.md`
- `docs/software/README.md`与`docs/software/protocols.md`
- `software/lingban/protocols.py`中的MCP_VERSION、A2A_VERSION、Agent Card及A2A方法实现
- `software/lingban/mcp.py`中的握手状态机、工具列表和stdio处理
- `software/test-output/latest-tests.txt`中已记录的MCP握手/真实stdio、HTTP鉴权和A2A生命周期/归属/持久化等测试结果

本次融资稿同步**没有重新运行软件或固件测试**。上述协议测试结果引用已有软件验收记录，不冒充本会话复测或官方测试。收尾时软件完成记录已报告LB1集成代码与模拟测试修复完成，最终构建据此将“修复中”更新为“待实机验证”。此处引用软件会话记录，本任务未复跑软件/固件测试；编译或模拟测试不能证明硬件已接通。

MCP未覆盖resources/prompts/sampling/elicitation/roots/subscriptions/cancellation、进度、分页、listChanged、HTTP transport、OAuth及官方SDK端到端互通。A2A未覆盖流式/SSE、取消、重订阅、推送、异步、多轮上下文、文件/数据part、扩展metadata、gRPC、HTTP+JSON binding、签名/扩展Agent Card及OAuth。完整叙述随18页讲稿交付。

收尾复核已纳入最新`software/COMPLETION.md`、两份软件协议文档和`protocols.py`：A2A不支持内容类型的错误码为-32005（稿中不引用错误码），MCP/A2A版本、方法、支持子集和限制保持一致。最新hero原图也已在本轮重新导入。source-manifest.json记录此次构建的源文件截止时间和SHA-256；后续软件修复不自动纳入本次交付验收。

## 未验证与保留限制

- 没有在Microsoft PowerPoint或Google Slides中实际打开、编辑并保存。PPTX在其他电脑的字体替换效果仍须本机验证。
- 无实机连接、烧录、板级、供电、EMC、耐久、人体工学或认证验证；不把最新渲染的几何修复当作这些测试。
- 无官方协议SDK端到端互通、生产授权安全或企业连接器上线验证。
- 无真实客户/订单/收入/留存、供应商报价、制造良率、融资到账或退出估值证据。

## 文件与执行边界

最终实际构建命令为`./pitch/build.sh final-20260906-r5`。其5个交付文件经逐文件SHA-256一致性校验复制到稳定目录`pitch/deliverables/final-20260906/`。已验证原件归档在`.build/archived-deliverables/final-20260906-r5/`，此前同步版与版面修订稿也保留在归档目录。原始验证报告保持不变，复制链路见delivery-copy.json。

定稿文件SHA-256及大小见release-manifest.json。源文件清单包含最新BP、实际财务CSV/说明、研究资料、软件文档/源码/测试记录与硬件图源，见source-manifest.json。源码/素材哈希见authoring-manifest.json及assets/manifest.json。

本轮仅写pitch，未修改pitch/business-plan/或BP PDF，未执行Git、不付费、不读取原始input/1.txt或env、不对外联系。仅使用bundled LibreOffice，没有使用桌面LibreOffice。PPTX/PDF edit开始标记各成功执行一次。旧QA保留于`.build/content-sync-before/qa/`，不作为本轮结果。
