# B1 `val_loss` 来源和口径审查（2026-09-24）

## 可信范围

B1 原件 `data/raw/real_attachments/B_scaling_laws/pythia_training_log_existing.csv` SHA256 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`；`source_manifest.json` 仅称其来自 EleutherAI Pythia Scaling Suite、保留为赛题数据，没有逐行生成/评估代码。B12 检查点索引 SHA256 `0f7f63535cbc1bbef5165776562e71401af9f762cfe02aaea30c824f45fbc9ed`。独立来源核查了 [EleutherAI Pythia 官方仓库](https://github.com/EleutherAI/pythia) 与 [Pythia-70m 模型卡](https://huggingface.co/EleutherAI/pythia-70m)（访问：2026-09-24 北京时间）；官方资料说明 8 个主模型规模、训练步数、每步 2,097,152 token、共享数据顺序和 GPT-NeoX-20B tokenizer，但并未证明**本附件** `val_loss` 每一行来自官方原始评估日志，也未给本附件的评估语料、聚合公式和原始未舍入值。不能由模型卡的 tokenizer 推断 B1 `val_loss` 的 tokenizer 已独立核实。

## 字段级核查

实际运行脚本及完整数值见 `experiments/cyj/20260924-b1-loss-provenance.md`、`outputs/cyj/diagnostics/b1_loss_provenance.json`。

| 核查项 | 结果 | 等级 |
|---|---|---|
| `run_id` | 1176 行全部唯一；8 个 N 组，每组 147 检查点 | verified |
| `steps` ↔ B12 | B1 的 147 个唯一 step 均在 B12 step 集合中；尚无 B1 行到 B12 模型 checkpoint commit 的严格一一映射 | partially_verified |
| `D_tokens_B` | 全部 1176 行与 `steps×2,097,152/10^9` 在三位小数舍入误差 ±0.0005B 内一致；显示 `batch_tokens_M` 为 2.09/2.1，不能用其舍入显示值逐行精确重算 | verified as derived rounded column |
| `C_FLOPs_1e21` | 与 `6×N_B×D_B×10^-3` 的差落在四位小数舍入带约 ±0.00005；不是额外独立的算力测量证据 | verified as formula-compatible display |
| `ppl` | 1139 行等于 `round(exp(显示的 val_loss),2)`；全部 1176 行与 val_loss 四位和 ppl 两位独立舍入的区间相容 | verified as natural-exp-compatible display |
| `val_loss` 显示精度 | 1055 行 4 位、113 行 3 位、8 行 2 位小数（尾零省略）；原始更高精度未知 | verified display only |
| 原始 checkpoint 独立评估 | 无原始逐 checkpoint Loss 追踪表或可调用评估脚本与本 CSV 对接 | unknown |
| 生成/插值/smoothing | 当前附件和来源表未说明 `val_loss` 是否由公式构造、插值或平滑；近乎精确重构本身不能裁定 | unknown |
| tokenizer / validation corpus / log base / aggregation | 官方 Pythia 背景与 `ppl≈exp(val_loss)` 提供线索，但本附件评估管线未证 | unknown for B1 Loss |

## 模型残差和轨迹

现有 B1 五参数式在本表全样本 RMSE `0.0001465764`、R² `0.9999998164`；8 个 N 组各 147 点均随 D 严格下降。组内残差 RMSE 在约 `0.0001005–0.0002032`；相邻 Loss 差减去模型相邻差的 RMSE `0.00020477`。极高同源重构、D/C/ppl 的派生显示关系与统一平滑形状都触发**来源核查**，但并不证明 Loss 一定由此五参数公式生成，也不能单独判断是否有真实训练噪声。外部 Pythia 文档不包含可把本 CSV 逐行对应回原始评估值的证据链。

## 结论与使用限制

整体 `partially_verified`：B1 的若干协变量/派生列可核，`val_loss` 生成与评估口径仍 `unknown`。论文及接口只能说“在 B1 同源数据上近乎精确重构”，不能说“具有极高外部预测精度”。正式跨源 Loss 比较须先找到同 tokenizer、同验证语料、同 log base、同聚合定义及可追溯 checkpoint 评估链；找不到时保持 descriptive-only。
