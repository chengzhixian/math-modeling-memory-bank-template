# 问题一章节草稿：数据质量评价与训练数据配比效应（严谨重构版）

> 状态：2026-09-24 重构。仅依据当前清理后的可见题面、附件 A 的真实字段/结果及已独立核验的方法资料。原“用 1M/60M/1B 三个离散实验组拟合连续配比尺度衰减 `eta`”不再进入第一问主模型；历史计算仅保留审计，不作为正式接口。

## 1. 问题分析与可识别性边界

问题一由两个统计结构不同的子任务组成：A1–A3 提供 22 维质量信号，用于七个语料域的质量评价与指标冲突分析；A4–A15 提供 17 维训练配比和 13 个目标验证域 Loss，用于分析训练配方与目标域 Loss 的关系。质量域与配方域不一一对应，因此两条线分别建模，再通过 A16 的 mapping type 和显式接口连接，不能人为制造 7 域与 17 域之间的精确数值真值。

A4+A5 是 512 组 1M 配方及对应 Loss；A6+A7、A8+A9、A10+A11 分别是 1M、60M、1B 检验组；A12–A15 被数据说明标记为 estimated/extrapolated。配比表只含 17 个比例，Loss 表只含 13 个目标域 Loss；这些配方实验没有对应的 `D_tokens` 字段。模型规模 1M、60M、1B 只是不同实验文件组的标签。

因此第一问可以回答“1M 配比代理在题目给定的其他实验组上是否保持排序信息”，但不能仅凭附件 A 识别连续的 (N-D) 标度律，也不能把三个离散实验组拟合为普适的 (N) 衰减函数。A6–A11 在本问中只承担冻结模型后的 held-out 验证，不再拟合任何 `b_k(N)` 或公共 `eta`。

## 2. A 侧综合质量代理

### 2.1 列表字段压缩

A1–A3 的 22 个质量信号中有 8 个列表字段。根据 SlimPajama-Meta-rater 数据卡中已核验的字段语义：

- `fineweb_edu`：取唯一元素；
- `ad_en`、`fluency_en`：对二分类 logits 做 softmax，取 `no_ad` / `fluent` 的概率；
- 四个 `modernbert_*`：对 0–5 六级 logits 做 softmax 后取期望等级；
- `qurater`：四个维度取均值。

argmax 只作为敏感性方案，不与主方案混用。

### 2.2 稳健标准化

计数型指标先作 (log(1+x))，DSIR 三项作 signed-log。只在 A1 上冻结中心和尺度：

[
z_{ij}
=
operatorname{clip}
left[
rac{x_{ij}-operatorname{median}(x_j)}
{1.4826operatorname{MAD}(x_j)},
-5,5
ight].
]

A2/A3 复用 A1 的全部处理参数。

### 2.3 指标方向

八个 model-based 指标的正向语义由数据卡直接给出，定义锚点

[
A_i=rac{1}{|mathcal M_i|}sum_{jinmathcal M_i}z_{ij}.
]

其余 14 个统计指标不根据字段名主观指定方向，而在 A1 的各质量域内计算

[
ho_{jd}=ho_S(z_{ij},A_imid iin d),
]

再以 Fisher 变换按 (n_{jd}-3) 汇总：

[
ar z_j=
rac{sum_d(n_{jd}-3)operatorname{arctanh}(ho_{jd})}
{sum_d(n_{jd}-3)},
qquad
arho_j=	anh(ar z_j).
]

方向取 (d_j=operatorname{sgn}(arho_j))，并令 (z^+_{ij}=d_jz_{ij})。

这里必须明确：这是“相对于语义锚点的方向对齐”，不是从附件中发现了客观质量真值。域间符号一致率和 leave-one-domain-out 稳定性只用于检查方向是否依赖具体领域。

### 2.4 综合质量代理的定义

附件没有样本级真实质量标签，因此任何单一质量标量都不可能由数据唯一识别。主方案采用透明的“家族内等权、家族间等权”定义，而不是把权重写成已被数据证明：

