# zhh 接口结果 v1

状态：已运行基线，尚未进入 `main`。

## 给 chm 的 C7 情景

机器可读文件：`outputs/zhh/context_scenarios.csv`。

| 情景 | 上下文长度（Token） | 依据 |
|---|---:|---|
| low | 2,048 | C7 实际观测 |
| medium | 8,192 | C7 实际观测 |
| high | 131,072 | C7 实际观测 |

用于 Q3 时须把它们作为外生敏感性情景，不作为内点寻优变量。

## 给 cyj/chm 的桥接约束

- 高可比样本仅 7 条；75 条分级加权模型按 Loss 排序留出集 RMSE 为 7.06 Benchmark 分，`R²=-1.376`。
- 因此 Q1–Q3 的 Loss 输出不能直接换算成确定的 Benchmark 增益。建议至少以 ±7.06 分作为经验映射误差的量级参考，并另叠加上游模型不确定性；超出桥接数据 Loss/参数范围时不得外推为主结论。
- 完整数值和系数见 `outputs/zhh/q4_results.json` 的 `bridge` 字段。

## Q4 结果文件

- `outputs/zhh/q4_results.json`：全部口径、模型、验证和限制。
- `outputs/zhh/c8_bbh_task_aggregation.csv`：1,860 个模型的 24 项 BBH 聚合。
- `outputs/zhh/c8_parse_failures.csv`：4 个损坏 JSON 的文件级证据。
- `outputs/zhh/frontier_forecast.csv`：12 个月算力放缓情景预测。
