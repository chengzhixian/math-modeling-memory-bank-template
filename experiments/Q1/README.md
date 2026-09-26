# Q1 核心实验

[核心实验与完整复核](CORE_VALIDATION.md)记录质量、配比、数值选方、估算外推和重拟合验证的来源及边界。

逐次重拟合选方、逐目标估算压力和选方压力证据分别收录于 `outputs/Q1/refit_replicate_choices.csv`、`estimated_targetwise.csv`、`estimated_decision_stress.csv`，对应 `refit_stability.json` 和 `estimated_stress.json` 登记的 SHA256。当前生产代码、依赖、原始输入和七幅正式图的生成入口均在 main；可再生过程表写入忽略的 `data/processed/Q1/`。历史来源仍保留于冻结 CHM 提交，`interfaces/Q1/code_manifest.json` 记录 main 改写后的实际代码身份。
