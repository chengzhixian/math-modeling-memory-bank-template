# F 题 LaTeX 协作稿

`main.tex` 汇集 `sections/Q1/main.tex`、`sections/Q2/main.tex`、`sections/Q3/theory.tex`、`sections/Q3/numerical.tex` 及现有 Q4/公共章节。对应图位于 `figures/Q1`、`figures/Q2`、`figures/Q3`。各问结论与冻结证据入口见 `outputs/Q1`、`outputs/Q2`、`outputs/Q3`。Q4 和公共段落仍由其负责人更新，不把当前总稿当作提交终稿。

`template_source/` 保存用户提供的第二十二届华为杯原模板；工作版 `gmcmthesis.cls` 修复条件块，字体不可用时回退。2026 年正式封面、匿名、文件命名与提交规则仍须按当届官方要求核对。

有 XeLaTeX 与 BibTeX 的环境从本目录依次运行：

```powershell
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

构建产生的临时文件和 PDF 不进入本次 main 同步。总稿的 Q1–Q3 只陈述已在各自来源和审查中支持的条件结论；所有跨源假设及支持域限制必须保留。
