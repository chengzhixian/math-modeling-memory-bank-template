# Q1 全量 22 信号质量结果

主方向：8 个语义模型字段固定正向，14 个统计字段由 A1 全局 Spearman 符号决定；LOO 仅作诊断。A1/A2/A3 全量 51,230 / 17,523 / 203,752 行。
三个输入哈希、A1 标准化参数、随机种子 20260923、bootstrap=1000 见 quality_analysis_manifest_v0.json。

| A1 域 | 记录数 | Q 中位数 | 条件 bootstrap 95% CI |
|---|---:|---:|---:|
| book | 171 | 2.918313 | [2.787906, 2.960625] |
| arxiv | 1419 | 2.688694 | [2.662148, 2.726221] |
| commoncrawl | 9640 | 0.436724 | [0.422387, 0.454322] |
| stackexchange | 10000 | 0.251670 | [0.237005, 0.266000] |
| wikipedia | 10000 | -0.294437 | [-0.319440, -0.270633] |
| c4 | 10000 | -0.303982 | [-0.319317, -0.283969] |
| github | 10000 | -0.485351 | [-0.511670, -0.460243] |

域级排序：expectation 与 argmax 的 Spearman=1.000000；三家族等权与 22 指标等权=0.964286。
稳健性方案的具体域级排序见 quality_orientation_sensitivity_v1.csv；不能宣称排名完全稳健。

## 抽样与扩展

ID 核对发现 A1 的 1,419 条 arxiv 和 10,000 条 github 全部包含于 A2/A3。扩展集对照是覆盖度检查，不能称为独立实验。
新增非重叠部分分别为 16,104 / 193,752 条；仍复用 A1 的所有变换、方向和 Q 均值/标准差。
| 域 | A1 Q | 扩展 Q | 非重叠部分 Q |
|---|---:|---:|---:|
| arxiv | 2.688694 | 2.725253 | 2.727865 |
| github | -0.485351 | -0.505485 | -0.506298 |

## 冲突复核与边界

所有 231 个指标对在同域 sample/extended 中重算相关；另保存非重叠扩展部分相关。常数指标相关不可定义，排除该域后注明实际 n_domains。
冲突只作描述性负相关，未完成相关系数 bootstrap 与多重比较，不写“显著冲突”。方向锚点是建模假设，不是客观质量真值；DSIR 被经验翻转不能解释为原指标语义改变。
部分指标全局 Spearman 相关较弱且 LOO 翻号；诊断见 quality_orientation_robustness_v1.csv。
Q 的区间只反映固定预处理下、假定记录独立的重抽样误差，不包含定向、权重和映射不确定性。book 仅 171 条。
Q 可为负，不能直接代入 B6 正值 Q_score 或幂律质量项；需 cyj 明确跨数据集映射。A16 的 11 个 inferred 域仍无数值填补。

## 复现

```powershell
./.venv/Scripts/python.exe src/chm/q1_quality_analysis.py
./.venv/Scripts/python.exe src/chm/q1_quality_delivery.py
./.venv/Scripts/python.exe -m unittest discover -s src/chm -p test_q1_quality_analysis.py
```

公开字段语义已于 2026-09-23 复核：https://huggingface.co/datasets/opendatalab/SlimPajama-Meta-rater 。未使用历史隐藏文字。
