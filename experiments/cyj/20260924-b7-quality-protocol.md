# B7 原生质量模型：运行前冻结方案

cyj，2026-09-24。任务是补齐 chm/zhh 需要的原生 Q 模型、导数、Loss 样本，不绕过跨来源口径门槛。

输入：B6/B7 按 F_MANIFEST 验证字节和 SHA。检查 B6 逐坐标/逐 Loss 为 B7 子集后只使用 B7，不双计 360 重复行。B8 calibrated/extrapolated 全部排除，B1/A 不进入该拟合。

候选：`L=E+A*N_B^-alpha+B*D_B^-beta+G*h(Q)`，h 分别为无质量项、1−Q、−ln(Q)。这是本轮可解释候选族，不是引用文献定律或已确认生成器。E/A/B/G 为正，alpha/beta 搜索 [0.02,1.5]，该范围仅数值搜索假设，触边不得发布通过。给定指数用最小二乘解析求幅度，再以四个固定起点 (.15,.15)/(.15,.6)/(.6,.15)/(.6,.6) 搜索指数。拟合目标为原始 Loss MSE，不继承 B1 Huber 目标或参数。系数非正的剖面拒绝，不声称实现完整边界 NNLS。

对三个候选都分别留出每个完整 N、D、Q 水平，重拟合全部参数；无逐行随机划分。以三个轴的平均折 RMSE 再取均值选候选；该分数参与模型选择，不作为独立无偏测试误差，需后续嵌套验证。无 Q 模型是质量消融。报告每折收敛/边界状态。

对选定族做 50 次 N,D 组 bootstrap，每组保留全部 Q，种子 20260924；拒绝不收敛/触边。区间仅固定族和半合成 B7 条件下的均值分布，不覆盖模型选择、真实训练、跨来源/配比/Benchmark 不确定性。样本共享 sample_id，消费者不能给不同请求重新随机配对。

输出 `outputs/cyj/quality/b7_quality_fit.json`；独立 `QualityPredictor` 严格要求文件 SHA 与 `mode=diagnostic`，只接受支持域内 N/D/Q，返回 B7-native Loss、梯度、等 Loss dN/dQ、同编号条件样本。Q3/Q4 正式状态仍 false，B1 旧接口保持兼容。

代码先提交，再将代码提交完整 SHA 传入命令，程序核验自身及依赖代码版本：

```powershell
& 'C:/Users/muyehuangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B src/cyj/quality_scaling.py --input-version <本轮代码提交40位SHA>
& 'C:/Users/muyehuangyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -m unittest discover -s src/cyj/tests
```

运行前状态：尚无真实 B7 候选比较或 bootstrap 结果。运行后另新增结果记录，不倒填此运行前方案。原始 CSV 不修改，分析遵循电子表格技能科研规则，仅生成 JSON。
