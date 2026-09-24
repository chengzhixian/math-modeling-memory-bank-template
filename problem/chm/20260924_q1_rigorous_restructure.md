# Q1 严谨重构说明：从“跨尺度拟合”退回附件 A 可识别结论

日期：2026-09-24  
角色：chm  
状态：已按用户要求重构论文主模型与生产者接口；本文件记录数学依据和删改理由。  
数据依据：当前清理后的可见数据说明、A1–A16 原始附件、`outputs/chm/local_recheck_v1/`、`outputs/chm/ablation_v1/`。  
禁用依据：历史隐藏页边文字及其衍生模型、参数和结论。

## 1. 重构原则

本轮不是为了“换一个更复杂的模型”，而是把第一问限制在附件 A 真正能够识别的量上。判断标准如下：

1. 公式中的每个自变量必须在对应附件中有观测或有明确的、可追溯的定义；
2. 训练、验证、外推数据的角色不能在同一结论中混用；
3. 组成数据的系数只能解释为相对重新分配；
4. 无真实质量标签时，质量标量只能称为代理指数，权重必须明确是定义/假设而非“由数据证明”；
5. A12–A15 的 estimated/extrapolated 标签必须保留；
6. 第一问不越界替代第二问的 (N,D,Q,p) 广义标度律。

## 2. 附件 A 能识别什么，不能识别什么

### 2.1 可识别

A4/A5 给出同一 512 个 `index` 下的：

[
mathbf p_iinDelta^{16},qquad
mathbf L_i=(L_{i1},ldots,L_{i,13}).
]

因此可以估计 1M 实验中的

[
mathbf plongmapsto L_k
]

关系。

A6/A7、A8/A9、A10/A11 给出三个真实检验组，因此可以检验 A4/A5 冻结代理在这些实验组上的预测排序。

A6 与 A8 的 256 个配方完全相同，因此可以直接比较同配方的 1M/60M Loss 排序，而不需要任何额外模型。

### 2.2 不可识别

A4–A15 的配比表没有 (D)，Loss 表也没有 (D)。模型规模只通过文件组名称区分。于是附件 A 不足以估计

[
L(N,D,mathbf p)
]

中的 (D) 作用，也不足以把三个离散实验组的差异唯一归因于 (N)。

原方案进一步拟合

[
L_k(N,mathbf p)
=
a_k(N)+b_k(N)s_k(mathbf p)+arepsilon
]

和

[
log b_k(N)
=
c_k-etalog(N/10^6)+arepsilon
]

虽然数值上可计算，但统计识别不成立：

- (N) 轴只有 1M、60M、1B 三个位置；
- 13 个目标域只是重复观测不同 target，并没有增加新的 (N) 位置；
- 1B 的 64 个配方与 1M/60M 的支持集不同；
- A6–A11 一旦用于估计 (a,b,eta)，便不再是该尺度模型的外部验证集；
- 附件 A 没有与这些实验对应的 (D)，无法排除训练数据量/训练流程的混杂。

因此 `eta=0.14503317` 从 Q1 主模型、论文结论和生产者接口中撤出。历史脚本和结果保留作审计，不再向 Q2/Q3 提供默认尺度参数。

## 3. 质量模型的严格定位

### 3.1 为什么不能称“真实质量”

A1–A3 只有 22 个质量信号，没有样本级真实质量标签 (Q^{m true})。所以不存在可由附件唯一识别的函数

[
Q^{m true}=f(x_1,ldots,x_{22}).
]

任何单标量都必须带聚合假设。论文因此统一改称：

[
Q_A=	ext{A-side composite quality proxy}.
]

### 3.2 列表字段压缩

压缩规则来自已独立核验的 Meta-rater 数据卡字段语义：

- 二分类 logits：softmax 后取目标正类概率；
- 0–5 六等级 logits：取 softmax 期望等级；
- qurater 四维：均值；
- fineweb_edu：唯一元素。

argmax 只做敏感性，不冒充数据卡唯一规定。

### 3.3 稳健标准化

对经过单调变换后的指标：

[
z_{ij}
=
operatorname{clip}
left(
rac{x_{ij}-operatorname{median}(x_j)}
{1.4826operatorname{MAD}(x_j)},
-5,5
ight).
]

