# Q2 结果图册

基于远程 main `a19039b5d11c91cf32e301dc85b2f4d50b5a75b7` 的冻结 `cyj.ndqp.scenario.v8` 结果，仅新增展示层，不重拟合、不改写原始数据或既有结果。

入口：`gallery.html`。每张图有 300 DPI PNG、PDF、SVG 和灰度 PNG；统一沿用 Q1 的蓝 `#0072B2`、绿 `#009E73`、橙 `#E69F00`，类别同时用圆点、方块、三角等形状区分。当前为 7.2 英寸宽的论文双栏草稿，中文字体 Microsoft YaHei；最终排版如改变尺寸，应按实际尺寸重出。

| 文件 | 论证目标 | 数据与表达方式 |
| --- | --- | --- |
| 01_baseline | 骨架能否重建 B1 记录 | 1,176 个观测—拟合散点及训练量—残差散点；残差放大 1,000 倍 |
| 02_scale_surface | N、D 的联合变化 | 冻结 B1 解析式的双对数热力图、等值线；只画正式 Q2 N–D 范围 |
| 03_quality_validation | 质量扩展的留出表现 | B7 外层 24 折分布，按 N / D / q 分组 n=9 / 5 / 10；横线为均值 |
| 04_elasticities | 相对变化尺度的局部敏感度 | 冻结 CSV 的三个规模情景；展示负弹性，线仅连接有序情景 |
| 05_quality_tradeoff | 假想质量提升的规模等价 | 固定配方、D=100B、基准 q=0.67136；q 绝对增加 0.05 / 0.1 的同 Loss 根 |
| 06_bridge_sensitivity | 映射强度假设的影响 | 压缩、默认、扩张三个情景逐点展示，横轴注明局部放大 |
| 07_local_transfers | 可行局部配比转移方向 | 136 对转移导数扩展为 17×17 反对称矩阵；列减配、行增配 |

主文建议优先选 02、04、05、06；01、03 支持验证说明，07 支持配比局部分析。小样本验证用逐点图，可替代的箱线图会压缩 n=5 的分布；17 域配方关系用矩阵，避免 136 条线造成遮挡。规模跨数量级用对数轴；质量变化仅有三个离散情景，不用连续拟合曲线或虚构误差带。

## 结论边界

- B1 同源重建 RMSE≈0.0001466；不能据此声称真实模型家族的跨源预测精度。
- B7 为 450 条半合成记录。留出误差不是独立真实实验的重复；均值线不表示置信区间。
- Q2 正式范围 N∈[0.070542,11.965825]B、D∈[10,299.893]B、q∈[0.1,1]；配方限已观测 A4 或其凸包。图 01 的 B1 原始记录包含 D<10 的骨架训练点，不是完整 v8 的正式预测点。
- 质量与配比桥都未经验标定，重复计数尚未识别。图 05 的固定 p 质量变化是数学情景，不等于实际清洗数据的节省；图 06 是假设敏感性，不是统计区间。
- 图 07 的基准为 512 个 A4 配方均值，N=1B、D=100B、13 目标等权。导数单位是每单位绝对份额；不能直接当作有限步长收益。各方向可行最大步长不同。
- Q1 上游代理存在负交叉熵预测的诊断，Q2 的指数桥并不能消除其物理有效性问题。本任务不修正模型，相关收益表述仍须接受上游有效性限制。

## 复现与检查

```powershell
& C:/Users/Administrator/.codex/skill-runtimes/scientific-figures/Scripts/python.exe -B src/visualization/q2_redesign.py
# 人工查看 PNG 后再导出矢量图
& C:/Users/Administrator/.codex/skill-runtimes/scientific-figures/Scripts/python.exe -B src/visualization/q2_redesign.py --finalize
```

其他机器需 numpy、pandas、matplotlib、Pillow，以及 SciPilot skill 的 scripts；可用 `--skill-dir` 指定安装路径。字体按本机可用中文字体调整。SVG 保留可编辑文字，其他电脑缺字体时优先用已嵌入字体的 PDF。

`scipilot_profiles.json` 保存数据剖析；`manifest.json` 保存每个输入的 SHA-256、版本、图尺寸及布局检查。`baseline_reconstruction.csv`、`quality_outer_folds.csv`、`same_loss_size_reductions.csv`、`transfer_derivative_matrix.csv` 是可核对的展示派生数据，不是新拟合。

7 张图均经过 PNG 读图；修复公式缺字、热力图刻度重叠、浅色等值线标签和图例与轴标签挤压。最终布局检查无 WARN/FAIL；28 个导出文件经检查，PNG 分辨率及 SVG 通过。SciPilot PDF 字体检查对 Type0 字体发出误报，已用 PyMuPDF 逐字体提取嵌入字节核实全部存在，且无 Type3；细节保存在 `export_audit.json`。
