# Q1：质量、冲突与配比

- [完整答案](ANSWER.md)：方法推导、主要结论、适用范围。
- `domain_quality.csv`、`quality_robustness.json`、`conflict_validation.json`：质量评分与冲突核查。
- `interaction_feature_definition.json`、`interaction_coefficients_13_targets.json`、`targetwise_validation.csv`：13 个目标域的二阶配比代理及验证。
- `recipes_512.csv`、`domain_mapping.csv`、`qa_mapping.json`、`targetwise_oof.csv`、`interaction_fold_stability.csv`：冻结接口所需的配方、映射与折级证据。
- `hull_bounds.json`、`numerical_signoff.json`：四种政策的连续凸包数值界及独立重算。
- `estimated_stress.json`、`refit_stability.json`：估算外推压力和重新拟合选方敏感性。
- `decision_panel.csv`：45 个情景的离散备用配方；`curated_manifest.json` 校验本目录精简文件。
- [核心实验与复核](../../experiments/Q1/CORE_VALIDATION.md)：输入角色、方法、验证设计、复现和科学边界。

正式接口 `chm.q1.v2.0` 的清单 SHA256 为 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`。main 将原清单中九个 `outputs/chm/q1_v2/` 文件按原字节放在本目录，读取器校验原文件哈希并保持清单本身不变。其余为精简结果；完整生产代码和实验记录可从远端 `integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be` 追溯。主模型只识别 A 侧 1M 配比的目标域相对效应，A12–A15 是 estimated/extrapolated 压力测试。
