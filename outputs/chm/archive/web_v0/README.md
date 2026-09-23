# 历史配比输出，仅供差异审计

旧网页端配比表与当前确定性复跑有数值差异。逐文件差异摘要保留在 `outputs/chm/q1_local_reproduction_check.json`，关键 alpha 变化见 `experiments/chm/20260923-q1-local-reproduction.md`。旧表已从当前文件树移除以防误用；审计时可在 clean 分支历史提交 `44e8db4` 中读取，不能当作当前模型输入。

当前计算与绘图统一读取 `outputs/chm/local_recheck_v1/`。
