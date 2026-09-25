> 历史验收稿：2026-09-25 用户已授权将交互模型升为主模型；当前口径见 interfaces/chm/Q1_V2_DOWNSTREAM.md。本文件保留 v1.3 候选阶段的证据，不再表示当前主模型。

# 问题一第三小问整改验收稿（2026-09-25）

状态：**待 chm/参赛者验收；不改变 `chm.q1.v1.3` 正式机器接口。** 论文 LaTeX 的第三小问已补充本稿结论；按用户最新要求，新增论文 PDF 暂缓生成。先前 `chm-q1-third-part-review-20260925.pdf` 保留为上一检查点。

## 1. 对 cyj 两个 Q1 派生包的所有者核验

- `q1_q2_bundle_v1`：源 A4 SHA256 `04a32ef4...`，A5 SHA256 `49a959aa...`；512 行 index 与 A5 顺序一致，17 域顺序与 v1.3 参考配方一致。逐行除以原始行和后，与包内配方的最大绝对差 `2.22e-16`。质量、映射、系数、参考与验证五表的规范化字节哈希均与冻结 `cdda1ad` 的 v1.3 manifest 一致。重新运行导出器所得 manifest SHA256 `b0dda7caac30513c0f37e74ccb143064606847fdc35fd7607c999ac2f8647ecb`，与 cyj 发布一致。
- `q1_interaction_bundle_v1`：A4/A5 原始哈希一致；五个域仅按 A4 归一化配方方差选取，10 个配对、13 个目标、五折不打乱与 chm `2450971` 已发布候选定义一致。重新运行导出器后四个实质输出文件的 SHA256 均与 cyj 发布一致；13 个 CV RMSE 与原审计最大差 `3.33e-16`。本机 NumPy 2.3.5、cyj 发布时 2.5.3，故包含环境版本字段的 interaction manifest 字节哈希不同；系数、折稳定性、特征定义与 CV 四文件完全一致。源包仍为 **候选敏感性**，不是 v1.3 替代。
- 发现质量口径差异：cyj `qa_mapping.json` 对 arxiv/github 使用 A2/A3 extended 的 `Q_A`（`2.725253/-0.505485`），而 v1.3 主接口 `Q1Interface.quality()` 取 A1 sample（`2.688694/-0.485351`）。两组均有来源标记，但质量约束政策不能称为与 v1.3 主口径完全一致。以同一 512 配方、同一冻结 Ridge 参考 Loss 为分母重算，direct 条件下主/扩展相对目标值分别 `-0.118193990/-0.118192535`，direct+near 为 `-0.113929292/-0.113892859`，最优凸组合权重也变化。应将 sample 设为主口径，extended 单列敏感性，并让 cyj 重算受影响的质量约束情景；原 v1 包保留不可变复现。

核验程序：`src/chm/audit_cyj_q1_exports.py`；复现输入及完整结果：`outputs/chm/q1_third_part_review/review_manifest.json`。可供验收后发布新导出版本的 17 域主口径候选文件为 `outputs/chm/q1_third_part_review/qa_mapping_primary_candidate.json`，它逐域保留 A1 sample 主值、A2/A3 extended 敏感性值和未知域 null，并在 review manifest 中固定 SHA；当前标记 `USER_REVIEW_REQUIRED_NOT_FORMAL_INTERFACE`。两个 cyj 包的科学来源未使用历史隐藏 PDF 或作废模型。

## 2. 第三小问主模型建议

**补充检验后的建议：将交互模型作为 Q1 支持域内的优先预测候选，保留 Ridge 为透明基线；用户验收前正式接口仍为 Ridge `v1.3`。** 在严格 A4+A5 训练内部嵌套五折中，交互对 13/13 目标的外层 RMSE 均低于 Ridge 和常数；真实 1B 检验按 A4 凸包内 17、外 47 条拆分，两组各有 13/13 目标 RMSE 下降。但 1B 绝对 RMSE 仍有 2/13 未优于常数基线，完整 1B 组排序仅 7/13 目标高于 Ridge，且模型形式曾被团队结合检验观察。二阶系数只能解释为给定组成基底和 1M 数据上的拟合关联，不能宣称因果协同、跨尺度法则或 B7 性能效应。逐目标同条件表与训练内嵌套结果见 `experiments/chm/20260925-q1-third-part-model-comparison.md`。

等权相对、最坏目标相对、arxiv 单域三个显式偏好下，Ridge 在已观测 512 配方分别选 index `136/163/300`，交互候选选 `136/477/3`。在 214 组权重中，两模型无质量约束的选方一致率约 77.1%，加 direct 约 52.6%，加 direct+near 约 63.6%；故不报一个唯一全局最优。index 136 的 17 域配方中 56.86% 权重落在 11 个没有数值 `Q_A` 的 inferred 域；只报告已映射覆盖，不填补全局质量。数据和决策权重见 review manifest 与 selection stability manifest。本文不把 1M 对比幅度外推到 60M/1B 或 B 侧 Loss。

## 3. 验收后版本关系

验收前：`chm.q1.v1.3` 仍是唯一正式 Q1 配比生产者；cyj v6/Q2 使用 v1.3 Ridge 派生包与显式条件桥接；交互包只作 Q2 敏感性；Q3 已验收的 v4 条件数值不追溯改写。`ready_for_Q3=false` 仍成立。

修正质量主口径后的 Q2 条件工程情景已在 chm 侧独立复算：原 cyj 两个政策的 Loss 均在 `1e-9` 内复现，改为 A1 sample 后 direct/direct+near 条件 Loss 分别由 `2.263949598560/2.274988571899` 变为 `2.263945861618/2.274895033444`；最优顶点集合未变，但混合权重改变。机器输出见 `outputs/chm/q2_mapping_sensitivity_v1/`。这不是 cyj 正式发布，`ready_for_Q3=false`。

若参赛者认可交互成为 Q1 正式主模型：发布新的不可变 Q1 接口，要求 cyj 对 Q2 配比效应及受影响质量约束情景重跑并固定消费 manifest SHA，随后 chm 验收新版 Q3 消费、更新第三问论文和复现。若选择维持 Ridge 主模型：仍需发布**仅修正 Q1 导出/质量映射口径**的新版本并由 cyj 重跑两项质量政策。两种路径均保留旧包不可变，不能将旧 v6 标为新版本。

未完成人工质量真值/盲评；按用户许可跳过该可选环节并明示局限。此验收稿不作为正式模型发布。
