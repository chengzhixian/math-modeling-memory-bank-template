# chm 交付约定 v1.4

> 2026-09-24 本机复核：以下“未实跑前”“完整本地重跑前”等句子是 09-23 网页提交时状态。现已完成真实 A1–A3 敏感性、RegMix 折分、eta 配对重抽样与图表复跑；输出与边界见 `problem/chm/20260924_cross_branch_delta_review.md`。Q/p 仍为 producer-validated draft，跨成员尺度与 Loss 桥接未联合冻结。

日期：2026-09-23  
生产者：chm  
消费者：cyj（Q2/Q3）、zhh（Q4/不确定性）  
状态：Q1 producer-validated draft；跨成员接口仍需消费者验收后才能标记 joint-validated。

> 历史 v1.2 已移至 `interfaces/chm/archive/CONTRACT_v1.2.md`。该文件仅供审计，禁止作为当前输入。

## 1. 质量 Q 接口

当前文件：

- `outputs/chm/domain_quality.csv`：面向下游的 7 域描述性 Q；
- `outputs/chm/domain_quality_v0.csv`：详细统计；
- `outputs/chm/domain_mapping.csv`：A16 direct / near_direct / inferred 映射；
- `outputs/chm/quality_analysis_manifest_v0.json`：输入哈希、随机种子、标准化参数与警告；
- 后续稳健性输出：`outputs/chm/quality_review_v1/`。

定义：A1 上对 22 个指标做稳健标准化和方向统一，先在 RPS / DSIR / model 三家族内等权，再三家族等权，得到样本级综合分数并标准化为 `Q_z`。域级主统计量为中位数。

当前 7 域 `Q_z` 中位数：

| domain | Q_z median |
|---|---:|
| book | 2.771089 |
| arxiv | 2.682585 |
| commoncrawl | 0.506149 |
| stackexchange | 0.187411 |
| c4 | -0.217345 |
| wikipedia | -0.375921 |
| github | -0.517070 |

边界：

- `Q_z` 可为负，是描述性潜在指数，不等于 B6–B8 `Q_score`；
- A1 的 arxiv/github 被 A2/A3 包含，独立复核使用非重叠 16,104 / 193,752 条；
- A16 有 3 direct、3 near_direct、11 inferred；禁止为 11 个 inferred 域伪造精确 Q；
- Q 定向、权重、Qurater 与 domain-balanced 敏感性由 `src/chm/q1_quality_sensitivity.py` 生成，未实跑前不得声称这些稳健性已通过；
- Q1→Q2 的可识别性边界见 `interfaces/chm/Q2_BRIDGE.md`。

## 2. 配比 p→Loss 接口

**当前唯一有效目录：**

`outputs/chm/local_recheck_v1/`

旧网页端结果已原样归档到 `outputs/chm/archive/web_v0/`，只用于差异审计，禁止与新版混用。

核心文件：

- `mixture_effect_ridge_v0.csv`
- `mixture_effect_ridge_v0_cv.csv`
- `mixture_effect_ridge_v0_manifest.json`
- `mixture_reference_v0.csv`
- `q1_regmix_ridge_domainwise_metrics.csv`
- `q1_regmix_direct_scale_rank_stability.csv`
- `q1_regmix_composition_overlap.csv`

对 13 个目标域分别拟合

\[
\widehat L_k(\mathbf p)
=
\beta_{0,k}
+
\sum_{j=1}^{17}\beta_{k,j}p_j,
\qquad
\sum_j p_j=1.
\]

每行配比先重新归一化到单纯形。系数使用零和对比参数化，因此 `beta` 是相对配比效应，不是独立因果贡献。

训练/验证边界：

- A4+A5：唯一训练和 alpha 选择数据；
- A6+A7、A8+A9、A10+A11：1M / 60M / 1B held-out 验证；
- A12–A15：estimated/extrapolated，只作尺度外推压力测试。

Pile-CC 当前 Spearman：

- 1M：0.900735
- 60M：0.891900
- 1B：0.887592

13 域中位 Spearman：

- 1M：0.838053
- 60M：0.838115
- 1B：0.706685

A12–A15 的 63 个配方全部来自 1M 训练配方，因此只能称为**已见配方上的尺度外推**，不能称新配方泛化。

CV 折分敏感性代码已加入 `q1_regmix_cv_split_sensitivity.csv` 生成逻辑；完整本地重跑前当前主输出仍使用既有确定性五折。

## 3. 配比效应尺度传递

当前文件：

- `outputs/chm/local_recheck_v1/mixture_scale_calibration_v0.csv`
- `outputs/chm/local_recheck_v1/mixture_scale_transfer_v0_manifest.json`

经验模型：

\[
\log b_k(N)=c_k-\eta\log(N/10^6)+\varepsilon_{k,N}.
\]

当前公共估计：

\[
\widehat\eta=0.14503317,
\]

现有目标域 bootstrap 95% CI：

\[
[0.10686793,\;0.18669841].
\]

边界：

- 只有 1M、60M、1B 三个真实尺度；
- 1M/60M 使用同一组 256 配方，1B 使用另一组 64 配方，因此 eta 可能混入配方支持集变化；
- 当前已提交代码会额外计算“目标域 + 校准样本”bootstrap，但仍条件于 A4+A5 Ridge；
- eta 是经验尺度传递修正，不是新的普适 Scaling Law，也不是纯规模因果弹性。

## 4. Q1→Q2 联合使用

正式规则见：

- `interfaces/chm/Q2_BRIDGE.md`
- `interfaces/chm/UNCERTAINTY.md`

核心禁止项：

- 不允许 `Q_z == Q_score`；
- 不允许 `pile_cc == B1 val_loss`；
- 不允许将 13 个原始 Loss 简单平均后当作 Q2 Loss；
- 不允许把跨 Loss 口径桥接系数默认为 1。

在 cyj 未验收桥接前，Q3 只能做接口测试/情景分析，不发布正式最优配置。

## 5. Q3 后续接口

Q3 输出至少包含：

- 算力预算与上下文情景；
- N / D / Q / p；
- 分项成本和总成本；
- cyj predictor 版本、输入单位与有效范围；
- 使用的 Q1 target / mapping / eta 情景；
- 预测 Loss 与不确定性；
- 求解状态和约束残差。

Q3 只能使用 cyj 已 validated 的预测器与 zhh 已验收的 C7 情景。

## 6. 可复现入口

- 质量主分析：`src/chm/q1_quality_analysis.py`
- 质量稳健性：`src/chm/q1_quality_sensitivity.py`
- 配比逐域 Ridge：`src/chm/q1_regmix_domainwise.py`
- 配比接口：`src/chm/q1_mixture_interface.py`
- 尺度传递：`src/chm/q1_mixture_scale_transfer.py`
- 图表：`src/chm/q1_figures.py`

消费者必须记录精确 commit SHA、文件 SHA、接口版本和 draft/validated/integrated 状态。
