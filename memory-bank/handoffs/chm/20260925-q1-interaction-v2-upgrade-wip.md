# Q1 v2 交互主模型升级检查点（进行中）

2026-09-25；分支 integration/chm-q1-clean-20260923。用户明确授权主模型切换。已发布 v2 代码及冻结输出：`src/chm/q1_interface_v2.py`、`src/chm/release_q1_v2.py`、`interfaces/chm/q1_interface_v2.json`、`outputs/chm/q1_v2/`。默认 `src/chm/q1_interface.py` 指向 v2，旧 v1.3 移至独立历史读取器。

配方决策改为 512 已观测 A4 配方的精确枚举，支持 13 目标权重、minimax、A1 主质量政策；45 情景在 `outputs/chm/q1_v2_decisions/`。等权无约束 index 136，direct index 301，direct+near index 172；最差域保护 index 477。非凸连续凸包不声称有限枚举最优。chm 侧以 cyj 86526a1 B7 系数重算新条件情景，见 `outputs/chm/q2_interaction_scenarios_v2/`；cyj 自有 v6 发布尚未替换。Q3 p 支持诊断已改为 v2 且 `ready_for_Q3=false`。

Q1 30 项单测通过，包含新版预测、梯度、支持域、决策和 Q2 重算。后续仍需迁移旧 Q3 选择验证入口、同步其他文档、复跑相关测试；本交接为中途远程备份。