这是为解决不同量纲和长尾/极端值问题；A2/A3 复用 A1 参数，防止重新定义尺度。

### 3.4 方向对齐

8 个 model-based 指标由字段语义直接确定正向，构造锚点

[
A_i=operatorname{mean}_{jinmathcal M_i}z_{ij}.
]

其余指标只做“相对于锚点的方向对齐”，在每个域内计算 Spearman，再用 Fisher-z 汇总：

[
ar z_j=
rac{sum_d(n_{jd}-3)operatorname{arctanh}ho_{jd}}
{sum_d(n_{jd}-3)},qquad
d_j=operatorname{sgn}(	anhar z_j).
]

这一步不被表述为发现了客观“好坏方向”，而是为了让复合指标在同一语义参考下可加和。

### 3.5 家族等权是定义，不是假装“推导”

定义三个家族分数 (G_{ig})，再令

[
S_i=rac13(G_{i,m RPS}+G_{i,m DSIR}+G_{i,m MODEL}),
]

最后标准化为

[
Q_{A,i}=rac{S_i-mu_{S,A1}}{sigma_{S,A1}}.
]

这里的 (1/3) 是“避免指标数量决定家族权重”的显式建模约定，不是附件中的事实。为了防止把它写得过强，必须同时报告：

- 22 指标完全等权；
- 列表 argmax；
- 家族删除；
- 方向过滤/LOO 稳定性。

现有结果表明前两者七域 Spearman=0.9643，但去掉 RPS 后降为 0.8214，说明家族选择不确定性不可忽略。

## 4. 冲突分析为什么改成直接 Spearman

原稿定义了

[
H_j
]

和

[
C_{jk,d}=max(0,-ho_{jk,d}).
]

这些是人为汇总统计，不是题目必须要求。为减少不必要的自定义量，正式论文只保留标准 Spearman：

[
ho_{jr,d}
=
ho_S(z^+_j,z^+_rmid d).
]

负值只解释为“方向统一后两个指标在该域的样本排序相反”。在没有 bootstrap CI 和多重比较校正前，不写“显著冲突”。

## 5. 配比模型的严格推导

### 5.1 为什么是逐目标域而不是 13 域平均

A5 的 13 列是不同目标验证域 Loss，量级和变异程度不同。若先算

[
ar L_i=rac1{13}sum_kL_{ik},
]

相当于未经标准化地假设 13 个目标域具有相同尺度和相同效用权重；附件并没有提供这种权重依据。因此主模型必须保留 13 个目标域。

### 5.2 单纯形约束

归一化后：

[
mathbf 1^	opmathbf p_i=1.
]

定义

[
mathbf p_{m ref}=rac1{512}sum_imathbf p_i,
qquad
mathbf q_i=mathbf p_i-mathbf p_{m ref},
]

则

[
mathbf 1^	opmathbf q_i=0.
]

因此设计空间实际只有 16 个自由方向。

### 5.3 Ridge 目标函数

对目标域 (k)：

[
(hatalpha_k,hat{oldsymboleta}_k)
=
argmin_{alpha,eta}
sum_i
left[
L_{ik}-alpha-eta^	opmathbf q_i
ight]^2
+
lambda_k|eta|_2^2,
quad
mathbf 1^	opeta=0.
]

Ridge 是 RegMix 已验证使用的线性代理路线；(lambda_k) 仅在 A4+A5 做 5-fold CV。A6–A15 不进入模型选择。

### 5.4 零和系数为什么成立

对于任意常数 (c)：

[
(eta+cmathbf1)^	opmathbf q
=
eta^	opmathbf q
+c,mathbf1^	opmathbf q
=
eta^	opmathbf q.
]

因此 (eta) 沿 (mathbf1) 方向不可识别。零和约束

[
mathbf1^	opeta=0
]

只是选择一个规范代表，不增加预测假设。当前代码在原始单纯形上拟合 Ridge 后，将系数平移为零和形式；预测不变。

### 5.5 中心化效应

[
m_k(mathbf p)
=
hat{oldsymboleta}_k^	op
(mathbf p-mathbf p_{m ref})
=
widehat L_{k,1M}(mathbf p)
-
widehat L_{k,1M}(mathbf p_{m ref}).
]

这一定义是从同一个 1M Ridge 直接相减得到的，不需要任何新参数。

