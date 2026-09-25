# chm → zhh / 集成人：Q3 正式结果接口 v2

状态：schema frozen，尚无 formal 数据。正式文件只能由 `src/chm/q3_publish.py` 在 readiness v2 通过后生成。

## 1. 主配置 optimization.csv

每行对应一个正式情景：预算 × C7 上下文 × 质量成本族；若 p 为 validated bridge，则包括唯一 p。

必需字段：
- run_id
- budget_FLOPs
- context_tokens
- quality_family
- result_scope：full_NDQP 或 NDQ_with_p_sensitivity
- N_params_B, D_tokens_B, Q_score
- loss_value, loss_coordinate_id
- C_train_FLOPs, C_quality_FLOPs, C_attention_FLOPs, C_total_FLOPs
- budget_residual_FLOPs, budget_utilization
- active_set, kkt_check_pass
- support_status, extrapolation_status
- status：正式发布时必须为 formal_validated
- cyj_ref, chm_q1_version, zhh_ref

若 result_scope=full_NDQP，还需：
- p_mixture_id 或版本化完整 17 维 p 文件引用；
- p_policy=validated_bridge；
- p_target；
- lambda_status=validated。

若 result_scope=NDQ_with_p_sensitivity：
- 主配置行不得伪造唯一 p；
- p_policy=sensitivity_only；
- 配比结论写入 p_sensitivity.csv。

## 2. p_sensitivity.csv

用于未识别唯一跨 Loss bridge 时的正式 p 敏感性。至少包含：
run_id、target、loss_coordinate_id、scale_transfer_status、mixture_id、A_target_delta、selection_support、large_scale_reliability_flag、status。

loss_coordinate_id 固定为 `A4_A5_1M_target_cross_entropy_contrast`；scale_transfer_status 固定为 `not_identified_from_attachment_A`。禁止 eta 和 lambda_scenario 字段；A_target_delta 必须有限。每个主配置 run_id 均需对应不确定性记录及（敏感性模式下）配比记录。

zhh 不应把这些 target-specific A-side 变化直接当 B1 Loss。

## 3. uncertainty_summary.csv

每个 run_id × variable 一行，字段：
variable、point、median、p025、p975、n_draws、coverage_scope、sources。

coverage_scope 必须说明区间覆盖了哪些层：cyj 标度律参数、B-native Q、chm 的 A 原生配比对比、数值求解、zhh bridge 等。没有覆盖的层不得被隐去。

## 4. manifest.json

记录 schema version、formal readiness snapshot、cyj/chm/zhh 精确 SHA、输入输出 SHA256、运行命令/随机种子、支持域、p policy、不确定性覆盖范围、生成环境。

## 5. zhh 消费规则

zhh 只消费：
- status=formal_validated；
- loss_coordinate_id 明确；
- kkt_check_pass=true；
- 预算残差在容差内；
- 支持域/外推标志明确；
- 不确定性文件与 manifest 匹配。

diagnostic_only、scenario_only、software_validation_only 不进入最终 Loss→Benchmark 主结果。
