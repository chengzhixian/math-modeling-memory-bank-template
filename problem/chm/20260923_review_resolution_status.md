# chm Q1 审查问题处理状态

日期：2026-09-23  
工作分支：`integration/chm-q1-clean-20260923`  
原则：按“会影响当前结论/下游接口 > 统计稳健性 > 复现与协作”排序处理。

## P0：结论与下游接口

| 编号 | 状态 | 当前处理 |
|---|---|---|
| R03 | CLOSED | 当前活动文档已删除来自作废历史的候选方法表述，且不再保留具体方法名；后续方法必须独立举证。 |
| R10 | CHM-BOUNDARY-CLOSED / WAIT-CYJ | 已新增 `interfaces/chm/Q2_BRIDGE.md`：明确 `Q_z` 与 `Q_score` 无成对标定、13 域 Loss 与 B1 `val_loss` 未证明可比；禁止恒等/MinMax/单位系数硬拼。等待 cyj 在其 predictor 接口接受后才可 joint-validated。 |
| R11 | PROTOCOL-CLOSED / WAIT-DOWNSTREAM | 已新增 `interfaces/chm/UNCERTAINTY.md`，明确 Q 定义、域映射、anchor、eta、跨 Loss 桥接和 zhh 桥接误差的传播层级。最终数值传播等待 cyj/zhh predictor。 |
| R15 | CLOSED | 活动实验说明与 anchor policy 已刷新为 `local_recheck_v1` 数值；旧 handoff 标记为 historical snapshot。 |
| R07 | CLOSED | A12–A15 明确改写为“已见 1M 训练配方上的尺度外推”，不再称新配方泛化。 |
| R08 | CLOSED | eta 明确降级为经验尺度传递参数；论文/实验均注明 1B 配方支持集不同，不能解释为纯规模弹性。 |
| R09 | IMPLEMENTED / RECOMPUTE-PENDING | 现有区间已明确标为条件 bootstrap；`q1_mixture_scale_transfer.py` 已增加“目标域 + 校准样本”二层重抽样，仍条件于 A4+A5 Ridge。新数值需完整本地重跑。 |

## P1：Q 与回归稳健性

| 编号 | 状态 | 当前处理 |
|---|---|---|
| R05 | IMPLEMENTED / LFS-RUN-PENDING | `q1_quality_sensitivity.py` 已加入 leave-one-domain-out 方向稳定性、稳定指标过滤版本和 rank 对照。需要 A1–A3 LFS 正文实跑后才能判断主 Q 是否要改。 |
| R06 | IMPLEMENTED / LFS-RUN-PENDING | 已加入 RPS/DSIR/model 三家族权重单纯形扫描（默认步长 0.05），输出各域 rank 范围和 top/bottom 频率。 |
| R12 | INTERFACE-RISK-CLOSED / LFS-RUN-PENDING | 因 R10 已禁止把 A 侧 Q 数值直接映射到 B 侧，样本量主导的绝对标准化不再进入下游主模型；同时已加入 equal-domain-weight 标准化敏感性以量化数值尺度差异。 |
| R16 | IMPLEMENTED / LFS-RUN-PENDING | 已加入 Qurater 四分量分别稳健标准化后再聚合的敏感性版本，与当前 mean4 主方案比较七域排序。 |
| R13 | CODE-CLOSED / RERUN-PENDING | 主分析新增按域空 ID/重复 ID 硬断言、manifest 审计输出和回归测试；下次主分析重跑即生成 `quality_id_integrity_v0.csv`。 |
| R14 | IMPLEMENTED / RERUN-PENDING | 保留当前 unshuffled 5-fold 作为可复现主协议，同时新增固定 seed shuffled 5-fold 敏感性和 held-out Spearman 对照。公开 RegMix notebook 未独立固定 Ridge 行顺序，不再声称 `shuffle=False` 是论文精确实现。 |

## P2：文档、协作与图表

| 编号 | 状态 | 当前处理 |
|---|---|---|
| R04 | CLOSED | 当前合同重写为 `CONTRACT v1.4`；历史全文移至 `interfaces/chm/archive/CONTRACT_v1.2.md`，并加 DO NOT CONSUME 标记。 |
| R01 | CLOSED | 环境文档规定统一以 SHA/parent/topology 判定先后，时间显示统一注明 Asia/Shanghai；不再用页面时钟判提交顺序。 |
| R02 | CLOSED | 当前可集成工作已建立在 clean main 血缘上；环境文档明确以后只用 `fetch + merge origin/main` 接公共更新，禁止逐文件复制伪同步。 |
| R17 | IMPLEMENTED / LOCAL-RUN-PENDING | `q1_figures.py` 已固定读取 `local_recheck_v1`，并新增输入/图片 SHA256 provenance manifest；当前远程尚未提交正式 PNG，必须在完整本机运行后生成。 |

## 必须执行的完整本地验收

由于 ChatGPT 当前 GitHub 连接器只能读取 A1–A3 的 Git LFS pointer，无法获取其压缩正文，因此下列数据密集型敏感性**没有伪造运行结果**。在 chm 有完整 LFS 的机器执行：

```powershell
./.venv/Scripts/python.exe src/chm/q1_quality_analysis.py
./.venv/Scripts/python.exe src/chm/q1_quality_delivery.py
./.venv/Scripts/python.exe src/chm/q1_quality_sensitivity.py
./.venv/Scripts/python.exe src/chm/q1_regmix_domainwise.py
./.venv/Scripts/python.exe src/chm/q1_mixture_interface.py
./.venv/Scripts/python.exe src/chm/q1_mixture_scale_transfer.py
./.venv/Scripts/python.exe src/chm/q1_verify_local.py
./.venv/Scripts/python.exe src/chm/q1_figures.py
./.venv/Scripts/python.exe -m unittest discover -s src/chm -p test_q1_quality_analysis.py
```

验收后必须把新生成的 `outputs/chm/quality_review_v1/`、CV split sensitivity、更新后的 eta manifest、图表及 figure manifest 一起提交，再决定 R05/R06/R09/R12/R14/R16/R17 是否从 pending 关闭。

## 当前禁止事项

- 不直接 merge `team/chm-data` 到 main；
- 不从 `outputs/chm/archive/web_v0/` 读取当前系数；
- 不把尚未实跑的敏感性写成“已验证稳健”；
- 不在 cyj 验收前发布 Q3 正式最优配置；
- 不从已作废历史恢复任何方法、参数、阈值、数值或结论。
