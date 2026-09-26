# Q3：预算约束下的条件最优配置

- [完整条件答卷](ANSWER.md)：公式、配置表、结构转移与局限。
- `fixed_policy_grid.csv`、`observed_joint_grid.csv`、`native_Q_sensitivity_grid.csv`：三种求解口径的 36 格主结果。
- `transitions.csv`、`transition_resolution.json`：82 个数值转移括区与分辨率。
- `assumption_sensitivity.json`：九个单因素质量和桥接压力情景。
- `external_nd_audit.json`、`external_nd_budget_comparison.csv`、[外部检验说明](../../experiments/Q3/EXTERNAL_VALIDATION.md)：真实公开训练记录仅验证 $N,D$ 子结构。
- [完整审查](../../experiments/Q3/REVIEW.md)：题面要求、变量来源、识别边界和结论等级。
- [实验索引](../../experiments/Q3/README.md)：数值审查、真实 N/D 部分外测与完整来源。

原始发布位于远端 `integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be`，消费 `team/cyj-scaling@fd2dbb3b2002983430329cdb2ec6a275c2eed4f6` 的 v8 生产者。`upstream_manifest.json` 保留原发布所有文件、代码和论文哈希；本目录只镜像核心表，`curated_manifest.json` 校验所收录文件。完整复跑需在原始发布提交按 `upstream_manifest.json` 的命令执行。

状态：**在成本代理、A/B 桥接假设、87 条 A4 已观测配方和共同支持域内完成题面第三问的条件解**。跨来源质量及配比效应尚未成对标定；数值误差、半合成同源验证和真实 $N,D$ 部分外测均不证明真实训练的无条件四变量最优。