[
G_{ig}
=
rac{1}{|mathcal J_{ig}|}sum_{jinmathcal J_{ig}}z^+_{ij},
qquad
S_i
=
rac13
sum_{gin{mathrm{RPS},mathrm{DSIR},mathrm{MODEL}}}G_{ig}.
]

再用 A1 全体记录标准化：

[
Q_{A,i}
=
rac{S_i-mu_{S,A1}}{sigma_{S,A1}}.
]

因此 (Q_A) 是 **A 侧综合质量代理**，不是“真实质量”也不是 B6–B8 的 `Q_score`。

A1 七域中位数保持当前已复跑结果：

| 质量域 | n | (Q_A) 中位数 | 条件 95% CI |
|---|---:|---:|---:|
| arxiv | 1419 | 2.6826 | [2.6518, 2.7084] |
| book | 171 | 2.7711 | [2.6735, 2.8086] |
| c4 | 10000 | -0.2173 | [-0.2376, -0.1997] |
| commoncrawl | 9640 | 0.5061 | [0.4923, 0.5224] |
| github | 10000 | -0.5171 | [-0.5438, -0.4886] |
| stackexchange | 10000 | 0.1874 | [0.1723, 0.2025] |
| wikipedia | 10000 | -0.3759 | [-0.4003, -0.3473] |

主方案与 argmax、22 指标完全等权方案的七域排名 Spearman 都为 0.9643；删除 RPS 家族后降至 0.8214，且 4/7 域名次变化。因此 bootstrap 窄区间只反映固定评分规则下的记录抽样误差，不能被解释为评分规则本身高度确定。

### 2.5 指标冲突

不再额外定义人为的 (H_j) 或 (C_{jk,d}=max(0,-ho)) 作为主论文公式。方向统一后直接计算标准 Spearman：

[
ho_{jr,d}
=
ho_S(z^+_{ij},z^+_{ir}mid iin d).
]

若 (ho_{jr,d}<0)，只表示两个指标在该域对记录排序方向相反。当前没有完成全部相关系数区间和多重比较校正，因此只报告“描述性负相关”，不写“显著冲突”。

A1 中 arxiv 1419 条和 github 10000 条均包含在对应扩展集，因此 A2/A3 不是独立验证。去除重叠后，新增记录分别为 16104 / 193752 条；冻结 A1 处理口径后，(Q_A) 中位数为 2.7146 / -0.5363，与 A1 的 2.6826 / -0.5171 接近。

## 3. 17 域配比与 13 个目标域 Loss

### 3.1 配比是组成数据

每一行配比先按行归一化：

[
mathbf p_i=(p_{i1},ldots,p_{i,17})^	op,
qquad
p_{ij}ge0,
qquad
mathbf 1^	opmathbf p_i=1.
]

定义 A4 归一化配方均值

[
mathbf p_{m ref}
=
rac1{512}sum_{i=1}^{512}mathbf p_i.
]

于是 (mathbf q_i=mathbf p_i-mathbf p_{m ref}) 满足 (mathbf 1^	opmathbf q_i=0)。

### 3.2 逐目标域零和 Ridge

13 个验证域的 Loss 水平和波动尺度不同，不能先对原始 Loss 做算术平均。因此对每个目标域 (k) 独立建立：

[
(hatalpha_k,hat{oldsymboleta}_k)
=
argmin_{alpha,oldsymboleta}
left{
sum_{i=1}^{512}
left[
L_{ik}
-
alpha
-
oldsymboleta^	op(mathbf p_i-mathbf p_{m ref})
ight]^2
+
lambda_k|oldsymboleta|_2^2
ight},
]

并施加

[
mathbf 1^	opoldsymboleta=0.
]

这个零和约束不是额外的经验猜测。因为 (mathbf 1^	op(mathbf p-mathbf p_{m ref})=0)，所以给所有系数同时加常数不会改变预测；只有系数对比可识别。零和形式只是在等价表示中选择唯一的规范化表示。当前代码在精确归一化单纯形上拟合 Ridge，再把系数平移成零和形式，预测不变。

(lambda_k) 只在 A4+A5 内做 5 折交叉验证；A6–A15 不参与调参。

