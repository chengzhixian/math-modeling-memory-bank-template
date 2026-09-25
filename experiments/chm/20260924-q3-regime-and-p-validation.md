# Q3 诊断阶段：连续预算扫描、结构转移与配比选择验证

日期：2026-09-24（北京时间）
状态：diagnostic/scenario only；不发布正式 Q3 最优配置。

## 上游边界

本阶段固定 cyj 6c17cb4e 的 B1 N-D diagnostic 参数和 zhh d47cd2dc 的 C7 三个候选上下文。cyj 仍 ready_for_Q3=false，Q 性能项、B1↔B7 Loss、p primary anchor 与 lambda_loss 未完成，因此本阶段只验证求解器结构、支持域和 A-side 配比选择能力。

## 连续预算结构

固定 Q=Q0、p=p_ref 时，成本为 C=c(Lc)ND，其中 c(Lc)=6e18+2e14*Lc。B1 diagnostic Loss 为 L0=E+A*N^(-alpha)+B*D^(-beta)。

在声明支持域内，随预算增加依次出现 N_min_bound、interior、D_max_bound、support_corner。三个 C7 情景的关键预算见 regime_thresholds.csv。attention/train 成本比恒为 Lc/30000，因此 2048 / 8192 / 131072 Token 对应约 0.0683 / 0.2731 / 4.3691。

2048 Token 的 N_min 释放、D_max 激活、支持域饱和预算约为 7.95e17、9.33e21、2.30e22 FLOPs；8192 为 9.47e17、1.11e22、2.74e22；131072 为 3.99e18、4.69e22、1.16e23。

这些是当前 B1 支持域下的诊断约束相位，不能提前写成含 Q/p 的最终结构性转移。

## 多起点数值交叉验证

在三档题面预算和每个解析临界预算处，用 25 个起点在约束可行的一维约化问题上运行 L-BFGS-B。最佳数值解与解析解的 Loss 最大差约 4.44e-16，N/D 最大相对误差约 4.23e-08。个别边界起点的 success 标记受停止判据影响，但最佳可行解与解析解一致。

## 配比优化有效性验证

仅使用 A4/A5 拟合的逐 target 线性代理，对 A6/A8/A10 held-out 配方做“预测最优选择”，随后用 A7/A9/A11 的真实 target Loss 验证。

全部 13 targets × 3 scales：25/39 次直接选中真实最优，34/39 次落在真实前 10%。1M 为 13/13 前 10%、10/13 精确最优；60M 为 13/13 前 10%、8/13 精确最优；1B 为 8/13 前 10%、7/13 精确最优。

主 sensitivity panel（pile_cc / wikipedia_en / arxiv / stackexchange / github）：11/15 次精确最优，14/15 次前 10%。唯一明显偏离是 1B pile_cc：第 10/64，relative regret 约 2.63%。

这比单独报告 Spearman 更直接验证了“代理用于候选选择”的能力，同时也确认 1B 的 target-dependent 失效风险。

## 为什么不做连续单纯形 p 最优

A4 训练支持内的五个主 target 最佳候选都很集中：最大单域占比中位数约 0.954，5/5 高于 0.7，4/5 高于 0.9。因此即使限制在训练出现过的配方，最小预测值也有明显极端化倾向。

当前 m_k(p)=beta_k^T(p-p_ref) 为线性函数；若 lambda_loss>0，尺度因子也为正，则固定 target 下 p 的排序不随预算、上下文、N、lambda 或 eta 改变。当前模型本身不能识别预算驱动的 p 支持集结构转移。

因此正式 Q3 不发布无约束连续单纯形 p optimum；使用已观测/受支持候选集；主 target 与 lambda 未识别时保留多 target scenario；1B 及更大规模传播 p 选择失效风险；真正 N/D/Q 的资源替代转移等待 cyj 的 Q 性能模型。
