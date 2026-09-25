# Q1 图表自动化说明

状态：脚本已提交；PNG 图需在本地/完整 Python 环境运行后生成并核验。

运行：

```powershell
python src/chm/q1_figures.py
```

输入：
- `outputs/chm/local_recheck_v1/q1_regmix_ridge_domainwise_metrics.csv`
- `outputs/chm/local_recheck_v1/q1_regmix_direct_scale_rank_stability.csv`
- `outputs/chm/local_recheck_v1/mixture_scale_calibration_v0.csv`
- `outputs/chm/local_recheck_v1/mixture_scale_transfer_v0_manifest.json`

生成摘要表：
- `outputs/chm/local_recheck_v1/q1_regmix_scale_summary.csv`
- `outputs/chm/local_recheck_v1/q1_regmix_target_robustness.csv`

生成论文候选图：
- `paper/sections/chm/figures/q1_domainwise_spearman_box.png`
- `paper/sections/chm/figures/q1_domainwise_spearman_lines.png`
- `paper/sections/chm/figures/q1_direct_rank_stability_1m_60m.png`
- `paper/sections/chm/figures/q1_mixture_effect_scale_decay.png`

建议论文正文优先使用：
1. 13 域 Spearman 箱线图：突出整体跨尺度迁移和域间异质性；
2. 1M↔60M 同配方直接排名稳定性条形图：这是无需回归模型的直接证据；
3. 配比效应幅度随规模衰减图：用于引出 Q1→Q2 的尺度传递接口。

逐域折线图可放附录或作为补充图，避免正文过密。

注意：图中不能把 A12–A15 estimated 数据画成“实测大模型”；当前四张主图都不使用 10B/70B estimated Loss 作为实测结果。
