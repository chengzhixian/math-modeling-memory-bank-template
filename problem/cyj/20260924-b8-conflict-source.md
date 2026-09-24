# B8 与 B7 的质量方向冲突（2026-09-24）

## 来源与逐点证据

B7 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`，B8 SHA256 `bda0d449f75c73bbd04141e5cffbf4bea7002073e34b7fa95a638570fa095ffe`。可见说明只称 B8 为大规模半合成、含外推；source manifest 对 B8 无生成公式、质量坐标定义或 `calibrated`/`extrapolated` 的具体算法说明。

同一字段名 `Q_score` 无法证明语义/方向相同。B7 45/45 固定 `(N,D)` 组的 Q 端点 Loss 下降；B8 calibrated 90/90 组和 extrapolated 60/60 组均上升。两表有 224 个精确 `(N,D,Q)` 共坐标，全部 Loss 不相等，且 B8−B7 在 213 点为负、11 点为正，范围 `[-2.5769,.0569]`。这些冲突不能由简单“更多数据点”解释为独立重复测量。

B8 的 `val_loss=0.5` 精确堆积为 362/1704：calibrated 129/984（13.11%），extrapolated 233/720（32.36%）；主要在较低 Q。这个现象**兼容**硬下限或 clipping，但也可能来自半合成公式或显示/存储规则；当前无生成代码，原因 `unknown`。`calibrated` 与 `extrapolated` 目前只有 CSV 标签，没有可核验的具体校准步骤；不得把标签变成真实外部测试资格。

## 决策

`unresolved_keep_isolated`。B8 不加入 B7 拟合、选模或独立验证，不做 `Q→1-Q` 后强行合并，不把 0.5 当真实物理下界。若能取得生成脚本/原始校准数据、Q 坐标定义、floor 规则和同坐标 Loss 说明，再检验有依据的变换；本次没有证明 `compatible_after_verified_transform` 或 `separate_data_generating_process` 中任一更强结论。脚本、复现命令和输出哈希见 `experiments/cyj/20260924-b8-conflict-source.md`。
