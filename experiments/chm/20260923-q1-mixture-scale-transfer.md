> **历史诊断，已从 Q1 主模型撤出（2026-09-24）。** 本文件保留用于审计旧的三尺度后验校准计算；其中 (b_k(N))、(eta=0.14503317) 及其区间不再属于当前 Q1 生产者接口，也不得作为 Q2/Q3 的默认跨规模参数。原因是附件 A 的配方实验未提供对应 (D)，真实规模仅有 1M/60M/1B 三个离散位置，且 1B 配方支持集不同。当前正式方案见 `problem/chm/20260924_q1_rigorous_restructure.md` 与 `interfaces/chm/CONTRACT.md`。

# EXP-CHM-Q1-003：配比效应的尺度衰减校准

日期：2026-09-23（北京时间）
角色：chm
状态：draft post-validation calibration
上游：EXP-CHM-Q1-002、mixture_effect_ridge_v0

## 目的

Q1 的逐域 Ridge 已验证“配方排序”能够从 1M 迁移到 60M/1B，但 Q2 需要的不仅是排序，还要将配比 `p` 纳入 Loss 模型。因此需要把“配比效应方向”与“效应幅度随模型规模变化”分开。

## 两阶段原则

第一阶段（已完成）：A4+A5 拟合 1M 代理；A6–A11 作为 held-out 数据验证跨尺度排序。模型族和评价口径由此冻结。

第二阶段（本实验）：在模型族冻结后，允许使用 A6–A11 估计一个下游尺度传递接口。这意味着本实验的校准参数不能再声称是在 A6–A11 上完全外部验证；真正的外推压力测试仍保留 A12–A15。

## 定义

对目标域 k，A4+A5 学到

\[
s_k(\mathbf p)=\beta_{0,k}+\boldsymbol\beta_k^\top\mathbf p.
\]

定义 A4 归一化配方的均值为参考配方 (\mathbf p_{\mathrm{ref}})，则

\[
m_k(\mathbf p)
=
s_k(\mathbf p)-s_k(\mathbf p_{\mathrm{ref}})
=
\boldsymbol\beta_k^\top(\mathbf p-\mathbf p_{\mathrm{ref}}).
\]

这样配比项在参考配方处严格为 0，不会和 Q2 的基准标度律截距重复计数。

在 N=1M、60M、1B 三个真实检验尺度分别拟合

\[
L_k(N,\mathbf p)
=
a_k(N)+b_k(N)s_k(\mathbf p)+\varepsilon.
\]

13 个目标域的 (b_k(N)) 均为正，说明小模型代理方向没有发生整体翻转。

## 公共衰减指数

考虑目标域固定效应：

\[
\log b_k(N)
=
c_k-\eta\log(N/10^6)+\varepsilon_{k,N}.
\]

对 13×3 个点做域内去均值固定效应回归，得到

\[
\widehat{\eta}=0.14503317.
\]

按目标域整体重采样 10,000 次，seed=20260923，bootstrap 95% CI：

\[
[0.10686793, 0.18669841].
\]

固定效应模型解释域内 (\log b) 变化的 (R^2\approx0.6477)。

但域特异 $\eta_k$ 范围为 0.0412–0.3074，说明不同目标域的配比效应衰减速度差异不可忽略。因此下游至少需要“公共 eta 主模型 + 域特异 eta 敏感性”两套结果。

## 推荐给 Q2 的接口

若 Q2 使用某个可比 Loss 目标域 k，则配比修正写成

\[
\Delta L_p(N,\mathbf p)
=
c_k\left(\frac{N}{10^6}\right)^{-\eta}
m_k(\mathbf p),
\]

其中 (c_k) 用本实验拟合的目标域幅度常数，(eta) 主值用 0.14503317。现有 bootstrap 区间只按目标域整体重采样，条件于已拟合的 Ridge、当前配方样本和尺度校准，因此只能作为**条件不确定性区间**，不能当作完整预测区间。

更稳妥的实现是让 cyj 将该项视为一个带先验范围的配比修正，而不是固定成不可调整常数。

## 重要限制

1. 只有 1M、60M、1B 三个真实尺度，不能称为新的普适 Scaling Law；
2. A6–A11 已在 EXP-002 中承担验证作用，本实验属于“模型冻结后的后验校准”；
3. A12–A15 不参与 eta 拟合，且其 Loss 为 estimated/extrapolated；
4. p 的 Ridge 系数是闭合组成上的相对对比，不是独立因果效应；
5. Q2 的 N、D、Q 主标度律仍必须由附件 B 独立拟合；
6. 1M 与 60M 校准使用同一组 256 个配方，而 1B 使用另一组 64 个未见配方。因此公共 $\eta$ 可能同时吸收“规模变化”和“配方支持集变化”，不得解释成纯参数规模弹性；
7. 当前 95% 区间只重采样 13 个目标域，尚未传播训练配方、Ridge 拟合和各尺度校准样本的不确定性。


> 数值版本说明：本文件已按 `outputs/chm/local_recheck_v1/mixture_scale_transfer_v0_manifest.json` 刷新。
