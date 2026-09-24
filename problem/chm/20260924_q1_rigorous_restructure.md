# Q1 严谨重构说明

日期：2026-09-24  
维护分支：\`integration/chm-q1-clean-20260923\`

## 原则

第一问只使用附件 A 能直接识别的变量和关系：
1. A1--A3 没有真实质量标签，因此质量标量只能作为显式定义的代理指数；
2. A4+A5 可识别 17 维配比到 13 个目标域 Loss 的关系；
3. A6--A11 可用于冻结模型的外部验证；
4. A4--A15 没有与配方实验对应的 \(D\)，不能单独建立 \(N-D\) 标度律；
5. A12--A15 是 estimated/extrapolated，只用于压力测试。

## 正式模型

质量侧：
\[
Q_A=\text{A-side composite quality proxy}.
\]

配比侧：
\[
\widehat L_{k,1M}(\mathbf p)
=
\hat\alpha_k+
\hat{\boldsymbol\beta}_k^\top
(\mathbf p-\mathbf p_{\rm ref}),
\]
\[
m_k(\mathbf p)
=
\hat{\boldsymbol\beta}_k^\top
(\mathbf p-\mathbf p_{\rm ref}).
\]

多维形式：
\[
\mathbf m(\mathbf p)
=
\mathbf B(\mathbf p-\mathbf p_{\rm ref}),
\qquad
\mathbf B\in\mathbb R^{13\times17}.
\]

决策支持域：
\[
\mathcal P_A
=
\operatorname{conv}\{\mathbf p_1,\ldots,\mathbf p_{512}\}.
\]

允许的决策口径：已知权重标量化、明确声明的等权情景、minimax、重点 target + 保护约束、Pareto。未知权重与阈值不由 Q1 人为补造。

## 撤出的旧结论

旧
\[
\log b_k(N)=c_k-\eta\log(N/10^6)
\]
及 \(\eta=0.14503317\) 只保留历史审计，不再作为 Q1 主模型或 Q2/Q3 默认参数。

## clean 分支并行成果

本轮融合时保留 clean 分支并发完成的 Q3 文件与 Q1 冲突复制性证据，不覆盖其 Q3 预算扫描、质量成本、p 支持域、发布器和 handoff。Q1 冲突复制性也进入正文证据链。
