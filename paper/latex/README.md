# F 题 LaTeX 协作稿

`main.tex` 汇集 `sections/Q1/main.tex`、`sections/Q2/main.tex`、`sections/Q3/theory.tex`、`sections/Q3/numerical.tex`、`sections/Q4/main.tex` 和 `sections/common/`。正式图按 `figures/Q1` 至 `figures/Q4` 放置，各问答案与冻结证据见 `outputs/Q1` 至 `outputs/Q4`。Q4 论文已对齐 v3 数值版；四问构成当前完整 LaTeX 答卷。

`template_source/` 保存用户提供的第二十二届华为杯原模板；工作版 `gmcmthesis.cls` 修复条件块，字体不可用时回退。2026 年正式封面、匿名、文件命名与提交规则仍须按当届官方要求核对。

有 XeLaTeX 与 BibTeX 的环境从本目录依次运行：

```powershell
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

构建产生的临时文件默认不进入 main。`scripts/check_paper_integrity.py` 已检查章节、引用和 11 幅正式图；当前环境尚未安装 XeLaTeX/BibTeX，因此 PDF 编译与视觉排版仍待独立核验。四问跨源假设及支持域限制必须保留；2026 年正式提交规则尚须按当届官方要求核对。
