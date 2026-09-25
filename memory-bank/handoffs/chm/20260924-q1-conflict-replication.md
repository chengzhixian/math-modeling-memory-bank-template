# chm 阶段交接：Q1 冲突复制性增强

日期：2026-09-24（北京时间）

完成基于既有全量实跑产物的冲突复制性汇总，不需要重新下载 LFS：
- arxiv 92/96 个样本负相关在完整扩展和非重叠扩展继续为负；
- github 91/91；
- 两域共同三层复制的负相关对 56 个；
- 最强共同例子最弱 |rho| 仍约 0.7393。

输出：
- `src/chm/q1_conflict_replication.py`
- `outputs/chm/quality_conflict_replication_summary.json`
- `outputs/chm/quality_conflict_shared_robust.csv`
- `experiments/chm/20260924-q1-conflict-replication.md`

限制：没有 bootstrap CI / FDR；该项仍需本地 LFS 逐记录重跑后才能使用“显著”措辞。
