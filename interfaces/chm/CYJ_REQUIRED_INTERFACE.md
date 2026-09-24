# 请 cyj 定义并交付的接口（chm 的消费需求）

日期：2026-09-24  
适配 Q1 生产者：`chm.q1.v1.2`

用户已确定：A 侧 Q/p 由 chm 定义，B 侧标度律、Loss 目标与 Q3 理论由 cyj 定义。Q1 v1.2 已将“由附件 A 拟合连续配比尺度衰减”的旧做法撤出，因此下面的要求不再假定 chm 会提供 `eta` 或任何 (N,D)-dependent 配比幅度。

## 1. B 侧 Loss 与预测器（Q3 启动门槛）

请提供版本化、可调用的 `predict` 入口或等价机器可读参数文件，至少明确：

- 输入 `N_params_B`（十亿参数）、`D_tokens_B`（十亿 token）；若使用质量，说明 B-native `Q_score` 的定义、允许范围和基准值。
- 输出 `loss_value`、`loss_coordinate`（评估语料、tokenizer、交叉熵单位/对数底、模型族）、适用域与外推标记；返回版本和 `ready_for_Q3`。
- 模型公式、参数、单位、训练数据来源/版本、B1 行级 Loss 来源判定、按模型规模/轨迹分组的验证结果，以及参数/预测不确定性。
- 至少一个真实输入→输出验收样例与数值容差。非正 N/D、超出质量范围、未支持 target 等错误输入必须报错或显式标外推，不得静默回退。

## 2. A→B 质量消费规则

请以附件 B6–B8 **自带**的 `Q_score` 作为 B 侧质量模型坐标，并保留 B6/B7 半合成、B8 calibrated/extrapolated 的数据性质。

chm 的

[
Q_A
]

是 A1–A3 22 个质量信号构造的综合质量代理，没有与 B-native `Q_score` 的成对标定，且 A16 仅 6/17 个域属于 direct/near-direct。因此默认：

```text
A_Q_mapping_status = unidentified
```

这不阻塞 B-native Q 模型，只意味着不能把 A 侧 (Q_A) 数值直接送入 B 预测器。若 cyj 以后提出 A→B 质量映射，必须同时交付配对数据、公式、误差、有效范围和 held-out 验收证据。

## 3. A→B 配比/Loss 桥接

Q1 v1.2 交付的是

[
m_k(mathbf p)
=
hat{oldsymboleta}_k^	op
(mathbf p-mathbf p_{m ref}),
]

其坐标固定为：

```text
A4_A5_1M_target_cross_entropy_contrast
```

并明确：

```text
cross_scale_transfer = not_identified_from_attachment_A
bridge_to_B1_val_loss = unidentified
```

因此请 cyj 判定 B1 `val_loss` 与 Q1 13 个 target Loss 是否存在可验证的可比关系。

### 若可以识别桥接

请定义完整形式，例如一般地写为

[
Delta L_B
=
Phi_k(N,D,Q_B,m_k(mathbf p);	heta_k),
]

其中函数 (Phi_k) 的具体形式不能由 chm 预设，必须由 cyj 根据可用的 B 侧/跨附件证据确定。至少交付：

- target (k) 的选择依据；
- (Phi_k) 的数学形式与推导；
- 参数 (	heta_k) 的估计数据和单位；
- (N,D,Q_B) 的有效范围；
- held-out 验证；
- `bridge_status=validated`；
- 至少 3 个 target 的敏感性结果。

不得默认 (Phi_k=m_k)，也不得默认 (Phi_k=(N/N_0)^{-eta}m_k)。

### 若不能识别桥接

正式使用：

```text
p_policy.mode = sensitivity_only
unique_p_claim_allowed = false
```

此时 Q2/Q3 的主体结果在 B-native (N,D,Q_B) 坐标完成，Q1 的 13-target (m_k) 只用于配比敏感性分析。**不需要为了形式完整而人为制造唯一 anchor、lambda 或 eta。**

## 4. Q3 理论与调用边界

请给出：

- 目标函数和三项成本的精确定义；
- FLOPs 与 N/D 的单位换算；
- B-native 质量成本函数及参数来源；
- 配比若进入正式模型时的桥接状态；
- 同一个 D 在各成本项中的使用规则；
- 允许的预算/模型范围；
- 边际效用和结构转移判据；
- 参数及预测不确定性。

上下文长度由 zhh C7 作为外生情景，不作为可自由内点寻优变量。

## 5. 正式 readiness 机器字段

下一版 cyj Q3 bundle 至少应明确：

```text
quality_policy.coordinate = B_native_Q_score
quality_policy.performance_status = validated
quality_policy.joint_NDQ_status = validated
quality_policy.loss_coordinate_id = <明确坐标>
quality_policy.A_Q_mapping_status = unidentified | not_required | validated

p_policy.mode = validated_bridge | sensitivity_only
```

解释：

- `A_Q_mapping_status=unidentified` 可以进入正式 B-native Q3，只要没有把 (Q_A) 数值直接作为 B 模型输入。
- 若 `p_policy.mode=validated_bridge`，必须有可验证的跨 Loss 公式、参数和 held-out 证据。
- 若 `p_policy.mode=sensitivity_only`，至少给出多个 target 情景，且 `unique_p_claim_allowed=false`。
- Q1 v1.2 **没有 `eta` 字段**。任何 downstream 的跨规模配比参数均属于 downstream 自己的模型/情景，不得标成“由 Q1 已验证”。

## 6. 交付格式

请在 `interfaces/cyj/` 定义正式合同，在 `src/cyj/` 放可调用实现，在 `outputs/cyj/` 放参数、验证与 manifest，并记录：

- 精确 Git SHA；
- 文件 SHA256；
- schema/version；
- 生成命令与随机种子；
- 数据来源和性质；
- 训练/验证/外推划分；
- 尚未识别的桥接项；
- `ready_for_Q3`。

chm 只按 cyj 的正式版本写适配器；在 `ready_for_Q3=true` 且 p/Q 的状态清楚以前，不发布论文最终最优配置。