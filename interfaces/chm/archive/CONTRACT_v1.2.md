# [ARCHIVED — DO NOT CONSUME] chm 交付约定 v1.2

此文件仅保存历史接口文本用于审计。当前消费者必须读取 `interfaces/chm/CONTRACT.md`。本文件中的旧路径、旧 eta、旧 alpha、旧状态不得作为当前计算输入。

---

# chm 交付约定 v1.3

## 2026-09-23 本地交付修订 v1.3（当前有效状态）

- A1–A3 已全量实跑，outputs/chm/domain_quality.csv 是当前描述性 Q 接口，domain_quality_v0.csv 为详细统计。domain_mapping.csv 保留 A16 的 direct/near_direct/inferred 类型，11 个 inferred 无填值。
- Q 定义为 A1 拟合的三家族等权 z 分数之域中位数；可为负，不等于 B6 Q_score。进入 Q2 前需另行定义映射；尚不标记为最终 validated 质量真值。
- 当前配比输入统一从 outputs/chm/local_recheck_v1/ 读取，文件名与上述约定一致。旧结果已移至 outputs/chm/archive/web_v0/，仅供历史对照；四个配比脚本默认指向新版目录。
- 新版 eta=0.14503317，bootstrap 区间 [0.10686793,0.18669841]，其余数值以新版 CSV/manifest 为准。训练五折固定不打乱；仅 A4/A5 调参。
- Q 的 sample/extended 存在完整样本包含关系，非重叠复核在 quality_nonoverlap_validation_v0.csv 与 quality_conflict_nonoverlap_v0.csv。条件 bootstrap 不包含权重、方向及映射不确定性。
- 缺失列表不再经 argmax 伪造为 0；分组均值使用现有非缺失指标。quality_analysis_manifest_v0.json 保存输入哈希和最终 Q 标准化参数。
- 证据：experiments/chm/20260923-q1-local-quality.md 与 20260923-q1-local-reproduction.md。


# 历史 v1.2 约定（数值与路径以顶部 v1.3 为准）

生产者 chm；使用者 cyj（Q2）、chm（Q3）、zhh（论文/不确定性）。
状态：Q1 配比部分已有 draft_verified_ridge；质量 Q 部分仍因 A1–A3 LFS 正文未在当前网页运行环境解压而待完成。

## 1. domain_quality.csv（待生成）

字段至少包含：
- `quality_domain`
- `dataset_scope`：sample / arxiv_extended / github_extended / combined
- `n_rows`
- `Q`
- `Q_scale_definition`
- `uncertainty_low` / `uncertainty_high`
- `missing_note`
- `score_version`

要求：A1/A2/A3 分开标识；列表型指标先压缩；22 指标方向和变换可追溯；arxiv/github 必须给抽样与扩展集对照。

## 2. domain_mapping.csv（待质量 Q 完成后冻结）

来源：A16。
当前已核对 17 个配方域中 3 direct、3 near_direct、11 inferred。
字段至少包含：
- `mixture_domain`
- `quality_domain`
- `mapping_type`
- `mapping_weight_or_rule`
- `mapping_confidence`
- `note`

禁止对 11 个 inferred 域伪造精确质量真值；若只能给区间或情景，应显式保留不确定性。

## 3. mixture_effect_ridge_v0.csv（已生成，draft_verified_ridge）

路径：`outputs/chm/mixture_effect_ridge_v0.csv`

这是 Q1→Q2 当前可用的配比接口。定义为 13 个目标验证域各自的 17 域配比→Loss Ridge 代理模型，而不是把 13 个原始 Loss 先平均。

预处理：
1. 对输入 `p` 检查非负；
2. 将 17 维配比重新归一化为 `p_normalized = p / \sum(p)`；
3. 预测式为

\[
\widehat L_k(\mathbf p)
=
\beta_{0,k}
+
\sum_{j=1}^{17}\beta_{k,j}p_j.
\]

参数采用单纯形上的零和对比表示：

\[
\sum_{j=1}^{17}\beta_{k,j}=0.
\]

因此各 `beta` 只能解释为“相对于平均训练域的配比对比效应”，不能写成独立因果效应。

### 字段

- `target`：13 个验证目标域之一；
- `alpha`：仅用 A4+A5 训练数据 5 折 CV 选择的 Ridge 正则；
- `cv_rmse`；
- `intercept`；
- 17 个训练域零和系数；
- `test_1m_spearman/pearson`
- `test_60m_spearman/pearson`
- `test_1B_spearman/pearson`
- `est_10B_spearman/pearson`
- `est_70B_spearman/pearson`

