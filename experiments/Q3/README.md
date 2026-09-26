# Q3 实验与审查

- [题面与数值完整审查](REVIEW.md)：变量来源、可识别性、成本与求解器、结构转移、敏感性和从零 red-team；从 CHM 固定提交选择性迁入。
- [真实公开 N/D 部分外测](EXTERNAL_VALIDATION.md)：公开模型筛选、同族排序及预算选择反例；不检验跨来源 Q/p 联合最优。
- [CYJ 独立条件验收](INDEPENDENT_ACCEPTANCE.md)：三模式 108 格和九情景 243 格复核，及未独立重跑的公开外测范围。报告原文取自 CYJ `53b4fb5`；其中的 main SHA 是验收时快照，机器 JSON 已按问题收录到 `outputs/Q3/`。
- 机器结果集中在 [`outputs/Q3`](../../outputs/Q3/README.md)：三模式各 36 格、82 个转移括区、九个桥接压力情景、1449 行假设扫描和当前 main 发布清单。当前生产代码已纳入 main 的 `src/chm/`，来源为 `c052b6918c3f77a2285622521d8abb1b429513be`。
- 九情景官方预算逐格表和 42 个公开模型逐行外测表保留了从摘要到逐行观测的证据。公开外测默认用冻结的 42 行表复核当前 B1 预测、排名和预算选择；原始 104 模型若需重新下载，应核对 `a003c4913793ac2ae7ef87b28ecb562955d026d5` 的来源仓库提交。

上述两份原始审查记录内的 `outputs/chm/...` 路径是来源提交中的复现路径；main 的精简对应文件位于 `outputs/Q3/`。数值解只在声明的成本代理、支持域、87 条可行已观测配方与 A/B 桥接假设下成立。

由仓库根目录、Python 3.12.14 和 `scripts/requirements-integrated.txt` 中的依赖运行：

```powershell
python -B src/chm/q3_conditional_v8.py
python -B src/chm/q3_v8_transition_scan.py
python -B src/chm/q3_v8_assumption_sensitivity.py
python -B src/chm/q3_external_nd_audit.py
python -B src/chm/q3_v8_publish.py
python -B src/chm/test_q3_conditional_v8.py
```

重跑前先校验 Q1/Q2 当前输入。为保留已签核表，原始数值网格亦可调用 `q3_conditional_v8.generate(Path('data/processed/Q3/repro'))` 写入忽略目录，再按 LF 口径比较；当前主表和复核表数值一致。`src/chm/q3_v8_publish.py` 校验 main 当前代码、论文和输出的哈希。外部检验重新计算得到三个来源内 Spearman 约 0.974、0.987、0.974，但不验证四变量最优。
