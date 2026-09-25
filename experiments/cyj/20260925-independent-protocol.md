# CYJ 独立推进：冻结执行协议与审查发现

起点 `team/cyj-scaling@6e73e7a3dc389fc62089d42e67bd04d26993fc2c`，工作区干净。任务源为用户指定的 `CYJ_NEXT_TASKS_INDEPENDENT_2026-09-25.md`。外部验收不阻止本人独立工作。首次 fetch 因网络失败；已知精确发布仍是 e36aa23，当前不修改该历史 v3 的模型字节。

## 先审查后修正

MAJOR：旧 `base_exponents` 用 no-quality 族估计 alpha/beta，再固定指数做双交互线性回归；八参数并未共同优化平方残差。此结论直接来自源码，不以新实验成绩倒推。

可信来源：可见正文 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`、按原始清单核验的 B7（SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`）。禁止来源：隐藏 PDF 文字、已作废 Gemini 历史、无法追溯的聊天数字。B7 的 N/D/Q/val_loss 是半合成字段；N/D 单位十亿，Q 无量纲，Loss 坐标 B7 原生。B6 为精确子集，不作独立测试；B8 隔离，A p 与 B Loss 桥接未识别。

从零审查：仅看半合成 NDQ 表，最多支持给定函数族的域内条件拟合与预测检查；数据不识别真实训练因果参数、跨源映射或外推规律。新联合拟合仍是条件候选，历史全 B7 探索无法撤销。此次所有验证保持 `ready_for_Q3=false`。

## P0 运行前冻结

八参数同一 SSE 目标，SLSQP 解析参数 Jacobian，12 个固定随机种子起点；E∈[0,10]，A/B∈[1e-8,100]，alpha/beta∈[.01,3]，G 系数∈[-10,10]。这些是数值搜索界，不是物理先验；再扩大上界/放宽指数下界检查敏感性。四角线性约束 G≥1e-8 保证完整 log 矩形内 Q 单调；该阈值仅为数值正性裕度。

联合/两阶段对照使用同一 24 折 N/D/Q 留级；逐折重新拟合且不读外层 held-out。AIC/BIC 用 Gaussian iid 工作似然、8 均值参数加1方差参数；旧两阶段不是该似然 MLE、数据为半合成网格，故信息准则仅描述，不据其单独选择。检查全部起点状态、参数范围、边界及多解。200 次 ND 簇 bootstrap、局部 Jacobian/Gauss–Newton 与列归一条件数用于检查条件数值可估计性，不当成因果识别证明。

## 任务清单（持续更新）

- [x] P0 联合拟合、两阶段对照与取舍（结果见 joint-fit 记录）
- [x] P1 偏导、正向改善弹性、局部/有限替代和图
- [x] P2 嵌套五族选择、可识别性、留出覆盖检查（同源条件范围）
- [x] P3 B1 结构、B4/B5 口径、B7/B8 冲突审计；生成机制未知和跨源同口径未建立已明确记录
- [x] P4/P5 稠密预算/上下文、约束状态/转变点、成本/KKT 推导；见 `20260925-q3-joint-conditional-sweep.md` 和本人论文
- [x] P6 v4 joint 接口 metadata、边界/无效输入/梯度/manifest/CLI 自测；CHM 本人验收仍待
- [x] P7 本人 Q2/Q3 论文与 `20260925-claim-strength-and-dependencies.md`
- [x] P8 14 项总审计，结果 `PASS_WITH_LIMITATIONS`；审计只校验冻结的重拟合和扫描产物，不将其冒充重新计算
- [x] P9 外部依赖登记（CHM owner acceptance、ZHH Benchmark bridge、原附件来源和真实外测）

补充数值 red-team：用同一 B7 四个质量项消融对 36 个成本情景交叉优化，144 行中 132 可行；发现 N/D 配置对族选择显著敏感而条件 Loss regret 较小，见 `20260925-q3-form-sensitivity-{protocol,results}.md`。增强 Q3 求解边界的非有限值拒绝；v4 条件 API 明示支持 10 个上下文，并将 7 个新增情景标为 CYJ 外生敏感性。此补充不打开正式科学准入。

再用独立的二维微分进化算法抽检 36 个 Q3 情景，33 个可行场景相对 CHM 求解器的 B7 Loss 差最大 `8.03e-9`、3 个最低支持成本不可行判据一致，见 `20260925-q3-independent-optimizer-{protocol,results}.md`。总审计现 16 项 PASS、62 项单测 PASS；两数值算法一致不证明全局最优，更不构成真实训练验证。