### 数据边界

- 训练：A4+A5；
- 正式检验：A6+A7、A8+A9、A10+A11；
- 外推压力测试：A12+A13、A14+A15；
- A12–A15 的 Loss 属于题面标记的估算/外推数据，不能称为真实大模型观测。

### anchor target 策略

当前**不冻结单一标量配比分数**。原因：EXP-CHM-Q1-001 已验证，先平均 13 个原始 Loss 会显著破坏跨尺度排序信号。

当前推荐给 cyj：
- 首选检查 `pile_cc` 是否与 Q2 的 Loss 口径可比。其 Ridge 在 1M/60M/1B 的 held-out Spearman 约为 0.902/0.893/0.881，并与公开 RegMix 线性基线近复现；
- 至少再用 arxiv、pubmed_central 等不同目标域做敏感性；
- 若 Q2 的 Loss 无法与任何单域合理对应，则保留 13 维 `mixture_effect`，不要擅自压成一个未经验证的平均值。

## 4. mixture_scale_transfer_v0（已生成，draft_post_validation_calibration）

路径：
- `outputs/chm/mixture_scale_calibration_v0.csv`
- `outputs/chm/mixture_reference_v0.csv`
- `outputs/chm/mixture_scale_transfer_v0_manifest.json`

用途：给 Q2/Q3 提供“配比效应随参数规模变化”的经验传递接口，不替代附件 B 的正式标度律。

先定义参考配方 (\mathbf p_{ref}) 为 A4 中所有归一化训练配方的分量均值，并令

\[
m_k(\mathbf p)=\boldsymbol\beta_k^\top(\mathbf p-\mathbf p_{ref}).
\]

该量在参考配方处为 0，因此可作为 Q2 基准 Loss 上的配比修正，避免重复计算截距。

A6–A11 在 EXP-002 中先承担 held-out 排名验证；模型族冻结后，本接口再使用它们拟合后验尺度校准

\[
L_k(N,\mathbf p)=a_k(N)+b_k(N)s_k(\mathbf p)+\varepsilon.
\]

13 个目标域在 1M、60M、1B 三尺度的 (b_k) 均为正。目标域固定效应模型

\[
\log b_k(N)=c_k-\eta\log(N/10^6)+\varepsilon
\]

得到公共 (\widehat{\eta}=0.14537)，按目标域整体 bootstrap 的 95% CI 为 [0.10787, 0.18686]；域特异 $\eta_k$ 范围约 [0.04467, 0.30742]。

解释边界：
- 只有三个真实模型尺度，该指数只是经验传递修正，不得写成普适 Scaling Law；
- A12–A15 未用于估计 (eta)，仍只作 estimated/extrapolated 压力测试；
- cyj 应使用“公共 eta 主结果 + 域特异 eta/CI 敏感性”，不能把单值当作无误差常数。

## 5. 可复现代码

- `src/chm/q1_regmix_domainwise.py`：逐域 RegMix/Ridge 近复现与 LightGBM 待跑框架；
- `src/chm/q1_mixture_interface.py`：归一化单纯形 + 零和 Ridge 接口生成；
- `src/chm/q1_mixture_scale_transfer.py`：验证后尺度幅度校准、公共 eta 与域 bootstrap；
- `experiments/chm/20260923-q1-regmix-domainwise.md`：验证与方法决策证据。

## 6. optimization 文件（后续 Q3）

字段至少包括：
- 预算；
- 上下文情景；
- N/D/Q/p；
- 分项成本与总成本；
- 预测 Loss；
- 求解状态；
- 约束残差；
- 使用的 cyj/zhh 接口版本。

Q3 只能使用 cyj 已验证的标度律接口与 zhh 已复核的 C7 情景；不得把当前 Q1 配比代理直接当完整广义标度律。

## 验收

- p 各分量非负、归一化后和为 1；
- 质量聚合和跨域映射假设可追溯；
- 训练/检验/外推不混用；
- 配比代理按目标域分别验证；
- 任何单一 anchor 的选择有 Loss 口径依据并做敏感性；
- Q3 输出满足单位、边界、预算与约束，并报告未收敛。

输出由 chm 放入 `outputs/chm/`；接口说明仅 chm 修改。cyj/zhh 的修改建议写各自交接。


