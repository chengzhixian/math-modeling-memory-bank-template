# Q3 独立优化器抽检结果

运行前协议与执行偏离见 `20260925-q3-independent-optimizer-protocol.md`。用 `python -B src/cyj/q3_independent_optimizer_check.py` 重跑，Python 3.12.14、NumPy 2.3.5、SciPy 1.18.1，seed `20260925`；代码 SHA256 `261543d0161819ad91d4b11a85a430a4b1be26f50f1992e3aab6f93d46c706d0`。B7 joint 输入 SHA256 `c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a`，输出 CSV SHA256 `de0a24d1c280a3b85cb6549d64e4801cf3bfa5452e2b0936dab54a003c157f1e`。输出 JSON 留存预算/上下文/族、DE 设置、feasibility、Loss 差及原 CHM 网格身份。

36 个冻结情景中，3 个低预算/长上下文场景经支持域最低成本代数判据再次确认为不可行；33 个其余情景独立算法均找到支持域与预算可行解，且 `solver_success=True`。两算法使用同一 B7 joint 目标重新评价：`L_DE-L_CHM` 最小 `1.31e-10`、最大 `8.03e-9` B 原生 Loss，未见 DE 比 CHM 低 `1e-4` 以上的可行点。这是很强的**数值交叉一致性**，但仅覆盖 36 个条件场景和两个启发式/局部数值过程，不证明全域全局最优或真实训练可迁移。

本检查的三维降维基于本 joint 候选内 `L_D<0` 与成本对 D 严格递增，故固定 `(N,Q)` 时把可行 D 取至预算或 D 上界。它不适用于随 D 非单调的其他未知目标。原拟启用 SciPy trust-constr polish，在边界外质量探测时报错；正式完整运行关闭局部 polish，该偏离在代码和 JSON 明示。该结果不提升 `ready_for_Q3=false` 的正式科学状态。
