# 2026 F 题 LaTeX 协作初稿

本目录以用户提供的“第二十二届华为杯latex模板”为排版基础。`template_source/` 保留原始模板的源文件、示例、封面素材及随附 DOC，未收录示例 PDF、编译日志和往年未使用的图片。实际论文入口为 `main.tex`，章节拆在 `sections/`；`figures/chm/` 当前保存第一问的五张自有数据图。**该模板来自第二十二届（2025 年）；正式提交前必须再按第二十三届（2026 年）当年官方模板、封面、匿名及提交规则逐项核对。** 现有主文件只作为整体初稿，不是可直接提交的终稿。

## 文件归属与交接

| 文件 | 日常写入者 | 内容 |
|---|---|---|
| `sections/chm/q1.tex`、`sections/chm/q3_numerical.tex`、`figures/chm/` | chm | 第一问正文、图表及第三问数值求解 |
| `sections/cyj/q2.tex`、`sections/cyj/q3_theory.tex` | cyj | 第二问标度律、第三问目标函数和理论 |
| `sections/zhh/*.tex` | zhh | 摘要、问题重述、公共假设、第四问、全文评价 |
| `main.tex`、`gmcmthesis.cls`、`references.bib`、最终 PDF | 集成人（建议 zhh） | 总装、模板维护、文献合并与最终编译 |
| `template_source/`、`gmcm.bst` | 集成人 | 原模板归档；普通写作者不修改 |

各成员只在本人分支编辑所属文件并交付；不要三人直接同时修改 `main.tex` 或同一份 LaTeX 文件。集成人检查交接的模型口径、图表来源与编译结果后，串行合入 `main`。若某章节需公共宏包或版式调整，先在本人交接说明中提出，由集成人改主文件或类文件。当前 `main` 上的 `q1.tex` 是 chm 初稿快照；后续 chm 以其个人分支该文件为唯一写入线，由集成人合并。

## 源模板与本地修正

`template_source/gmcmthesis.cls` 是原件。工作用 `gmcmthesis.cls` 作两处最小调整：原类文件的 `\ge@maketitle` 里开启了 `\if@gmcm@preface` 却未闭合，现于 `\makenametitle` 前补 `\fi`；将第二十二届的图片标题换成不带年份的文字，防止 2026 初稿显示过期届次。当前 `main.tex` 选用 `withoutpreface`，因为 2026 年封面及身份字段尚待核对，且仓库为公开仓库；正式版本由集成人按当年官方要求调整，避免在公开稿中写入真实姓名、学校或队号。

原 `makefiles.bat` 会遍历目录中所有 `.tex`，不适合这个多文件项目；不要直接运行。若本机已有 XeLaTeX 与 BibTeX，在 `paper/latex/` 内依次运行：

```powershell
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

编译日志、`.aux`、`.toc` 和 PDF 先留在本地，不作为研究结论自动入库。集成人检查实际 PDF 的分页、中文字体、图注、目录、引用、匿名信息和官方提交要求后再决定保留何种交付物。此机器目前未找到 XeLaTeX，故本次只完成了源文件、章节入口、五图文件和静态引用检查；**尚未宣称 PDF 编译通过**。

第一问数值来自 `integration/chm-q1-clean-20260923` 的 `paper/sections/chm/q1_draft.md` 和 `outputs/chm/` 固定版本。第二至四问均为明显标注的占位文字，无最优配置或外推数值。后续提交前要删除这些占位文字并更新摘要。
