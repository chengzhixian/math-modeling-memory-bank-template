# chm → cyj Q2 桥接边界 v2.0

日期：2026-09-24  
状态：A 侧生产者边界已按 Q1 严谨重构更新；等待 cyj 在 B 侧接口中接受/实现。  
当前 Q1 机器版本：`chm.q1.v1.2`。

## 1. 质量坐标：(Q_A) 不等于 B-native `Q_score`

A1–A3 提供 22 个质量信号，但没有样本级真实质量标签。chm 输出的

[
Q_A
]

是稳健标准化、方向对齐和三家族等权得到的 **A 侧综合质量代理**。它可以为负，且其权重规则存在已量化的敏感性。

B6–B8 自带 `Q_score`，属于 B 侧半合成 N-D-Q 数据中的原生质量坐标。当前附件没有 (Q_Aleftrightarrow Q_{m score}) 的成对标定样本。

因此：

- 禁止恒等映射；
- 禁止 MinMax、线性平移或手调映射后宣称“已标定”；
- Q2 的质量效应优先在 B-native `Q_score` 上估计；
- (Q_A) 只作为 A 侧域间质量描述、排序和敏感性证据；
- 若 Q3 使用连续质量变量，应使用 cyj 已验证的 B-native 质量坐标，除非未来出现真正的跨附件配对证据。

## 2. 配比坐标：(m_k(mathbf p)) 只属于 A4+A5 的 1M target Loss

Q1 对 13 个目标验证域分别拟合 A4+A5 的 1M Ridge，并定义

[
m_k(mathbf p)
=
hat{oldsymboleta}_k^	op
(mathbf p-mathbf p_{m ref}).
]

严格含义是：

[
m_k(mathbf p)
=
widehat L_{k,1M}(mathbf p)
-
widehat L_{k,1M}(mathbf p_{m ref}).
]

因此它是 **A4+A5 的 1M target-specific cross-entropy contrast**，不是绝对 Loss，也不是跨规模 Loss 修正。

B1 只有一个 `val_loss` 字段，当前可见说明没有证明它等于 Pile-CC、arxiv、github 或其他任一 Q1 target。

所以继续禁止：

- 默认 `pile_cc == B1 val_loss`；
- 把 13 个 target 原始 Loss 直接平均后当 B1 `val_loss`；
- 把 (m_k(mathbf p)) 以系数 1 直接加到 B1 Loss。

## 3. Q1 不再提供跨规模幅度函数

旧接口曾输出经验 `eta` 并允许构造

[
m_k(mathbf p)(N/10^6)^{-eta}.
]

该做法已从 v1.2 正式接口撤出。原因：

1. A 配方实验没有对应 (D)；
2. 真实规模只有 1M/60M/1B 三个离散位置；
3. 1B 配方支持集与前两组不同；
4. A6–A11 应作为 held-out 验证，而非 Q1 跨规模参数拟合数据。

因此 **Q1 不定义任何 (N,D)-dependent 的配比幅度函数**。

如果 cyj 认为 Q2 必须把 p 纳入 B-native Loss，应由 cyj 在自己的模型中明确回答：

- B1 Loss 与哪个/哪些 Q1 target 可比较；
- 是否存在可估计的 A→B Loss 桥接；
- 桥接是否依赖 (N,D,Q_B)；
- 参数从哪些数据估计；
- held-out 验证在哪里；
- 状态是 `validated_bridge` 还是 `sensitivity_only`。

在没有证据时，不需要强行构造唯一的 (mathbf p) 数值项；可以把 13-target 配比结果作为敏感性面板。

## 4. Q1 可供 Q2 使用的证据

### 4.1 冻结代理排序验证

A4+A5 的 1M Ridge 冻结后，13 个 target 的 Spearman 中位数：

| 检验组 | 中位 Spearman |
|---|---:|
| A6+A7 1M | 0.8381 |
| A8+A9 60M | 0.8381 |
| A10+A11 1B | 0.7067 |

这些结果支持的是“target-specific 配方排序有迁移信息”。

### 4.2 同配方直接证据

A6 与 A8 的 256 个配方完全相同。真实 1M/60M Loss 的 13-target Spearman 中位数为 0.9944。

这是附件 A 最强的跨实验组证据，但由于没有相应 (D) 等控制变量，不能写成纯 (N) 的因果/尺度效应。

### 4.3 1B 支持集边界

A10 的 64 个 1B 配方与 A4/A6 没有完全重复。1B 结果可以作为未见配方集合的排序泛化，但不能与 1M/60M 一起拟合连续幅度。

### 4.4 A12–A15

10B/70B 是 estimated/extrapolated，且 63 个配方均来自 A4 train 子集。只能做压力测试。

## 5. target panel

在需要做多 target 敏感性时，当前验证结果支持至少保留以下面板：

| target | 1M/60M/1B 最小 Spearman | A16/扩展信息 |
|---|---:|---|
| pile_cc | 0.8876 | near-direct→commoncrawl |
| wikipedia_en | 0.8385 | near-direct→wikipedia |
| arxiv | 0.7446 | direct；A2 扩展 |
| stackexchange | 0.7323 | direct |
| github | 0.6721 | direct；A3 扩展 |

这个 panel 只用于比较不同 target 下结论是否稳健，不自动产生“总体 Loss”。

## 6. Q3 启动门槛

Q3 正式优化必须满足：

1. cyj 给出同一 B-native Loss 坐标上的 validated N-D-Q predictor；
2. p 若进入正式模型，必须说明 `p_policy.mode`：
   - `validated_bridge`：有可验证 A→B Loss 桥接；
   - `sensitivity_only`：NDQ 为主，p 只做多 target 情景；
3. 不把 A 侧 (Q_A) 数值直接输入 B-native Q 模型；
4. 不从 Q1 历史文件默认读取 `eta`；
5. 不确定性和外推边界明确。

## 7. 当前推荐机器语义

```text
Q1 quality:
  coordinate = A_composite_quality_proxy_z
  B_Q_score_mapping = unidentified

Q1 mixture:
  coordinate = A4_A5_1M_target_cross_entropy_contrast
  cross_scale_transfer = not_identified_from_attachment_A
  bridge_to_B1_val_loss = unidentified

Q2/Q3:
  any N/D-dependent p bridge must be defined and validated downstream
```

这不是缺少实现，而是由现有附件的可识别性决定的边界。