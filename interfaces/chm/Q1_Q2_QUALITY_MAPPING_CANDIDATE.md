# CHM → CYJ：Q1 质量口径修订候选

日期：2026-09-25；状态：**待用户验收，不替换 `chm.q1.v1.3` 与 cyj v6。**

## 精确输入

- 当前正式 Q1 配比系数、参考配方：`chm.q1.v1.3@cdda1ad62c5c7eb72b413c4228caeff87d2bad30`，保持不变。
- cyj Q1 派生配方包 v1：`outputs/chm/q1_exports/q1_q2_bundle_v1/export_manifest.json`，SHA256 `b0dda7caac30513c0f37e74ccb143064606847fdc35fd7607c999ac2f8647ecb`。
- 新 17 域质量口径候选：`outputs/chm/q1_third_part_review/qa_mapping_primary_candidate.json`，schema `chm.q1.q2_quality_policy.candidate.v2`，SHA256 `d18993de119652987b114525e16eaea14b346ab31637cc5628a80bfe09c2bfd8`。

新文件明确使用 `A1_sample` 的 7 个质量域主评分；arxiv/github 的 A2/A3 扩展分数仅保存在 `Q_A_extended_sensitivity`。3 direct、3 near-direct、11 inferred；inferred 的 `Q_A` 均为 null。A 侧分数不等于 B7 `Q_score`。

## 对 Q2 v6 条件政策的影响

CHM 侧以 cyj `team/cyj-scaling@86526a1` 的 `model_coefficients.json` 原始字节（SHA256 `d6f5b665d3806a322d0ebf87da46889822d2eff89324eacded6040383e7b6733`）独立重算 v6 的两项质量约束 LP。旧值在 `1e-9` 内复现；在 `N=1B,D=100B,Q_B=0.5,lambda=1,eta=0,13` 目标等权下：

| 政策 | cyj v1 扩展值 | A1 主口径值 | 最优配方 L1 变化 |
|---|---:|---:|---:|
| direct | 2.263949598560 | 2.263945861618 | 0.0000768742 |
| direct+near | 2.274988571899 | 2.274895033444 | 0.004045006 |

完整 17 域配方、活跃 A4 顶点及可行性残差在 `outputs/chm/q2_mapping_sensitivity_v1/`；运行 `python -B src/chm/q2_quality_mapping_recheck.py` 重生。该计算是**条件工程情景**，没有识别 A/B 共同质量坐标或 `lambda/eta`，`ready_for_Q3=false`。

## 消费者动作与版本门槛

CYJ 在其本人分支上、用户验收后应发布新的不可变 Q1 导出消费版本，保持旧 v1 文件不变。重算 `quality_direct` 和 `quality_direct_and_near` 的 Q2 政策结果、质量映射敏感性、manifest、论文对应数字和 v6/v7 fixture；记录本文件所指 Q1 候选哈希及正式发布后的新哈希。若用户将交互模型升为 Q1 主模型，还须另外重算配比效应与 Q2/Q3，而不是只换质量分数。CHM 在 CYJ 新版发布后执行 owner acceptance；当前 Q3 消费仍固定已验收的条件 v4/Ridge 路径。
