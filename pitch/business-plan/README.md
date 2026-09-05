# 灵伴中文商业计划书

交付：`lingban-business-plan.pdf`，A4竖版16页，约3.5MB。包含原创产品概念渲染、需求与主动交互、公司授权边界、20人验证方案、官方竞品事实、完整价格梯度、BOM/单位贡献图、三情景现金图、500万元建议融资用途、7天/30天门槛、工厂验收、半年生态、团队与10个月战略选择、来源页。

本PDF是详细中文BP关键内容的阅读版，非18页横版投资演示稿；完整叙述与可修改假设保留在 `../../docs/business/business-plan.md`、`financial-model.md`、其余商业Markdown和CSV中。正文排版稿在 `build_pdf.py`，财务图表和情景表读取原始CSV，生成时检查关键财务口径；不改变原始模型。融资第11节已追加到源BP。

## 复现

在项目根目录执行：

```bash
/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 pitch/business-plan/build_pdf.py
/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 pitch/business-plan/validate_pdf.py
```

依赖本机bundled Python中的reportlab、pypdf、pdfplumber、Pillow及bundled Poppler。使用本机 `/System/Library/Fonts/Supplemental/Arial Unicode.ttf`，只在PDF中嵌入必要字体子集；目录没有复制或分发字体文件。未用LibreOffice、网络下载或外部服务。非本机复现需自行提供合法可用的中文TTF和更新脚本中的字体/运行时路径。

`qa/`保留16页实际Poppler渲染、全页拼图、结构/字形检查、抽取文本、布局记录和来源哈希。人工检查结论见 `QA.md`。若修改正文或CSV，重新构建、渲染并目检；修改源Markdown不会自动替代所有编辑过的PDF排版文案。

## 财务与真实性口径

- 500万元为本方案建议的天使融资金额，不是用户原文指定金额、已承诺投资或已到账资金；用途为建议，不构成支出授权。
- 60万元是独立的精简验证模型。500万元用途尚未建立同口径分月模型，因此不报告跑道和投资回报。
- 产品图是原创三维概念渲染，非实物/制造证明；留存、订单、销售与交付门槛均未声称已经达成。
- 官方竞品标价/性能主张与独立测试、订单和众筹成功明确分开。
