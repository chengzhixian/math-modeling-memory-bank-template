# CYJ v3 条件接口与 CHM 精确求解器实测（2026-09-25）

## 身份与命令

- CYJ B7 原始附件 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`；冻结模型 SHA256 `ed6b01b113110b90b25c5f6cc01d7686cb77602f29464bc068843b36d881c9bf`；固定族留级 SHA256 `cae1c827587c49d6484d2fcdb7686f9202f522aacdb39d5f63f74085d422491d`；条件经验区间 SHA256 `54c2ceb24472aa1bc53f3207d0064529545fa37385f6f5845114b88657121608`。
- CHM 求解器精确 Git commit `92e0592000cba58fca355a881dc59caadbd446b2`；测试脚本从该对象读取 `q3_generic_solver.py`、`q3_quality_cost_geometry.py`、`q3_nd_baseline.py`，逐文件 SHA 写入结果，使用临时目录导入，未在 CYJ 分支长期修改 CHM 文件。
- Windows / Python 3.12.14 / NumPy 2.3.5 / SciPy 1.18.1。SciPy 安装于忽略的 `data/processed/cyj_scipy_runtime`，不是仓库依赖锁。复现：`python -B src/cyj/test_chm_solver_consumption.py --scipy-path data/processed/cyj_scipy_runtime --starts 36`。其他环境先安装兼容 SciPy 并传入路径。
- 输出 `outputs/cyj/interfaces/chm_solver_consumption_b7_candidate.json` SHA256 `0a6dc8e9696dabf70cf625d26d8f98ee1b063fedd674df4eb9b529e6b8daf839`，重跑两次相同。

## 实测结论

`CHMAdapterV3.value_grad → CHM Support → solve_generic` 实际运行 3 预算 × 3 上下文 × 3 质量成本族，共 27 场景；Q0=.5，每个可行场景 36 起点。24 场景收敛且 primal feasible，24 个 CHM `kkt_check_pass=true`；3 场景 1e19 预算、131072 token、三种成本族均低于该支持域最低成本，被 CHM 明确以 `budget below minimum supported cost` 拒绝。1e22 / 2048 / exponential 的条件示例解 N=7.59656109、D=190.38788490、Q=1，Loss=2.13911405，预算利用率≈1；这些数值仅为 B7 半合成模型的软件联调结果，不能称正式 Q3 最优配置。

CHM 求解器取 `model.support` 且要求 `Support` 类型，CYJ 接口公开 `bounds`；消费者包装映射后正确使用 D_min=10。SLSQP 的 `exp(log(bound))` 在界上有微小浮点偏差，本地包装仅容忍 `1e-12 × 上界` 以内并裁回界，超过即拒绝；最终包装归 CHM 所有者。KKT 检查是必要条件，不保证全局最优。尚无 CHM 所有者提交的 consumer acceptance，`ready_for_Q3=false`。

v3 manifest SHA256 `059ecb420f7277a93c0f20714c76978ea5e739d3a3dff9c916fff11df2ff9f66`。两次构建比较同哈希；样例响应 SHA256 `38b36f20704c1d2af02089db4b6a64eab614216fb23e5a65274cf8c655171a39`。v3 保持科学状态 `conditional_within_B7_pending_independent_test`，因为模型族受完整 B7 启发、经验区间无未触碰样本覆盖率校准，A/B Loss 桥接未识别。
