# Q3 通用求解器、KKT 与 readiness v2 软件验证

日期：2026-09-24  
状态：software validation only；synthetic 模型数值禁止作为赛题结果。

## 通用求解器

新增 `q3_generic_solver.py`，把性能模型抽象为 `value_grad(N_B,D_B,Q)`。未来 cyj 只要交付同一 B-native Loss 坐标上的 validated N-D-Q predictor，即可替换 synthetic callback，不改成本和 KKT 框架。

变量变换：N/D 使用对数坐标，Q 使用映射到 [Q0,1] 的 logistic 坐标；SLSQP 多起点求解，输出预算残差、活跃约束和一侧 KKT。

定义边际收益/成本比

[
r_x=-rac{L_x}{C_x}.
]

预算约束活跃且变量为内点时应有 (r_N=r_D=r_Q=mu)。若变量在下界，要求 (r_xlemu)；在上界要求 (r_xgemu)。Q=Q0 使用质量成本右导数。若预算不活跃，互补松弛给出 (mu=0)。

## 软件验证

- generic solver 单元测试 4/4 PASS；
- readiness policy 单元测试 4/4 PASS；
- synthetic quality benefit 下扫描 3 种成本函数 × 5 个预算，共 15 个 KKT 点，15/15 通过；
- 自由变量边际比最大相对离散约 3.83e-7。

这些只证明数值实现与一阶条件一致，不证明 synthetic quality benefit 正确。

## readiness v2

旧 gate 把 A-native Q_z ↔ B-native Q_score 未识别当绝对 blocker，这会错误激励人为造 mapping。v2 改为：

### 质量性能

正式 Q3 必须有：
- coordinate = B_native_Q_score；
- performance_status = validated；
- joint_NDQ_status = validated；
- 明确 loss_coordinate_id。

A_Q_mapping_status 可以继续是 unidentified；此时 Q1 的 Q_z 只作 A 侧描述，Q3 使用 B-native Q_score。

单独的 B7 Q 模型仍不够：N/D/Q 必须最终落到同一 B-native Loss 坐标，或由生产者给出验证过的桥接。

### 配比 p

允许两种正式政策：

1. validated_bridge：有 primary anchor 且 lambda validated，可发布 full_NDQP；
2. sensitivity_only：至少三个 target，明确 unique_p_claim_allowed=false，可发布 NDQ 主优化 + p 多 target 敏感性，但不得声称唯一 p。

当前 cyj.q3.v1 两者都尚未满足，因此 formal_ready 仍 false。
