# 问题一：数据质量评价与训练数据配比效应（严谨重构版）

当前正式 LaTeX 见 \`paper/latex/sections/chm/q1.tex\`。本草稿只保留建模逻辑与可识别性边界。

## 1. 质量代理

A1--A3 没有样本级真实质量标签，因此定义 A 侧综合质量代理 \(Q_A\)，不把它解释成客观质量真值。22 个指标先按字段语义压缩，使用 A1 的 median/MAD 冻结标准化；8 个 model-based 指标作为语义锚点，其余指标用域内 Spearman + Fisher-z 对齐方向。三个指标家族采用组内等权、组间等权：
\[
G_{ig}
=
\frac1{|\mathcal J_{ig}|}\sum_{j\in\mathcal J_{ig}}z^+_{ij},
\qquad
Q_{A,i}
=
\frac{\frac13\sum_gG_{ig}-\mu_{S,A1}}{\sigma_{S,A1}}.
\]
家族等权是透明定义，不是数据唯一识别结果；必须结合 argmax、22 指标等权、家族删除敏感性解释。

指标冲突直接使用方向统一后的域内 Spearman，不再额外发明主模型冲突函数。clean 分支新增复制性结果显示：arxiv 的 96 个样本负相关中 92 个、github 的 91 个中 91 个，在完整扩展和 non-overlap 扩展仍为负；两域共有 56 个三层稳定负相关指标对。当前仍不宣称 bootstrap/FDR 显著性。

## 2. 13-target 配比代理

A4 配方归一化后
\[
\mathbf1^\top\mathbf p_i=1.
\]
以
\[
\mathbf p_{\rm ref}
=
\frac1{512}\sum_i\mathbf p_i
\]
为参考，对每个验证域 \(k\) 独立拟合零和 Ridge：
\[
(\hat\alpha_k,\hat{\boldsymbol\beta}_k)
=
\arg\min
\sum_i
[L_{ik}-\alpha-\boldsymbol\beta^\top(\mathbf p_i-\mathbf p_{\rm ref})]^2
+
\lambda_k\|\boldsymbol\beta\|_2^2,
\quad
\mathbf1^\top\boldsymbol\beta=0.
\]
\(\lambda_k\) 只在 A4+A5 内五折选择。

相对效应：
\[
m_k(\mathbf p)
=
\hat{\boldsymbol\beta}_k^\top
(\mathbf p-\mathbf p_{\rm ref}).
\]
若从域 \(r\) 向域 \(j\) 转移 \(\delta\)，则
\[
\Delta m_k
=
\delta(\hat\beta_{k,j}-\hat\beta_{k,r}).
\]

## 3. 多维 Loss

将 13 个 target 联立：
\[
\widehat{\mathbf L}_{1M}(\mathbf p)
=
\widehat{\boldsymbol\alpha}
+
\mathbf B(\mathbf p-\mathbf p_{\rm ref}),
\qquad
\mathbf B\in\mathbb R^{13\times17}.
\]
因此
\[
\mathbf m(\mathbf p)=\mathbf B(\mathbf p-\mathbf p_{\rm ref}).
\]

配比决策限定在 A4 观测配方凸包
\[
\mathcal P_A=\operatorname{conv}\{\mathbf p_1,\ldots,\mathbf p_{512}\}.
\]

决策层按需求选择：
\[
J_{\mathbf s}(\mathbf p)
=
\mathbf s^\top\mathbf m(\mathbf p)
\]
（已知权重或明确声明的等权情景）；
\[
\min_{\mathbf p\in\mathcal P_A}\max_km_k(\mathbf p)
\]
（鲁棒最差能力）；
或
\[
\min m_q(\mathbf p)
\quad
{\rm s.t.}\quad
m_k(\mathbf p)\le\varepsilon_k
\]
（重点能力 + 保护约束）。若没有权重或阈值，Q1 不自行创造数值。

## 4. 文献函数与主模型

Data Mixing Laws 使用逐验证域指数混合律，BiMix 建模配比与数据量的双变量关系，DoReMi 使用 Group DRO 的最坏域 excess-loss 思想。它们支持“逐维建模后再做多目标决策”的框架，但附件 A 没有对应 \(D\)，所以不直接照搬 BiMix 的双变量尺度项，也不把 DoReMi 等同于本题 minimax。

当前已经在 A6--A11 held-out 上验证的是 Ridge；Data Mixing Laws 的指数形式只能作为候选模型，必须在同一 A4+A5 拟合/调参协议下与 Ridge 比较后才能替换。

## 5. 跨实验组验证

冻结 1M Ridge 后：
\[
\rho_{k,\ell}
=
\rho_S(
\widehat L_{k,1M}(\mathbf p_i^{(\ell)}),
L_{ik}^{(\ell)}
).
\]
13-target 中位 Spearman：
- 1M：0.8381；
- 60M：0.8381；
- 1B：0.7067。

A6/A8 同一 256 配方真实 Loss 的 1M↔60M 中位 Spearman 为 0.9944。

## 6. 不再拟合连续跨规模幅度

A 配方实验没有对应 \(D\)，真实 \(N\) 位置只有 1M/60M/1B，且 1B 支持集改变。因此旧 \(b_k(N)\)、公共 \(\eta\) 不再进入 Q1 主模型。A12--A15 只作为 estimated/extrapolated 压力测试。

## 7. Q1 → Q2

Q1 正式输出：\(Q_A\)、A16 映射、13-target Ridge、\(\mathbf m(\mathbf p)\)、held-out 排序证据。Q1 不提供 \(Q_A\to Q_{\rm score}\) 数值映射，不把 \(m_k\) 直接加到 B1 Loss，也不提供 \(N,D\)-dependent 的配比尺度函数。
