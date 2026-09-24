# 请 cyj 定义并交付的接口（chm 的消费需求）

用户已确定：A 侧 Q/p 由 chm 定义并发布 `chm.q1.v1.1`，B 侧标度律、Loss 目标与 Q3 理论由 cyj 定义，chm 按其接口调用。本清单只描述 chm 必需的**输入、输出与验收条件**，不替 cyj选择模型、参数或编造跨附件映射。

## 1. B 侧 Loss 与预测器（Q3 启动门槛）

请提供版本化、可调用的 `predict` 入口或等价机器可读参数文件。至少明确：

- 输入 `N_params_B`（十亿参数）、`D_tokens_B`（十亿 token），若使用质量则说明 `Q_score` 的 B 原生定义、允许范围、基准值；若使用配比则说明接收 `chm.q1.v1.1` 的 17 维顺序/名称和 target，还是由 cyj 内部做情景化处理。
- 输出预测 `loss_value`、`loss_coordinate`（评估语料、tokenizer、交叉熵单位/对数底、模型族）、适用域与外推标记；返回版本和是否 `ready_for_Q3`。不能只给五参数点估计或 audit JSON。
- 模型公式、参数与单位、训练数据来源/版本、B1 行级 Loss 来源判定、按模型规模或轨迹分组的验证结果、参数与预测不确定性及其条件范围。B2/B3 半合成/插值和 B4/B5 同尺度未证实部分单独标识。
- 至少一个真实输入→输出验收样例与数值容差，错误输入（非正 N/D、超出质量范围、未支持的 target）必须报错或显式标外推，不可静默回退。

## 2. A→B 质量消费规则（cyj 定义）

请以赛题附件 B6–B8 **自带**的 `Q_score` 为 B 侧质量模型坐标，并保留 B6/B7 半合成、B8 calibrated/extrapolated 分层；B8 的 extrapolated 行不得当成独立观测来拟合或验证。明确 Q 的模型形式、成本函数、基准值及范围。chm `Q_z` 是 A1–A3 派生量，没有与 `Q_score` 的成对标定，且官方 A16 只有 6/17 个 direct/near-direct 映射，不能形成完整 17 维 Q 向量。默认返回 `mapping_status=unidentified`，将 A 侧排序与 B 原生数值情景分开报告；不能用恒等、MinMax 或手调平移宣称已识别映射。若提出映射，交付配对数据、公式、有效范围、误差与实测验收样例。

## 3. A→B 配比/Loss 桥接规则（cyj 定义）

请判定 B1 `val_loss` 的评估口径是否能与任一 A 侧目标 Loss 可比。交付主 target（若可识别）、至少 3 个敏感性 target、选择证据、参考配比及 p 项进入 B Loss 的公式。若采用 `λ_k(N) × m_k(p)`，请给 λ 的单位、来源、有效范围、区间；无可估证据则标 `scenario`，不能默认为 1，也不能把 13 域原始 Loss 简单平均。chm 提供的 η 仅控制 A 侧相对配比效应的经验尺度变化，不能充当 λ。

## 4. Q3 理论与调用边界（cyj 定义）

请给目标函数和三项成本的精确定义、FLOPs 与 N/D 的单位换算、质量成本函数及参数来源、配比约束、同一个 D 在成本项中的使用规则、允许的预算/模型范围、边际效用和结构转移判据。上下文长度由 zhh C7 作为外生情景，需说明其进入成本或性能公式的位置，不作为可自由内点寻优变量。提供与 `predict` 一致的输入校验、约束残差定义和至少一个可复核算例。

## 交付与验收格式

请在 `interfaces/cyj/` 定义正式合同，在 `src/cyj/` 放可调用实现，在 `outputs/cyj/` 放参数、验证与 manifest；记录精确 Git SHA、各文件 SHA256、形状/字段、状态 `draft/validated`、生成命令、随机种子及尚未识别的桥接项。chm 将按你定义的**正式版本**写适配器并复核验收样例；在 `ready_for_Q3=true` 且对应桥接/情景状态清楚前，只做条件情景或求解器联调，不发布论文最终最优配置。


## 2026-09-24 formal readiness v2 机器字段

为避免把不可识别量硬拼成一个模型，下一版 cyj Q3 bundle 请显式给出：

```text
quality_policy.coordinate = B_native_Q_score
quality_policy.performance_status = validated
quality_policy.joint_NDQ_status = validated
quality_policy.loss_coordinate_id = <明确坐标>
quality_policy.A_Q_mapping_status = unidentified | not_required | validated

p_policy.mode = validated_bridge | sensitivity_only
```

说明：

- `A_Q_mapping_status=unidentified` **允许**进入正式 B-native Q3，只要 Q3 不把 A 侧 `Q_z` 数值直接输入 B 模型。
- 单独拟合一个 B7 Q 项还不够；必须证明或构造一个经过验证的联合 N-D-Q predictor，使三者落在同一 B-native Loss 坐标。
- 若 `p_policy.mode=validated_bridge`，需提供 `primary_anchor` 且 `lambda_status=validated`，才允许发布唯一 p/完整 NDQP。
- 若 `p_policy.mode=sensitivity_only`，至少给 3 个 target，且 `unique_p_claim_allowed=false`；此时正式主结果是 NDQ，p 只做多 target 敏感性，不要求人为制造唯一 anchor/lambda。
