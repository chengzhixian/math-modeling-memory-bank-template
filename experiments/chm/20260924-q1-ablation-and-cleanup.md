# Q1 消融与工作树收敛（2026-09-24）

基线：clean integration `44e8db4`，仅消费该提交的 chm 当前输出和真实 RegMix 配对表。运行：

```powershell
./.venv/Scripts/python.exe src/chm/q1_ablation.py
```

如果独立 worktree 的 LFS 数据只有指针，使用 `--data-root` 指向已通过 `scripts/verify_raw_data.ps1` 校验的同仓库真实附件目录。本轮使用主工作树的真实附件；输入 SHA256 见 `outputs/chm/ablation_v1/ablation_manifest.json`。消融脚本先复算完整 Ridge 在三组 held-out 的 RMSE，并逐目标域与既有输出核对，失配则中止。

## 质量三家族消融

基于 A1 实跑的 0.05 权重网格，逐次将 RPS、DSIR、model 家族权重置零，其余两家族各 0.5。比较七域排序，不比较 Q 的绝对尺度。

| 去掉 | 与主 Q 排序 Spearman | 变化域数 | 第一域 | 最后一域 |
|---|---:|---:|---|---|
| RPS | 0.8214 | 4 | arxiv | c4 |
| DSIR | 0.9643 | 2 | arxiv | github |
| model | 1.0000 | 0 | book | github |

这说明**在本数据的域级排序**中 RPS 最关键，model 家族对排序没有增量；不能据此认定 model 指标对样本级评分或外部数据无用。主三家族 Q 不替换。

## 配比输入消融

完整模型为 A4+A5 训练的逐目标域 Ridge，使用已冻结的 alpha；消融模型只预测对应目标域的训练 Loss 均值。两者在同一 A6–A11 held-out 配对表上比较 RMSE。均值模型恒定，不定义 Spearman。

| 测试尺度 | 目标数 | 完整 RMSE 中位数 | 无配比 RMSE 中位数 | 完整模型改善目标数 | 完整 Spearman 中位数 |
|---|---:|---:|---:|---:|---:|
| 1M | 13 | 0.4478 | 0.6759 | 13 | 0.8381 |
| 60M | 13 | 1.4450 | 1.4724 | 13 | 0.8381 |
| 1B | 13 | 3.2079 | 3.2514 | 4 | 0.7067 |

1M/60M 上配比有一致增益；1B 上仅 4/13 域改善，两个模型都受从 1M 到 1B 的 Loss 截距迁移影响，因此这张表不验证已校准的尺度传递，也不能用中位数差异代替逐域配对效应。详细 39 行见 `outputs/chm/ablation_v1/mixture_feature_ablation.csv`。

## 清理范围

保留交付接口、当前系数/尺度清单、质量审计、关键敏感性、图表与本消融代码。移除已被当前逐域脚本取代的早期“13 域先平均”基线脚本、一次性 web-vs-local 对照脚本及其 CV 临时表、旧网页配比 CSV。差异摘要 `outputs/chm/q1_local_reproduction_check.json` 和本日志保留；旧文件可从 Git 提交 `44e8db4` 定点审计，当前生产代码不读取它们。未触碰原始附件、他人成员分支或公共记忆。
