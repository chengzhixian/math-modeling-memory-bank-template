# Q1 v2.0 交互主模型及 Q2/Q3 版本交接

日期 2026-09-25。分支 `integration/chm-q1-clean-20260923`。用户明确指示交互模型直接升为主模型。本交接替代同日 WIP；精确来源和复现见 `experiments/chm/20260925-q1-v2-primary-interaction.md`，消费者合同见 `interfaces/chm/Q1_V2_DOWNSTREAM.md`。

## 已完成

- 默认 `src/chm/q1_interface.py` 指向 `chm.q1.v2.0`，不可变清单 `interfaces/chm/q1_interface_v2.json`，SHA256 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`；17 主项、10 二元交互、13 目标、A1 sample 质量主值。v1.3 Ridge 读取器与输出留历史比较。
- 默认配方决策改用 `src/chm/q1_hull_bounds_v2.py` 的 McCormick LP 松弛加空间分支定界；四个等权主情景全局数值上下界间隙均 <0.001。完整可行配方在 `outputs/chm/q1_v2_hull_bounds/bounds.json`。另有 512 条 A4 单配方精确枚举 45 情景，`outputs/chm/q1_v2_decisions/`。质量 direct 和 direct+near 约束下，连续凸混合显著优于单条 A4 方案，旧 LP 顶点最优结论已撤回。
- CHM 侧以 cyj `86526a1` 冻结 B7 系数、显式 lambda=1/eta=0，在连续支持域重算三政策，条件 B7 Loss 约为 2.271859、2.302976、2.318334；文件 `outputs/chm/q2_interaction_scenarios_v2/`，仍属条件工程情景。
- `q3_p_support.py`、`q3_p_selection_validation.py`、诊断 `q3_solver.py` 已消费 v2，输出带 Q1 SHA。旧 cyj v4/v6 与旧 Q3 数值保留历史身份，未假称新版。
- `paper/latex/sections/chm/q1.tex` 的第三小问改为交互主模型、连续凸包界和明确下游版本；按用户要求暂缓 PDF。

## 验证与边界

Q1 32 项、Q3 38 项单测通过；原始 2014 文件与安全阅读门禁通过。A4 凸包优化给出浮点数值最优性界，并非严格区间算术证明。13 目标权重由情景显式给出，11 个质量域仍未知。A/B 配比 Loss 与 Q_A/Q_B 未成对标定，当前 `ready_for_Q3_empirical_absolute_loss=false`。CYJ 需在本人分支明确消费 v2 manifest SHA、重新发布 Q2/Q3 接口和其论文结果；CHM 再验收并更新下游正式配置。zhh/集成人读取本交接及接口，不直接复用旧 Q3 数值。
