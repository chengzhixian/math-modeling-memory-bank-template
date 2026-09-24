# chm → cyj Q2 桥接边界 v2.0

日期：2026-09-24  
Q1 生产者：\`chm.q1.v1.2\`

## 1. 质量坐标

\(Q_A\) 是 A1--A3 的描述性综合质量代理；B6--B8 的 \`Q_score\` 是 B 侧原生质量坐标。附件没有 \(Q_A\leftrightarrow Q_{\rm score}\) 的成对标定样本，因此默认
\`\`\`text
A_Q_mapping_status = unidentified
\`\`\`
禁止恒等、MinMax 或手调线性映射后宣称“已标定”。

## 2. 配比坐标

Q1 对 13 个目标域分别给出
\[
m_k(\mathbf p)
=
\hat{\boldsymbol\beta}_k^\top
(\mathbf p-\mathbf p_{\rm ref}),
\]
其坐标固定为
\`\`\`text
A4_A5_1M_target_cross_entropy_contrast
\`\`\`
它不是绝对 Loss，也不是 B1 \`val_loss\`。

## 3. 不再提供跨规模幅度

Q1 v1.2 明确
\`\`\`text
cross_scale_transfer = not_identified_from_attachment_A
bridge_to_B1_val_loss = unidentified
\`\`\`
旧的 \(\eta\) 仅保留历史审计。若 Q2 需要 \(N,D\)-dependent 配比项，必须由 cyj 基于 B 侧或跨附件证据重新识别并验证；无法识别时使用
\`\`\`text
p_policy.mode = sensitivity_only
unique_p_claim_allowed = false
\`\`\`

## 4. 多 target 消费

Q1 的正式对象是
\[
\mathbf m(\mathbf p)\in\mathbb R^{13}.
\]
若 Q2/Q3 没有唯一 target anchor，应保留多 target 面板或采用明确声明的等权/minimax/保护约束情景，不得把 13 个原始 Loss 无依据平均成 B1 Loss。

## 5. Q3 readiness

正式 Q3 至少需要：
1. 同一 B-native Loss 坐标上的 validated \(N,D,Q\) predictor；
2. 明确的 p policy：\`validated_bridge\` 或 \`sensitivity_only\`；
3. 不把 \(Q_A\) 直接作为 B-native \`Q_score\`；
4. 不读取 Q1 历史 \(\eta\) 作为默认参数。
