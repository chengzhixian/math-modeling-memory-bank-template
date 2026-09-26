# Q3：预算约束下的条件最优配置

- [完整条件答卷](ANSWER.md)：公式、配置表、结构转移与局限。
- `fixed_policy_grid.csv`、`observed_joint_grid.csv`、`native_Q_sensitivity_grid.csv`：三种求解口径的 36 格主结果。
- `transitions.csv`、`transition_resolution.json`：82 个数值转移括区与分辨率。
- `assumption_sensitivity.json`：九个单因素质量和桥接压力情景。
- `assumption_official_grid.csv`：九个情景在官方预算下的逐格结果，支撑上述摘要。
- `external_nd_audit.json`、`external_nd_runs.csv`、`external_nd_budget_comparison.csv`、[外部检验说明](../../experiments/Q3/EXTERNAL_VALIDATION.md)：42 个公开模型的逐行与预算结果，仅验证 $N,D$ 子结构。
- `independent_grid_audit.json`、`independent_sensitivity_audit.json`、`independent_source_audit.json`：CYJ 对 CHM 发布的独立条件验收和 B/C 原始来源审计；[验收报告](../../experiments/Q3/INDEPENDENT_ACCEPTANCE.md)。
- [完整审查](../../experiments/Q3/REVIEW.md)：题面要求、变量来源、识别边界和结论等级。
- [实验索引](../../experiments/Q3/README.md)：数值审查、真实 N/D 部分外测与完整来源。

原始发布位于远端 `integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be`，消费 `team/cyj-scaling@fd2dbb3b2002983430329cdb2ec6a275c2eed4f6` 的 v8 生产者。`upstream_manifest.json` 保留来源发布记录；`manifest.json` 校验 main 当前代码、论文和核心结果。现可在 main 运行 `src/chm/q3_v8_publish.py` 验收，以及各生产入口复算；外部 N/D 检查默认复核本目录 42 行冻结公开数据，若要重新抓取原公开仓库，可给审计脚本指定同一提交的外部检出目录。命令见 [实验索引](../../experiments/Q3/README.md)。

状态：**在成本代理、A/B 桥接假设、87 条 A4 已观测配方和共同支持域内完成题面第三问的条件解**。跨来源质量及配比效应尚未成对标定；数值误差、半合成同源验证和真实 $N,D$ 部分外测均不证明真实训练的无条件四变量最优。

CYJ 验收提交 `53b4fb5` 已完成声明范围内的独立条件签收；未重跑公开外测，且尚无 `direct` 映射政策的完整 Q3 对照。原验收报告中的 main SHA 是 CYJ 执行时的历史比较对象，当前 main 以本目录的精选文件和最新提交为准。
