# zhh接口 v2：条件Q4答卷与默认拒绝跨坐标换算

发布者zhh；分支 `team/zhh-frontier`，尚未main集成。完整答案 `outputs/zhh/Q4_FINAL_ANSWER_V2.md`；完整审查 `experiments/zhh/20260926-q4-v2-full-review.md`。

## C7接口保持

`outputs/zhh/context_scenarios.csv` 为2048/8192/131072 Token观测外生情景；SHA256 `b494a8949a74133e779b683c8a46021b5e16308970150bd18e033553c6fc8608`。131072支持稀疏，不改成连续优化变量。

## 能力和资源

六任务等权，百分制；提交日；空/非有限/越界排除，同名最新行去重。主基础204，chat477+领域微调1143；持续预训练/合并/多模态只作扩展敏感性。开放规则为Epoch=no优先排除，其余yes/许可证代理；strict yes与许可证允许清单另列，不声称逐仓库权重/许可核验。

C4资源使用截至2025-03-13、明确Token、语言生成、开放、阶段/架构线索和置信筛选的81条主记录，93宽比值敏感性。C4算力可能由6ND估算，不能视为独立机制验证。全部剔除与单位证据见 `q4_v2/c4_resource_audit.csv`。

## 前沿预测接口

根 `outputs/zhh/frontier_forecast.csv` 是16条主条件预测：两模型类型×12/24月×四算力对数增长情景，起点2025-03-13。前沿定义为近期两月实际六任务均分q90的局部演化；不是全世界最大值或平均模型分数。

主要列：origin/target_date/horizon_months/type/scenario/predicted_score、conditional_parameter_p05/p95、scenario_lower/upper、eta_assumed/drift_retention_assumed、N/D/C情景配置、支持域外距离、带符号贡献。参数条件范围与情景包络都不叫95%预测区间。完整筛选/窗口/分位/速度敏感性及基线见 `q4_v2/`。

主资源式为C≈6ND，eta=.5时N/D等比例对数配置，lambda=.5时间漂移保留。eta与lambda均是假设；C2无D，不补造独立D能力系数。基础模型回测不优于基线，不给“准确预测”评级。

## Loss→Benchmark接口及上游

`outputs/zhh/bridge_interface.json` 发布 `zhh.bridge.conditional.v2`：

- formal_cross_coordinate_status=unidentified，ready_for_conversion=false；formal请求继续拒绝。
- conditional_mapping_status=sensitivity_only。显式声明同Loss坐标假设并在等级Loss/N支持内，可读 `q4_v2/bridge_mappings.csv` 的单调候选，S=100 sigmoid(a+bLoss L+b_logN log10N)。
- high7与medium68独立拟合、四类基线/留一，报告别名及相邻版本整族留出。high常数RMSE0.426优于Loss0.538，纯Loss机制没有验证。
- `q4_v2/q3_bridge_sensitivity.csv` 的assumption_score只可作条件分析；empirically_calibrated_score、joint_95_prediction_interval为空。out_of_support_or_infeasible行不给分数。

临时未集成Q3输入固定 `integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be`，生产者v8 release subject为615c0785；原manifest/grid快照逐字节hash核验。上游是条件跨A/B模型，没有联合95%区间；本接口不提高其证据等级。

## 旧结果和复现

原Node基线（含撤回的空预测）输出到 `outputs/zhh/legacy_baseline/`；根三文件是当前v2，Node历史测试不会覆盖新发布。完整命令/环境/输入输出hash见q4_v2/manifest.json；答案/图/LaTeX hash见answer_manifest.json。数据上下文继续受AI_READING_RULES约束，不恢复隐藏文字或作废历史模型。
