# Q2→Q3 当前消费状态（2026-09-26）

Q2 v8 的数值生产与其冻结输出不重算。`acceptance.json` 中 `q3_consumer_verified_by_CHM=false`、`q3_v8_consumer_sample.json` 中 `CHM_owner_consumption_verified=false`、`requirement_evidence.csv` 中的 `owner_acceptance_pending` 记录的是 **Q2 生产者发布时** 的下游状态，不能作为当前 main 的验收结论。

当前 main 的 Q3 已消费 v8 并发布固定配方、87 个已观测配方联立、独立 B7 原生质量三种 36 格结果。`outputs/Q3/independent_grid_audit.json` 对三模式分别给出 36 格，发布与独立复核可行格数分别相同（30、33、33），`mismatches` 均为空；`outputs/Q3/ANSWER.md` 记录消费者的条件发布与 CYJ 后续验收。18 个 v8 冻结请求样例可由 `src/cyj/verify_v8_fixtures.py` 重放。

此处的“验收”只表示接口、数值和给定模型内的配置求解得到复核，不表示 A/B 质量与 Loss 坐标已实证标定。保持上游冻结产物和 manifest 原字节，避免将发布时快照误改成追溯性的伪记录。
