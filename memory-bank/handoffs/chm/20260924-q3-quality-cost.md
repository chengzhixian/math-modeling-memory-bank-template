# chm 阶段交接：Q3 质量成本函数敏感性

日期：2026-09-24（北京时间）

## 完成

在不使用未验证 Q 性能收益的前提下，对题面三种质量成本族完成解析成本比较：

- exp/power 凸，log 凹；
- 识别 Q0 的正部函数 kink 和单侧导数；
- 推导 C_Q/C_train、C_Q/C_attn 两个与 D 无关的比例；
- 用 Q0=0.5 的接口示例给出增量成本交叉与成本同量级 N 阈值；
- 明确这些结果只用于成本侧敏感性，不产出最优 Q。

输出：
- `src/chm/q3_quality_cost_sensitivity.py`
- `outputs/chm/q3_quality_cost_sensitivity_q0_0p5.csv`
- `outputs/chm/q3_quality_cost_crossings_q0_0p5.json`
- `experiments/chm/20260924-q3-quality-cost-sensitivity.md`

## 下一步

等待 cyj B-native Q 性能接口后，把 (-L_Q/C_Q') 接入统一 KKT；在此之前继续推进不依赖 Q 性能的 solver 稳健性和 p 支持域分析。
