# chm → cyj Q1 生产者接口 v2.0

日期：2026-09-24  
当前推荐机器版本：\`chm.q1.v1.3\`
生产者：chm  
消费者：cyj（Q2/Q3）、zhh（需要 Q1 证据时）  
维护分支：\`integration/chm-q1-clean-20260923\`

状态：**A1--A3 全量实体数据已按 22 信号、全局 Spearman 符号重跑并更新 canonical `domain_quality.csv`；配比相对效应与排序验证继续可消费。Q1 不提供由附件 A 拟合的连续跨规模幅度参数。**

> 版本提示：v1.2 的质量数值为旧口径，已由 v1.3 替代。消费者须显式记录新接口 SHA，并重新检查依赖 $Q_A$ 的结论；配比 Ridge/排序证据未因本轮质量修订而改变。

当前机器入口：\`interfaces/chm/q1_interface_v1_3.json\`。旧版本保留审计，新消费默认使用 v1.3。

## 1. Q1 正式科学边界

附件 A 的 A4--A15 配比/Loss 表没有与每个配方实验对应的训练数据量 \(D\) 字段；真实模型规模只有 1M、60M、1B 三个离散位置，且 1B 的配方支持集与 1M/60M 不同。因此旧的
\[
L_k(N,\mathbf p)=a_k(N)+b_k(N)s_k(\mathbf p),
\qquad
\log b_k(N)=c_k-\eta\log(N/10^6)
\]
只保留历史诊断，不再属于 Q1 主模型或接口。

Q1 正式交付：
- A1--A3 的七域综合质量代理 \(Q_A\)，其含义是描述性 composite proxy，不是 B6--B8 的原生 \`Q_score\`；
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
因此禁止把 \(Q_A\) 直接输入 B-native Q 模型、禁止默认某个 Q1 target 等于 B1 \`val_loss\`、禁止把旧 \(\eta\) 作为 Q2/Q3 正式参数。

## 5. v1.2 机器接口

\`src/chm/q1_interface.py\` 提供：
- \`quality(domain)\`；
- \`mapped_quality(mixture_domain)\`；
- \`relative_effect(mixture,target)\`，返回单个 target 的 1M contrast；
- \`effect_vector(mixture)\`，一次返回 13 维配比效应向量；
- \`interaction_matrix()\`，返回 $13\\times17$ 零和 Ridge 作用矩阵；
- \`ranking_validation(target)\`。

manifest 状态：
\`\`\`text
quality_coordinate = A_composite_quality_proxy_z
mixture_effect_coordinate = A4_A5_1M_target_cross_entropy_contrast
scale_transfer_status = not_identified_from_attachment_A
\`\`\`

## 6. Q3 正式结果发布接口

Q3 的正式交付协议仍单列于 [Q3_RESULTS_CONTRACT.md](Q3_RESULTS_CONTRACT.md)。只有 readiness gate 通过并由发布器验证成功的结果，才允许标记 \`formal_validated\`。Q1 v1.2 的科学修订不删除或覆盖 clean 分支既有的 Q3 诊断、预算扫描、质量成本和发布协议成果。
