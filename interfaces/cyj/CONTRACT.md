# cyj 交付约定 v1.8（生产者草案）

角色：cyj 负责 Q2 标度律与 Q3 理论；chm/zhh 消费。当前 `ready_for_Q3=false`，未获联合验收或 main 集成。可调用接口、公式、字段、单位、成本与约束详见 [Q3_API.md](Q3_API.md)，此处只保留当前入口与证据索引。

## 本版接口

- `src/cyj/q3_interface.py::Predictor`，机器包 `outputs/cyj/interfaces/q3_bundle.json`（`cyj.q3.v1`），SHA256 `a153cbb6a45925317dcae1727d50bd0b20e2ec6b85767981b4d8a689b5144332`。
- 上游固定为 `integration/chm-q1-clean-20260923@7c14a0c894072048d09f04bd03653be1301f7257` 的 `chm.q1.v1`；采用其原生读取器、六文件清单、17 维顺序、参考 p、五 target 面板及不确定性分类。Git/LF 与生产者/CRLF 的精确哈希恢复见 Q3_API 与 bundle provenance。
- 预测支持 B1 N-D `diagnostic` 及显式 p/target/lambda/eta `scenario`；默认 formal 报错。Q_score 性能项尚未拟合，有值时报错；A-native Q_z 只作相对排序，mapping unidentified。
- `src/cyj/q3_costs.py` 提供题面三成本族、FLOPs 单位换算、Q0 单侧导数和约束残差。C7 为 zhh 发布外生候选，未因本次消费自动成为联合 validated。
- 代码/输入版本 `6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`；真实 B1 示例请求在 `outputs/cyj/interfaces/b1_example_request.json`。26 项测试通过，具体命令与验收边界见 Q3_API。

## 当前结果与复现入口

| 结果 | 文件/复现记录 | 已验证范围 |
|---|---|---|
| 附件 B 身份和字段审计 | `outputs/cyj/b_data_audit.json`；`experiments/cyj/20260924-b-data-audit-stage1.md` | 19 CSV，155 pass/5 warning/0 fail |
| B1 经典 N-D 基线 | `outputs/cyj/classic/classic_fit.json`；`experiments/cyj/20260924-classic-baseline.md` | 全样本 RMSE 0.0001465764；LOSO 均值 0.0001461277；token-tail 0.0001160041 |
| C 显示舍入与八行敏感性 | `outputs/cyj/diagnostics/b1_precision_sensitivity.json`；同名实验记录 | 显示 C 与四位小数舍入一致；剔除八行最大预测变化 7.6652e-06 |
| B2/B3 轨迹形状 | `outputs/cyj/diagnostics/b2_b3_shapes.json`；`experiments/cyj/20260924-b2-b3-shape-diagnostic.md` | 半合成/插值形状，不是独立验证 |
| B1 组级 bootstrap | `outputs/cyj/diagnostics/b1_group_bootstrap.json`；`experiments/cyj/20260924-b1-group-bootstrap.md` | 78/80 收敛未触边；只覆盖固定 B1 经典模型条件波动 |
| B1 E/N/D 消融 | `outputs/cyj/ablation/b1_terms.json`；`experiments/cyj/20260924-interface-adoption-ablation.md` | 三删项×9 划分全部收敛未触边，三项均改善 B1 重构 |

基线公式为 `E+A*N_B^(-alpha)+B*D_B^(-beta)`；N/D 单位均为十亿。拟合范围 N=[0.070542,11.965825]、D=[0.134,299.893]。五参数从 JSON 读取，不重复手抄；基线 SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`，输入版本 `cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`。其他结果的完整输入/代码 SHA、数据哈希、环境、随机种子和命令见对应实验记录及 JSON。

## 尚未通过的门槛

B1 近乎精确重构的生成/预处理来源未明；tokenizer、评估语料、对数底、聚合口径未知。B4/B5 绝对 Loss 可比性为 `not_established`，已保存的外部预测只作描述；不报告跨来源统一 RMSE。B6–B8 的 Q 项、B1↔B6–B8 Loss 可比性、A↔B Q 标定、主 anchor/lambda、完整预测区间及 Loss–Benchmark 桥接仍缺证据。

B8 extrapolated 不参与拟合/独立验证；B9/B10 外推讨论尚待完成。已有分组验证、bootstrap 和消融均不能绕过这些门槛。chm 可消费接口做联调和标记清楚的情景分析，正式 Q3 配置须待后续 validated predictor；zhh 必须传播独立的 Loss–Benchmark 桥接误差。
