# CYJ 预测不确定性范围审查（2026-09-24）

| 层 | 现有证据 | 机器接口状态 | 可报告内容 |
|---|---|---|---|
| U1 参数估计 | B1 8 组 bootstrap；B7 50 次 N/D 组 bootstrap，均固定已选模型 | B7 `conditional_mean_interval` 有值 | 仅半合成 B7 固定 constant-G 家族条件均值波动；不能叫总预测区间 |
| U2 模型形式 | B7 no-Q/恒定 G/交互候选的同源探索性比较；发明时已看全部 B7 | `model_form_uncertainty=not_quantified` | 报告候选间分数、参数和梯度差；无校准数值区间 |
| U3 样本/残差 | B1 残差极低且生成来源未明；B7 半合成构造噪声机制未证 | `prediction_interval=null` | 不填虚构残差噪声或观测区间 |
| U4 跨来源桥接 | A target↔B Loss、Q_A↔Q_score、B1↔B7 Loss 均无同口径成对样本 | `cross_source_uncertainty=null` | 保持 unidentified；不以宽区间假装可识别 |
| U5 Benchmark 桥接 | zhh 负责，CYJ 未消费同坐标 validated bridge | `benchmark_bridge_uncertainty=null` | Q4 需另行验证并传播 |

`src/cyj/chm_adapter_v2.py` 的 `capabilities.uncertainty_policy` 与 `evaluate.uncertainty.components` 将这些边界编码为机器字段；旧 `cyj.q3.v1` 已 deprecated。B7 50 条条件样本及原 fit SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`。新比较输出 SHA256 `1d28169ce10f5bc274a82037320fdf003f7e3d2148eff2be91d3c3618708925b`，仅用于模型形式敏感性。任何 Q3/Q4 论文区间必须列明覆盖层；当前 U2–U5 缺证，`ready_for_Q3=false`。
