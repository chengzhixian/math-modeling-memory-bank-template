# chm → cyj Q1 生产者接口 v2.0

日期：2026-09-24  
当前推荐机器版本：`chm.q1.v1.2`  
生产者：chm  
消费者：cyj（Q2/Q3）、zhh（需要 Q1 证据时）  
状态：**A 侧质量代理、配比相对效应与排序验证可消费；跨 A/B 数值桥接未识别；Q1 不再提供跨规模幅度传递参数。**

当前机器入口：`interfaces/chm/q1_interface_v1_2.json`。旧 `v1` / `v1.1` 保留追溯，但新消费默认使用 v1.2。

## 1. 本轮科学修订

旧接口曾包含经验尺度参数 `eta=0.14503317`，并允许将

[
m_k(mathbf p)
]

乘以 ((N/10^6)^{-eta}) 形成条件尺度情景。重新核对附件 A 后，该做法从 Q1 正式接口中撤出，原因是：

1. A4–A15 的配比/Loss 表没有与实验相对应的训练数据量 (D)；
2. 真实模型规模只有 1M、60M、1B 三个离散位置；
3. 1M/60M 共用 256 个配方，而 1B 使用另一组 64 个配方，支持集改变；
4. A6–A11 的正式职责是冻结 A4+A5 模型后的 held-out 检验，若继续用其拟合尺度参数，则它们不再是该尺度模型的外部验证集。

因此 v1.2 的生产者边界是：**只交付 1M target-specific 配比对比 + 跨实验组排序证据，不交付由附件 A 推出的连续 (N)/(D) 幅度函数。**

## 2. 正式交付

| chm 交付 | 数据/定义 | 状态与边界 |
|---|---|---|
| A 侧质量代理 | A1–A3 的 22 个质量信号，经稳健标准化、方向对齐和三家族等权得到 7 域 (Q_A) | 描述性 composite proxy，可为负；不是 B6–B8 `Q_score`，不允许直接输入 B predictor |
| 17 域映射 | A16：3 direct、3 near-direct、11 inferred | inferred 不填 Q；near-direct 只作代理 |
| 参考配比 | A4 归一化 512 配方的均值 (mathbf p_{m ref}) | 17 维非负、和为 1 |
| 逐目标域 Ridge | A4+A5 对 13 个 target 分别拟合的零和系数 (hateta_k) | 只在 A4+A5 1M target-loss 坐标解释；系数是组成对比，不是独立因果效应 |
| 相对配比效应 | (m_k(mathbf p)=hateta_k^	op(mathbf p-mathbf p_{m ref})) | A4+A5 1M target cross-entropy contrast；不是绝对 Loss，不自动适用于 60M/1B/B1 |
| 排序验证 | A6–A11 上冻结 1M Ridge 的逐 target Spearman；A6/A8 同配方真实 Loss 直接比较 | 支持“排序迁移”，不构成幅度标定 |
| 外推压力测试 | A12–A15 | estimated/extrapolated；不参与训练和参数拟合 |

## 3. 组成效应的数学解释

归一化后 (mathbf1^	opmathbf p=1)。以 (mathbf p_{m ref}) 为中心，只有 16 维切空间可识别。当前系数采用

[
mathbf1^	ophat{oldsymboleta}_k=0
]

的零和规范表示。对从域 (r) 向域 (j) 转移比例 (delta)：

[
m_k(mathbf p+deltamathbf e_j-deltamathbf e_r)-m_k(mathbf p)
=
delta(hateta_{k,j}-hateta_{k,r}).
]

因此消费者不得把单个 (hateta_{k,j}) 解释成“独立增加域 (j) 的因果作用”。

## 4. v1.2 机器接口

调用入口：`src/chm/q1_interface.py`。

- `quality(domain)`：返回 A 侧 (Q_A) 域中位数、条件区间与 `B_Q_score_mapping=unidentified`。
- `mapped_quality(mixture_domain)`：仅 direct/near-direct 返回对应 A 侧代理；inferred 返回 `None`。
- `relative_effect(mixture, target)`：只返回 `delta_target_loss_1m`，不接收 (N)、(D) 或 `eta`。
- `ranking_validation(target)`：返回 1M/60M/1B held-out Spearman，以及 10B/70B estimated 压力测试 Spearman。

机器 manifest 明确：

```text
quality_coordinate = A_composite_quality_proxy_z
mixture_effect_coordinate = A4_A5_1M_target_cross_entropy_contrast
scale_transfer_status = not_identified_from_attachment_A
```

## 5. Q1 → Q2 禁止项

当前附件没有成对证据支持以下等式，均禁止作为默认接口：

[
Q_A=Q_{m score},
]

[
L_{k,m Q1}=L_{m B1},
]

[
m_k(mathbf p;N)
=
m_k(mathbf p)(N/10^6)^{-eta}.
]

因此：

- 禁止用恒等、MinMax、手调线性映射把 (Q_A) 变成 B-native `Q_score`；
- 禁止默认 `pile_cc == B1 val_loss` 或把 13 域原始 Loss 直接平均成 B1 Loss；
- 禁止从 v1/v1.1 历史 `scale` 文件读取 `eta` 作为 Q2/Q3 的正式默认参数；
- 任何 (N,D)-dependent 的配比幅度、A→B Loss 系数或函数，都必须由 cyj 在 B 侧给出独立证据并标明 `validated` 或 `sensitivity_only`。

## 6. 版本兼容

- `chm.q1.v1`：旧 CRLF/LF 文件身份协议；
- `chm.q1.v1.1`：修复跨平台文本哈希，科学数值不变，但仍暴露 eta 尺度情景；
- `chm.q1.v1.2`：**科学语义修订**。底层 Q、Ridge 系数、参考配比、validation 数值不变；删除 scale 文件依赖和自动 eta 缩放，明确只交付 1M target contrast + ranking evidence。

历史 `mixture_scale_transfer_v0*` 文件为审计材料，不删除，但不再属于当前生产者接口。

## 7. 消费记录要求

cyj/zhh 若消费 Q1，必须记录：

- 分支与完整 commit SHA；
- `schema_version=chm.q1.v1.2`；
- manifest SHA/文件身份；
- 使用的 target；
- 是否仅使用 (m_k(mathbf p)) / ranking evidence；
- A→B bridge 的状态。

如 downstream 仍需要连续 (N,D)-dependent 的配比项，应在自己的接口中明确证明来源，不得把 Q1 历史 `eta` 当作已识别事实。