# cyj 接口审查：2026-09-24

## A. 范围与版本

按 `REPOSITORY_REVIEW_PROTOCOL.md` 对**本地 cyj 接口的可消费性**审查，先冻结状态、再检查数据—变量—模型—代码—结论链。仓库 `chengzhixian/math-modeling-memory-bank-template`；分支 `team/cyj-scaling`，审查起点 `e84c0a529ad7f56e83db5c91b3b62c9e43200d99`（已合并 `origin/main@af4857045e5df62afc9815bce4b98dbbb8867253`），工作区干净。上轮远端 cyj SHA 已与 `157e340eb3310e5313ec49dd740947b701ff1841` 核对一致；本轮审查与 main 合并的推送另行核验。main 尚无 cyj 的 Q3/B7 实现；这些仍只在个人分支。chm 推荐接口在 `origin/integration/chm-q1-clean-20260923@a552593`（未作为 main 已验收输入），zhh 候选在 `origin/team/zhh-frontier`。

可信来源：当前 F 题 DOCX SHA256 `bc99a72460fa3d947a442d502969a13212cebff3b55339da4c4`、清理版数据说明 PDF 的可见页面、`problem/readable/DATA_DESCRIPTION_VISIBLE.md`、附件 B 与各自哈希、chm v1.2 生产者合同与 manifest、cyj 实际代码/输出/测试。禁止来源：历史隐藏页边文字、作废 Gemini 历史提交、无验收的 legacy 参数、聊天中未落盘数字。此次未独立审查全部附件 A/C、外部文献原文或论文终稿，故不作全仓发布判定。

## B. 题目—数据及变量追溯

| 要求/量 | 实际字段及单位 | 性质/角色 | 当前可识别性与接口 |
|---|---|---|---|
| B1 经典 `L(N,D)` | B1 `N_params_B,D_tokens_B,val_loss`；十亿参数/十亿 token/未完全证实的交叉熵口径 | B1 主拟合；N 组留出及 token-tail 同源检验 | 五参数仅在固定 B1 模型条件下可估，绝对跨来源解释弱；`cyj.q3.v1` diagnostic 可调用 |
| B 原生 Q 效应 | B7 `N_params_B,D_tokens_B,Q_score,val_loss`；Q=[0.1,1] | 半合成；B6 是 B7 子集；B8 另行隔离 | B7 条件模型可估，真实训练/跨来源效应未识别；`cyj.b7_quality.v1` diagnostic 可调用 |
| A 侧质量 `Q_A` | Q1 A1–A3 综合代理 | 描述性 A 侧输出 | 与 B `Q_score` 无成对标定，mapping **not identified** |
| 配比 `p`、目标效应 `m_k(p)` | A4/A5 17 域 simplex 与 13 target Loss | chm v1.2：1M centered contrast；A6–A11 排序检验 | 1M 内条件可估；跨 N/D 连续衰减 `eta` **not identified** |
| `lambda_loss`、主 anchor | 需 A target 与 B1 同口径成对 Loss；附件无对应字段 | 只能由调用者显式设情景 | B1↔A Loss 标度 **not identified**；不能默认 1 或某域 |
| Q3 成本的 `N,D,Q,Q0,L_ctx` | 题面参数与 C7 情景；N/D 十亿、L Token、预算 FLOPs | N/D/Q 情景、Q0 显式假设、C7 外生候选 | 成本函数定义可核；不证明质量提升的性能收益 |
| Q4 能力 | C 侧 Benchmark 与 Loss 桥接 | zhh 候选；需独立误差传播 | 当前没有可调用的同坐标、已验证 B1/B7→Benchmark 换算 |

数据角色与泄漏：B1 用于五参数拟合和同源分组 CV，近乎精确重构不能视为独立外部验证；B2 半合成、B3 插值只作形状诊断；B4/B5 虽是跨族/文献数据，tokenizer、评估语料与 Loss 单位未与 B1 对齐，不能报告合并绝对 RMSE；B6 全部 360 行包含于 B7，不能当独立检验；B7 的 N/D/Q 留级分数同时用于三候选选型，不能视为嵌套无偏测试；B8 与 B7 同坐标 224 点 Loss 全异且 Q 方向相反，隔离；B9 元数据/B10 估算 Loss 仅作外推情景，非真实独立测试。支持域：B1 N=[0.070542,11.965825]、D=[0.134,299.893]；B7 N=[0.07,11.97]、D=[10,600]、Q=[0.1,1]。范围重叠不证明 Loss 同坐标。

## C–D. 发现、影响及修复门槛

### BLOCKER 1：cyj 仍绑定已撤回的 Q1 跨规模接口

`outputs/cyj/interfaces/q3_bundle.json` 固定 `chm.q1.v1@7c14a0c`，含 `eta_producer_estimate=0.145033...` 与条件区间；`src/cyj/q3_interface.py` 的 scenario 仍调用 `relative_effect(p,target,n_params,eta)` 并把结果加到 B1 Loss。chm 当前推荐 `v1.2` manifest 明确 `scale_transfer_status=not_identified_from_attachment_A`，`relative_effect(p,target)` 仅返回 1M contrast；`interfaces/chm/Q2_BRIDGE.md` 禁止使用历史 eta 作正式 Q2/Q3 参数。因此旧 bundle **可执行但已与当前科学生产者合同不兼容**。影响 p 修正、N 导数和任何据其优化的跨规模数值。修复需发布新的 cyj 版本，固定 chm v1.2 精确提交/manifest，只消费 1M 13-target contrast；若跨规模仍需要 p 项，保持 sensitivity-only 或寻找独立识别证据。重跑相应接口样例、导数测试和全部下游 Q3 情景；旧 v1 仅保留历史复现，不进入正式链路。

