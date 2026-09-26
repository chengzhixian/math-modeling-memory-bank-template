# Q2：条件广义标度律

- [结论与验证](ANSWER.md)；论文推导见 `paper/latex/sections/Q2/main.tex`。
- [核心实验](../../experiments/Q2/README.md)：B1 基线、B7 质量扩展、v8 完整审查及复现边界。
- `model_definition.json`、`model_coefficients.json`、`b7_quality_extension.json`：冻结模型与参数。
- `classic_fit.json`：Q2/Q3 实际消费的 B1 五参数拟合及留组验证原始记录。
- `b2_b3_model_validation.csv`、`scale_order_validation.csv` 及各自 summary、`b7_backbone_comparison.csv`：逐组与汇总验证；B2/B3 均不充当独立真实外测。
- `quality_bridge_sensitivity.csv`、`quality_scale_local_tradeoff.csv`、`domain_pair_substitution.csv`：桥接情景、质量与规模替代、领域转移。
- `domain_pair_reference.json`：136 个领域对局部转移的配比参考点。
- `q2_v8_runtime_audit.json`、`q2_v8_release_verification.json`：冻结生产运行的输入访问审计与远端发布核验。
- [v8 条件接口与 18 组冻结样例](../../interfaces/Q2/README.md)：Q3 消费 Q2 时使用的边界与请求/预期结果。
- `acceptance.json`、`upstream_manifest.json`：发布状态与原冻结包文件哈希；`curated_manifest.json` 校验本目录选择性收录的文件。

本目录从远端 `team/cyj-scaling@74e678e319b58e2aab230a7b7233fa53f3053fa5` 选择 `q2_v8` 冻结包及其 B1 输入、运行／发布审计的核心文件，数值生产者固定于 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`；没有迁入此前 v7、诊断缓存或个人实验中间表。`upstream_manifest.json` 的完整清单可在来源提交查看，本目录并不镜像全部文件。复现需在来源提交运行 `python -B src/cyj/fit_b7_quality_extension_from_b1.py` 和 `python -B src/cyj/build_q2_v8.py`；原始附件仍应按 `memory-bank/DATA_INDEX.md` 校验。
