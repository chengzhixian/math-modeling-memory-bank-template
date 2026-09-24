# zhh 接口结果 v1

状态：已运行基线及开放性/模型类型敏感性，尚未进入 `main`。结果仅为短窗口关联。

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
- 因此 Q1–Q3 的 Loss 输出不能直接换算成确定的 Benchmark 增益。7.06 分是一次留出测试的 RMSE，不是可加减的误差界或 95% 预测半宽；按 Loss 来源留出的 RMSE 为 9.887 分。当前机器接口返回 `unidentified`，不得据此生成能力区间。
- 完整数值和系数见 `outputs/zhh/q4_results.json` 的 `bridge` 字段。

## Q4 结果文件

- `outputs/zhh/q4_results.json`：全部口径、模型、验证和限制。
- `outputs/zhh/c8_bbh_task_aggregation.csv`：1,860 个模型的 24 项 BBH 聚合。
- `outputs/zhh/c8_parse_failures.csv`：4 个损坏 JSON 的文件级证据。
- `outputs/zhh/frontier_forecast.csv`：算力放缓预测状态 `not_identified_for_compute_slowdown`，预测与区间字段为空。

## 开放性和模型类型敏感性

主扩展集排除了 Epoch 明确标为 `no`、但有 Hub License 的 6 条冲突记录，共 2,672 条；许可证只是开放权重的代理，不能证明权重可获取。仅纳入 Epoch 明确 `yes` 的严格集有 424 条。两集分别重跑了关联回归、窗口分解和时间留出，详见 `q4_results.json` 的 `openFilterSensitivity`。扩展集的绝对值归一规模份额为 43.85%，严格集为 48.97%；两组选择机制不同，这些份额均非技术贡献因果比例。

扩展集中 pretrained 254 条的分组时间斜率为 0.431 分/月，non-pretrained 2,418 条为 1.115 分/月；含类型交互的拟合及每个模型仅保留最新记录的复核见 `typeSensitivity`。共同时间斜率不应用于正式 12 个月外推。
