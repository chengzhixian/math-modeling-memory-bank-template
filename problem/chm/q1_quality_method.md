> **版本说明：** 主模型在 A1 全量记录上以 Spearman 符号定向 14 个统计指标，8 个模型指标固定正向，全部 22 个信号进入综合评分。七域相关和 LOO 只用于诊断；本地 A1--A3 LFS 实体已全量重跑，结果见 `outputs/chm/quality_analysis_manifest_v0.json`。

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

## 4. 22 指标的主方向与独立诊断

八个模型型字段经本文定义的压缩后固定正向。其标准化值的逐记录均值 $A_i$ 是语义方向参考，并非附件提供的真实质量标签。其余 14 个统计字段在 A1 全部有效记录上计算 $\rho_j=\rho_S(z_j,A)$，以 $d_j=+1$（$\rho_j\ge0$）或 $-1$（$\rho_j<0$）定向，得到 $z^+_{ij}=d_jz_{ij}$。Spearman 只决定单调方向，不作为重要性权重或因果效应。主模型全部 22 个字段的方向只能为 $-1,+1$；弱相关字段继续保留。

七域内 Spearman、跨域符号一致率以及删去一个领域后在其余全部 A1 记录上重算的 LOO 相关，是独立的稳健性诊断，不改变主评分。Fisher 型 pooled 相关若用于历史对照，仅属于 Spearman 的近似敏感性汇总；不能直接套用 Pearson 的 $1/(n-3)$ 方差结论。方向脆弱的指标只在 `drop_loo_flip` 压力测试中暂时删除。

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

为避免“某一类仅因指标数量多就权重更大”，主评分采用**先家族内等权、再三家族等权**。记 $\mathcal J_{ig}$ 为家族 $g$ 中在记录 $i$ 上非缺失的指标集合，则
\[
G_{ig}
=
\frac{1}{|\mathcal J_{ig}|}
\sum_{j\in\mathcal J_{ig}} z^+_{ij},
\qquad
S_i=\frac13\left(G_{i,\mathrm{RPS}}+G_{i,\mathrm{DSIR}}+G_{i,\mathrm{MODEL}}\right).
\]

主规则保留 11 个 RPS、3 个 DSIR 和 8 个 model-based 字段，共 22 个；LOO 翻号字段只在压力测试中删除。

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
