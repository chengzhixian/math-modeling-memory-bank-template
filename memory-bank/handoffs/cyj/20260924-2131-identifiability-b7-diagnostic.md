# CYJ Handoff：联合可识别性与 B7 质量斜率

## Task

完成任务清单 Task 2 的联合结构审查及 Task 3 的 B7 组内 Q 诊断。Task 1 的 v2 工程迁移已本地完成并通过测试；CHM 侧真实 pull/消费与远端发布仍待执行，不能写成接口最终验收完成。

## Input

- branch/base：`team/cyj-scaling@ad1d312c15bcf79c23d715dd199eec7c2e65a0af`；本地 `origin/main@af4857045e5df62afc9815bce4b98dbbb8867253`。两次 fetch 因 GitHub 连接失败，远端最新状态未核。
- producer：chm v1.2 `a5525935b37f873235d2f650e4810a787b9a8788`。
- B7 输入 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`；B7 fit SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`。

## Changes

- `problem/cyj/20260924-q2-q3-identifiability-review.md`：Requirement→Data、变量来源、识别、角色、泄漏/支持域、模型与代码、claim ladder、red-team 和分支门槛。
- `src/cyj/diagnose_b7_quality_interaction.py` 与 `outputs/cyj/diagnostics/b7_quality_interaction.json`；实验记录见 `experiments/cyj/20260924-b7-quality-interaction-diagnostic.md`。

## Commands / Tests

上述脚本命令实际运行成功，输出 SHA256 `7977a3ed0614e896e82c316d770b9bb50a3195e4f5e790541ebee6005dc99f50`。CYJ 全部单测 `44/44 PASS`，`0 FAIL`，命令见 v2 交接。未运行 CHM 的实际分支消费测试。

## Results / Claim Level

45 组、450 点；组内 Q 斜率范围 `[-0.60721818,-0.19307879]`，相对恒定 `-G` 的组斜率 RMSE `0.10780881`。`log N + log D` 描述回归 R² `0.86014`。最高 L1 描述；B7 半合成，不推因果或真实外推。

## Identifiability / Ready State

完整 `L(N,D,Q,p)`：`not_identified`。B1/B7 各自条件模型为 `conditionally_identified`；A↔B Q、A target↔B Loss、旧 eta 为 `not_identified`。`ready_for_Q3=false`，`ready_for_Q4=false`。

## Limitations / Next

cyj：先写 B7 少量交互候选比较 protocol，再执行分组验证；追溯 B1 Loss 生成/评估口径并核 B4/B5、B8。CHM：在精确 CYJ 发布提交可拉取后运行真实 consumer smoke test，并让求解器读取 B7 `model.bounds`。集成人：验收后更新公共记忆。GitHub 连通性恢复后优先 fetch、提交、push、ls-remote 核对；当前未宣称远程备份成功。
