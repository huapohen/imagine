# 灵伴 LINGBAN 中文VC演示稿

最终交付是 **18页、16:9、中文** 的可编辑PPTX、同内容PDF、自包含HTML和逐页讲稿。指定会话口径为 gpt-6-astra / high。所有本会话写入限定在 `pitch/`，主控负责后续集成、Git和对外发布。

## 最终交付

**唯一发布入口：`deliverables/final-20260906/`**。旧release已移至`.build/archived-deliverables/`，不作为当前版本：

- [可编辑PPTX](deliverables/final-20260906/lingban-vc-deck.pptx)
- [同内容PDF](deliverables/final-20260906/lingban-vc-deck.pdf)
- [自包含HTML](deliverables/final-20260906/lingban-vc-deck.html)
- [逐页演讲稿](deliverables/final-20260906/speaker-notes.md)
- [与幻灯片一致的正文](deliverables/final-20260906/deck-content.md)

PPTX包含原生文字、6张原生表格及可编辑架构图，18页均写入演讲者备注和来源。产品图作为嵌入图像，可替换或缩放；封面原创图同时提供[SVG源文件](assets/crystal-mouse.svg)。PDF通过bundled LibreOffice直接从最终PPTX生成，包含已嵌入的中文字体。HTML将最终PDF的18张1600×900渲染页完整嵌入，不依赖网络、字体下载或相邻文件；其展示页为图像，编辑请使用PPTX或构建源代码。

## HTML使用

双击HTML在浏览器打开。方向键、空格、PageUp/PageDown切页，Home/End跳到首尾，N显示或隐藏当前讲稿，F进入或退出全屏，P打开打印。移动端支持按钮及横向滑动。全屏控制栏靠近底部悬停或聚焦后显示。打印样式输出全部18页，不包含操作栏或讲稿。

## 内容和口径

1. 首发299元，99/199/499/899元为目标价格及后续方案，1499/3999仅生态探索。透明晶鼠、原创城堡、电脑承担AI、HID与ESP32-S3伴随模块分离。
2. 个人先受益，企业只看逐项明确批准的业务结果和≥5人聚合。禁止个人钻取、秘密采集、键盘记录、情绪/生理员工评分和自动雇佣决策。人数阈值不等于匿名化。
3. 协议页已按软件源码及验收记录同步：**MCP 2025-06-18 stdio JSON-RPC tools子集**，覆盖initialize、notifications/initialized、ping、tools/list、tools/call，4个本地工具；**A2A 0.3.0 JSON-RPC子集**，覆盖Agent Card、message/send、tasks/get，同步新建文本摘要任务、按身份隔离和持久化。页面列出实际测试覆盖与主要未覆盖项，讲稿列出完整限制。无官方SDK端到端互通或认证。本稿以电脑端本地规则演示为验收范围，审批只写本地outbox，没有外部发送器；可选模型适配由主控独立验收，不纳入本稿验证。最新软件完成记录报告LB1集成代码与模拟测试修复完成，仍待实机验证，未接设备、未验证硬件连通。
4. 299元版贡献66.51元、22.24%、827台/月来自商业CSV。1000台规模成本108元含10元损耗预留，良率未验证；13%销项税预留、不抵进项。小批170元成本时贡献约3.27元。
5. 最新研究已补充Microduck官方产品页：预售价399美元、税运另计，不能再沿用“查无标价”。Violoop仍为预发布预约页，399美元起、优惠后369美元起。均无本次可核验销量或交付实绩。
6. **500万元是本方案提出的建议融资目标，并非用户原文指定金额**，用途200/100/60/80/60万元，与商业计划第11节一致。独立运营模型仍是假设起始60万元、NRE12万元、月固定5.5万元，基准10个月期末现金60494.30元（约6.05万元）。500万元建议尚未建立分月扩张现金模型，不报告其跑道、收入、估值或回报，也不声称融资到账。
7. 7天5台样机和30天试销均为有门槛的计划。未声称客户、订单、收入、团队履历、实物打样或认证完成。10个月1亿美元退出只在收束页及讲稿中列为无估值依据、无收购承诺的目标情景。

## 来源和素材

