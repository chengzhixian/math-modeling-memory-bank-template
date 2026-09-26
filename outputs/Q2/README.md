# Q2：条件广义标度律

- [结论与验证](ANSWER.md)；论文推导见 `paper/latex/sections/Q2/main.tex`。
- [核心实验](../../experiments/Q2/README.md)：B1 基线、B7 质量扩展、v8 完整审查及复现边界。
- `model_definition.json`、`model_coefficients.json`、`b7_quality_extension.json`：冻结模型与参数。
- `b2_b3_validation_summary.json`、`scale_order_validation_summary.json`、`b7_backbone_comparison.csv`：按来源分开的验证。
- `quality_bridge_sensitivity.csv`、`quality_scale_local_tradeoff.csv`、`domain_pair_substitution.csv`：桥接情景、质量与规模替代、领域转移。
- `acceptance.json`、`upstream_manifest.json`：发布状态与原冻结包文件哈希；`curated_manifest.json` 校验本目录选择性收录的文件。

本目录只从远端 `team/cyj-scaling@74e678e319b58e2aab230a7b7233fa53f3053fa5` 的 `q2_v8` 冻结包选取核心文件，数值生产者固定于 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`；没有迁入此前 v7、诊断缓存或个人实验中间表。`upstream_manifest.json` 的完整清单可在来源提交查看，本目录并不镜像全部文件。复现需在来源提交运行 `python -B src/cyj/fit_b7_quality_extension_from_b1.py` 和 `python -B src/cyj/build_q2_v8.py`；原始附件仍应按 `memory-bank/DATA_INDEX.md` 校验。
