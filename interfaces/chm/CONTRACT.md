# chm → cyj 当前 Q1 v2.0 主模型合同

2026-09-25 用户明确授权将交互模型升为主模型。默认入口为 `src/chm/q1_interface.py::Q1Interface`，冻结清单是 `interfaces/chm/q1_interface_v2.json`。原 v1.3 Ridge 改为历史比较基线，读取器在 `src/chm/q1_interface_v1_3.py`；旧接口与结果保持可复现。

Q1 v2.0 对每个目标使用 17 个配比主项和 10 个按 A4 方差选定的二元乘积项，返回参考配方中心化的 1M Loss 对比。相对效应除以交互模型自身的正参考 Loss。新接口提供 `predict(p)`、`relative_effect(p,target)`、`effect_vector(p)`、`gradient(p)` 与 `support(p)`。默认拒绝凸包外推；若用于压力测试，须显式设置 `allow_extrapolation=True`。交互模型没有固定的 13×17 作用矩阵，`interaction_matrix()` 明确报错。

质量主评分采用 A1 sample；A2/A3 extended 只做敏感性；11 个 inferred 域保持 null。模型、原始归一化配方、质量映射和验证结果均由 v2 manifest 固定 SHA256。

默认配方决策 `src/chm/q1_multiloss_decision.py::solve` 使用 `q1_hull_bounds_v2.py` 在 A4 凸包内求解。十个双线性项采用 McCormick 线性松弛与空间分支定界；返回可行配方、目标上下界和数值间隙。等权主场景的加权、direct、direct+near 及 minimax 均已达到相对目标值 0.001 内的数值上下界；结果在 `outputs/chm/q1_v2_hull_bounds/bounds.json`。有限候选备用入口 `choose_observed` 在 512 个已观测 A4 配方中精确枚举，结果在 `outputs/chm/q1_v2_decisions/`。两类结果的支持集与最优性证据必须分别标明，不能沿用旧线性规划的顶点最优论证。

Q2 的 v2 条件复算在 `outputs/chm/q2_interaction_scenarios_v2/`，固定 cyj `86526a1` 的 B7 参数。这是 chm 侧复核，cyj 需在其本人分支明确锁定新 Q1 哈希并重新发布。Q3 的 A 侧配方诊断已改用 v2。旧 cyj v4/v6 和 Q3 数值按原消费版本保留；它们不能自动改称为 v2 下游结果。A/B Loss 桥接及质量共同坐标仍无成对标定，经验绝对 Loss 的 `ready_for_Q3` 为 false。

## 以下为 v1.3 历史合同
# chm → cyj Q1 生产者接口 v2.0

日期：2026-09-24  
当前推荐机器版本：`chm.q1.v1.3`
生产者：chm  
消费者：cyj（Q2/Q3）、zhh（需要 Q1 证据时）  
维护分支：`integration/chm-q1-clean-20260923`

状态：**A1--A3 全量实体数据已按 22 信号、全局 Spearman 符号重跑并更新 canonical `domain_quality.csv`；配比相对效应与排序验证继续可消费。Q1 不提供由附件 A 拟合的连续跨规模幅度参数。**

> 版本提示：v1.2 的质量数值为旧口径，已由 v1.3 替代。消费者须显式记录新接口 SHA，并重新检查依赖 $Q_A$ 的结论；配比 Ridge/排序证据未因本轮质量修订而改变。

当前机器入口：`interfaces/chm/q1_interface_v1_3.json`。旧版本保留审计，新消费默认使用 v1.3。

## 1. Q1 正式科学边界

附件 A 的 A4--A15 配比/Loss 表没有与每个配方实验对应的训练数据量 \(D\) 字段；真实模型规模只有 1M、60M、1B 三个离散位置，且 1B 的配方支持集与 1M/60M 不同。因此旧的
\[
L_k(N,\mathbf p)=a_k(N)+b_k(N)s_k(\mathbf p),
\qquad
\log b_k(N)=c_k-\eta\log(N/10^6)
\]
只保留历史诊断，不再属于 Q1 主模型或接口。

Q1 正式交付：
- A1--A3 的七域综合质量代理 \(Q_A\)，其含义是描述性 composite proxy，不是 B6--B8 的原生 `Q_score`；
- A16 的 3 direct、3 near-direct、11 inferred 域映射；
- A4+A5 的 13-target 1M Ridge；
- 参考配方 \(\mathbf p_{\rm ref}\)；
- 13 维相对效应
  \[
  \mathbf m(\mathbf p)
  =
  \mathbf B(\mathbf p-\mathbf p_{\rm ref}),
  \qquad
  \mathbf B\in\mathbb R^{13\times17};
  \]
- A6--A11 的 held-out 排序验证；
- A12--A15 的 estimated/extrapolated 压力测试。

## 2. 配比效应解释

归一化后 \(\mathbf1^\top\mathbf p=1\)。零和系数
\[
\mathbf1^\top\hat{\boldsymbol\beta}_k=0
\]
只是组成数据的规范表示。若从训练域 \(r\) 向训练域 \(j\) 转移比例 \(\delta\)，则
\[
\Delta m_k
=
\delta(\hat\beta_{k,j}-\hat\beta_{k,r}).
\]
消费者不得把单个 \(\hat\beta_{k,j}\) 解释成独立因果效应。

## 3. 多维 Loss 决策层

13 个 target Loss 不在生产者层强行压成唯一总体 Loss。可用决策口径包括：
- 已知验证域权重：\(\sum_k s_km_k(\mathbf p)\)；
- 无偏好时的等权情景：\(s_k=1/13\)，仅表示能力等权，不等于官方总体 Loss；
- minimax：\(\min_{\mathbf p}\max_k m_k(\mathbf p)\)；
- 重点能力 + 保护约束；
- Pareto 多目标分析。

配比决策支持域建议限制在
\[
\mathcal P_A=\operatorname{conv}\{\mathbf p_1,\ldots,\mathbf p_{512}\},
\]
避免未观测单纯形顶点外推。

## 4. Q1 → Q2 禁止项

当前附件没有成对证据支持
\[
Q_A=Q_{\rm score},\qquad
L_{k,\rm Q1}=L_{\rm B1},
\]
也不支持由 Q1 给出
\[
m_k(\mathbf p;N)
=
m_k(\mathbf p)(N/10^6)^{-\eta}.
\]
因此禁止把 \(Q_A\) 直接输入 B-native Q 模型、禁止默认某个 Q1 target 等于 B1 `val_loss`、禁止把旧 \(\eta\) 作为 Q2/Q3 正式参数。

## 5. v1.2 机器接口

`src/chm/q1_interface.py` 提供：
- `quality(domain)`；
- `mapped_quality(mixture_domain)`；
- `relative_effect(mixture,target)`，返回单个 target 的 1M contrast；
- `effect_vector(mixture)`，一次返回 13 维配比效应向量；
- `interaction_matrix()`，返回 $13\\times17$ 零和 Ridge 作用矩阵；
- `ranking_validation(target)`。

manifest 状态：
```text
quality_coordinate = A_composite_quality_proxy_z
mixture_effect_coordinate = A4_A5_1M_target_cross_entropy_contrast
scale_transfer_status = not_identified_from_attachment_A
```

## 6. Q3 正式结果发布接口

Q3 的正式交付协议仍单列于 [Q3_RESULTS_CONTRACT.md](Q3_RESULTS_CONTRACT.md)。只有 readiness gate 通过并由发布器验证成功的结果，才允许标记 `formal_validated`。Q1 v1.2 的科学修订不删除或覆盖 clean 分支既有的 Q3 诊断、预算扫描、质量成本和发布协议成果。
