# Q3 质量成本函数：纯成本几何与临界条件

日期：2026-09-24
状态：cost geometry only；不包含 Q 性能收益，不生成正式最优 Q。

题面三类质量成本均写为 C_Q=1e9*D_B*max(g(Q)-g(Q0),0)。训练与注意力成本之和为 N_B*D_B*(6e18+2e14*L_ctx)。

因此可约去 D_B：

C_Q/(C_train+C_attn) = [g(Q)-g(Q0)] / {N_B [6e9+2e5 L_ctx]}.

这说明质量升级相对基础计算的成本比例与 D 无关，随 N 按 1/N 下降。临界模型规模为

N_crit = [g(Q)-g(Q0)]/[6e9+2e5 L_ctx].

若 N_B > N_crit，则该质量升级的额外成本小于 train+attention；反之更大。

曲率方面，exponential 与 power 为凸成本，logarithmic 为凹成本。前两者高 Q 边际成本上升；logarithmic 的边际成本下降，因此未来接入单调质量收益后更容易出现边界解，需要多起点和 KKT 检查。

Q=Q0 处由于 max(.,0) 存在拐点：左导数为 0，右导数为 1e9*D_B*g'(Q0)。正式优化不能把不存在的双侧导数写成 0。

诊断场景 Q0=0.5→Q=1 仅用于比较量级，不是题面默认值。2048 Token、N=1B 时 exponential/power/logarithmic 的质量成本相对 train+attention 约为 0.598/0.731/0.189；N=10B 时约 0.0598/0.0731/0.0189。131072 Token、N=1B 时约为 0.119/0.146/0.0376。

这些结果只说明成本侧相对价格，不能推出提高 Q 是否值得。净收益、最优 Q 与 N/D/Q 结构转移必须等待 cyj 的 validated B-native Q 性能模型。
