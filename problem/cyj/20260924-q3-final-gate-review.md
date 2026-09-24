# CYJ Q3 理论接口前置验收（2026-09-24）

## 范围

本地 `team/cyj-scaling` 的 `cyj.chm.v2` 诊断接口、B1/B7/来源审计和 CHM 发布交接。精确发布身份须以后续最新 release handoff 与远端 `ls-remote` 记录为准；本审查不代替 CHM 在其工作分支真实 pull/求解验收，也不审查 zhh 的 Benchmark 桥接原件。

| 正式 Q3 gate | 当前证据 | 结果 |
|---|---|---|
| N/D predictor 在声明范围验证 | B1 同源近乎精确重构但 Loss 来源不明；B7 半合成且模型发明已用全 B7 | diagnostic only |
| Q 与所用 Loss 同坐标 | B7 原生 Q_score 与 B7 Loss 同表；B1 与 B7 Loss 未证同坐标 | B7 diagnostic only |
| p policy | chm v1.2 13-target 1M contrast；v2 `sensitivity_only`，不加到 B7 Loss | policy valid, joint effect unidentified |
| 无 legacy eta / 未验证 lambda | v2 读取 chm q1.v1.2 精确 blob，拒绝 eta 输入；无 lambda | pass |
| 支持域、单位、梯度、成本 | v2 B7 N/D/Q 边界、解析梯度、三成本、预算残差与样例可调用 | software pass |
| 不确定性字段 | U1 固定模型条件区间；U2/U3 未量化，U4/U5 null | total interval absent |
| CHM 真实消费 | CYJ 本地 smoke PASS；CHM 本人分支 pull/调用/求解器验收尚未记录 | pending |

## 数学与实现边界

B7 旧 constant-G 基线梯度 `(-\alpha A N^{-\alpha-1},-\beta B D^{-\beta-1},-G)` 与 v2 实现及三维差分测试一致。N/D 单位各为 10^9，成本 FLOPs。Q=Q0 的成本使用单侧导数。p 输出仅 A 侧目标向量，不进入 B7 Loss，避免重复标度与无来源 Loss 变换。B7 矩形内未观测组合仍属插值假设，支持域外默认拒绝。JSON 入口拒绝重复键、字符串数值、非有限输入、缺字段和 formal 模式。

反事实地只看数据：B7 可给同源 N/D/Q 经验条件面，A4/A5 可给 1M 目标配比差；没有共同 Loss 的 N/D/Q/p 表，也没有将 B7 性能转到真实训练和 Benchmark 的成对证据。因此任何正式四维目标、跨来源参数区间或最优配比都是超出证据的主张。旧 v1 eta bundle 明示 deprecated，不能因存在可运行代码而恢复。

## 判断与下一步

**NOT READY**，`ready_for_Q3=false`。诊断/敏感性接口工程上可由 CHM 拉取，科学上不发布正式 Q3 最优 N/D/Q/p，也不发布 Q4 能力换算。CHM 必须在精确 release commit 上运行 smoke 并记录 handoff；cyj 需要 B7 同口径独立验证、B1/B8 来源与总预测不确定性证据，无法取得则持续降级；zhh 负责独立 Benchmark 桥接；集成人验收双方记录后更新公共状态。