如果把 (delta) 从域 (r) 转移到域 (j)：

[
mathbf p'
=
mathbf p+deltamathbf e_j-deltamathbf e_r,
]

则

[
m_k(mathbf p')-m_k(mathbf p)
=
delta(hateta_{k,j}-hateta_{k,r}).
]

所以“域 (j) 系数为负/正”本身不是独立因果解释；只有相对另一个域的重新分配差异有明确线性含义。

## 6. 跨实验组验证只用排序，不再拟合幅度

冻结 A4+A5 后，对每个真实检验组：

[
ho_{k,ell}^{m pred}
=
ho_S
left(
widehat L_{k,1M}(mathbf p_i^{(ell)}),
L_{ik}^{(ell)}
ight).
]

现有 13 域中位数：

- 1M：0.8381；
- 60M：0.8381；
- 1B：0.7067。

A6/A8 是同一 256 配方，直接真实 Loss 排序中位 Spearman=0.9944。这个直接比较不需要任何代理。

A10 的 64 个 1B 配方与 A4/A6 无完全重复，因此 1B 的代理结果是“新配方集合上的排序检验”，但不是“纯 N 效应”。

## 7. 绝对尺度诊断

冻结 1M 代理直接预测其他实验组时：

| 实验组 | Ridge RMSE 中位数 | 常数 RMSE 中位数 | Ridge 改善目标数 |
|---|---:|---:|---:|
| 1M | 0.4478 | 0.6759 | 13/13 |
| 60M | 1.4450 | 1.4724 | 13/13 |
| 1B | 3.2079 | 3.2514 | 4/13 |

因此正文结论改成：

> 配比代理主要支持排序迁移，不能支持附件 A 内的绝对 Loss 连续尺度外推。

## 8. A12–A15

10B/70B 的 63 个配方相同，且均属于 A4 train 子集。两组 estimated Loss 的直接排名中位 Spearman=0.9907，但 1M Ridge 对 10B/70B 的 13 域 Spearman 中位数只有 0.5136/0.4148。

因此它们仅用于压力测试，不能称真实大模型验证。

## 9. 正式 Q1→Q2 接口变更

旧接口 `chm.q1.v1.1` 暴露了默认的 `eta` 尺度情景。重构后发布 `chm.q1.v1.2`：

- 保留：7 域 (Q_A)、17 域映射、13 target Ridge、(mathbf p_{m ref})、held-out validation；
- 保留：(m_k(mathbf p))，但只标记为 A4/A5 1M target-loss contrast；
- 删除：`scale` 文件作为生产者接口依赖；
- 删除：`relative_effect(..., n_params, eta)` 的自动尺度缩放；
- 明确：A→B Loss bridge、任何 (N,D) 依赖的配比系数均由 Q2 另外识别；没有证据时只能做情景敏感性。

历史 `mixture_scale_transfer_v0*` 文件不删除，以保留审计，但其结果不得再作为 Q1 主模型或默认下游参数。

## 10. 对团队公共规则的影响

当前公共 `TEAM_COLLABORATION_DEPENDENCIES.md` 仍写有“chm 必须交付 p 效应的跨规模传递”。该要求与本轮重新确认的附件可识别性冲突。按照协作规则，chm 不直接修改公共文件；本轮 handoff 将请求集成人把公共规则更新为：

> chm 交付 1M target-specific (m_k(p)) + A6–A11 排序迁移证据；任何跨规模幅度/跨 Loss 坐标桥接由 cyj 在 Q2 侧识别或显式标为 sensitivity-only。

## 11. 论文主线的最终结构

[
oxed{
	ext{A1--A3}
ightarrow
Q_A	ext{ 质量代理+冲突复核}
}
]

[
oxed{
	ext{A4+A5}
ightarrow
widehat L_{k,1M}(mathbf p)
ightarrow
m_k(mathbf p)
}
]

[
oxed{
	ext{A6--A11}
ightarrow
	ext{排序验证，不拟合尺度参数}
}
]

[
oxed{
	ext{A12--A15}
ightarrow
	ext{estimated/extrapolated 压力测试}
}
]

再由问题二利用附件 B 建立真正的

[
L(N,D,Q,mathbf p).
]

这条链路不需要为附件 A 没有提供的 (D) 或跨 Loss 坐标关系补造参数。