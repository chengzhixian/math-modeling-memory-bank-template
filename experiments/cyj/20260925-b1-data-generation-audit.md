# B1 异常低误差的结构审计

运行 `python -B src/cyj/independent_data_audits.py`，B1 SHA256 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`；机器结果 `outputs/cyj/classic/b1_structure_audit.json` SHA256 `f595e8af3158c774bd47002be825704716ceeffa6997e0fa4ca12647f2fe0267`。此审计补充既有 `20260924-b1-loss-provenance.md`，并未找到新生成脚本。

1176 行分成 8 个 N 组，每组 147 检查点；8 组使用完全相同的 147 个 D 值网格。1176 个 `run_id` 唯一，没有精确重复 `(N,D)`。D 与 step×2,097,152/1e9 的最大绝对差为 0.000496 B，符合显示舍入。把每组 Loss 减去组均值后，各 N 轨迹的同 D 横向标准差 RMS 仅 0.00013536；这种近乎平行和先前五参数残差极小一起构成生成机制审查信号。train_loss 与 val_loss 相关 0.9912，差值的四分位为 0.081975/0.12135/0.158225，但同源评估流水线是否相同无法由两列判定。

没有本附件逐 checkpoint 原始评估文件、生成代码或同 tokenizer/语料的交叉复核。不能判断 Loss 究竟来自显式公式、平滑、插值还是真实评估。B1 只支持同源条件重构，不报告真实外部预测能力。原始来源追溯、ppl/算力显示列核对仍见前日 provenance 审计。
