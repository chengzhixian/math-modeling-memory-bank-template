# Q1 自身答案定型交接

日期 2026-09-25；维护分支 integration/chm-q1-clean-20260923。数据说明只使用 problem/readable/DATA_DESCRIPTION_VISIBLE.md，不使用历史隐藏页边文字。正式接口 chm.q1.v2.0 的 SHA256 仍为 c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9。

本轮将 Q1 自身答案定型为 outputs/chm/Q1_FINAL_ANSWER_V2.md，并使 paper/sections/chm/q1_draft.md 和 interfaces/chm/CONTRACT.md 明确指向该结论入口。答案覆盖 A1–A3 质量代理、冲突评价与扩展复核，A4+A5 主模型，A6–A11 真实检验，A12–A15 估算压力，以及给定权重和质量政策的四类配方数值决策。此前的机器结果与代码保持冻结，不因负向压力证据而调整模型或偷换数据角色。

定型判断：问题一在附件 A 与清楚工程假设下已经解决。四个连续凸包配方是冻结交互代理下的浮点数值解；13 域权重、质量映射与支持集必须随答案报告。A12–A15 未支持大规模排序稳健，属于已如实处理的有效范围，不是未完成的必做建模。质量案例无人工真值，不报告分类准确率。

复核入口：src/chm/test_q1_v2.py、src/chm/audit_q1_v2_signoff.py、src/chm/q1_v2_estimated_stress.py、src/chm/q1_v2_refit_stability.py；输出、参数与哈希汇总见定型答案末尾。论文排版或跨人整合按用户当前范围暂缓，不影响 Q1 自身答案的定型判断。
