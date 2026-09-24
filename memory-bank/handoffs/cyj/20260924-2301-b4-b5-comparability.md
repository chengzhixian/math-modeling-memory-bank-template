# CYJ Handoff：Task 6 B4/B5 可比性

## Task / Input / Changes

B1/B4/B5 原件 SHA256 分别为 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2` / `2272983ded93de35e05f9acbf95ebceedf43f283345e4be72b54fee94080391e` / `dd858c5e48610e28589340d5db023d6abfb31df597506789ccdfc6a546731bbd`。新增可复现脚本、JSON、问题审查及实验记录，路径见 `problem/cyj/20260924-b4-b5-loss-comparability.md`。本轮起点 `ac51e32`，完成提交以后续 Git 记录为准。

## Commands / Tests / Results

实际运行命令见 `experiments/cyj/20260924-b4-b5-comparability.md`；输出 SHA256 `28c3efa18b2acdd417e2a2f31d5163ead256ed07eabe7f9bf5fdd077611f79e1`，源哈希/非有限值校验通过。B4 57 行中 8 行落 B1 N/D 矩形内，B5 44 行中 8 行在内；其余分别 49/36 行越界。tokenizer、语料、Loss 定义、log base、聚合和 checkpoint 同一性均未证。

## Identifiability / Claim / Interface

`same_loss_coordinate=not_established`，`descriptive_only=true`；最高 L1 来源分层描述，正式 external RMSE 不允许。现有 B1 预测器与 v2 B7 接口不改，`ready_for_Q3=false`。若未来取得同口径证据，应先限定真正同 Loss 子集与支持域，再独立评估。负责人 cyj；集成人不要池化跨源误差。
