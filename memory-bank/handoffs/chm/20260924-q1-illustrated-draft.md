# 第一问图文初稿交接（2026-09-24）

- 变更：`paper/sections/chm/q1_draft.md` 嵌入 5 图、增加质量冲突实例表；新图和可重生脚本位于 `paper/sections/chm/figures/` 与 `src/chm/q1_paper_figures.py`。
- 证据：图 1 取自 `outputs/chm/domain_quality_v0.csv`，图 5 取自 `outputs/chm/ablation_v1/mixture_ablation_summary.csv`；其余三图使用已提交的 `local_recheck_v1` 图表，来源哈希见 `q1_figures_manifest.json`。正文图路径检查 5/5 存在。
- 复盘：`problem/chm/20260924_q1_paper_comparison_and_improvements.md`，P0 是质量家族敏感性和 1B 绝对 Loss 预测弱；本轮没有改变模型参数或将未跑检验写成已完成。
- 集成人下一步：根据正式模板统一中英字体、图号和版心，检查 PDF 缩放后的图中文字；跨附件 Q/Loss 桥接继续由 cyj 接口和证据决定。
