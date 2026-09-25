# chm 交接：Q1 消融与目录收敛

日期：2026-09-24（北京时间）；分支：`integration/chm-q1-clean-20260923`。

本次变更：新增可复跑 `src/chm/q1_ablation.py` 与 `outputs/chm/ablation_v1/`；删除旧网页配比表及两份已被当前主流程替代的过程脚本。核心证据、数值、消融定义与局限见 `experiments/chm/20260924-q1-ablation-and-cleanup.md`。当前接口仍使用 `outputs/chm/local_recheck_v1/`、`outputs/chm/domain_quality.csv` 和 `interfaces/chm/CONTRACT.md`；主模型未变。

未解决：Q_z 与 B 侧 Q_score、13 域 Loss 与 B1 val_loss 的映射仍需 chm/cyj 联合冻结；1B 配比校准不确定性大，不能将消融改善数直接用于 Q3。下一步由 chm 在 cyj 验证 predictor 后进行 Q3 接口验收；zhh 的 C7 情景须经其正式合同验收。旧网页输出只在历史提交 `44e8db4` 用于审计。
