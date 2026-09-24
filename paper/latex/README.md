# chm 第一问 LaTeX 初稿

本分支在共享的第二十二届华为杯模板上保存第一问完整正文、五张自有结果图和已编译的 `output/chm-q1-draft-20260924.pdf`。`main` 只保留可编译的空白协作模板；chm 的结果、图和 PDF 不提交到 main，须待集成人验收后再选择性合入。

`template_source/` 是用户给的原模板。工作版 `gmcmthesis.cls` 修复原类文件未闭合的条件块，并优先使用原模板的 `LiSu`（隶书）。这台机器没有正版 `SimLi.ttf`，故仅在缺字时对原模板使用隶书的标题自动回退到楷书；将来安装字体后不必再改 LaTeX 源码。

## 协作分工

| 文件 | 唯一写入负责人 |
|---|---|
| `sections/chm/q1.tex`、`sections/chm/q3_numerical.tex`、`figures/chm/` | chm |
| `sections/cyj/*` | cyj |
| `sections/zhh/*` | zhh |
| `main.tex`、`gmcmthesis.cls`、`references.bib`、最终提交 PDF | 集成人（建议 zhh） |

成员只在本人分支修改所属章节，集成人串行总装。本分支 `main.tex` 是为阶段编译保留的总稿快照；第二至四问仍是明确占位，不代表已完成的结论。

## 本机编译

已在 Windows 的 MiKTeX 25.12 上用 XeLaTeX、BibTeX、XeLaTeX 两次编译成功，产出 19 页 A4 PDF，并检查中文、图表、页面、目录和文献。新终端在 `paper/latex/` 下运行：

```powershell
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

`output/chm-q1-draft-20260924.pdf` 是同步 2026-09-24 Q1 可识别性修正后重新编译的固定快照：保留冻结 1M 代理的跨实验组排序检验，不再把经验幅度差异解释为连续的配比尺度律。构建过程文件由 `.gitignore` 排除；如正文、图表、类文件发生变化，应重新编译并替换该 PDF。该模板来自 2025 年第二十二届，2026 年提交前必须核对当年官方封面、匿名要求和最终格式。本稿使用 `withoutpreface`，尚非正式提交版。

第一问数值源见 `paper/sections/chm/q1_draft.md`、`outputs/chm/local_recheck_v1/` 和 `outputs/chm/ablation_v1/`。第二、四问的占位内容在完成接口验收后由各负责人替换。第三问现含 B1 解析诊断与 B7 半合成质量模型的条件联调；cyj 的正式 `ready_for_Q3=false`，表中配置不能作为最终最优结果。
