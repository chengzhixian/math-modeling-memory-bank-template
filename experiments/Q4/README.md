# Q4 当前 v3 实验与复现

当前答卷是 `team/zhh-frontier@ee23b200e9de7f78477d945b186233741bd3b8fd` 的 v3 核心数值及 main 对应的 v3 论文段落。输入为 C2、C3、C4、C6、C7、C8 原始附件和 main 已验收的 Q3 条件格；`outputs/Q4/prepared/` 仅保留 v3 必需的六个处理输入与清单，其余可再生过程表不进入正式交付。

| 实验 | 生产入口 | 当前证据 | 限制 |
|---|---|---|---|
| C7/C8 整理 | `node src/zhh/q4_analysis.js` | `outputs/Q4/context_scenarios.csv`、`c8_bbh_task_aggregation.csv`、`c8_parse_failures.csv` | C7 是观测上下文情景；C8 不与 C2 强行配对 |
| 能力及资源筛选 | `src/zhh/q4_complete.py` → `q4_core_v3.py` | `c4_resource_gate_comparison.csv`、`c3_row_metric_audit.csv`、`results.json` | 开放性为权重与许可证代理；C3 历史评分分来源，不拼成单轨迹 |
| 历史贡献 | `q4_core_v3.py` | `historical_standardized_contributions.csv`、`historical_common_cells.csv`、`historical_contribution_bootstrap.csv` | 格内时间项不是已识别的纯技术因果份额 |
| 两月 q90 与累计最高边界 | `q4_core_v3.py` | `frontier_model_comparison.csv`、`frontier_maximum_backtest.csv`、`frontier_maximum_scenarios.csv` | 四个重叠窗口仅作诊断；纪录保持基线与 q90+尾差条件边界分开，长期范围没有覆盖率保证 |
| Loss 与能力 | `q4_core_v3.py` | `bridge_source_coordinate_validation.csv`、`q3_source_coordinate_stress.csv`、`q3_policy_ranking_stress.csv` | Q3→C6 坐标未标定；固定、联立、独立质量三模式共 14580 行明示压力 |

原分支 v2 论文与 v3 核心不一致，故当前 `paper/latex/sections/Q4/main.tex` 依据 v3 结果重写。`source_manifest_v2.json` 和 `source_manifest_v3.json` 只保留来源身份，不作为 main 当前生成清单；main 当前输入、代码和输出哈希由 `outputs/Q4/manifest.json` 核验。[设计](20260926-q4-core-v3-design.md)、[完整审查](20260926-q4-core-v3-review.md)、[验收澄清](20260926-q4-acceptance-clarification.md) 与[图表登记](FIGURES.md)记录原分支的范围和局限。

在仓库根目录、Python 3.12.14 与 Node 24.19.0 环境运行；Python 包版本见 `scripts/requirements-integrated.txt`。先按 `memory-bank/DATA_INDEX.md` 校验 LFS 原始附件，再依次执行：

```powershell
node src/zhh/q4_analysis.js
node --test src/zhh/q4_analysis.test.js
python -B src/zhh/q4_complete.py
python -B src/zhh/q4_core_v3.py
python -B src/zhh/test_q4_complete.py
python -B src/zhh/test_q4_core_v3.py
python -B src/zhh/verify_q4_core_v3.py
python -B src/zhh/plot_q4_core_v3.py
```

这些命令从 main 当前输入运行；`q4_complete.py` 会在 `outputs/Q4/prepared/` 重新生成临时 v2 处理表，只有 v3 实际调用的六项在 Git 中保留。源码生成的 `results.json`、关键表和三幅正式图经本次集成复算，与来源 v3 数值产物哈希一致。未识别的技术因果份额、跨坐标 Loss 映射和未来覆盖率保持明确限制。
