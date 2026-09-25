# chm 交接：Q1 方向稳定性规则提升为主模型

日期：2026-09-24（北京时间）；分支：`integration/chm-q1-clean-20260923`。

## 背景与证据

- 旧主规则对 14 个非锚点指标计算域内 Spearman、Fisher-z pooled rho 后，直接按 pooled rho 的正负取方向。
- `outputs/chm/quality_review_v1/quality_orientation_stability_v1.csv` 已显示两个指标的 LOO 方向跨 0：
  - `rps_lines_numerical_chars_fraction`：full pooled rho = 8.034789312334326e-05，LOO [-0.0275225611, 0.0274344800]；
  - `rps_doc_frac_chars_top_3gram`：full pooled rho = -0.0180959166，LOO [-0.0631002929, 0.0181451838]。
- 旧 review manifest 明确为 `review_sensitivity_not_primary` 且 `primary_quality_definition_unchanged=true`。R05 待办只要求构造“剔除不稳定指标的 Q 敏感性版”，没有“评审通过后自动回写主模型”的验收项。

## 本次主模型变更

- `src/chm/q1_quality_analysis.py` 新增 `orientation_stability()` 与 `freeze_primary_orientation()`。
- 默认 `PRIMARY_ORIENTATION_POLICY = "stable_loo"`。
- 8 个模型型语义锚点固定正向；其他指标只有在删除任意一个 A1 域后 pooled 方向均不翻转才纳入主 Q_A。
- 不稳定指标的 `orientation=0` 仅作排除标记；`orient()` 会把对应列置为 NaN，使其不参与家族均值，避免数值 0 稀释评分。
- `stable_consensus_075` 仍只作压力测试，因为现有结果会删除全部 DSIR 指标并改变三家族结构。
- `src/chm/q1_quality_sensitivity.py` 已改为复用主脚本的 LOO 稳定性实现，未来重跑时以 stable_loo 为 primary。
- `src/chm/test_q1_quality_analysis.py` 新增“不稳定方向从主评分排除”的回归测试。
- `problem/chm/q1_quality_method.md`、`paper/latex/sections/chm/q1.tex` 与 R05 审查清单已同步方法定义；论文源显式标记 canonical 数值待重跑。

## 当前验证状态

- 已基于既有真实 A1 敏感性输出核对：stable_loo 保留 20 个指标（9 RPS + 3 DSIR + 8 model），只排除上述两个方向翻转指标；旧主 Q 与 stable_loo 的七域排名 Spearman 为 1.0。
- 已做新准入/排除逻辑的最小逻辑检查；远端运行环境无法取得 Git LFS 的 A1--A3 实体文件，因此不能在本轮声称完成全量回归或刷新 bootstrap 区间。
- `domain_quality.csv`、`domain_quality_v0.csv`、扩展集复核、图表和论文数值仍是旧 sign-only 规则下的 canonical 结果，必须在本地 `git lfs pull` 后重跑 `src/chm/q1_quality_analysis.py` 才能更新。
- R05 原本还要求方向 bootstrap 稳定性；该项尚未实现，不能把 LOO 当成已完成 bootstrap。后续如加入 bootstrap，应先作为附加证据，只有在规则、重抽样单位和结果冻结后再决定是否改变主准入。

## 下一步

1. 在有完整 LFS 数据的 chm 本地环境重跑 `python src/chm/q1_quality_analysis.py --bootstrap 1000`；
2. 核对新的 `quality_orientation_v0.csv` 确实只把两个已知 LOO 不稳定指标标为 orientation=0，并检查是否出现新异常；
3. 刷新 `domain_quality.csv`、图表、扩展集复核和 Q1 LaTeX 数值；
4. 重建/核对 Q1 机器接口哈希后，才将新 Q_A 标为 producer-validated；
5. 若实现 R05 的方向 bootstrap CI，记录重抽样单位、seed、CI 判据，并检查它是否会导致整类指标消失。