冻结的 1M 代理为

[
widehat L_{k,1M}(mathbf p)
=
hatalpha_k
+
hat{oldsymboleta}_k^	op
(mathbf p-mathbf p_{m ref}).
]

定义相对参考配方效应

[
m_k(mathbf p)
=
widehat L_{k,1M}(mathbf p)
-
widehat L_{k,1M}(mathbf p_{m ref})
=
hat{oldsymboleta}_k^	op
(mathbf p-mathbf p_{m ref}).
]

因此 (m_k) 的单位只属于 **A4+A5 的 1M 目标域交叉熵坐标**。它不能直接解释为 60M/1B 的绝对 Loss 修正，更不能直接加到 B1 `val_loss`。

组成数据下单个 (eta_j) 也没有“独立提高该域比例”的意义。如果把 (delta) 的比例从域 (r) 转移到域 (j)，则

[
m_k(mathbf p+deltamathbf e_j-deltamathbf e_r)-m_k(mathbf p)
=
delta(hateta_{k,j}-hateta_{k,r}).
]

因此真正可解释的是两域重新分配时的系数差。

## 4. 13 维 Loss 向量、作用矩阵与多目标决策

补充文献复核后，第一问的 13 个 target Loss 不再只被视为“13 个并列回归结果”，而是统一写成一个向量模型：

\[
\widehat{\mathbf L}_{1M}(\mathbf p)
=
\widehat{\boldsymbol\alpha}
+
\mathbf B(\mathbf p-\mathbf p_{\rm ref}),
\qquad
\mathbf B=[\hat\beta_{k,j}]
\in\mathbb R^{13\times17}.
\]

于是相对于参考配方的多维配比效应为

\[
\mathbf m(\mathbf p)
=
\widehat{\mathbf L}_{1M}(\mathbf p)
-
\widehat{\mathbf L}_{1M}(\mathbf p_{\rm ref})
=
\mathbf B(\mathbf p-\mathbf p_{\rm ref}).
\]

这里 \(\mathbf B\) 是本题 Ridge 下的“训练域 × 验证域”作用矩阵。它与 Data Mixing Laws Eq.7 中 \(t_{ij}\) 的训练域—验证域交互思想对应，但不能混同：我们的数值来自 A4+A5 的线性 Ridge，而不是指数混合律。严格可识别的两域重新分配效应仍是

\[
\delta(\hat\beta_{k,j}-\hat\beta_{k,r}).
\]

为画热力图时只做显示归一化：

\[
\widetilde B_{k,j}
=
\frac{\hat\beta_{k,j}}
{\max_r|\hat\beta_{k,r}|}.
\]

这与 Data Mixing Laws Fig.4 按每个 validation domain 的最大绝对交互系数归一化的可视化方式一致，但不进入预测或优化计算。

### 4.1 为什么不先把 13 个 Loss 平均

Data Mixing Laws 的多域标准处理是先逐验证域建模，再在总体决策层用权重聚合。BiMix 也先保留逐域 Loss，再在配比约束下求解；DoReMi 则强调 worst-case excess loss，而不是直接盯住某个原始最高 Loss。

因此本题主输出保持

\[
\mathbf m(\mathbf p)\in\mathbb R^{13},
\]

再根据任务偏好选择决策准则。

### 4.2 数据支持域

为了避免线性模型在未见的单纯形顶点上外推，第一问的配比决策域定义为 A4 的 512 个观测配方凸包：

\[
\mathcal P_A
=
\operatorname{conv}
\{\mathbf p_1,\ldots,\mathbf p_{512}\}.
\]

任意候选配方写成

\[
\mathbf p=\sum_{i=1}^{512}\omega_i\mathbf p_i,
\qquad
\omega_i\ge0,
\qquad
\sum_i\omega_i=1.
\]

这不是额外的人为上下界，而是直接由题目已给配方支持域产生。

### 4.3 标量化

若有验证域权重 \(\mathbf s\in\Delta^{12}\)：

