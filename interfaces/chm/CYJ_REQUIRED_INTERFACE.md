# 请 cyj 定义并交付的接口（适配 chm.q1.v1.2）

## 1. B-native Loss predictor

请提供版本化 \`predict\` 入口，至少明确 \(N_{\rm params}\)、\(D_{\rm tokens}\)、B-native \(Q_{\rm score}\) 的单位、有效范围、Loss 坐标、训练/验证数据与不确定性。

## 2. A→B 质量边界

chm 的 \(Q_A\) 与 B6--B8 的 \`Q_score\` 没有成对标定。若没有新增证据，应保持
\`\`\`text
A_Q_mapping_status = unidentified
\`\`\`
这不阻塞 B-native Q 建模。

## 3. A→B 配比/Loss 桥接

Q1 只交付
\[
m_k(\mathbf p)
=
\hat{\boldsymbol\beta}_k^\top
(\mathbf p-\mathbf p_{\rm ref}),
\]
坐标为 A4+A5 1M target cross-entropy contrast。若 cyj 能识别 B1 \`val_loss\` 与某个或某组 target 的关系，请交付桥接函数、参数来源、单位、有效范围和 held-out 验证；否则正式使用
\`\`\`text
p_policy.mode = sensitivity_only
unique_p_claim_allowed = false
\`\`\`
不需要为了形式完整人为制造 anchor、\(\lambda\) 或 \(\eta\)。

## 4. 多目标接口

Q1 提供 13 维 \(\mathbf m(\mathbf p)\)。若 Q2/Q3 需要标量目标，请显式声明：
- 已知 target 权重；
- 等权情景；
- minimax；
- 重点 target + 保护阈值；
- 或 target panel/Pareto。

## 5. Q3 readiness

正式 bundle 至少明确：
\`\`\`text
quality_policy.coordinate = B_native_Q_score
quality_policy.joint_NDQ_status = validated
p_policy.mode = validated_bridge | sensitivity_only
\`\`\`
并记录精确 Git SHA、文件 SHA256、schema/version、训练/验证划分和外推边界。
