# CYJ Handoff：Task 8 不确定性范围

## Task / Changes

将 v2 `capabilities.uncertainty_policy` 与 `evaluate.uncertainty.components` 分成 U1 参数、U2 模型形式、U3 预测残差、U4 跨来源、U5 Benchmark 桥接，见 `problem/cyj/20260924-uncertainty-scope.md`。机器响应只给 U1 固定 B7 constant-G 条件均值区间，其余未证项为 null/未量化，不能把窄 bootstrap 解释为总预测区间。

## Input / Commands / Tests

B7 fit SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`；交互比较输出 SHA256 `1d28169ce10f5bc274a82037320fdf003f7e3d2148eff2be91d3c3618708925b`。`python -B src/cyj/build_chm_release_v2.py` 已重生成机器样例，CYJ 单测 44/44 PASS；最终发布提交/manifest SHA 以后续 release handoff 为准。

## Identifiability / Claim / Interface / Next

U1 `conditionally_identified` 于固定半合成 B7 模型，U2/U3 尚未量化，U4 `not_identified`，U5 未消费。最高报告条件均值波动，不提供总预测区间。`ready_for_Q3=false`、`ready_for_Q4=false`。CHM/zhh 必须读取 null 与覆盖范围，不手工填数字；cyj 待新独立数据和桥接证据再更新。
