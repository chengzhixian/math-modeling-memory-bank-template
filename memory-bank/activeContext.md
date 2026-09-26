[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

## 2026-09-26 第二轮复审整改检查点（进行中）

本轮以代理成功刷新并核实的远端 `main@b789e3fc02ba894c4787ea351f87e56fc4e7daa8` 为基线。已在 Q4 v3 增加累计最高分纪录保持基线、q90 加近期尾差的条件边界，以及 Q3 固定配方、观测联立配方、独立原生 Q 三模式条件桥接；原始资料 2,014 文件/564,436,312 字节 SHA256 校验通过。历史最高边界在四个重叠回测窗内未刷新，动态尾差情景尚未得到独立验证；Q3→C6 坐标仍为 `unidentified`，超支持域不给分数。审计与最终复跑未完成；本次先按用户要求提交并推送进行中检查点。论文/PDF 未修改。交接见 `memory-bank/handoffs/integration/20260926-second-review-wip-checkpoint.md`。

## 2026-09-26 评委视角审查整改（当前）

用户要求在最新 main 直接整改桌面 `数模F题_main分支_评委视角审查报告_a19039b.md`，并核对 cyj、zhh、chm 三个留存分支。本轮在 main 起点 `a19039b` 核实三分支的正式数值已集成，旧分支没有解决报告中的终稿表达缺口；新补 Q2 有限联合效应、Q3 独立质量投入对照、Q4 两类贡献代理/前沿边界/能力换算、四问摘要和数据利用表，修正 Q2 fixture 浮点尾差。详细证据、18 阶段审查及当前限制见 `audits/review_followup_20260926/REVIEW.md`。当前 main 的论文和精选答复哈希已刷新；来源分支冻结 manifest 未改。论文 AI 使用说明只覆盖已核实事实，队友实际使用范围仍待本人确认；本机无 XeLaTeX，未编译终稿 PDF。推送状态以本轮最终远端 SHA 核对为准。

## 2026-09-26 集成人当前状态

本轮按用户桌面《分支成果集成到main方案.md》重新集成：远端 `main@5869353c9c1979286a8bcb659441dcf87b6929b7` 已由 PR #4 合并四问当前交付，Git 与仓库连接器核对同一远端 SHA，目录树为 `d19f090faa389cbfb014ffffeed63599c9f30c33`。来源为 CHM `c052b6918c3f77a2285622521d8abb1b429513be`、CYJ `d5e05cedeba3b86abe4ab624239504a21d1abee4`（Q2 v8 数值生产者 `fd2dbb3`）、ZHH `ee23b200e9de7f78477d945b186233741bd3b8fd`。四问当前答案、代码、接口、实验和结果已按 Q 归类；独立工作树的 2,014 项原始资料、Q1/Q2/Q3 主链及 Q4 v3 45 项哈希门禁复核通过。Q3 Windows CSV 换行和 Q4 清单循环两处复现缺陷已修；审查见 `experiments/20260926-main-q1-q4-integration-review.md`。Q2/Q3 桥接、Q3 最优、Q4 未来覆盖仍是条件结果。用户本轮仅要求四问 main 集成，论文编译/排版留待后续。

Q1–Q3 的精简成果按问题放在 `outputs/Q1`、`outputs/Q2`、`outputs/Q3`，论文推导按现有 LaTeX 结构放在 `paper/latex/sections/Q1`、`Q2`、`Q3`。本次来源为远端 CHM `c052b6918c3f77a2285622521d8abb1b429513be`、CYJ `046abaeede95868827fd001dcfee62eb58614eaa`，其中 Q2/Q3 消费的 v8 冻结生产者为 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`。Q1 仅识别附件 A 内质量代理与配比相对效应；Q2 的 A/B 桥接及 Q3 四变量最优均是指定假设和支持域内的**条件结果**。Q3 已有完整条件作答、结构转移和部分外测，不得表述为真实训练的无条件联合最优。各目录 `curated_manifest.json` 指向精简文件哈希，`upstream_manifest.json` 指向原发布包。此前下文的“当前个人分支状态”和旧计划是当时快照，以本节及新交接为准。

2026-09-26 后续整理：main 的旧 `outputs/chm` 目录经逐文件核对后清理；正式 Q1 v2 清单仍保持原 SHA，九个输入的同字节副本集中于 `outputs/Q1` 并由读取器复核。Q1–Q3 的关键实验方法与验证记录进入 `experiments/Q1`、`Q2`、`Q3`，索引见 `experiments/experiment-log.md`；个人分支继续保存全量运行中间文件。CYJ 当时的远端 `74e678e319b58e2aab230a7b7233fa53f3053fa5` 只追加 Q3 合作计划，Q2 v8 数值生产者不变；最新签收见下段。

本轮远端三分支复查又补入 Q1 逐次重拟合及估算压力记录、Q2 的 B1 冻结输入和逐项验证及 18 组接口样例、Q3 的官方预算假设逐格表及 42 个公开模型外测逐行表。审查期间 CYJ 远端前进到 `53b4fb51fc697d4e1584502b1fe66af40dd5242f`，对 CHM 固定 Q3 结果完成声明范围内的独立条件签收；报告、三份机器审计与理论节更新亦已收录。精确发现和核验见 `experiments/20260926-cross-branch-completeness-review.md`。公开 N/D 外测尚未由 CYJ 独立重跑，`direct` 映射政策的 Q3 全预算对照待补；A/B 桥接仍未实证识别。

更新时间：2026-09-23（北京时间）。阶段：F 题启动、三人并行协作初始化。

> 2026-09-24 论文入口更新：`paper/latex/main.tex` 是第二十二届华为杯模板基础上的整体协作初稿，Q1 已迁入 `sections/chm/q1.tex` 并附五图，其余问保持清晰占位；写入权按 `paper/latex/README.md` 和 `TEAM_WORKFLOW.md` 分配。2026 年官方格式及本机缺少 XeLaTeX 导致的 PDF 编译均尚待核验。

## 已完成

- 已按用户决定将 F 题设为唯一当前赛题。
- 已读取本地 DOCX 题面正文及数学文本，登记题面和数据说明 SHA256。
- 已初始化六个记忆文件、每日计划和工作区/仓库入口规则。
- 已明确额度预留、任务结束提交和远程 SHA 核验流程。
- 已按三人拆分任务：chm 负责 Q1 与 Q3 求解；cyj 负责 Q2 与 Q3 理论支持；zhh 负责 Q4，建议兼集成人。人名已由用户确认。
- 新增 TEAM_WORKFLOW.md、三人成员记忆、交接记录规范、三个接口草案与 PR 验收模板；TASK_PLAN.md 已补逐时点三人任务矩阵。
- 按用户要求将题面/说明迁入 problem/F/、全部附件迁入 data/raw/real_attachments/；2,014 文件逐一通过迁移前后 SHA256 校验。共享入口 DATA_INDEX.md，四个压缩数据文件使用 Git LFS。

## 当前事实

用户已明确要求所有模型绝对不得参考隐藏页边文字，已落实到 AI_READING_RULES.md、各模型入口、公共/个人记忆和 AI_CONTEXT.md。默认正文为 problem/readable/DATA_DESCRIPTION_VISIBLE.md；96 行已知隐藏文字已过滤，其他字符在过滤阶段完整保留。完整审计引用移入隔离区，普通报告仅保留结论。既有会话须重新核验来源，不假定能自动清除模型记忆。

历史原版数据说明 PDF 已完成隐藏文字审计；报告见 problem/PDF_TEXT_AUDIT.md。当前 `problem/F/数据说明.pdf` 已在 `55743ca` 替换为清理版，SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`，13 页且无文本层；旧隐藏文字特征计数为 0。机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

用户已明确批准公开上传并指定 chm、cyj、zhh。更名、成员文件及接口路径更新完成；题面和全部原始资料已随提交 a9ab4058a33ef56ba2c93b7fb451d776cb0c2e50 上传到现有远端，已核对远端 main SHA 一致。Git LFS 上传报告 4/4 对象、310 MB 全部完成；本地 2,014 文件 SHA256 校验通过。

Gemini 历史建模结果已作废并由 `58f4f0a` 丢弃文件内容；当前没有从该历史工作继承的可用于论文的数值结论。数据说明 PDF 已完成安全替换与字符层复核。`team/chm-data` 已创建并与当前 main 文件树一致；cyj/zhh 分支状态仍需各成员实际核对。完整附件编号映射与正式数据审计仍待完成。

## 2026-09-24 全团队审查规则升级

用户已明确要求将完整仓库/模型审查流程作为 main 公共规则。根目录新增 `REPOSITORY_REVIEW_PROTOCOL.md`，适用于 chm / cyj / zhh 与所有接入本项目的 AI。

以后“审查远程仓库/分支、本地仓库、代码、数学模型、问题、结果、论文结论”等请求不得只做代码级检查，必须覆盖变量来源、可识别性、数据角色、泄漏/support shift、文献条件、公式-代码一致性、baseline/敏感性、验证、结论等级、跨附件接口、可复现性和从零 red-team。

本规则源于 Q1 的 identifiability failure：数值可拟合不代表结构参数可识别。以后任何无法由字段和实验设计识别的量必须标记为 unidentified / sensitivity-only，而不是为了下游衔接补造。

## 下一步优先级

1. 23 日 10:00 前核对官方规则与版本、由 chm/cyj/zhh 确认唯一集成人与提交人；各自 clone 和建立个人分支。
2. 23 日 12:00 前完成附件 A/B/C 文件、字段、规模、可信度与编号对应表，核验数据说明。
3. 23 日 18:00 前明确指标口径、清洗规则、训练/检验/外推边界、四问输入输出接口。
4. 23 日 22:00 前完成首批基线、论文骨架和实验记录规范。

详细时点见 `TASK_PLAN.md`。若接手时已过计划时点，先记录差距并调整剩余安排，不得把待办自动记为完成。

## 交接与备份

普通成员每次只更新本人成员记忆与新增交接，再提交推送本人分支并核验 SHA；本文件与 progress.md 由集成人验收合并后维护。此前初始化提交 `3d0e0b1` 已推送并核验；本次新增协作方案的推送状态以实际 Git 与远端核验为准。失败时下次优先恢复同步。

## 2026-09-23 跨分支依赖与协作规则同步

公共协作规范已新增：`TEAM_COLLABORATION_DEPENDENCIES.md`。本节是该规范在 Memory Bank 中的公共入口；成员开工时除 `AGENTS.md`、`TEAM_WORKFLOW.md` 外必须同时读取该文件。

### 当前个人分支状态（仅作未集成观察）

以下内容已存在于个人远端分支，但尚未因本次公共规则更新而自动视为 main 已验收成果：

- `team/chm-data` @ `462713303b0db1be47d7260699ada3e12692c105`：Q1 配比侧已有逐目标域 Ridge、跨尺度验证、p 的经验尺度传递和 Q1 草稿；A1–A3 质量 Q 代码已准备，但 LFS 正文尚待完整环境实跑。
- `team/cyj-scaling` @ `932e22baff62c9349b8d82f354f4641901abfa4a`：附件 B 结构/身份审计已完成；正式 N-D-Q-p 标度律尚未拟合，当前没有可供 Q3 调用的验证版 predictor。
- `team/zhh-frontier` @ `d47cd2dc921333caecfcb95f09eb5a2f2714d0db`：Q4 基线、C7 上下文情景和 Loss–Benchmark 桥接已有个人分支结果；其 `interfaces/zhh/CONTRACT.md` 与成员记忆存在状态滞后，正式集成前需由 zhh 自己同步。

### 当前必须联合冻结的接口

1. **Q 的共同尺度**：chm 的 Q1 评分尺度与 B6–B8 的 `Q_score` 不是天然同一坐标，chm+cyj 必须明确跨附件 mapping，并做敏感性。
2. **p 对 Q2 Loss 的接法**：chm 的 p 接口对应 13 个具体验证域 Loss，而 B1 只有泛化 `val_loss`；不得未经验证把 Pile-CC 或其他单域直接当成 B1 Loss。chm+cyj 必须共同冻结 Loss 定义、anchor 与敏感性面板。
3. **Loss → Benchmark**：zhh 的个人分支桥接留出结果显示外推较弱，因此 Q1–Q3 的 Loss 不能直接等同于 Benchmark 增益；最终必须传播桥接不确定性。

### 当前跨题硬依赖

- Q2 的经典 N-D 基线可以不等 Q1；但最终 `L(N,D,Q,p)` 必须等待 chm 的正式 Q/p 接口。
- Q3 可先搭框架，但真实优化结果必须等待 cyj 的验证版 predictor；上下文长度使用 zhh 的 C7 外生情景。
- Q4 的历史/评测部分可独立推进；对 Q3 结果做能力解释时必须接收 chm/cyj 的正式 Loss 输出并传播桥接误差。

### main 同步要求

所有成员在接收跨成员接口、开始当天工作或公共规则更新后，先执行 `git fetch origin --prune`，再在本人分支合并 `origin/main`。若暂不合并，至少用 `git show origin/main:TEAM_COLLABORATION_DEPENDENCIES.md` 阅读最新公共规则。个人分支成果只有经过验收并进入 main 后才成为正式公共输入。
