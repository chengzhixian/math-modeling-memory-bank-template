# Q1 核心实验与复核记录

来源：远端 `integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be` 的冻结 Q1 v2、最终答案及三份交接（`20260925-q1-interaction-v2-final.md`、`20260925-q1-v2-evidence-signoff.md`、`20260925-q1-v2-estimated-refit-closure.md`）。该分支当前 `experiments/chm/` 不再保留对应 Q1 实验 Markdown，故本记录从已签核结果和清单汇总，不冒充原始运行日志。题面和字段只采用可见资料与原始附件；历史 PDF 隐藏边字及作废提交完全排除。

| 实验 | 输入角色与方法 | 核心证据 | 结论边界 |
|---|---|---|---|
| 质量与冲突 | A1 51,230 条、A2/A3 扩展；22 个质量信号统一方向，A1 冻结规则外推；231 个指标对的相关与复现 | `outputs/Q1/domain_quality.csv`、`quality_robustness.json`、`conflict_validation.json` | `Q_A` 是工程评分代理；冲突是指标分歧，不是因果冲突或人工标签准确率 |
| 配比主模型 | A4/A5 的 512 条 17 域配方和 13 个目标 Loss；每目标 17 主项加 10 个二元交互，L2 正则；与 Ridge/常数基线对照 | `interaction_feature_definition.json`、`interaction_coefficients_13_targets.json`、`targetwise_validation.csv`、`targetwise_oof.csv` | A6–A11 为真实组比较，但曾参与形式选择，不能称完全未触碰最终盲测；1B 存在支持集变化 |
| 数值选方 | 在 A4 凸包内按声明的目标权重和质量政策求解；McCormick 松弛与空间分支定界；另枚举 512 个已观测方案 | `hull_bounds.json`、`numerical_signoff.json`、`decision_panel.csv` | 四个情景数值界间隙均小于 0.001，是浮点证据，非区间算术证明；离散 index 不等于连续解 |
| 外推与重拟合压力 | A12–A15 的 10B/70B estimated Loss 各 63 个已见配方；另以种子 20260925 做 30 次 80% 训练行重拟合 | `estimated_stress.json`、`refit_stability.json` | estimated 不是实测；重拟合只评估 512 个已观测候选，不能充当连续最优解置信区间 |

冻结接口为 `chm.q1.v2.0`，原发布清单 SHA256 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`。main 在 `outputs/Q1/` 收录九个接口输入的原字节；`src/chm/q1_interface_v2.py` 对原清单路径作只读位置映射，逐文件校验原哈希且不改写冻结清单。现行生产与复核在 main 内运行，重算中间表默认进入忽略的 `data/processed/Q1/`。首先按 `memory-bank/DATA_INDEX.md` 校验 LFS 原始附件，再从仓库根目录执行：

```powershell
python -B src/chm/q1_quality_analysis.py --output-dir data/processed/Q1/quality --bootstrap 1000
python -B src/chm/q1_quality_delivery.py
python -B src/chm/q1_quality_sensitivity.py --output-dir data/processed/Q1/quality_review
python -B src/chm/q1_quality_robustness_final.py
python -B src/chm/q1_conflict_aware.py
python -B src/chm/q1_conflict_replication.py
python -B src/chm/q1_conflict_resolution.py
python -B src/chm/q1_regmix_domainwise.py --output-dir data/processed/Q1/regmix
python -B src/chm/q1_mixture_interface.py --output-dir data/processed/Q1/regmix
python -B src/chm/q1_mixture_final_audit.py
python -B src/chm/reproduce_q1_v2_core.py
python -B src/chm/q1_mixture_nested_model_comparison.py
python -B src/chm/q1_mixture_comparative_validation.py
python -B src/chm/q1_mixture_decision_v2.py
python -B src/chm/q1_hull_bounds_v2.py
python -B src/chm/audit_q1_v2_signoff.py
python -B src/chm/q1_v2_estimated_stress.py
python -B src/chm/q1_v2_refit_stability.py
python -B src/chm/q1_ablation.py
python -B src/chm/q1_paper_figures.py
python -B src/chm/q1_figures.py
python -B src/chm/plot_q1_interaction.py
python -B src/chm/plot_q1_v2_final.py
```

本次 main 集成验收中，重算质量表 9 行的 `Q` 与发布值最大差为 0，域映射表一致；冲突图重得 BH-FDR 0.05 下的 55 条复制性显著负相关边，冲突决策重得同一 A1 阈值及 27 个案例，100 次质量方向重抽通过。A4/A5 重新拟合的 13 个交互模型最大系数差 `6.14e-13`、CV 最大差 `2.22e-16`，A6–A11 三组发布的交互 RMSE 最大差 `4.44e-16`、Spearman 差 0。嵌套 CV 的 `targetwise_oof.csv`、实测比较的 `targetwise_validation.csv`、45 条选方、estimated 两张逐目标与选方表、30 次重拟合选方表均与发布文件哈希相同。四个连续凸包场景重算满足发布的 0.001 数值间隙要求，独立数值签核四项全部通过。全部输出保持主目录精简，不把重算缓存提交到 main。

字节口径提醒：`outputs/Q1/hull_bounds.json` 的 Git LF SHA256 为 `969f810c0bf54f03492afc243091c339aaf4b27aed5c2164c186e651c7589acc`；冻结签核 `numerical_signoff.json` 中的 `bounds_sha256=b27939f9...` 对应同内容的 Windows CRLF 工作区字节。换行转换会改变原始字节哈希，不改变四个数值情景；校验时必须说明所用口径，不能把两个哈希直接对比后误报模型更改。

复核重点：输入哈希、512×17 与 13 目标维度、配比和为 1、A1/A2/A3 重叠控制、A6–A11 的模型选择角色、绝对 Loss 基线、质量约束残差、有限值以及 A12–A15 estimated 身份。Q1 不识别跨附件 `Q_A→Q_B`、目标域 Loss→B1 总体 Loss 或连续 N–D 尺度传递；这些只能在 Q2/Q3 明示为条件假设。
