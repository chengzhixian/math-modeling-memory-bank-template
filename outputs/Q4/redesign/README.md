# Q4 统一配色结果图

入口：[完整图册](gallery.html)。每张图均有 300 dpi PNG、矢量 PDF / SVG 和 `_gray.png` 灰度版。Q1–Q4 在同一 `visual/q1-redesign-20260926` 分支维护。

## 图的用途

| 图 | 文件前缀 | 读图目标 | 建议用途 |
|---|---|---|---|
| 01 | `01_history` | 提交样本散点与当月 q90，区分后训练 / 基座 | 历史概览 |
| 02 | `02_contributions` | 规模分布、规模内时间、支持差额的有符号分解 | 主文 |
| 03 | `03_sensitivity` | 三种参数分箱下的规格敏感性与共同支持限制 | 稳健性 |
| 04 | `04_resources` | C / N / D 年度边际 q90 与筛选口径 | 情景依据 |
| 05 | `05_backtests` | 四窗口原始误差与候选 RMSE | 主文 |
| 06 | `06_forecasts` | 12 / 24 月四候选点预测与固定条件分位范围 | 主文 |
| 07 | `07_uncertainty` | 固定参数、情景并集、偏差压力三层范围 | 主文 |
| 08 | `08_growth_scenarios` | 四种算力对数增长情景 | 预测敏感性 |
| 09 | `09_bridge_validation` | 三个 validation 来源的原始点与同源留出误差 | 主文 |
| 10 | `10_bridge_stress` | 固定配方 172 的有支持跨坐标兑换范围 | 桥接敏感性 |
| 11 | `11_maximum_boundary` | 累计最高分与 q90 的区别、尾差边界及纪录保持验证 | 主文 |
| 12 | `12_policy_bridge` | 固定配方、配方联立、独立质量三模式名义兑换 | 三模式桥接 |

## 结论与边界

- 后训练标准化增量 5.763 分 = 规模分布 −0.758 + 规模内时间 6.521；再加支持差额 −1.542，得到全样本净增 4.222。时间项不是已识别的纯技术贡献，条件份额 −13.15% / 113.15% 不宜画饼图。
- C2 主分析仅用 `pretrained / chat / domain_finetuned`：基座 204、后训练 1,620。01 月度 q90 是新增描述性汇总，不等于预测对象“最近两个日历月”的 q90。C3 异口径 Average 不合并成长轨迹。
- C4 年度表的 N / D 对数是参数数 / token 数，作图后转换为十亿单位。三个 q90 是各自边际统计，不能相乘构造模型。主筛选 81、宽筛选 93 为总资源样本，图中逐年 n 单独标注。
- 四个重叠滚动窗口中，后训练分位资源 RMSE 2.199 最低，基座常数 RMSE 7.633 最低。全部测试 R² 为负，同窗口选择与比较不是独立盲测。
- 算力对数增长减半下，资源候选 η=0.5、漂移保留 0.5；常数 / 趋势候选沿用其自身冻结规则。后训练起点 2025-03-13，12 / 24 月目标 2026-03-13 / 2027-03-13，所选点预测 53.828 / 66.681。基座起点 2025-03-09，常数点 21.032。没有以当前日期新增数据或重新预测。
- 后训练 12 月固定条件 5–95 分位 50.302–56.007，情景并集 37.755–72.236，偏差压力 31.590–78.400。均没有未来覆盖率校准，不称为 95% 预测区间。
- Qwen2 / Qwen2.5 同源小样本桥优于常数，Pythia 未优于常数；Loss 来源标签未独立核验。Q3 → C6 Loss 坐标仍未经验标定。
- 10 选择固定配方 172 的名义兑换点 22.371 / 28.695；支持情景范围 13.601–27.462 / 15.057–39.197。最新 main 已将桥扩展到三模式，同预算联立推荐也是 172、分数相同；12 进一步展示独立原生质量的名义结果及低预算支持缺口。未支持格不补零。这条桥接压力路径不直接进入 C2 / C4 前沿预测。
- 11 的预测对象为“目标日前累计最高分”，与两月 q90 区分。减半算力增长时，后训练 12 / 24 月条件最高边界 60.600 / 73.453，基座保持历史纪录 38.441。1–3 月尾差敏感性不是置信区间；四个验证窗口均未刷新纪录，纪录保持 RMSE=0，动态上尾未优于它，不能保证未来不出现新纪录。

## 来源、复现与检查

远程 main `4098b8c6ca0b91b7ecd35e9251d08710dc0d6098`；上游 manifest 的来源字段保留 `ee23b200e9de7f78477d945b186233741bd3b8fd`、Q3 引用字段 `c052b6918c3f77a2285622521d8abb1b429513be`，实际重画的是最新 main 中已刷新的表与哈希。只重画冻结结果，不重拟合 Q4，不修改原始附件、论文或既有结果表。

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:MPLCONFIGDIR='C:/Users/Administrator/.codex/visualizations/2026/09/26/01a0db13-09d1-7e13-aff5-1aa8e8610a7a/mpl-cache'
& C:/Users/Administrator/.codex/skill-runtimes/scientific-figures/Scripts/python.exe -B src/visualization/q4_redesign.py --skill-dir C:/Users/Administrator/.codex/skills/scipilot-figure-skill
# 读图复核后导出矢量
& C:/Users/Administrator/.codex/skill-runtimes/scientific-figures/Scripts/python.exe -B src/visualization/q4_redesign.py --finalize --skill-dir C:/Users/Administrator/.codex/skills/scipilot-figure-skill
& C:/Users/Administrator/.codex/skill-runtimes/scientific-figures/Scripts/python.exe -B C:/Users/Administrator/.codex/skills/scipilot-figure-skill/scripts/check_figure.py 'outputs/Q4/redesign/*.png' 'outputs/Q4/redesign/*.pdf' 'outputs/Q4/redesign/*.svg' --strict
```

已核对 30 个冻结输出 hash，并核对被使用的 prepared 输入 hash（兼容 Git CRLF 规范化）；复算六任务均分、历史分解闭合、q90 / 累计最高四窗口 RMSE、最高边界公式。`scipilot_profiles.json` 为八张输入表的数据剖析；`monthly_score_summary.csv` 为图01描述性汇总。

十二张 PNG 已逐张视觉复核，调整过图例、底行裁切和标注；图03灰度复核可通过形状区分曲线。布局审计十二图无 FAIL / WARN。`export_check.txt` 的 36 个主导出严格检查无 FAIL；其 PDF Type0 字体 WARN 已通过 PyMuPDF 实测嵌入字节独立排除。`export_audit.json` 保存嵌入字体、尺寸与检查结果：十二份 PDF 均无 Type3 字体、无位图，SVG 无 base64 图像，PNG 尺寸符合 300 dpi。`qa/pdf_review.png` 与 `qa/maximum_pdf_review.png` 为图06 / 11 PDF 实际渲染复核。
