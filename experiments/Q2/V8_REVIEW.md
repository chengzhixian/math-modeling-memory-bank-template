# Q2 v8 论文定稿审查与数值追溯

时间：2026-09-25（北京时间）。审查对象：本地 `team/cyj-scaling`，起点 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`，相对 `origin/main@f9693bbf4c205aa46d3719f6f8a1d6f26561d05f`；开始时工作区干净、远端 CYJ SHA 与本地相同。审查范围为 `paper/latex/sections/cyj/q2.tex`、`q3_theory.tex`、v8 接口、冻结输出及当前可见题面；不宣称全队 Q1/Q3/Q4 已完成审查。按根目录 `REPOSITORY_REVIEW_PROTOCOL.md` 执行。

## 可信来源与 requirement→data

直接读取当前题面 DOCX 问题二段落 22–26、附录段落 50，使用当前可见数据说明 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`；原始附件 B1/B7 CSV 表头分别含 `N_params_B,D_tokens_B,val_loss` 和 `N_params_B,D_tokens_B,Q_score,val_loss`。B1、B7 当前文件 SHA256 分别与 `outputs/cyj/classic/classic_fit.json`、`outputs/cyj/q2_v8/b7_quality_extension.json` 登记值一致。Q1 只消费 CHM v2 派生接口，其 manifest SHA256 为 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`，不重读附件 A。旧 PDF 隐藏文字与作废 Gemini 历史提交完全排除。

| 题面要求 | 证据字段/文件 | 数据角色与限度 |
|---|---|---|
| 经典 N--D 标度律 | B1 `N_params_B,D_tokens_B,val_loss` | 主拟合；1176 同源记录，8 规模组 |
| 质量进入模型 | B7 `Q_score,val_loss` | 450 条半合成点；B6 与 B7 重叠，B8 冲突另审 |
| Q1 的 Q 与 p | CHM v2 质量映射、配比 interaction surface、13 目标参考 Loss | A 侧派生；无 A/B 成对质量或共同绝对 Loss |
| 轨迹、跨族/文献检验 | B2/B3 轨迹、B4/B5 同族规模配对 | B3 插值、B2 半合成；B4/B5 只作方向验证 |
| 百亿以上外推 | B9 元数据、B10 estimated Loss | 只作支持域压力，不作真实外测 |
| 边际、弹性、替代/互补 | v8 解析导数、冻结 `marginals_elasticities.csv`、`quality_scale_local_tradeoff.csv`、136 对领域 CSV | 条件模型内部、局部、非因果 |

## 变量来源与识别性

| 符号 | 来源、单位和支持域 | 识别状态 |
|---|---|---|
| $N,D$ | B1/B7，同为十亿参数/十亿 token；正式交集 $[0.070542,11.965825]\times[10,299.893]$ | B1 同源条件可估计 |
| $Q_B$ | B7 半合成 `Q_score`，范围 $[0.1,1]$ | 仅 B7 内条件可估计 |
| $Q_A(p)$ | CHM Q1 v2 中 6 个 direct/near-direct 已映射 A1 评分的条件均值 | A 侧派生；未映射域缺失 |
| $g(Q_A)$ | 已映射评分极值到 B7 区间的单调代理及截断 | A/B 映射未识别，敏感性假设 |
| $r_w(p)$ | CHM Q1 v2 的 13 目标相对参考 Loss 与给定权重 | A 侧条件对比可计算；向 B 迁移未识别 |
| $L$ | B1 骨架＋B7 质量项，再乘 $\exp(r_w)$ | 同源 B 项可检验；跨源绝对 Loss 不可识别 |

数据角色在拟合前冻结；B6 与 B7 的完全坐标重叠不作独立检验。B3 与 B1 风格轨迹同源，B4/B5 目标口径不同，B10 estimated。B7 的 240 条点位于 B1 的 N/D 矩形外，正式预测只取交集。文献标度式提供候选形式，不能证明 A/B 桥接。B1 小残差也可能受到生成/舍入结构影响，缺少原始评估记录，正文已降级为同源重构。

## 公式、验证、数值与 claim ladder

代码 `src/cyj/ndqp_scenarios_v8.py` 与论文式一致：固定 B1 五参数、B7 三参数质量增益、`Q_A(p)` 的 clip 代理、`exp(r_w(p))`；N/D/q 偏导和 p 的两条路径均在文中分别说明。质量代理在 clip 边界取单侧导数。示例弹性把输出的带符号 $xL_x/L$ 取负，符合论文 $-xL_x/L$ 的定义。质量提高 0.05 对应旧质量扩模 `1.144490` B、等 Loss 新规模 `0.875789` B；10 B 点提高 0.1 时旧质量扩模无支持域内根。领域对采用可行零和方向，不能把环境偏导当可执行操作。

冻结 `manifest.json` 的 22 个输出文件 SHA256 全部匹配；B1/B7 原始 CSV 哈希匹配；B1 1176 行、B7 450 行/24 个外层折、136 对领域结果计数匹配。论文关键数值逐项对照 `classic_fit.json`、`b7_quality_extension.json`、`b7_backbone_comparison.csv`、`b2_b3_validation_summary.json`、`scale_order_validation_summary.json`、`marginals_elasticities.csv`、`quality_scale_local_tradeoff.csv`、`domain_pair_substitution.csv` 与 `domain_pair_interaction.csv`。冻结发布记录证明主体提交 `615c078` 曾在远端；本次没有重跑会改写发布记录的 finalizer。

基线/消融：B1 无项模型与八参数 B7 比较结果已在冻结诊断，本文只用八参数作 comparator。B7 的 nested held-level 验证仍属半合成同源条件泛化；B2/B3 不是独立真实外测，B4/B5 只支撑方向，B9/B10 只支撑压力讨论。质量桥接尺度 0.5/1/1.5 的示例 Loss 为 2.385343/2.344348/2.303352，表明结论依赖桥接假设，不能写成置信区间。主要结论最高为 L1/L2 条件模型内描述与预测；不进入因果 L4 或支持域外 L5。

从零 red-team：只看题面与表头，最多得到 B1 的同源 N/D 关系、B7 半合成 N/D/Q 关系、A 侧 Q/p→逐目标 Loss 对比及给定桥接假设下的情景计算。附件没有识别 $Q_A\to Q_B$ 或 A/B Loss 统一的成对实验；因此一个数值稳定的联合曲面也不能升级为实证跨源规律。论文正文已把这些桥接写成代理和敏感性。

Git 集成检查：`origin/main...HEAD` 在开工时为 main 独有 0、CYJ 独有 98 提交；本轮只写 CYJ 所属章节、实验记录、成员记忆和交接，不修改公共或他人成员文件。历史 v7 发布文件保持不变。

发现分级：**BLOCKER（若主张经验跨源规律）**：A/B 质量及 Loss 坐标不可识别，必须先取得同目标成对实验；当前论文已经按条件模型降级，故不阻断此范围论文。**MAJOR**：CHM Q3 正式 consumer 验收仍待完成，不能称问题三完成。**MINOR**：总稿还有 CHM Q1 两处 overfull 与公共未定义文献引用，交给集成人/对应负责人；不在 CYJ 范围直接改。最终判断：**VALIDATED FOR STATED SCOPE**（Q2 v8 条件论文及 CYJ 理论接口），并非跨来源实证验证或整篇论文 submission-ready。
