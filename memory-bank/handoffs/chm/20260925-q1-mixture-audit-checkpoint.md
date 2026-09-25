# Q1 配比审计检查点交接

日期：2026-09-25；分支：`integration/chm-q1-clean-20260923`。前置提交 `cdda1ad`。新增代码、表与说明见 `src/chm/q1_mixture_final_audit.py`、`outputs/chm/q1_mixture_final/` 和 `experiments/chm/20260925-q1-mixture-final-audit.md`。

A4--A15 十二个源文件均核对 index、列序和 SHA；真实 A6/A8 配方256对精确对应。A10 64个配方中17个在A4凸包内、47个超出。原Ridge 1B绝对RMSE仅4/13优于训练均值基线。训练内选择的交互候选在真实检验组改善RMSE，但未改变正式Ridge接口、未证明因果协同。下一步：多目标情景、17域质量覆盖、v1.4只读包、论文与复现验收。无人工真值/盲评条件，按用户指示跳过并明确局限。
