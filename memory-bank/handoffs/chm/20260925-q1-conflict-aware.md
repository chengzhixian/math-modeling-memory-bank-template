# Q1 第二小问：冲突成因与二维评价交接

日期：2026-09-25；成员：chm；分支：`integration/chm-q1-clean-20260923`。

## 本次变更

- 已从远端获取更新并确认本分支远端最新提交为 `e256fd7`；旧 `team/chm-data` 远端已删除，因此在当前 chm 集成分支工作。
- 新增 `src/chm/q1_conflict_aware.py`：沿用 Q1 的 A1 冻结预处理与 22 指标方向；对 231 对指标做 Spearman、各分析范围内 BH-FDR 0.05、A2/A3 去重扩展复制性判定、七域相关模式分类、样本级冲突边分歧度。
- 输出 `outputs/chm/conflict_aware_v1/`，包括完整相关表、冲突图表、样本 `(Q,D)`、域级汇总、二维图、极端值诊断、manifest。更新 Q1 LaTeX 与 Markdown 草稿。

## 证据与复现

命令：`& 'H:\研究生数模\math-modeling-memory-bank-template\.venv\Scripts\python.exe' src/chm/q1_conflict_aware.py`（在本工作树根目录）。最终全量运行退出码 0；原 Q1 质量分析 7 项单元测试通过。

A1 51,230 行，A2 17,523 行，A3 203,752 行。首轮计算得 A1 总体 66 对显著负相关，其中 55 对在去重扩展集显著负相关。域级 D 中位数及表见输出 CSV。`Q_A` 不变；`D` 是方向统一后已确认冲突边的样本分歧，不能解释为低质量。

## 限制与下一步

- 相关性与跨域复现只能支持成因模式，不能证明因果或指标语义上的必然取舍。
- A2/A3 只覆盖 arxiv/github；其他五域无独立扩展复核。book 在 A1 仅 171 条。
- 最强 10 条边去除两指标双侧各 1% 极端记录后仍为负，已补入 LaTeX；集成人需复核 Q1 LaTeX 并重新编译整篇 PDF。
- `Q_A` 与 B 侧 `Q_score` 仍未建立数值映射，Q1/Q2 接口不变。
