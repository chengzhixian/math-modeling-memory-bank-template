# chm Q1 v2.0 定型主模型合同

Q1 自身题面答案已定型，权威结论见 outputs/chm/Q1_FINAL_ANSWER_V2.md。定型范围为附件 A 的工程质量代理、冲突处理、冻结交互配比代理、条件性配方决策及验证和压力测试；不扩大接口的跨规模或跨附件数值有效范围。

2026-09-25 用户明确授权将交互模型升为主模型。默认入口为 `src/chm/q1_interface.py::Q1Interface`，冻结清单是 `interfaces/chm/q1_interface_v2.json`。原 v1.3 Ridge 改为历史比较基线，读取器在 `src/chm/q1_interface_v1_3.py`；旧接口与结果保持可复现。

Q1 v2.0 对每个目标使用 17 个配比主项和 10 个按 A4 方差选定的二元乘积项，返回参考配方中心化的 1M Loss 对比。相对效应除以交互模型自身的正参考 Loss。新接口提供 `predict(p)`、`relative_effect(p,target)`、`effect_vector(p)`、`gradient(p)` 与 `support(p)`。默认拒绝凸包外推；若用于压力测试，须显式设置 `allow_extrapolation=True`。交互模型没有固定的 13×17 作用矩阵，`interaction_matrix()` 明确报错。

质量主评分采用 A1 sample；A2/A3 extended 只做敏感性；11 个 inferred 域保持 null。模型、原始归一化配方、质量映射和验证结果均由 v2 manifest 固定 SHA256。

默认配方决策 `src/chm/q1_multiloss_decision.py::solve` 使用 `q1_hull_bounds_v2.py` 在 A4 凸包内求解。十个双线性项采用 McCormick 线性松弛与空间分支定界；返回可行配方、目标上下界和数值间隙。等权主场景的加权、direct、direct+near 及 minimax 均已达到相对目标值 0.001 内的数值上下界；结果在 `outputs/chm/q1_v2_hull_bounds/bounds.json`。有限候选备用入口 `choose_observed` 在 512 个已观测 A4 配方中精确枚举，结果在 `outputs/chm/q1_v2_decisions/`。两类结果的支持集与最优性证据必须分别标明，不能沿用旧线性规划的顶点最优论证。

Q2 的 v2 条件复算在 `outputs/chm/q2_interaction_scenarios_v2/`，固定 cyj `86526a1` 的 B7 参数。这是 chm 侧复核，cyj 需在其本人分支明确锁定新 Q1 哈希并重新发布。Q3 的 A 侧配方诊断已改用 v2。旧 cyj v4/v6 和 Q3 数值按原消费版本保留；它们不能自动改称为 v2 下游结果。A/B Loss 桥接及质量共同坐标仍无成对标定，经验绝对 Loss 的 `ready_for_Q3` 为 false。

证据口径：A4+A5 嵌套外层五折比较中，交互模型 13/13 个目标 RMSE 低于 Ridge。A6--A11 的 1M、60M、1B 对比为 11/13、13/13、13/13；这些组曾参与模型形式选择，故不是最终未触碰盲测。1B 有 47/64 个配方在 A4 凸包外，且交互模型在 1B 的绝对 Loss RMSE 仅 11/13 个目标优于训练均值常数基线。质量案例无人工真值，不报告分类准确率。

独立数值复核见 outputs/chm/q1_v2_signoff/audit.json：四份配方的总量、非负性、凸包重构、质量约束和上界目标值均通过；数值间隙依次为 0.0009621、0.0004410、0.0007504、0.0009956。这些是浮点 LP/McCormick 数值界，不是严格数学证明。质量判断依赖已声明的工程评分和映射假设。

历史合同与线性 Ridge 复现入口见 [v1.3 归档](archive/CONTRACT_v1_3.md)。

A12--A15 的 v2 压力测试见 outputs/chm/q1_v2_estimated_stress/：两组各 63 个 A4 已见配方，Loss 为 10B/70B 外推估算值。v2 的逐目标 Spearman 中位数分别为 0.4915、0.3941，略低于 Ridge 的 0.5136、0.4148；不能称为大模型实测验证，也不能推断跨规模排序可靠。30 次 80% 训练行重拟合诊断见 outputs/chm/q1_v2_refit_stability/；其中质量约束及 minimax 的已观测候选选择较敏感。该诊断只覆盖 512 个有限候选，不是连续凸包最优解的置信区间。以上新证据不修改冻结 v2 系数或主接口哈希。
