> **版本说明（2026-09-24）：** 本文件最初是质量侧方法设计 v0。经方向稳定性复核，主模型代码已将“pooled Spearman 只看正负号”升级为 **leave-one-domain-out (LOO) 方向稳定准入**：非锚点指标只有在删除任意一个 A1 质量域后 pooled 方向均不翻转，才进入主 $Q_A$；否则记为方向不确定并从主综合质量中排除。`stable_consensus_075` 等更激进筛选仍只作压力测试。当前远端环境无法取得 Git LFS 的 A1--A3 实体文件，因此新规则的 canonical 数值表、区间和论文结果表必须在完整 LFS 重跑后刷新，旧数值不得与新规则混写。

# Q1 质量评分与冲突分析方法设计 v0

日期：2026-09-23（北京时间）
角色：chm
状态：本地已全量实跑，结果见 experiments/chm/20260923-q1-local-quality.md；方法仍为描述性初版。后文设计中的差值 CI、冲突显著性、外部权重比较尚未实现，不应当作完成。

## 1. 数据与独立依据

题面可见数据说明要求：
- A1：51,230 条，22 个质量指标，7 个质量域；
- A2：arxiv 扩展集 17,523 条；
- A3：github 扩展集 203,752 条；
- 22 指标中 14 个为标量、8 个为列表型，列表必须先压缩成标量；
- A2/A3 与 A1 使用同一套 22 指标口径；
- A2/A3 必须用于检验抽样域级 Q 与冲突结论。

独立核验来源：
- SlimPajama-Meta-rater 数据卡：
  https://huggingface.co/datasets/opendatalab/SlimPajama-Meta-rater
- Meta-rater 论文：
  https://arxiv.org/abs/2504.14194

官方数据卡给出的 8 个列表型字段结构为：
1. `fineweb_edu`：长度 1；
2. `ad_en`：长度 2，[has_ad, no_ad] logits；
3. `fluency_en`：长度 2，[not_fluent, fluent] logits；
4. `qurater`：长度 4，[Writing Style, Required Expertise, Facts and Trivia, Educational Value]；
5–8. 四个 `modernbert_*`：长度 6，对应 0–5 等级 logits。

这些信息来自公开数据卡，而不是历史隐藏文本。

## 2. 8 个列表字段压缩

主方案尽量保留连续信息，不直接把 logits 只做 argmax：

- `fineweb_edu`：取唯一元素；
- `ad_en`：取 softmax 后“no_ad”概率；
- `fluency_en`：取 softmax 后“fluent”概率；
- `qurater`：4 个维度的算术平均；同时保留四维原值用于敏感性检查；
- `modernbert_professionalism/readability/reasoning/cleanliness`：
  对 0–5 logits 做 softmax 后计算期望等级
  [
  E[R]=\sum_{c=0}^{5} c,P(R=c).
  ]

敏感性方案：按官方数据卡示例，把二分类和 PRRC logits 改为 argmax；若域级 Q 排名发生明显改变，必须在论文中披露。

## 3. 数值预处理

不把不同量纲指标直接相加。

- `rps_doc_word_count`、`rps_doc_num_sentences`：先 (\log(1+x))；
- `dsir_books/wiki/math`：因存在大幅负值，采用 signed-log：
  [
  x'=\operatorname{sgn}(x)\log(1+|x|).
  ]
- 其余连续量保持原量纲；
- 每个指标在 A1 上计算 median 与 MAD，构造
  [
  z_{ij}=\frac{x_{ij}-\operatorname{median}(x_j)}
  {1.4826\,\operatorname{MAD}(x_j)};
  ]
- 为避免极端值主导聚合，将稳健 z 截断到 [-5,5]；
- A2/A3 必须复用 A1 的变换、median/MAD 和方向，不能在扩展集重新拟合口径。

## 4. 22 指标方向统一：锚定而非拍脑袋指定

8 个模型评分经过上述压缩后均定义为“越大越好”，构成方向锚点：

\[
A_i=\frac{1}{8}\sum_{jin\mathcal M} z_{ij}.
\]

对剩余 14 个标量指标，不预先武断规定高低好坏，而是在 A1 的 7 个域内分别计算

\[
\rho_{jd}=\operatorname{Spearman}(x_j,Amid d).
\]

再做 Fisher-z 加权汇总，权重使用 $(n_d-3)$，得到 pooled correlation $\bar\rho_j$。完整 A1 上先得到原始方向
\[
s_j=\operatorname{sgn}(\bar\rho_j).
\]

**主模型不再仅凭这个正负号直接定向。** 对每个非锚点指标，再分别删除 7 个质量域中的一个，重新计算 pooled Spearman，记为 $\bar\rho_j^{(-d)}$。定义主模型准入集合
\[
\mathcal J^*
=
\left\{
j:
\operatorname{sgn}\!\left(\bar\rho_j^{(-d)}\right)=s_j,
\ \forall d
\right\}.
\]
于是
\[
d_j=
\begin{cases}
s_j, & j\in\mathcal J^*,\\
0, & j\notin\mathcal J^*.
\end{cases}
\]
其中 $d_j=0$ 不表示“指标值为 0”，而表示**当前数据不足以稳定判定方向，该指标不进入主 $Q_A$ 聚合**。8 个模型型语义锚点仍固定为正向并保留。

