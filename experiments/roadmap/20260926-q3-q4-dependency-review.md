# 第二章技术路线图 Q3/Q4 依赖复核

日期：2026-09-26。对象：`paper/latex/drafts/total_technical_roadmap.tex` 的跨问题箭头；本地分支 `codex/problem-restatement-20260926`，修改前 HEAD `13593401b124d48be78d7360de803c7d16d7ac51`，工作区无未提交修改，较跟踪分支领先 1 个尚未推送的提交。初查时使用本地 `origin/*` 快照；修订完成后 `git fetch origin --prune` 成功，复核远端 `main` 为 `a19039b5d11c91cf32e301dc85b2f4d50b5a75b7`，本分支跟踪端为 `fc9e8d030d117b483ea1962b470ffbfded5a3735`。

## 可信来源与范围

- 权威要求：`problem/F/算力约束下提升大语言模型能力的资源配置建模.docx` 可见正文（三、建模任务及问题三、四）；机器可读数据角色：`problem/readable/DATA_DESCRIPTION_VISIBLE.md`。
- 实施状态：`paper/latex/sections/cyj/q2.tex`、`paper/latex/sections/cyj/q3_theory.tex`、`paper/latex/sections/chm/q3_numerical.tex`、`paper/latex/sections/zhh/q4.tex`、`interfaces/cyj/CONTRACT.md`、`TEAM_COLLABORATION_DEPENDENCIES.md`；fetch 后又查看 `origin/team/zhh-frontier@ee23b200e9de7f78477d945b186233741bd3b8fd` 的 `interfaces/zhh/CONTRACT.md` 与 `paper/latex/sections/zhh/q4.tex`。
- 禁止来源：历史 PDF 隐藏文字及作废的 Gemini 历史提交，未用于本图或本次判断。
- 范围只审查路线图表示的依赖和主张，不复算 Q1–Q4 模型结果；因此数值、代码、原始附件完整性和 held-out 表现仍以各成员审计为准，本记录不提升任何模型的证据等级。

## Requirement → data / 变量追溯

| 要求 | 数据/变量 | 角色与边界 | 图中路径 |
|---|---|---|---|
| Q3 约束优化 | Q1 配比与质量，Q2 条件 Loss，C7 上下文 | Q2 跨源桥接依赖明示假设；C7 是外生取值 | Q1→Q2→Q3，Q3 生成条件配置与预测 Loss |
| Q4 历史能力演进 | C1/C3/C4/C8 等能力与元数据 | 可独立先做描述/预测候选；贡献解释、远期外推另需验证 | 附件 C→Q4 历史分支 |
| Q4 解释前三问 Loss | Q2/Q3 Loss 与 C5/C6 Benchmark 桥接 | Loss 坐标须可比；当前 zhh 合同称桥接弱识别，不能确定性换算 | Q2→Q4，Q3 条件 Loss→Q4 映射→误差传播 |

| 符号 | 来源 | 单位/性质 | 可识别性 |
|---|---|---|---|
| $N,D$ | 附件 B；Q3 的选择变量 | 参数量、token；论文中均以十亿计 | B1 支持域内条件预测；跨来源外推不自动成立 |
| $Q_A,\boldsymbol p$ | 问题一附件 A | 质量评分、17 维比例；$\boldsymbol p$ 和为 1 | $Q_A\to Q_B$ 缺成对观测，属于条件桥接 |
| $\widehat L^*$ | Q2 条件模型在 Q3 候选配置上的输出 | 验证交叉熵损失；情景预测 | 跨数据源绝对坐标未经验标定 |
| Benchmark | 附件 C 的多维评测 | 得分，任务口径不同 | 与 Loss 的映射弱识别，误差须传播 |

## 发现与修正

**MAJOR：原图省略 Q3→Q4 条件输入。** 题面称前一问输出为后一问输入，且问题四要求把前三问的 Loss 与 Benchmark 联系起来；团队依赖文档第 9 节也要求 Q3 向 Q4 提供配置、预测 Loss、区间及版本。原图只有 Q2→Q4 和 Q3/Q4 最终汇合，容易被读作两问完全独立。修正为 Q3 条件损失到 Q4 损失—能力映射的虚线箭头；保留附件 C 驱动的 Q4 历史分析支路。

**MAJOR：不能把虚线桥接解释为已验证能力增益。** Q2 跨源 $Q/\boldsymbol p$ 桥接无成对观测；zhh 当前 v3 合同仍将正式 Loss–Benchmark 转换标为 `unidentified`，条件转换只作敏感性。已有 12/24 月算力放缓情景和参数条件范围，但完整 Q4 仍为 `NOT READY`，参数范围及情景包络不能冒称 95% 预测区间。因此虚线只表示条件传递。图中 Q3 输出改写为“条件配置与预测损失”，Q4 输出改为“条件能力前沿及情景范围”。

**MINOR：现有工程完成状态与论文路线不同。** 当前检出的 `paper/latex/sections/zhh/q4.tex` 是占位；zhh 远端分支有候选论文与条件结果，但未进入当前论文主文件，合同标为完整 Q4 未验收。其分解只有规模关联与非规模综合项，不能识别纯技术因果份额。图中相应节点已降级命名。本图属于第二章研究流程，不是完成进度图。

## 其他审查 Gate 与结论

- 数据角色：A4/A5 为训练、A6–A11 为检验、A12–A15 为估算外推；B7 半合成；C5/C6 桥接混合可比性。图不将这些数据互作独立验证。
- Overlap / support：本图无逐行 join 或新拟合，不能据图证明 A/B/C 同一 Loss 坐标，也不能据图证明 C 预测可外推。图不复用历史作废结果。
- 文献、公式↔代码、非有限值、baseline/ablation、held-out：此次只改可视化依赖，不引入参数或新算法；相应数值审查不由图稿代替。
- Claim ladder：Q4 历史分支至多表示待验证的描述/预测路线；Q3→Q4 只为 sensitivity-only/weakly identified 的条件桥接；不能表述为因果贡献或确定性能力提升。
- Red-team：仅从题面和附件分工出发，Q4 可先用 C 数据研究历史能力，但“前三问 Loss 转能力”必经可比性桥接，故两问应是部分并行、条件耦合。
- 本图范围判断：**VALIDATED FOR STATED SCOPE**（依赖关系表示）；Q2→Q3 与 Q3→Q4 的实证跨源桥接、Q4 能力预测仍 **NOT READY**，不能由版面验证代替科学验证。

复现：在仓库根目录用 XeLaTeX 编译 `paper/latex/drafts/total_technical_roadmap.tex`，以 `pdfinfo` 核对 A4 单页，并将 PDF 渲染为 PNG 检查箭头、分区与文字。PDF/PNG 路径见 `output/pdf/`。