\[
J_{\mathbf s}(\mathbf p)
=
\sum_{k=1}^{13}s_km_k(\mathbf p)
=
\mathbf s^\top\mathbf B(\mathbf p-\mathbf p_{\rm ref}).
\]

权重只允许三种来源：

1. 题目/下游任务给出已知验证集组成：直接使用；
2. 没有偏好信息：\(s_k=1/13\) 只能作为“13 能力等权”的对称情景；
3. 有总体 validation Loss 与逐域 Loss 的成对观测：才有数据基础学习 \(\mathbf s\)。

附件 A 没有总体 Loss，因此第一问不学习 \(\mathbf s\)，也不把等权平均写成“真实总体 Loss”。

### 4.4 极小极大：保护最差能力

借鉴 DoReMi 的 worst-case excess-loss 思想，在参考配方坐标下定义

\[
\min_{\mathbf p\in\mathcal P_A}
\max_{k=1,\ldots,13}
m_k(\mathbf p).
\]

这是对本题已拟合代理的鲁棒决策，不等价于重新实现 DoReMi 的在线 Group DRO。使用 \(m_k\) 而不是原始 \(L_k\)，是为了把各域都放在“相对同一参考配方的变化量”上。

### 4.5 重点能力 + 保护约束

如果重点优化 target \(q\)，又要求一组保护域不被明显破坏：

\[
\begin{aligned}
\min_{\mathbf p\in\mathcal P_A}\quad
& m_q(\mathbf p),\\
\text{s.t.}\quad
& m_k(\mathbf p)\le\varepsilon_k,
\quad k\in\mathcal K_{\rm protect}.
\end{aligned}
\]

\(\varepsilon_k\) 必须来自题目要求、业务容忍度或独立不确定性，附件 A 没给就不填数值。

### 4.6 向量/Pareto 优化

保留完整多目标形式：

\[
\min_{\mathbf p\in\mathcal P_A}
(m_1(\mathbf p),\ldots,m_{13}(\mathbf p))^\top.
\]

通过改变 \(\mathbf s\)、保护集合或阈值可以扫描 Pareto 折衷。BiMix 的约束优化给出了“逐域 Loss + 配比和为 1 + 数值求解”的文献范式；但 BiMix 的 Loss 律显式依赖训练步数/数据量，而附件 A 没有与配方实验对应的 \(D\)，因此我们只借鉴它的优化层，不照搬它的双变量 Loss 律。

### 4.7 Data Mixing Laws Eq.7 为什么暂时只作为候选模型

Data Mixing Laws 的逐验证域形式为

\[
L_k(\mathbf p)
=
c_k+a_k
\exp\left(\sum_{j=1}^{17}t_{k,j}p_j\right).
\]

它与当前 Ridge 的共同点是“13 条 Loss 律共享同一个 17 维配比输入”，但函数族不同。现在仓库里真正已经用 A6–A11 held-out 验证过的是 Ridge。没有在完全相同的五折协议与 held-out 集上跑过指数形式前，不能因为文献采用 Eq.7 就直接把主模型换掉。

后续若比较模型，只允许：

\[
\text{A4+A5 拟合/调参}
\rightarrow
\text{A6--A11 固定外部比较}
\]

然后依据 RMSE、Spearman 和稳定性选主模型。

## 5. 不拟合跨规模幅度，只验证跨实验组排序

对 A6–A11，不再拟合

[
L_k(N,mathbf p)=a_k(N)+b_k(N)s_k(mathbf p)
]

也不拟合

[
log b_k(N)=c_k-etalog N.
]

原因不是“公式形式不好看”，而是附件 A 对这些参数不可识别：没有配方实验的 (D)，只有三个离散模型规模位置，并且 1B 的配方支持集与 1M/60M 不同。

冻结 A4+A5 的 1M 代理后，对每个检验组只计算

[
ho_{k,ell}^{m pred}
=
ho_S!left(
widehat L_{k,1M}(mathbf p_i^{(ell)}),
L_{ik}^{(ell)}
ight),
qquad
ellin{1M,60M,1B}.
]

13 域结果：

