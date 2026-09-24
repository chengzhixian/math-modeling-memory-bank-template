# Q2–Q3 联合结构可识别性审查（2026-09-24）

## A. 范围与可信来源

审查本地 `team/cyj-scaling@ad1d312c15bcf79c23d715dd199eec7c2e65a0af` 及本轮未提交的 cyj v2 接口；本地 `origin/main@af4857045e5df62afc9815bce4b98dbbb8867253`，chm 生产者固定 `a5525935b37f873235d2f650e4810a787b9a8788`。远端 fetch 两次网络失败，故远端实时状态未核实。题面 DOCX SHA256 `bc99a72460fa3d947a442d502969a13212cebff3b55339da4c4`；清理版可见数据说明 PDF SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；机器可读正文为 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。原始 B 文件 SHA 见 `outputs/cyj/quality/b7_quality_fit.json`、`outputs/cyj/classic/classic_data_manifest.json`。本次没有独立复核全部 A/C 原件、外部文献、官方提交规则。

可信依据为可见题面、清理版说明、经 SHA 校验的 B 表、chm v1.2 生产者合同/manifest 及实际代码。禁止依据为历史 PDF 隐藏页边文字、作废 Gemini 提交、旧 `eta`、旧 `cyj.q3.v1` p/eta 情景、B10 估计 Loss 作真实外测、未落盘聊天数字。

## B. Requirement → Data

| 题目要求 | 需变量 | 文件/字段 | 单位及数据性质 | 是否足够 |
|---|---|---|---|---|
| N/D 标度关系 | N,D,Loss | B1 `N_params_B,D_tokens_B,val_loss` | 10^9 参数/10^9 token；同源训练轨迹，Loss 评估细节待核 | 同源条件重构；外部解释不足 |
| Q 纳入标度关系 | N,D,Q,Loss | B7 同名三字段、`Q_score,val_loss` | Q=[0.1,1]，半合成 | B7 原生条件关系可估；真实训练效应未证 |
| 配比 p 纳入关系 | p,同坐标 Loss,N,D,Q | A4/A5 的 17 配比、13 target Loss；B1/B7 无 p | A 侧 1M target 对比 | 联合项不足；A/B Loss 无成对桥接 |
| Q1 质量传入 Q2 | Q_A 与 Q_score 配对 | A1–A3 质量代理、B7 Q_score | 两种质量坐标 | 无成对标定，不可直接映射 |
| Q3 预算选择 | N,D,Q,p,成本、可比较 Loss | 题面成本式、C7 上下文；上述分层预测 | FLOPs；C7 外生情景 | 可做 B7 诊断/敏感性；正式四维最优不足 |
| 大规模检验 | 真实大规模 Loss | B9 元数据、B10 estimated Loss | N/D 支持域外，估算 | 压力/参考，不是独立真实外测 |

## Variable provenance 与可识别性

| 量 | 来源/性质 | 支持域和数据角色 | 状态 | 正式使用 |
|---|---|---|---|---|
| `N` | B1/B7 observed，10^9 参数 | B1 [.070542,11.965825]；B7 [.07,11.97] | conditionally_identified | 各自源内可用 |
| `D` | B1/B7 observed，10^9 token | B1 [.134,299.893]；B7 [10,600] | conditionally_identified | 各自源内可用 |
| `Q_score` | B7 半合成原生坐标 | [.1,1]，B7 训练/同源检验 | conditionally_identified | 仅 B7 原生诊断 |
| `Q_A` | A1–A3 derived proxy | A 侧描述/排序 | conditionally_identified | 不直接映射 B Q |
| `p` | A4/A5 observed simplex | 17 域，训练配方凸包；A6–A11 为检验 | conditionally_identified | 仅 1M、13 target 对比 |
| B1 `val_loss` | B1 observed column；行级生成机制 unknown | 同源拟合/分组检验 | weakly_identified | 同源经验重构 |
| B7 `val_loss` | 半合成 observed column | 450 个唯一 N/D/Q 坐标 | conditionally_identified | B7 原生诊断 |
| `lambda_loss` | 无 A/B 同口径成对样本，scenario | 无经验支持域 | not_identified | 不进入正式式 |
| 跨规模 `eta` | chm v1.2 撤回的 legacy 估计 | 无可隔离连续 N/D 效应 | not_identified | 禁止正式传播 |
| `Q_A→Q_score` 与 `A target Loss→B Loss` | 无配对桥接 | 无 | not_identified | 不填补 |
| B1/B7 经典式参数 | 固定函数族下估计 | 各自源内 | conditionally_identified | 仅各自源内条件预测 |

## C–D. Gate 发现与修复门槛

