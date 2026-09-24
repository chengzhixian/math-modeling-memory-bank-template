# chm Q1 接口使用说明（当前 `chm.q1.v1.2`）

这是 chm 发布给 cyj/zhh 的 A 侧只读接口。v1.2 的核心变化是：**不再提供由附件 A 拟合的跨规模 `eta` 缩放。**

当前 manifest：

`interfaces/chm/q1_interface_v1_2.json`

其文本身份规则仍为 `sha256_utf8_lf_normalized`。

## 快速验收

在仓库根目录执行：

```powershell
python src/chm/q1_interface.py
python -m unittest discover -s src/chm -p 'test_q1_interface.py'
```

成功时应报告：

```text
chm.q1.v1.2: 7 Q domains, 17 mixture domains, 13 loss targets;
1M contrasts + ranking evidence; no scale transfer
```

## Python 调用

```python
from pathlib import Path
from src.chm.q1_interface import Q1Interface

q1 = Q1Interface(Path("."))

book = q1.quality("book")
mapped = q1.mapped_quality("gutenberg_pg_19")  # near_direct -> book proxy
unknown = q1.mapped_quality("freelaw")         # inferred -> None

p = q1.reference.copy()
zero = q1.relative_effect(p, "pile_cc")

p["arxiv"] += 0.01
p["freelaw"] -= 0.01
effect = q1.relative_effect(p, "pile_cc")

validation = q1.ranking_validation("pile_cc")
```

当前固定文件下：

[
m_{m pile_cc}(mathbf p)
approx 0.002371904510480527
]

对应上述“arxiv 增加 0.01、freelaw 减少 0.01”的配比转移。这个数值的含义仅是：

> 在 A4+A5 拟合得到的 1M Pile-CC target cross-entropy 代理坐标中，相对于 A4 平均参考配方的预测 Loss 对比。

它**不是** 60M/1B 的 Loss 修正，也不是 B1 `val_loss` 修正。

## `quality()`

返回：

- `Q_A_median`；
- 固定评分规则下的条件 95% 区间；
- 样本数；
- `coordinate=A_composite_quality_proxy_z`；
- `interpretation=descriptive_composite_proxy_not_ground_truth`；
- `B_Q_score_mapping=unidentified`；
- `direct_B_predictor_input_allowed=False`。

(Q_A) 是从 A1–A3 质量信号构造的描述性复合代理，可为负。它不是 B6–B8 文件自带的 `Q_score`。

## `mapped_quality()`

A16 当前为：

- direct：3；
- near_direct：3；
- inferred：11。

`inferred` 不填数值。即使是 `direct`，也只表示名称/域映射直接，不代表 A 与 B 的质量总体已经数值标定。

## `relative_effect()`

输入必须包含恰好 17 个命名配比域，全部非负，且和为 (1pm10^{-6})。函数不做静默归一化。

定义：

[
m_k(mathbf p)
=
sum_jhateta_{k,j}
(p_j-p_{{m ref},j}).
]

返回字段包括：

```text
delta_target_loss_1m
reference = A4_mean_normalized_composition
loss_coordinate = A4_A5_1M_target_cross_entropy_contrast
cross_scale_transfer = not_identified_from_attachment_A
bridge_to_B1_val_loss = unidentified
direct_B1_addition_allowed = false
```

### v1.2 明确禁止的调用

旧版本曾允许：

```python
q1.relative_effect(p, target, n_params=..., eta=...)
```

v1.2 已删除这种接口。原因不是 API 风格变化，而是附件 A 不足以识别连续的 (N,D)-dependent 配比幅度。

如果 downstream 需要某种跨规模配比情景，必须在 downstream 自己的接口中显式给出：

- 数学形式；
- 参数来源；
- Loss 坐标；
- 是否 `validated`；
- 有效范围。

不能再把 Q1 历史 `eta` 作为默认科学参数。

## `ranking_validation()`

对冻结的 A4+A5 1M Ridge 返回：

- A6+A7：`test_1m_spearman`；
- A8+A9：`test_60m_spearman`；
- A10+A11：`test_1B_spearman`；
- A12+A13：`est_10B_spearman`；
- A14+A15：`est_70B_spearman`。

其中前三组是真实检验组；10B/70B 是 estimated/extrapolated 压力测试。

例如 Pile-CC：

```text
1M  = 0.9007345788509955
60M = 0.8918996051728083
1B  = 0.8875915750915748
```

这些值说明排序迁移，不说明绝对 Loss 尺度已校准。

## cyj 的消费边界

cyj 可直接使用：

- A 侧质量域排序/区间作为描述性证据；
- A16 mapping type；
- 13-target (m_k(mathbf p)) 做配比敏感性；
- held-out Spearman 选择/比较 target 的排序稳定性。

cyj 不能直接使用：

- (Q_A) 数值作为 B-native `Q_score`；
- (m_k(mathbf p)) 作为 B1 Loss 的单位系数修正；
- 历史 `eta` 作为 Q2/Q3 的默认跨规模参数。

B1 Loss anchor、B-native Q、A→B Loss bridge 以及任何 (N,D)-dependent 配比幅度，均由 cyj 的 B 侧接口负责识别和验证。

## 版本说明

`chm.q1.v1.2` 没有重算 A1/A4 的科学数值；它修订的是**接口能声称什么**。底层 Q、Ridge 系数、参考配比和 validation 表不变；自动尺度传递被删除。