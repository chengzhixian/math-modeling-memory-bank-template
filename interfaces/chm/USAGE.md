# chm Q1 接口使用说明（`chm.q1.v1`）

这是 chm 定义、cyj 直接消费的 A 侧接口。唯一有效清单为 `interfaces/chm/q1_interface_v1.json`；其中列出六个现有结果文件的 SHA256 与行数，**不复制一套新数据**。读取时先校验清单；文件更新后须发布新接口版本，不能静默覆盖。

## 快速验收

在仓库根目录执行：

```powershell
python src/chm/q1_interface.py
python -m unittest discover -s src/chm -p 'test_q1_interface.py'
```

第一条成功时报告 7 个 Q 域、17 个配比域、13 个 Loss 目标及哈希校验结果。需要从当前已审核输出重建清单时，仅由 chm 执行 `python src/chm/q1_interface.py --build-manifest` 并复核 Git diff；消费者不要自行重建清单以掩盖文件变化。

## Python 调用

```python
from pathlib import Path
from src.chm.q1_interface import Q1Interface

q1 = Q1Interface(Path('.'))  # 自动验 SHA256、行数、域数与参考配比
book = q1.quality('book')
mapped = q1.mapped_quality('gutenberg_pg_19')  # near_direct；A 侧 book 代理
unknown = q1.mapped_quality('freelaw')         # inferred；quality 为 None

p = q1.reference.copy()                       # 17 维，和为 1
effect_at_reference = q1.relative_effect(p, 'pile_cc', n_params=1_000_000)
p['arxiv'] += 0.01
p['freelaw'] -= 0.01
effect = q1.relative_effect(p, 'pile_cc', n_params=60_000_000)
```

在当前 manifest 下，上例 `effect['delta_target_loss'] ≈ 0.001309803924525102`，`effect['bridge_to_B1_val_loss'] == 'unidentified'`。这是文件及公式的最小验收样例，不是推荐的最优配比。

`quality()` 返回从 A1 官方质量信号**计算**的 `Q_z` 域中位数、条件 bootstrap 95% 区间及样本数；可为负，仅描述 A1 样本，不是 B6–B8 文件自带的 `Q_score`。返回 `direct_B_predictor_input_allowed=False`，表明不得把该数值直接送入 B 侧公式。`mapped_quality()` 的 `direct` 仅名称直接对应，不保证总体相同；`near_direct` 是语义代理，需敏感性；`inferred` 不填数值。

`relative_effect()` 输入**按名称给出的 17 维非负配比**，和须在 `1±1e-6` 内；缺列、多列、负值及非法和均报错，不静默归一化。目标 `target` 必须是 13 个 A 侧验证域之一。输出 `delta_target_loss = Σ_j β_{k,j}(p_j-p_ref,j) × (N/10^6)^(-η)`，其中 `N` 为**参数个数**，默认 η 来自清单中的尺度 manifest；在参考配比处恒为 0。此量是目标域交叉熵的**相对变化**，不是绝对 Loss，也不是 B1 `val_loss`；返回 `direct_B1_addition_allowed=False`。1M、60M、1B 是已见模型规模，**60M/1B 的函数返回值仍为条件 η 情景**，其他规模另标外推；配比是否在训练支持集内尚未自动检验。1B 的配方支持集也与前两者不同。

η 默认点估计 0.14503317；两个已有 95% 区间分别为仅重抽目标域 `[0.10686793, 0.18669841]` 与目标域加校准配方行的 `[0.09756180, 0.20097672]`，均条件于固定 A4+A5 Ridge，不是完整预测区间。可通过 `eta=` 做情景扫描，但不得把 η 当成 A→B Loss 单位转换。验证与稳健性文件位置见清单、`interfaces/chm/UNCERTAINTY.md` 及 `experiments/chm/20260924-q1-ablation-and-cleanup.md`。

## cyj 的消费边界

cyj 应直接读取 B6–B8 文件自带的 `Q_score` 来拟合 B 侧质量项，并记录三文件的半合成/外推分层；可将 `quality()` 用于 A 侧域相对排序与情景标签，将 `relative_effect()` 用于逐 target 的配比敏感性。**B1 Loss anchor、跨 Loss 系数和最终预测器由 cyj 定义**，要求清单见 `interfaces/chm/CYJ_REQUIRED_INTERFACE.md`。在 cyj 的模型把这些量定义并验收前，不能把本接口返回值直接加到 B1 Loss 或产出正式 Q3 最优配置。消费记录须写入实际分支、完整 Git SHA、接口版本、清单 SHA、使用 target 与 eta 情景。
