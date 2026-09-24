# CYJ Q3 独立优化器抽检交接

## 变更

新增预冻结 36 场景的二维独立优化器检查：借 `L_D<0` 和成本对 D 递增的候选内性质，解析消去 D，用 SciPy 约束微分进化搜索 N/Q。输出 `src/cyj/q3_independent_optimizer_check.py`、`outputs/cyj/q3/q3_independent_optimizer_check.{csv,json}`、实验协议/结果和公式对照单测；总审计加入独立算法比较。

## 证据与复现

运行 `python -B src/cyj/q3_independent_optimizer_check.py`；seed `20260925`、popsize 12、maxiter 150、tol `1e-8`。脚本 SHA256 `261543d0161819ad91d4b11a85a430a4b1be26f50f1992e3aab6f93d46c706d0`，输出 CSV SHA256 `de0a24d1c280a3b85cb6549d64e4801cf3bfa5452e2b0936dab54a003c157f1e`，模型 SHA256 `c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a`。33/36 情景可行且 DE 与 CHM B7 Loss 差最大 `8.03e-9`；余 3/36 均低于支持域最低成本。16/16 总审计现独立从原始 B1/B7 CSV 重算拟合 RMSE，62/62 单测和 XeLaTeX 8 页通过，统一 `PASS_WITH_LIMITATIONS`。原拟 local polish 因 SciPy 在 Q 边界外探测报错而关闭；已在机器 JSON 与实验记录标注，不能称全局最优证明。

## 未解决与下一步

CHM 仍需在本人分支消费精确 v4 扩展版 `3471530d91c8ee7eb709e5cd6c824eb9c423e0df`；ZHH/集成人仍需 Loss--Benchmark 桥接；数据源仍未给真实训练独立外测。这些均 `BLOCKED_EXTERNAL`，不影响 CYJ 条件数值结果。`ready_for_Q3=false`。cyj 后续维持代码/实验/接口 SHA 冻结，若有新证据须独立冻结协议再验证。本轮提交/远端 SHA 以 Git 实际核验为准。
