# Q4：技术演进与算力放缓

[完整条件答卷](ANSWER.md)与 [v3 论文段落](../../paper/latex/sections/Q4/main.tex) 使用同一 `results.json`、`interface.json` 和 `manifest.json`。主证据包括能力与资源筛选、共同支持历史分解、滚动回测、12/24 月算力情景、来源内 Loss 桥接，以及 Q3 上游误差传播；细目、命令和适用范围见[实验索引](../../experiments/Q4/README.md)。

`prepared/` 是从原始附件和 Q3 当前结果生成 v3 所需的最小处理输入。Q3 固定配方、观测配方联立和独立原生质量三张表均按上游清单冻结并校验。最高能力输出分为 `frontier_maximum_model_comparison.csv` 的纪录保持基线和 `frontier_maximum_scenarios.csv` 的 q90+尾差条件边界。当前接口仍标明纯技术贡献、Q3→C6 经验换算和长期预测覆盖率未识别；条件情景不能解释为已校准的真实未来得分。