### BLOCKER 2：完整 `L(N,D,Q,p)` 尚不可识别

B1 不含 Q/p，B7 的 Q 与 Loss 属半合成原生坐标且无 p，A 的 `Q_A` 和 13 target Loss 无与 B1/B7 成对共同口径。`src/cyj/q3_interface.py` 明确拒绝 `Q_score`，`src/cyj/quality_scaling.py` 明确不接受 p；两套预测不能相加。影响正式 Q2 广义标度律、Q3 四维联合寻优以及 Q4 能力解释。需先取得或论证同坐标桥接、定义可验证 p policy，并把不识别的量保留为情景；随后重跑联合模型、独立验证和不确定性传播。在此之前保持 `ready_for_Q3=false`、`ready_for_Q4=false`。

### MAJOR 1：预测验证范围有限

B1 组留出与 token-tail RMSE 约 1e-4 触发近乎精确重构警报，行级 Loss 生成/评估来源未证；B4/B5 绝对可比性未证。B7 三候选用相同 24 个留级折选择线性 Q，50 个 bootstrap 只覆盖所选模型的半合成条件均值；B8 方向冲突尚未解释。影响跨族预测、Q 的真实边际替代率及总预测区间。需核查原始评估口径、做嵌套或独立检验、模型形式敏感性并处理 B8 来源；重算所有泛化和区间陈述。当前只能给分层诊断，不可升格为 L2 外部预测、L3 结构关系或 L5 外推规律。

### MAJOR 2：下游 C7 与 Loss–Benchmark 未联合验收

`q3_costs.py` 固定 2048/8192/131072 Token 候选并标注待联合验收；zhh 合同称桥接弱识别、无可调用换算。影响 Q3 上下文正式情景和 Q4 Benchmark 区间。需由 zhh/集成人验收来源与接口，且只有同坐标 Loss 才能传播桥接误差；受影响的 Q3/Q4 结果重跑。

### MINOR：软件边界仍需强化

直接 `QualityPredictor.predict` 将可转成浮点的字符串作为输入，批量 JSON 适配器才严格拒绝数值字符串；两入口的类型策略不一致。`constraint_residuals` 输出残差而不判断完整 simplex 可行性，需调用者按声明容差处理。正式版本应统一输入类型与可行性报告；现有诊断样例不受影响。

## 数学、代码、数值与反事实复核

题面 DOCX 第 46–59 段要求 Q2 同时含 N/D/Q/p、Q3 至少三档预算及 C7 外生上下文；第 74–75 段要求 B1 主拟合、B2/B3、B4/B5、质量数据与 B9/B10。现有 `q3_costs.py` 的单位：`C_train=6e18 N_B D_B`、`C_attn=2e14 N_B D_B L_ctx`、质量项 `1e9 D_B[g(Q)-g(Q0)]_+`，与已记录题面公式一致。N=1B、D=100B、Q=Q0、L=2048 样例总成本 `6.4096e20` FLOPs；Q=Q0 处提供左右导数。`q3_interface` 的 B1 经典公式/导数与实现一致；scenario 导数对旧假设公式内部一致，但该跨规模假设已经被上游撤回。线性 p 在全 simplex 上可能诱导顶点解，A 侧训练配方凸包尚未自动检查。非有限数、正域、Q 范围、哈希与版本多数有拒绝逻辑；B1/B7 参数文件固定哈希。软件测试 37/37 通过；B1 样例 `4.738637013477364`，B7 样例 `3.492870995028143`，这些只证明软件复现。无新拟合、无新文献结论。

从零只看题目与数据表头：B1 可支撑同一 Loss 列的 N/D 经验关系；B7 可支撑半合成坐标内的 N/D/Q 条件关系；A4/A5 可支撑 1M 的配比相对排序。没有任何一表同时给出同坐标 N/D/Q/p 和同一验证 Loss。额外的 eta、lambda、Q 映射若出现在统一公式中，只能是明示情景，不能因下游需要而宣称数据估计。更简单解释还包括 B1 与 B7 共享构造方程、B7 的 Q 项只反映半合成生成规则，而非真实训练机制。文献形式不能补齐缺失的成对观测。

Git 集成：`origin/main@af48570` 与本分支的 merge base 相同；cyj 的实现/结果文件只存在个人分支，main 的公共接口摘要仍为旧草案。chm v1.2 位于独立 integration 分支，不能因本地 Git 可读取就视作 main 已验收。旧 Gemini 建模历史明确作废，未作为本报告来源。最新 main 此轮只增加审查入口说明，未改 Q1 或 cyj 科学字段。

## E. 结论

**NOT READY**：`cyj.q3.v1` 的 B1 diagnostic 与 `cyj.b7_quality.v1` 的 B7 diagnostic 在各自声明范围内可用于软件联调和分层分析；旧 p/eta scenario 已不符合 chm 当前推荐接口，不能作为正式 Q2/Q3 依据。完整四维预测、正式 Q3 最优配置及 Q4 能力换算仍有上述 blocker。由 cyj 发布兼容 chm v1.2 的新版本并处理本方验证；chm/zhh/集成人按各自文件归属联合验收、重跑下游。