商业与研究来源只读 `docs/business/` 与 `docs/research/`；协议实现另核对 `software/COMPLETION.md`、`docs/software/README.md`、`docs/software/protocols.md`、`software/lingban/protocols.py`、`mcp.py` 和现有测试输出，关键数据文件及研究快照版本的SHA-256保留在 [source-manifest.json](qa/source-manifest.json)。市场20人研究、200人/30团队名单等均为目标或假设，没有转写为实绩。讲稿标出逐页来源。

封面继续使用明确标注“原创产品概念示意”的SVG。第5页已同步本轮最新 `hardware/renders/hero_raw.png` 概念建模图，裁去空白背景并保留产品主体，原图副本保留在 `assets/hardware-hero-source.png`。素材裁剪参数及哈希见 [assets/manifest.json](assets/manifest.json)。两图均标为概念示意，不能替代实物。

## 可重复构建

在仓库根目录运行：

```bash
./pitch/build.sh review-20260906
```

每次使用新的版本名，不覆盖已定稿文件。输出在 `pitch/deliverables/<版本>/`，中间文件和报告在 `pitch/.build/<版本>/`。源文件：`src/build.mjs`、`src/postprocess.py`、`src/verify-html.mjs`。生成后仍须逐页目检再选择发布版本。

脚本读取已由商业会话生成的财务CSV，不运行会写商业目录的重算脚本。关键模型假设变化时会停止并要求同步讲稿，避免固定叙事与新数据混用。非数字文字及研究事实变化需要编辑者复核。源码与字体配置均仅写 `pitch/`。`src/postprocess.py`还输出deck-content.md，并确保286段PPTX文字都能在对应PDF页中找到。

运行时定位自 `/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime/runtime.json`：

- Node: `dependencies/node/bin/node`，v24.19.0
- Node packages: `dependencies/node/node_modules`，`@oai/artifact-tool` 2.8.59
- Python: `dependencies/python/bin/python3`，3.12.14
- **仅用bundled LibreOffice**: `dependencies/bin/override/soffice`，指向runtime的headless LibreOffice 25.2
- Poppler: `dependencies/bin/override/pdftoppm`
- 字体：本机已存在的 `Hiragino Sans GB`，仅通过仓库内Fontconfig配置加载，不修改全局设置、不打包系统字体文件。
- HTML验证使用bundled Playwright模块与 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` 的隔离headless会话。无新增浏览器或依赖下载。

`load_workspace_dependencies`本轮未暴露，因此使用用户指定runtime。模板picker不可用，使用用户指定的白/深墨蓝/青绿视觉。PPTX及PDF技能的artifact开始标记脚本在初次创作前各执行一次；本次内容同步在首次修改前各执行一次edit标记，构建重试不重复标记。不使用python-pptx、不修改runtime依赖。

## 实际验收与限制

详见 [QA报告](qa/QA-report.md) 与 [全稿拼图](qa/contact-sheet.jpg)。本次重渲染18页，检查受影响的第5/6/16页及全稿缩略图，检查包结构、字体策略、原生表格、融资金额合计、PPTX/PDF正文、18页讲稿与HTML一致性。既有HTML脚本15项检查通过，实际打印18页。软件测试结果引用已有验收记录，本融资稿任务未重跑软件/固件测试。用户已有Chrome profile对8765演示的拦截与本离线file://HTML验收无关，本次未访问8765、未绕过该拦截。

**没有在Microsoft PowerPoint或Google Slides中打开、编辑并保存验证。** PPTX依赖目标电脑有兼容中文字体，跨平台替换字体可能影响行宽，正式路演前建议在实际放映电脑检查。PDF和HTML已固化中文外观。未验证真实硬件、连接器/官方协议SDK端到端互通、用户留存、供应商报价、融资可得性及法律/认证结论。

## 中间文件

`src/`是可维护构建源，`assets/`是素材源及副本，`qa/`是最终验收证据。`.build/`包含草稿、旧版、字体缓存、独立LibreOffice配置、渲染页、HTML打印检查和node_modules符号链接，均非对外交付。主控不要把`.build/node_modules`或缓存打包进项目发布物。

本任务未执行Git操作、未读取原始需求/input/1.txt或env文件、未联系外部人员、未付费。本轮没有修改`pitch/business-plan/`及其中的BP PDF，该目录由另一任务负责。
