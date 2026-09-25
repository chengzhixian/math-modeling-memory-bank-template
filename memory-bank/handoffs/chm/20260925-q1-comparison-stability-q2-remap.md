# CHM Q1 第三小问比较、稳定性与 Q2 质量口径复算交接

日期：2026-09-25；分支：`integration/chm-q1-clean-20260923`。用户要求完成模型同条件比较、配方稳健性和修正质量口径后的 Q2 情景。本轮仍为**用户验收候选**；未修改 `chm.q1.v1.3` 机器接口或 cyj 分支，不发布正式 Q3 结论。

## 完成

1. A4+A5 训练内严格嵌套五折：外层留出，内层每折单独选 5 个高方差训练域与 alpha；交互候选 13/13 目标 OOF RMSE 优于 Ridge、10/13 Spearman 更高。目标域中位 RMSE 交互/Ridge/常数 = `0.449947/0.492123/0.779024`。代码与逐目标表：`src/chm/q1_mixture_nested_model_comparison.py`、`outputs/chm/q1_nested_model_comparison_v1/`。
2. 同一 A6--A11 检验行逐目标比较 Ridge、交互、训练均值常数；输出 RMSE、MAE、bias、Spearman、基线增益、成对平方误差 1000 次行 bootstrap。1B A4 凸包内 17 条、外 47 条各有 13/13 目标交互 RMSE 较低；全 1B 只有 11/13 交互绝对 RMSE 低于常数，Spearman 7/13 高于 Ridge。1M/60M 凸包内仅 2/256，不能作域内泛化。代码与表：`src/chm/q1_mixture_comparative_validation.py`、`outputs/chm/q1_mixture_comparison_v1/`；逐目标数值断言与本人既有审计一致。
3. 214 组显式权重 × 两模型 × 三质量政策 × A1 主/扩展敏感性口径，严格限 A4 的 512 个已观测配方；另外只在真实 held-out 候选内部计算选方实际遗憾。无质量约束的两模型选方一致率 77.1%，direct 52.6%，direct+near 63.6%；1B 凸包内 17 候选的实际相对遗憾中位数交互/Ridge `0.1597/0.1924`，前十分位命中 `32.7%/33.6%`，不能说所有决策指标均由交互占优。代码与数据：`src/chm/q1_mixture_selection_stability.py`、`outputs/chm/q1_selection_stability_v1/`。
4. 按 cyj `86526a1` 冻结 B7/Ridge 参数，以同一 B7 基线和 HiGHS 约束独立复现 cyj v6 两项质量政策旧 Loss 至 `1e-9`；A1 sample 质量主值的新条件 Loss：direct `2.263945861618`、direct+near `2.274895033444`，分别比旧值低 `0.000003736942`、`0.000093538455`。最优顶点集合未变，混合权重改变；详见 `src/chm/q2_quality_mapping_recheck.py`、`outputs/chm/q2_mapping_sensitivity_v1/`。交给 cyj 的精确消费说明是 `interfaces/chm/Q1_Q2_QUALITY_MAPPING_CANDIDATE.md`，Q1 候选映射文件 SHA256 `d18993de119652987b114525e16eaea14b346ab31637cc5628a80bfe09c2bfd8`。
5. `paper/latex/sections/chm/q1.tex` 已补模型比较和稳定性证据；按用户最新要求暂缓生成论文 PDF。完整论证与运行顺序见 `experiments/chm/20260925-q1-third-part-model-comparison.md`。

## 科学边界与验收选择

证据支持把交互模型作为 Q1 A4 支持域内的优先预测候选，但其模型族已经受前期 held-out 观察影响；本轮嵌套 CV 不等于从未触碰的外测。13 个目标的绝对跨规模 Loss 仍有偏差，11 个 inferred 质量域不填数值；条件 Q2 仍缺 A/B 标定、`lambda` 与 `eta` 识别。`ready_for_Q3=false`。

用户需验收是否将交互升为正式 Q1 配比预测模型。若升版，新不可变 Q1 接口、cyj Q2、chm Q3 都应显式重跑；若维持 Ridge，也必须发布仅更正 A1 主质量口径的新 Q1 派生包并让 cyj 正式重跑两项质量政策。旧 v1/v6 不覆盖。

## 复现与下一步

本机解释器 `H:\研究生数模\math-modeling-memory-bank-template\.venv\Scripts\python.exe`；顺序执行 `q1_third_part_review.py`、`q1_mixture_nested_model_comparison.py`、`q1_mixture_comparative_validation.py`、`q1_mixture_selection_stability.py`、`q2_quality_mapping_recheck.py`。每个输出目录的 `manifest.json` 固定原始输入、版本与结果 SHA。下一步由用户验收模型主次；cyj 在本人分支实现正式 Q2 新版；chm 接收后验收 Q3 消费和更新第三问论文复现。完整安全资料与原始数据检查仍按仓库三个入口脚本执行。
