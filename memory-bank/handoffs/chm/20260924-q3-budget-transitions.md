# chm 阶段交接：Q3 连续预算与结构转移

日期：2026-09-24（北京时间）  
分支：`integration/chm-q1-clean-20260923`

## 本阶段完成

在不等待 cyj Q/p 最终桥接的前提下，完成 B1 N-D diagnostic 的连续预算结构分析：

- 推导内点最优闭式解；
- 推导 N/D 对预算的弹性；
- 给出 3 个 C7 上下文下的精确活跃约束转移阈值；
- 用 2001 点对数预算扫描验证解析阈值；
- 明确 30000 Token 只是一条成本临界线，不是新增 C7 观测；
- 保持所有结论为 diagnostic，不发布正式 Q3 最优配置。

输出：
- `src/chm/q3_budget_scan.py`
- `outputs/chm/q3_budget_transitions.csv`
- `experiments/chm/20260924-q3-budget-transitions.md`

## 关键结论

内点预算弹性：
- N：0.451528388895
- D：0.548471611105

固定上下文的实际最优路径：
`infeasible → N_min → interior → D_max → support_corner`。

2048 Token 的两个主要高预算转移：
- 内点→D_max：约 `9.326e21` FLOPs；
- D_max→N_max+D_max：约 `2.300e22` FLOPs。

这为后续正式 solver 的结构转移判据提供解析 oracle。

## 仍然阻塞

cyj 仍需发布正式 B7 质量结果、B1/B7 Loss 处理、p anchor/lambda 决策和 `ready_for_Q3=true`；zhh 仍需更新 C7 合同。当前不改变 upstream gate。