### BLOCKER：完整 `L(N,D,Q,p)` 不可识别

没有一张表同时观测 `(N,D,Q,p)` 与同一定义的 Loss。B1 缺 Q/p，B7 缺 p，A 配比实验缺可与 B Loss 对齐的观测。跨源同名 `Loss` 不证明 tokenizer、评估语料、对数底、聚合方式相同。`lambda_loss` 和 Q 映射不能从当前表估计。若相加或映射，Q2 四维结构与 Q3 联合最优的科学结论失效。修复需独立同口径成对数据或明确降级：B1 `L(N,D)`、B7 `L(N,D,Q_score)` 各自限域；p 保留 13-target `sensitivity_only`，不加入 B Loss。新证据到来后需重跑桥接、分组验证和 Q3 求解。

### MAJOR：验证与支持域

B6 的 360 行包含于 B7，不是独立检验；B7 的留级折已用于三族选模，分数属于 selection evidence，不能再称无偏最终测试。B8 与 B7 同坐标 Loss 冲突且 Q 趋势相反，保持隔离；B9/B10 为大规模 estimated，且 B10 N 全在 B1 范围外。B1 高精度重构与来源机制未知并存；B4/B5 的 Loss 口径尚未证同一。需重设嵌套/冻结验证、追溯生成机制，并按支持域报告；受影响的预测误差和区间陈述须重算。

### MAJOR：当前模型形式和不确定性

B7 恒定 `-G` 质量边际效应与 45 组内 Q 斜率的显著变化不符（`outputs/cyj/diagnostics/b7_quality_interaction.json`）。已有 bootstrap 只覆盖固定模型、固定半合成来源的条件均值；残差、模型族、跨源及 Q4 Benchmark 桥接尚未纳入。先完成预注册交互候选和独立验证，再考虑主式；无证据的总预测区间保持 null。

### MINOR：工程合同

旧 `cyj.q3.v1` 的 p/eta scenario 仍可历史执行，易被误用。新 `cyj.chm.v2` 必须成为推荐入口，旧版显式 `deprecated=true, formal_use_allowed=false`；消费者不得从旧包复制参数。新版发布后重跑 CHM 侧消费测试，记录精确提交。

## 其他强制检查

- 数据角色：B1 拟合与同源组 CV；B2 半合成、B3 插值为形状；B4/B5 只描述跨族；B6 与 B7 去重后 B7 诊断/选模；B8 隔离；B9/B10 压力/参考；A4/A5 训练、A6–A11 检验、A12–A15 估算。现有 B7 留级 CV 不能再充当独立最终测试。
- 数据质量：B6/B7 精确坐标嵌套已校验；B7 数据与输入版本哈希见诊断 JSON。原有审计检查缺失/非有限、坐标重复、单位与范围；B8 的 0.5 堆积尚需来源解释。不同来源不得仅凭同名字段 join。
- 数学/代码：B1 与 B7 的 N/D 为 10^9 单位，Q 属 B 原生，p 属 A 的 17 单纯形；B7 质量式仅 B7 Loss。成本单位 FLOPs；Q=Q0 取单侧导数。旧 eta 情景公式内部可计算不等于参数可识别。
- baseline/消融：B1 E/N/D 消融和 B7 no-Q/constant-G 已运行；B7 交互与形式稳定性尚未完成。配比应有零效应/等权/minimax 等明示情景，不能补造统一目标。
- 文献：函数形式为候选，不以文献替代本题桥接条件；本审查不引用外部文献作识别依据。
- claim ladder：当前 B1/B7 同源条件拟合与 B7 斜率诊断最高为 L1 描述；固定数据生成机制下留级预测可附带 L2 条件限定；没有 L3 结构、L4 因果或 L5 真实外推证据。
- 从零 red-team：只看题面和表头，自然得到 B1 的 N/D、B7 的 N/D/Q 和 A 侧 1M 多 target p 对比。额外的 A/B Q 映射、Loss 换算及跨 N 的 p 衰减都需要表中不存在的配对观测。B7 趋势也可能仅由半合成生成式造成。
- 分支：本地 main 与 cyj merge base 为 `af4857045e5df62afc9815bce4b98dbbb8867253`；当前 cyj 实现尚未进入 main。远端 fetch 失败，实时 ahead/behind 与其他分支共同改动待恢复网络后再审。

## E. 判断

**NOT READY**。完整四维 `L(N,D,Q,p)` 为 `not_identified`。当前 Q3 降级为 B7 原生 NDQ 诊断预测、题面成本与独立 A 侧多 target 配比敏感性；`ready_for_Q3=false`。软件接口可发布供 CHM 联调，但正式 Q3 及 Q4 科学结论仍需上述验证和团队验收。
