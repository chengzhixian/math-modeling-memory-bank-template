# Q1 v2 外推与重拟合交接

数据说明：problem/readable/DATA_DESCRIPTION_VISIBLE.md；不使用历史隐藏页边文字。分支：integration/chm-q1-clean-20260923。Q1 清单 SHA256：c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9。

本轮按题面补了 A12--A15 对冻结 v2 主模型的逐目标压力比较，保留旧 Ridge 对照，并做 30 次训练行重拟合候选决策敏感性。代码为 src/chm/q1_v2_estimated_stress.py、src/chm/q1_v2_refit_stability.py；复现命令分别为 python src/chm/q1_v2_estimated_stress.py 和 python src/chm/q1_v2_refit_stability.py。输入/输出 SHA 与数据角色写在两个 outputs/chm/q1_v2_* 目录的 manifest.json，论证记录见 experiments/chm/20260925-q1-v2-estimated-and-refit-stress.md。

关键结论：A12--A15 各 63 个配方均是 A4 已见配方，但 10B/70B Loss 是外推估算。v2 与估算表的 Spearman 中位数为 0.4915/0.3941，Ridge 为 0.5136/0.4148；不能据此声称 v2 跨规模排序稳健。重拟合后无约束已观测候选较稳，质量约束和 minimax 的具体候选不稳。四个连续凸包数值界仅对冻结模型成立，重拟合实验只研究 512 个已观测候选，不能冒充连续解的置信区间。

下一步是由参赛者依据本记录决定实际推荐语气；不需要借此改动已冻结主模型。问题一自己的可复现建模闭环已覆盖 A12--A15，但不能把估算表当真实大模型验证。用户当前暂缓 PDF 和跨人整合，本轮未处理这些事项。