| 实验组 | 中位 Spearman | 均值 | 最小 | 最大 |
|---|---:|---:|---:|---:|
| 1M | 0.8381 | 0.8328 | 0.7446 | 0.9227 |
| 60M | 0.8381 | 0.8314 | 0.7521 | 0.9202 |
| 1B | 0.7067 | 0.7285 | 0.5691 | 0.8876 |

A6 与 A8 是完全相同的 256 个配方，因此可以直接比较真实 Loss，而不经过代理：

[
ho_k^{1Mleftrightarrow60M}
=
ho_S
left(
L_k^{1M}(mathbf p_i),
L_k^{60M}(mathbf p_i)
ight).
]

13 域范围 0.9801–0.9980，中位数 0.9944。这个结果只能表述为“题目给定的两个实验组中，同配方 Loss 排序高度稳定”，不能进一步写成“纯参数规模效应”，因为附件 A 没有 (D) 等控制变量。

A10 的 64 个 1B 配方与 A4/A6 没有完全重复，因此 1B 结果是未见配方集合上的排序泛化检验。它支持“1M 配比关系仍有迁移信息”，但不能用于连续尺度律拟合。

## 5. 为什么绝对 Loss 不能直接跨规模搬运

当前消融结果中，无配比常数基线与完整 1M Ridge 的 RMSE 中位数分别为：

| 实验组 | 完整 Ridge | 无配比常数 | RMSE 改善目标数 |
|---|---:|---:|---:|
| 1M | 0.4478 | 0.6759 | 13/13 |
| 60M | 1.4450 | 1.4724 | 13/13 |
| 1B | 3.2079 | 3.2514 | 4/13 |

这说明当前 A 数据对“相对排序”比对“绝对 Loss 水平”更有证据支持。特别是 1B 只有 4/13 个目标域的绝对 RMSE 下降，因此不能把 1M Loss 幅度按某个经验 (eta) 直接缩放到大模型。

## 6. A12–A15 只做 estimated/extrapolated 压力测试

10B/70B 两组使用相同 63 个配方，而且这些配方全部已在 A4 训练集合中出现。两组附件 estimated Loss 的逐域直接 Spearman 范围为 0.9754–0.9965，中位数 0.9907；但冻结 1M Ridge 对 10B/70B estimated Loss 的 13 域 Spearman 中位数只有 0.5136/0.4148。

所以 A12–A15 的作用是压力测试：它们不能充当真实大模型训练验证，也不能弥补 A 数据对 (N,D) 连续关系的缺失。

## 7. Q1 → Q2 的严格接口

第一问只交付：

1. 七个真实质量域的 A 侧综合质量代理 (Q_A) 及评分规则不确定性；
2. A16 的 direct / near-direct / inferred 映射类型，不给 11 个 inferred 域硬填质量；
3. 13 个目标域的 1M 配比代理与 (m_k(mathbf p))；
4. A6–A11 的排序验证，以及 A12–A15 的压力测试。

第一问 **不再交付**：

- 连续 (b_k(N))；
- 公共尺度衰减指数 (eta)；
- 任意由附件 A 推出来的 (N-D) 标度律；
- (Q_A	o Q_{m score}) 的无配对数值映射；
- 把 Q1 某个 target Loss 默认等同于 B1 `val_loss` 的桥接。

因此后续问题若要把配比加入 B 侧 Loss，必须由问题二提供可验证的 Loss 坐标桥接；没有证据时只能做 target-specific 敏感性，而不能默认单位系数。

## 8. 本问最终可写结论

第一，A1–A3 支持构造一个透明、可复核但依赖显式权重假设的 A 侧质量代理，不能把它写成客观质量真值。第二，A4+A5 逐目标域 Ridge 在 held-out 1M、60M、1B 配方上保留明显的排序信息；其中 1M/60M 同配方真实 Loss 排序的中位 Spearman 为 0.9944。第三，绝对 Loss 误差、1B 支持集变化及 A 中缺失 (D) 共同说明：第一问不具备识别连续配比尺度律的条件。

这套重构把第一问严格限定在附件 A 能支持的结论上，并把 (N,D,Q,p) 与统一 Loss 坐标的建模留给第二问。