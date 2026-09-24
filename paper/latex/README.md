# 2026 F 题 LaTeX 空白协作模板

本目录以用户提供的第二十二届华为杯 LaTeX 模板为基础。`template_source/` 保存原件；`gmcmthesis.cls` 为工作版，修复原类文件条件块。工作版优先使用原模板的 `LiSu`（隶书）；本机没有该字体时仅对这几处标题回退为楷书，安装正版 `SimLi.ttf` 后会自动恢复隶书。**本分支只保留空白总稿与各成员占位章节，不包含 chm 第一问初稿或结果图。** chm 的初稿、图和编译 PDF 保存在 `integration/chm-q1-clean-20260923`。

| 文件 | 唯一写入负责人 |
|---|---|
| `sections/chm/*`、`figures/chm/*` | chm |
| `sections/cyj/*` | cyj |
| `sections/zhh/*` | zhh |
| `main.tex`、`gmcmthesis.cls`、`references.bib`、最终提交 PDF | 集成人（建议 zhh） |

各成员在自己分支写稿并交接，集成人串行合入；不要同时改主文件。新增宏包、公共符号和文献由成员提出，集成人统一加入。

本机已验证 MiKTeX 25.12、XeLaTeX 和 BibTeX 可用。新终端在 `paper/latex/` 运行 `xelatex -interaction=nonstopmode -halt-on-error main.tex`；有文献引用时再运行 `bibtex main`，随后运行 XeLaTeX 两次。首次编译缺少宏包时 MiKTeX 会按用户配置自动安装。构建生成的 `.aux`、`.log`、`.toc`、本地 PDF 等文件不进入 main。chm 分支的 `output/chm-q1-draft.pdf` 是经过页面检查的阶段初稿。

此模板源自 2025 年第二十二届；2026 年正式提交前须核对当届官方封面、匿名、页面和上传规则。当前 `withoutpreface` 只为公开协作稿使用，不代表正式提交版式。`template_source/makefiles.bat` 会遍历全部 `.tex`，不适合本多文件项目；应从 `main.tex` 编译。
