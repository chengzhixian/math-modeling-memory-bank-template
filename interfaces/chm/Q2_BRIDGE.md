# chm→cyj Q2 桥接边界 v1.0

> 2026-09-24 职责决定：用户已指定 A 侧强相关接口由 chm 定义、cyj 直接消费；B 侧强相关接口由 cyj 定义、chm 直接消费。chm 的机器接口和用法见 `CONTRACT.md`、`USAGE.md`；cyj 需交付的 B 侧清单见 `CYJ_REQUIRED_INTERFACE.md`。下文的不可识别边界继续有效，协作分工不生成新的标定证据。

日期：2026-09-23  
状态：chm 生产者侧已冻结的**可识别性边界**；等待 cyj 在其接口中接受后才可标记 joint-validated。

## 1. 质量 Q：不做无配对数据支撑的数值映射

Q1 输出的 `Q_z` 是基于附件 A 22 个质量信号构造的描述性潜在质量指数，可为负；B6–B8 的 `Q_score` 是半合成 N-D-Q 实验中的原生质量坐标，当前可见数据没有 `Q_z ↔ Q_score` 的成对标定样本。

2026-09-24 官方字段复核：B6–B8 **已经提供** `Q_score`，B 侧质量项应优先在该坐标上拟合；A1–A3 只提供原始质量信号而无 `Q_z`，后者是 chm 自定义派生值。B8 的 extrapolated 行不能当作独立实测验证。完整来源和接口资格判断见 `OFFICIAL_DATA_REVIEW.md`。

因此当前正式决定是：

- **禁止**直接使用恒等映射、MinMax、线性平移或经验手调把 `Q_z` 转成 `Q_score`；
- Q2 的质量效应应在 B6–B8 的原生 `Q_score` 坐标上估计；
- Q1 的 `Q_z` 只提供域间相对质量排序、情景分组和不确定性，不提供 B 系列质量项的绝对数值；
- 若 Q3 需要把“数据质量选择”作为连续决策变量，必须由 cyj 明确给出可识别的跨附件桥接或把该变量保留为 B-native `Q_score` 情景，不能把 A 侧 Q 数值直接塞进 B 侧幂律。

这不是缺失实现，而是由现有数据决定的不可识别边界。

## 2. 配比 p：13 个目标域 Loss 不等于 B1 val_loss

Q1 配比接口为 13 个 The-Pile 目标验证域的响应函数

\[
\widehat L_k(\mathbf p)
=
\beta_{0,k}+\boldsymbol\beta_k^\top\mathbf p,
\]

其中 `k` 为具体目标验证域。B1 只有泛化字段 `val_loss`，当前可见说明没有证明它等于任一 Q1 目标域 Loss，也没有给出二者的成对观测。

因此：

- **禁止**默认 `pile_cc == B1 val_loss`；
- **禁止**把 Q1 的 13 域 Loss 做原始算术平均后当成 B1 `val_loss`；
- Q1→Q2 的主 anchor 必须由 cyj 根据 B1 validation set 的实际定义确认；
- 在确认前，Q1 只交付 target panel 与目标域敏感性，不交付“唯一正确”的 p→B1 Loss 标量。

当前 target panel（按 `local_recheck_v1`）至少包含：

| target | 1M/60M/1B 最小 Spearman | 说明 |
|---|---:|---|
| pile_cc | 0.8876 | 三尺度最稳；A16 near-direct→commoncrawl |
| wikipedia_en | 0.8385 | 高稳定；A16 near-direct→wikipedia |
| arxiv | 0.7446 | A16 direct；A2 有扩展质量数据 |
| stackexchange | 0.7323 | A16 direct |
| github | 0.6721 | A16 direct；A3 有扩展质量数据 |

## 3. 若必须联调 p 项，使用“中心化情景修正”而不是单位系数硬拼

在 cyj 尚未确认 Loss 可比性前，只允许用下式做接口联调/敏感性：

\[
m_k(\mathbf p)
=
\boldsymbol\beta_k^\top(\mathbf p-\mathbf p_{\mathrm{ref}}),
\]

并将其视为 target-specific 的相对配比效应。若要嵌入 B 侧 Loss，必须显式引入桥接系数

\[
L_B^{(k)}(N,D,Q_B,\mathbf p)
=
L_B(N,D,Q_B)
+
\lambda_k(N) m_k(\mathbf p),
\]

其中 `lambda_k(N)` 不能默认为 1；若无成对数据可估计，只能作为情景参数/敏感性参数，不能作为 validated 主模型。

Q1 的经验尺度衰减 `eta=0.14503317` 只能帮助描述 `m_k` 幅度随规模变化的情景，不能替代 `lambda_k` 的跨 Loss 口径标定。

## 4. Q3 启动门槛

Q3 正式优化必须同时满足：

1. cyj 提供 validated 的 B 侧预测器和 Loss 精确定义；
2. cyj 明确是否接受某个 Q1 target 作为主 anchor，或明确只做多 target 情景；
3. 若联合使用 Q，说明使用的是 B-native `Q_score` 还是有证据的跨附件映射；
4. p 项的单位和桥接系数来源明确；
5. 不确定性传播协议见 `interfaces/chm/UNCERTAINTY.md`。

在上述条件未满足前，只能进行接口测试和情景分析，不发布 Q3 “最优配置”。
