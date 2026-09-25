# cyj 交付约定 v1.13（joint B7 条件交付）

**2026-09-25 v5 增补：**[NDQP_SCENARIO_V5.md](NDQP_SCENARIO_V5.md) 是独立的 `cyj.ndqp.scenario.v5` 四变量条件情景入口，固定 CHM `chm.q1.v1.3@cdda1ad62c5c7eb72b413c4228caeff87d2bad30`。`lambda`、`eta`、权重均由调用者明确给出，A/B Loss 桥接与质量映射未识别；默认 `ready_for_Q3=false`。它不取代下述 B7 原生 `cyj.chm.v4`，也不将情景预测当作正式四维经验律。CHM 已签收 v4 条件数值消费；v5 配比扩展仍待本人验收。精确发布见 `memory-bank/handoffs/cyj/20260925-1401-v5-release-review.md`。

**状态更正：**下文旧段落中的“CHM 本人消费验收仍待”是 v4 发布当时的状态；CHM 后续在本人分支 `memory-bank/handoffs/chm/20260925-cyj-v4-owner-acceptance.md` 完成条件 NDQ 签收。该签收不包含 v5。

角色：cyj 负责 Q2 标度律与 Q3 理论；chm/zhh 消费。当前 `ready_for_Q3=false`，未获联合验收或 main 集成。可调用接口、公式、字段、单位、成本与约束详见 [Q3_API.md](Q3_API.md)，此处只保留当前入口与证据索引。

**当前 chm 条件候选入口：**[CHM_API_V4.md](CHM_API_V4.md)，`src/cyj/chm_adapter_v4.py::CHMAdapterV4(mode="conditional_diagnostic")`，本地精确发布 `3471530d91c8ee7eb709e5cd6c824eb9c423e0df`，manifest SHA256 `dcd50430b88cc754e1d8f43a3890013bcc45b07f877b315e9a812d2978fd41f7`。本版是 B7 八参数联合拟合、嵌套 N/D/Q 留级、200 次簇 bootstrap 的独立条件候选；N/D/Q 值与梯度、弹性、替代率、同源经验区间可调用。10 个上下文中 7 个为 CYJ 外生敏感性，机器字段明确标记。A 侧仍是 Q1 v1.2 13-target `p_policy=sensitivity_only`，不加进 B Loss。60/60 本人测试与 v4 精确 Git 对象 3 请求 consumer smoke 通过；CYJ 用 CHM pinned `92e0592` 求解器独立完成 330 个条件场景。B7 半合成、区间方法差异、函数族历史探索和 A/B 桥接缺失使 `ready_for_Q3=false`；CHM 后续已签收 v4 条件数值消费。远端发布状态需以实际 `ls-remote` 核验。

**历史 v3 发布：**[CHM_API_V3.md](CHM_API_V3.md) 与 `e36aa23143bda9f027853f5af825728625750c5b` 保留旧两阶段参数的精确复现。该发布的 51 项测试和 27 场景联调只对应 v3，不应替代 joint v4 数值，也不因 v4 发布而提升为正式准入。

旧 [CHM_API_V2.md](CHM_API_V2.md) 与 `cyj.q3.v1` 只保留历史诊断复现，`deprecated_for_formal_Q3=true`；不得以旧接口的 fixed constant-G 参数或缺失总预测区间替代 v4，也不得把任一条件状态提升为正式准入。

旧 `cyj.q3.v1`：`deprecated=true`，`historical_only=true`，`formal_use_allowed=false`；当前条件机器入口为 `outputs/cyj/interfaces/chm_v4_manifest.json`，不消费旧 `q3_bundle.json`。

**2026-09-24 接口审查结论：** `cyj.q3.v1` 的 B1 `diagnostic` 仍可作旧版软件复现；其 p/eta `scenario` 固定 chm `q1.v1` 的历史跨规模接口，已与 chm 当前推荐的 `q1.v1.2` 科学合同不兼容。chm v1.2 明确撤回附件 A 对连续跨规模 eta 的识别，旧 bundle 中的 `eta_producer_estimate` 和条件区间只能作历史审计，不能用于正式 Q2/Q3。新版 v2 已替代旧接口用于诊断性联调，但完整联合预测器仍不可识别。详细证据和升级门槛见 `problem/cyj/20260924-current-interface-review.md`、`problem/cyj/20260924-q2-q3-identifiability-review.md` 和 `problem/cyj/20260924-q3-final-gate-review.md`。

