# Q1 第三小问与 CYJ 导出包所有者复核（验收候选）

日期：2026-09-25；分支：`integration/chm-q1-clean-20260923`；基线：`2450971`。用户要求先完成 Q1 整改并交其验收，验收后才进入正式模型。因此本次不修改 `chm.q1.v1.3`，不启动正式 Q3 重算。

## 变更与证据

- 从 cyj `team/cyj-scaling@86526a1` 取回两个明确位于 `src/chm`、`outputs/chm/q1_exports` 的 Q1 派生导出，并在 chm 原始 A4/A5 实体环境复跑。`q1_q2_bundle_v1` manifest 与 cyj 完全同 SHA `b0dda7ca...`。`q1_interaction_bundle_v1` 四个实质文件 SHA 与 cyj 完全相同；manifest 仅因 NumPy 2.3.5/2.5.3 环境字段不同而变。所有者审计见 `src/chm/audit_cyj_q1_exports.py`，512 行归一化最大差 `2.22e-16`，13 目标 CV 最大差 `3.33e-16`。
- 两包的原始 A4/A5 哈希与 chm 冻结审计一致，五表身份与 `chm.q1.v1.3@cdda1ad` 一致，交互定义与 `2450971` 一致。但导出包 `qa_mapping.json` 对 arxiv/github 使用扩展集 `Q_A`，而主接口 `Q1Interface.quality()` 使用 A1 sample。已在 `src/chm/q1_third_part_review.py` 明确分为主口径与扩展敏感性，并计算受影响的两种质量约束政策；结果在 `outputs/chm/q1_third_part_review/review_manifest.json`。机器可读修订候选为 `qa_mapping_primary_candidate.json`，17 域主值/sample、extended 敏感性与未知域 null 均明确。故**数值身份通过，质量政策语义尚须更正版本后才能无条件签收整个 v1 包**。
- Q1 17 域质量覆盖实现与测试 `src/chm/q1_quality_coverage.py`、`test_q1_quality_coverage.py` 已本机运行；3 direct、3 near-direct、11 inferred，未知域不填零或假分数。原先未跟踪的相关文件在本次检查点纳入 chm 范围。
- 第三小问论文 `paper/latex/sections/chm/q1.tex` 已补 512 已观测配方上的多目标情景、质量覆盖、A10 凸包外 47/64、交互候选局限和正式 Ridge 版本边界。24 页验收 PDF 编译，引用/字形/溢出门禁通过；`paper/sections/chm/q1_third_part_acceptance_candidate.md` 为用户审阅短稿。

## 模型决定（待用户验收）

建议继续以 13 目标 1M Ridge `chm.q1.v1.3` 为正式主模型，完整交互系数仅作为 A 侧模型形式敏感性。候选在三真实检验组对 11/13、13/13、13/13 个目标降低 RMSE，但 1B 仅 11/13 优于常数基线；47/64 配方处于 A4 凸包外。二阶系数无因果协同或 B7 可传递含义。修正后的 Q1 质量政策应发布不可变新导出版本并让 cyj 重跑质量约束结果；用户验收前不改正式接口。

## 复现与未解决

本机命令：`H:\研究生数模\math-modeling-memory-bank-template\.venv\Scripts\python.exe -B src/chm/export_q1_q2_bundle.py`、`... export_q1_interaction_bundle.py`、`... audit_cyj_q1_exports.py`、`... q1_third_part_review.py`、`... -m unittest discover -s src/chm -p 'test_q1*.py'`；25 项 Q1 测试通过。论文：`./src/chm/build_paper.ps1 -OutputName chm-q1-third-part-review-20260925`，本机 MiKTeX 需获沙箱运行权限。

下一步负责人：用户/参赛者验收 Q1 主模型与质量主口径；chm 据结论发布不可变 Q1 版本并交 cyj；cyj 重跑受影响的 Q2 质量约束场景并固定消费 SHA；chm 此后验收 v6 Q3 消费、更新第三问论文与复现。正式 `ready_for_Q3=false` 不因本次工程复现而改变。
