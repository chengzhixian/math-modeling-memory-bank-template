# 2026-09-24 clean integration 与新分支增量审查

基线：`origin/integration/chm-q1-clean-20260923` at `7a958d7`；比较 `origin/team/cyj-scaling` at `3e20b3e` 与 `origin/team/zhh-frontier` at `d47cd2d`。只记此前审查之后新增内容及其接口影响；既有问题仍见 `20260923_review_resolution_status.md`。

## 按优先级处理的 clean 分支缺陷

1. **P0，真实数据运行中断**：质量敏感性严格筛选后 DSIR 家族无指标，原脚本直接报错。现改为对存活家族重新等权，manifest 显式标记 DSIR 缺席和“仅压力测试”；主 Q 定义没有替换。
2. **P1，eta 区间抽样单位错误**：1M/60M 校准表是同序同配方，13 个目标域共用配方行。原二层 bootstrap 对尺度和目标各自独立抽行，破坏配对相关性。现验证 1M/60M 行对齐，跨目标共享索引并将两尺度配对；1B 单独抽样。新的条件区间为 `[0.097562, 0.200977]`，点估计 `0.145033`；仍条件于固定的 A4+A5 Ridge，不能视为完整不确定性。
3. **P1，图表脚本无法运行**：无头 Windows 上需要 `Agg` 后端，当前 Matplotlib 使用 `tick_labels`，溯源输出缺 `hashlib` 导入。已修复并生成四幅图和输入/图片 SHA256 清单。

## 新增敏感性产物及判断

- 真实 A1–A3 重跑：ID 审计通过；LOO 稳定指标的七域排序与主 Q 完全一致。更严格的 0.75 consensus 方案使 book/arxiv 对调（Spearman 0.9643），但 DSIR 全部被过滤，因此只是两家族压力测试。
- Qurater 四分量先标准化后的排序与主 Q 一致。家族权重 0.05 网格共 231 组，包含零权重极端情景；结果存于 `outputs/chm/quality_review_v1/`，不可据此冻结 Q 尺度。
- RegMix 固定种子 shuffled 五折已生成 `q1_regmix_cv_split_sensitivity.csv`。13 个目标域中有超参数变化和部分 held-out Spearman 差异，主 unshuffled 协议暂不替换。
- 图表 `paper/sections/chm/figures/` 只对应清单中的 `local_recheck_v1` 哈希。

## cyj 新增提交：接口和可借鉴点

- 新的 B1 经典基线为 `L(N,D)=E+A N^{-alpha}+B D^{-beta}`，N、D 单位均为十亿；其接口仍标 `ready_for_Q3=false`。它没有 Q、p、可比 Loss anchor 或传播不确定性，故不能把本分支 Q/p 接到 B1 后发布 Q3 正式最优解。`interfaces/chm/Q2_BRIDGE.md` 的两处“不可直接等同”与 cyj 新合同一致，无新增字段冲突。
- cyj 对 B1 的显示精度/计算量舍入作了复核，且新增 B2/B3 轨迹形状诊断；B2 半合成、B3 插值性质继续限定其验证用途。可借鉴其按 N 分组及 token 尾段的诊断设计，检查后续 Q3 外推；不应把这些诊断当独立真实验证。
- B1 范围约 N=0.070542–11.965825B、D=0.134–299.893B。后续 Q3 预算扫描必须明确训练支持域、计算预算和外推标记。

## zhh 增量

`origin/team/zhh-frontier` 与前次记录的 `d47cd2d` 相同，本轮无新提交。C7 情景（2048/8192/131072 token）仍可作为 Q3 外生情景候选，但正式消费仍待其合同版本及集成验收。本轮没有改写既有 zhh 审查结论。

## 尚需跨成员联合确认

cyj 接受 `Q_z` 到 B 侧 `Q_score` 的可识别映射、以及 13 域 Loss 到 B1 `val_loss` 的 anchor 和单位之后，才能联合验证 Q2/Q3。zhh 的 Loss→Benchmark 桥接及其误差仍是 Q4/能力解释所需输入。chm 不单方填补这些接口。