**新增来源审查：** B1 Loss 生成/评估口径仍未知；B4/B5 与 B1 的同一 Loss 坐标未建立；B7 的 Q 交互比较只达半合成同源探索；B8 与 B7 在共有 NDQ 坐标上冲突，保持隔离。v2 条件均值区间不等于总预测区间，`prediction_interval=null`。证据分别见 `problem/cyj/20260924-{b1-loss-provenance,b4-b5-loss-comparability,b8-conflict-source,uncertainty-scope}.md`，机器结果见 `outputs/cyj/`。B9/B10 仅外推压力参考。正式门槛为 `NOT READY`。

## 旧版 API 与独立 B7 诊断入口（以下历史数值/测试数只对应旧发布）

- 新增独立 `cyj.b7_quality.v1`：`src/cyj/quality_scaling.py::QualityPredictor`，详见 [QUALITY_API.md](QUALITY_API.md)。已拟合去重 B7 原生 N-D-Q，返回梯度及 50 个同编号条件 Loss 样本；不接 p，不接 B1/Benchmark，不改变既有 B1/p API 的 Q 拒绝规则。参数文件 SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`。

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
| B6–B8 条件趋势/重复坐标 | `outputs/cyj/diagnostics/b_quality_audit.json`；`experiments/cyj/20260924-b8-quality-audit.md` | B6 全部 360 行重复于 B7；B7/B8 224 个同坐标 Loss 全异；Q 端点方向反转 |
| B7 原生 Q 候选/消融 | `outputs/cyj/quality/b7_quality_fit.json`；`experiments/cyj/20260924-b7-quality-results.md` | 三族×24 折均收敛未触边，选线性 Q；50/50 组 bootstrap 接受，仅半合成条件层 |
| B9/B10 外推证据 | `outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json`；`experiments/cyj/20260924-b9-b10-extrapolation-audit.md` | B10 128 行均与 B9 对应、均超出 B1 N 范围；Loss 为估算，非独立验证 |

基线公式为 `E+A*N_B^(-alpha)+B*D_B^(-beta)`；N/D 单位均为十亿。拟合范围 N=[0.070542,11.965825]、D=[0.134,299.893]。五参数从 JSON 读取，不重复手抄；基线 SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`，输入版本 `cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`。其他结果的完整输入/代码 SHA、数据哈希、环境、随机种子和命令见对应实验记录及 JSON。

## 尚未通过的门槛

B1 近乎精确重构的生成/预处理来源未明；tokenizer、评估语料、对数底、聚合口径未知。B4/B5 绝对 Loss 可比性为 `not_established`，已保存的外部预测只作描述；不报告跨来源统一 RMSE。B7 Q 项已有独立原生诊断模型，但 B1↔B7 Loss 可比性、A↔B Q 标定、主 anchor/lambda、完整预测区间及 Loss–Benchmark 桥接仍缺证据。

B8 calibrated 也暂不进入 B6/B7 共同质量拟合：90/90 固定 N,D 组的 Q 端点 Loss 上升，B6/B7 则分别 45/45 下降；原因未明，不反转 Q、不修改原始文件。B8 extrapolated 不参与拟合/独立验证；B6/B7 必须按 N,D,Q 去重（合并后仅 450 个坐标），不能互作独立验证。旧审计的 `fit_eligible_count=984` 仅按 calibrated 标签计数，不代表科学准入；当前以本版限制为准。

B9/B10 已完成数据角色与重叠审计，真实外推有效性仍未验证。已有分组验证、bootstrap 和消融均不能绕过这些门槛。chm 可消费 B1/B7 diagnostic 做联调；旧 p/eta scenario 只用于历史复现，正式 Q3 配置须待后续 validated predictor；zhh 必须传播独立的 Loss–Benchmark 桥接误差。机器可读使用策略在质量审计 JSON 的 `usage_policy`，B1/p 预测器 schema 和数值未变；当前总测试 37 项通过，软件通过不代表科学门槛通过。
