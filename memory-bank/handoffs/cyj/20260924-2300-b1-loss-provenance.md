# CYJ Handoff：Task 5 B1 Loss 来源

## Task / Input

追溯 B1 `run_id,steps,N,D,C,val_loss,ppl` 与 B12 索引、官方 Pythia 背景。B1 原件 SHA256 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`；既有 fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。分支 `team/cyj-scaling`，本轮起点 `ac51e32`；精确完成提交以后续 Git 记录为准。

## Changes / Commands / Tests

新增 `src/cyj/audit_b1_loss_provenance.py`、`outputs/cyj/diagnostics/b1_loss_provenance.json`、`problem/cyj/20260924-b1-loss-provenance.md`、对应实验记录。实际运行命令见实验记录，输出 SHA256 `a36bff5075da6911b90b6d2c50ad29a64586f268542fc61e0659cdec3df582da`。脚本完成源哈希、1176 行/8×147/非有限值检查，0 失败；CYJ 全量单测将在本轮收尾重跑。

## Results / Identifiability / Claim

1176 行 `D` 与 step×2,097,152 token 的舍入一致；ppl 全行与 `exp(val_loss)` 显示舍入相容；147 个 B1 step 均出现于 B12 step 集合。B1 Loss 真正生成/评估机制及 tokenizer、语料、聚合仍 **unknown**，整体 `partially_verified`。只允许 L1 同源近乎精确重构，不声称外部预测。

## Interface / Ready / Next

不改变 v2 接口参数；B1/B7 不自动同 Loss 坐标，`ready_for_Q3=false`、`ready_for_Q4=false`。若取得原始逐 checkpoint 评估日志，cyj 需按模型/step/未舍入 Loss 逐行比对；否则维持来源未知。集成人/CHM 不应把 B1 低 RMSE 升格为真实外部验证。
