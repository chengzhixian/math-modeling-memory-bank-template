# CYJ 条件模型数学推导

令 N、D 为十亿参数和十亿 token，Q 为 B7 原生质量；`L=E+A N^-alpha+B D^-beta+(1-Q)G`，`G=G0+GN ln N+GD ln(D/100)`。log 中使用这些固定数值单位，换单位时 G0 随之平移，不能把系数原样搬到参数个数。

## 一阶边际与交互

对 N 求导，A N^-alpha 给出 `-alpha A N^(-alpha-1)`，质量项给出 `(1-Q)GN/N`；两者相加得到 L_N。同理 `L_D=-beta B D^(-beta-1)+(1-Q)GD/D`，`L_Q=-G`。所以质量改善的收益 `-L_Q=G` 随 N/D 而变；交叉导数 `L_NQ=-GN/N`、`L_DQ=-GD/D` 描述该拟合曲面的交互。joint 拟合 GN/GD 均负，因而所有域内 N/D/Q 梯度均负。G 是 log N/log D 的仿射函数，完整矩形最小值必在四角；四角 G>0 即足以证明域内 Q 单调。

正向改善弹性定义 `epsilon_x=-x L_x/L`。N 增大 1% 时，Loss 的一阶相对降幅约为 epsilon_N%，D/Q 同理（Q>0）。历史 v3 返回的是带符号的 `x L_x/L`；新论文使用明确命名的 improvement elasticity，不悄悄改变旧 API 字段意义。

## 等损失替代

固定 D，微分 `dL=L_N dN+L_Q dQ=0`，故 `dN/dQ|L,D=-L_Q/L_N`。固定 N 时 `dD/dQ|L,N=-L_Q/L_D`。两者在本拟合内为负，表示提高 Q 可降低等损失所需规模；它们是模型条件曲面量，不是实测干预效应。有限变化用 brentq 在 N 或 D 的声明上下界求相同 Loss 根；若两端不能夹根，输出 no_equal_loss_root_in_support，不外推。缩放倍数 N1/N0、D1/D0 及替代率单位在机器 metadata 中记录。

## 成本偏导与 KKT

先用实际参数个数 n、token 个数 d：`C=(6+eta_att Lctx)nd+d[g(Q)-g(Q0)]_+`；eta_att=2e-4 为题面 attention 系数，区别于已废弃的 A/B 经验迁移 eta。Q≥Q0 内 C_n=(6+eta_att Lctx)d，C_d=(6+eta_att Lctx)n+g(Q)-g(Q0)，C_Q=d g'(Q)。在 Q0 处左导数0、右导数 d g'(Q0)，约束 Q≥Q0 采用右侧必要条件。代码 n=1e9 N、d=1e9 D，因此 C_N=(6e18+2e14 Lctx)D，C_D=(6e18+2e14 Lctx)N+1e9[g(Q)-g(Q0)]，C_Q=1e9 D g'(Q)。

拉格朗日式 `L+lambda(C-budget)+sum mu_low(x_low-x)+sum mu_high(x-x_high)` 给出驻点 `L_x+lambda C_x-mu_low+mu_high=0`。C_x>0 时 R_x=-L_x/C_x。内点 R_x=lambda；下界 R_x≤lambda，上界 R_x≥lambda。lambda≥0，且 lambda(C-budget)=0。预算松弛时 lambda=0；若所有 Loss 梯度负，松弛最优点只能被上支持界限制。该条件为必要条件，不能据 SLSQP/KKT 直接证明全局最优。

指数族 g=1e7 exp(6Q)，g'=6e7 exp(6Q)，g''=3.6e8 exp(6Q)>0；幂族 g=5e9 Q^4，g'=2e10 Q^3，g''=6e10 Q²>0；对数族 g=2e9 ln(1+10Q)，g'=2e10/(1+10Q)，g''=-2e11/(1+10Q)²<0。前两者质量边际成本递增，对数族递减；结合负 Loss 梯度和支持边界，会产生不同激活/触界行为，需数值比较而不能只凭凹凸断言配置。

attention/train=eta_att Lctx/6=Lctx/30000。等成本临界点为 30000 token，与 N/D 无关。30000 附近是成本组成等额点，并不自动成为最优活跃集发生变化的阈值；配置转变须另做扫描和根定位。新增上下文值均标为外生敏感性情景，不能声称全部来自已验收 C7 观测。
