# CYJ 交接：B7 固定族验证与经验区间（2026-09-25）

## 本次变更

新增 `src/cyj/validate_b7_frozen_model.py`、`src/cyj/build_b7_frozen_uncertainty.py`、对应两份机器结果及 `test_b7_frozen_evidence.py`。固定双交互族的 24 折 N/D/Q 留级验证、1350 条 OOF 残差、500 次 N-D 簇 bootstrap 与经验预测分位区间可由脚本重建。未改变旧 `cyj.chm.v2` 语义，也未开启正式 Q3 gate。

## 证据／复现

详情与数值见 `experiments/cyj/20260925-b7-frozen-validation-uncertainty.md`。两份输出 SHA256 分别为 `cae1c827587c49d6484d2fcdb7686f9202f522aacdb39d5f63f74085d422491d`、`54c2ceb24472aa1bc53f3207d0064529545fa37385f6f5845114b88657121608`。`python -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q` 实测 48/48 PASS。

## 未解决问题与下一步

候选族在全 B7 诊断后选定，重复固定族验证不构成未触碰的独立最终测试；经验区间未独立校准，B7 为半合成。`ready_for_Q3=false`；跨来源和 Benchmark 总区间仍未识别。cyj 下一步做 CHM 当前求解器的实际消费测试、v3 条件接口、论文对应表述和分支合并检查；chm 负责本人分支 consumer acceptance；集成人负责验收后公共记忆更新。
