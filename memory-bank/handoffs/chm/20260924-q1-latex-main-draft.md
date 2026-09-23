# chm 第一问 LaTeX 初稿交接（2026-09-24）

- 用户明确要求在 `main` 建立整体 LaTeX 初稿。本次从 `integration/chm-q1-clean-20260923` 的第一问图文稿迁入 `paper/latex/sections/chm/q1.tex`，复制五张自有数据图到 `paper/latex/figures/chm/`。
- 数据和图表的完整运行证据仍以 chm clean integration 分支的 `outputs/chm/`、图表 manifest、问题一审查文档为准；此提交是论文排版快照，不代表三人所有接口已验收。
- `paper/latex/check_draft.py` 对章节、图、标签和文献键的静态检查通过；此机器未安装 XeLaTeX，尚无可验证的编译 PDF。集成人需在具备 TeX 环境的机器上完成编译和页面目视检查。
- 后续 chm 只改 `sections/chm/q1.tex`、`sections/chm/q3_numerical.tex` 及自有图；cyj 改 `sections/cyj/`，zhh 改 `sections/zhh/`；总文件由集成人串行修改。模板和 2026 官方要求的差异由集成人统一核对。
