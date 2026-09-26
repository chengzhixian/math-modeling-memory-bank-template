# 论文参考文献修订版

以用户2026-09-26提供的 Huawei_Cup_2026_Mathematical_Modeling_latex-main.rar 为基准，仅在第四至七章新增34处引用并补充32篇文献，共引用34篇。正文、公式、数据和图表保持源文件原样。详细位置见 INSERTION_GUIDE.md；每篇网址见 REFERENCES_TABLE.md/CSV。

## 编译

使用 MiKTeX 或 TeX Live 的 XeLaTeX 和 BibTeX，在本目录执行：

```
xelatex -interaction=nonstopmode -halt-on-error -jobname=paper-cited example.tex
bibtex paper-cited
xelatex -interaction=nonstopmode -halt-on-error -jobname=paper-cited example.tex
xelatex -interaction=nonstopmode -halt-on-error -jobname=paper-cited example.tex
```

结果 paper-cited.pdf。模板使用 SimSun、SimHei、KaiTi 等中文字体；本机缺少 LiSu，因此仅相关封面字体回退为 KaiTi。修复模板原有未闭合条件分支；原编号格式保留，文献标题增加来源链接。

本次编译为47页；此前上传PDF为47页，分页因源项目与编译环境有所变化，精确定位请以小节及句子锚点为准。只核验引用关联和编译排版，本次未重新审查或改动模型结论。