现有真实 A1 敏感性结果已经识别出两个会在 LOO 中跨过 0 的指标：\`rps_lines_numerical_chars_fraction\` 的 full pooled $\rho\approx 8.03\times10^{-5}$，LOO 范围约为 $[-0.0275,0.0274]$；\`rps_doc_frac_chars_top_3gram\` 的 full pooled $\rho\approx-0.0181$，LOO 范围约为 $[-0.0631,0.0181]$。二者因此从主质量代理中排除。其余方向稳定指标保留。

同时继续记录 7 域符号一致率、pooled Spearman、LOO 最小/最大相关以及扩展集方向，作为解释和敏感性证据。更严格的 \`stable_consensus_075\` 会把全部 DSIR 指标过滤掉并改变指标家族结构，因此保留为压力测试，不作为当前主准入规则。

## 5. 冲突分析

### 5.1 指标自身方向冲突

若某指标在不同域中与质量锚点的相关方向反复改变，定义方向异质度

\[
H_j=1-\frac{|\sum_d w_d,\operatorname{sgn}(\rho_{jd})|}
{\sum_d w_d}.
\]

(H_j) 越大，说明该指标越依赖领域语境。

### 5.2 指标两两冲突

全部指标统一方向后，按域计算 Spearman 相关。连续冲突强度定义为

\[
C_{jk,d}=\max(0,-\rho_{jk,d}).
\]

不依赖单个任意阈值即可排序“最严重冲突对”。论文图中若需要标记显著冲突，再使用 bootstrap 95% CI 上界 < 0 作为统计判据。

## 6. 综合质量 Q

22 指标分为三组：

1. Natural/RPS：11 个；
2. DSIR：3 个；
3. model-based：8 个。

为避免“某一类仅因指标数量多就权重更大”，主评分仍采用**先家族内等权、再三家族等权**，但家族内只聚合通过主方向准入的指标。记 $\mathcal J_{ig}^*$ 为家族 $g$ 中通过 LOO 方向稳定性检查且在记录 $i$ 上非缺失的指标集合，则
\[
G_{ig}
=
\frac{1}{|\mathcal J_{ig}^*|}
\sum_{j\in\mathcal J_{ig}^*} z^+_{ij},
\qquad
S_i=\frac13\left(G_{i,\mathrm{RPS}}+G_{i,\mathrm{DSIR}}+G_{i,\mathrm{MODEL}}\right).
\]

按现有稳定性审查，主规则保留 9 个 RPS、3 个 DSIR 和 8 个 model-based 指标，共 20 个；两个 LOO 方向不稳定的 RPS 指标在聚合前被置为缺失而非乘成 0，因此不会稀释家族均值。

A1 上再把 (S_i) 标准化为 `Q_z`。域级 Q 主统计量使用中位数，同时报告 10% trimmed mean 与 bootstrap 95% CI。

额外输出：
- `Q_equal22`：22 维完全等权；
- `Q_argmax`：列表 logits 用官方 argmax 压缩；
- 若三种方法的域排名一致，则主结论稳健；不一致则必须报告。

## 7. A2/A3 抽样代表性检验

对 arxiv、github：
- 用 A1 已冻结的处理参数计算扩展集 Q；
- 比较 sample vs extended 的域级 Q 差：
  [
  \Delta Q_d=Q_{d,mathrm{extended}}-Q_{d,mathrm{sample}};
  ]
- bootstrap 差值 CI；
- 比较 22 个指标的标准化中位数漂移；
- 对 A1 中最强冲突指标对，在 A2/A3 重算 Spearman，检查方向是否保持。

只有通过这一层，A1 的域级 Q 才能交给 Q2。

## 8. 7 质量域 → 17 配方域

A16 已核对：
- direct 3；
- near_direct 3；
- inferred 11。

因此不生成“17 个看似精确的 Q 真值”。

正式交付：
- 7 域真实 Q；
- direct/near_direct 的映射值与映射类型；
- inferred 域标为 unknown/scenario；
- Q2 若必须构造 17 域质量向量，应以区间/情景传播映射不确定性。

p 的 17 域效应由 RegMix 配比模型独立提供，不用虚构 Q 填满 17 域。

## 9. 外部稳健性

Meta-rater 论文/数据卡提供了学习得到的多维质量权重。该权重不作为本题主评分的预设答案，只作为外部 benchmark：
- 比较域级排序；
- 比较与主 Q 的 Spearman；
- 若结论不一致，分析是权重、列表压缩还是域分布导致。

## 10. 预计输出

运行 `src/chm/q1_quality_analysis.py` 后生成：
- `outputs/chm/quality_metric_preprocessing_v0.csv`
- `outputs/chm/quality_orientation_v0.csv`
- `outputs/chm/quality_conflict_pairs_v0.csv`
- `outputs/chm/domain_quality_v0.csv`
- `outputs/chm/quality_sample_extended_v0.csv`
- `outputs/chm/quality_analysis_manifest_v0.json`

在 A1–A3 未实际运行前，上述输出不得预填结果。

## 本地实现补充

A1/A2/A3 已运行。列表含任意非有限元素时整项记缺失；组内按可用指标均值聚合。MAD=0 时回退标准差，再退 1；方向异质度实际用等域权重（相关可定义的域），与 Fisher-z 的样本量加权定向区分。模型锚点相关不伪填 1。A1 与 A2/A3 重叠，另报非重叠部分，不使用独立样本差值 CI。Q_z 均值/标准差已保存于 manifest。
