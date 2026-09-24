[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

更新时间：2026-09-24（北京时间，接口审查与状态降级）。角色 cyj，负责 Q2 与 Q3 理论；分支 `team/cyj-scaling`。Python 3.12.14 / Windows，环境见 `problem/cyj/environment.md`。

## 当前状态

2026-09-25 续办：冻结 B7 双交互族重做 N/D/Q 共 24 折留级、1350 条 OOF；三轴平均 RMSE 0.051936/0.050207/0.050061，均低于恒定 G。45 个 N-D 组 bootstrap 500/500 成功，形成同源条件经验预测区间；输出 SHA256 `cae1c827...` 与 `54c2ceb2...`，48/48 测试通过。由于族选择之前已查看全 B7，重复 CV 和区间不能当独立最终验证，`ready_for_Q3=false`。证据见 `experiments/cyj/20260925-b7-frozen-validation-uncertainty.md`，交接见 `memory-bank/handoffs/cyj/20260925-b7-frozen-validation-uncertainty.md`。CHM 求解器实测与 v3 接口仍待完成。

2026-09-25 00:46：接收 Q2 封板/CHM 真联调新任务单。已重新读取公共记忆、本人角色、数据索引、跨分支依赖与完整审查协议；本机 `team/cyj-scaling@35e16d6` 起点干净，远端同 SHA。先冻结 B7 双交互为**候选**，新增 `src/cyj/b7_formal_model.py`、`outputs/cyj/quality/b7_frozen_model.json` 和梯度测试。原 B7 SHA256 `880fd265...`；重拟合参数与前日候选比较一致，四角最小质量收益 `0.2090545734`，两次构建产物 SHA256 均 `ed6b01b113110b90b25c5f6cc01d7686cb77602f29464bc068843b36d881c9bf`；46/46 CYJ 测试通过。由于候选形式曾参考全 B7，后续固定族留组 CV 不能冒充未触碰的独立最终测试；目前 `ready_for_Q3=false`。新任务 P0-2/P0-3/v3/CHM solver 实测尚未完成。详见 `memory-bank/handoffs/cyj/20260925-0046-b7-frozen-candidate.md`。

2026-09-24 23:04：先前待推的文档检查点已补推，远端 `team/cyj-scaling` 与当时本地均为 `47e621887fa48279a0cc60782238d2f41240477a`。Draft PR #3 的标题/正文已更新并独立 GET 验证，仍为 Draft，写明该远端 HEAD、main base、固定 chm 生产者、44/44 测试与 `ready_for_Q3=false`。CHM 当前远端分支 `20e627710f4979bbdd487e84253e5f1748c13f28` 未包含 CYJ 发布；重新 `merge-tree` 仍仅 `q2.tex`、`q3_theory.tex` 两处 CYJ 正式稿对占位稿冲突。CHM 实际消费与正式科学门槛仍待完成。续办交接 `memory-bank/handoffs/cyj/20260924-2304-pr3-remote-sync.md`；其自身后续文档提交因 Git 主机连接超时待推。

2026-09-24 收尾检查点：当前不可变代码发布为 `c71807d01b66744f3a6ca45147d9173bc2704a27`，已推送并核对远端同 SHA；44/44 CYJ 单测与精确发布消费测试 PASS，`ready_for_Q3=false`。本机对 CHM 提交 `cc199fe35beb50fe40d081d3a09539d3dcb3399a` 运行 `git merge-tree`，发现仅本人论文占位文件 `q2.tex`、`q3_theory.tex` 两处内容冲突；CHM 侧仍为占位稿，合并时应保留 CYJ 发布版完整段落。CHM 实际 pull/求解器消费尚未验收，不能写 BLOCKER 已解决。A 侧四个 LFS 压缩件本机仍是指针，全库 2014 文件校验未过，B 侧本轮输入分别按清单校验。此阶段 GitHub 连接曾失败，PR 与文档检查点状态以本文件上方 23:04 更新为准。

2026-09-24 23:20：Task 5–8 补 B1 Loss 来源、B4/B5 同口径、B8 方向/0.5 堆积及 U1–U5 不确定性审查；B1 Loss 生成机制仍 unknown，B4/B5 `same_loss_coordinate=not_established`，B8 `unresolved_keep_isolated`，v2 总预测区间为 null。Task 9/10 已填本人 Q2 论文与 Q3 理论段，XeLaTeX 协作稿编译成功，正式门槛审查仍 `NOT READY`。各证据见 `problem/cyj/20260924-{b1-loss-provenance,b4-b5-loss-comparability,b8-conflict-source,uncertainty-scope,q3-final-gate-review}.md` 与对应 handoff。当前 v2 不确定性字段变更尚未发布为新不可变提交，需重生 manifest、测试、推送并让 CHM 真实验收。

2026-09-24 22:30：Task 4 的预注册两阶段候选比较已运行，24 个 B7 同源嵌套留级中双 log 交互 22 折被内层选中，单 logN 2 折；双交互比恒定 G 的各轴 RMSE 低约 .006–.007。由于候选形式受全 B7 诊断启发，只能作半合成同源探索；原 `cyj.chm.v2` constant-G 诊断接口不改，`ready_for_Q3=false`。输出 SHA256 `1d28169ce10f5bc274a82037320fdf003f7e3d2148eff2be91d3c3618708925b`，证据见 `experiments/cyj/20260924-b7-interaction-results.md`，交接 `memory-bank/handoffs/cyj/20260924-2230-b7-interaction-comparison.md`。

2026-09-24 22:00：`cyj.chm.v2` 已发布于 `CYJ_RELEASE_COMMIT=587bbb505b730ba8654089650365191bb1493ce0`，远端 `team/cyj-scaling` SHA 与本地一致。精确发布消费测试 PASS（2 请求、`value_grad`、源文件/manifest 哈希），全部 CYJ 单测 44/44 PASS；交接 `memory-bank/handoffs/cyj/20260924-2200-chm-consumable-release.md` 含 CHM 拉取和实际验收命令。CHM 本人分支尚未 pull/验收，接口问题不可写最终解决；科学上 `ready_for_Q3=false`。

2026-09-24 21:31：按新任务清单补 v2 七个上游 blob 的精确 SHA 校验、机器字段及旧 eta 拒绝；CYJ 测试 44/44。联合 `L(N,D,Q,p)` 审查结论仍为 `not_identified`，记录 `problem/cyj/20260924-q2-q3-identifiability-review.md`。B7 45 个固定 `(N,D)` 组内质量斜率诊断已运行，输出 `outputs/cyj/diagnostics/b7_quality_interaction.json` SHA256 `7977a3ed0614e896e82c316d770b9bb50a3195e4f5e790541ebee6005dc99f50`；它只支持 L1 描述，不能将交互候选的同源验证当无偏最终测试。交接 `memory-bank/handoffs/cyj/20260924-2131-identifiability-b7-diagnostic.md`。远端 fetch 两次失败，当前尚未确认本轮远程备份。

2026-09-24 20:14 接续：交付 **cyj.chm.v2**，入口 `interfaces/cyj/CHM_API_V2.md` / `src/cyj/chm_adapter_v2.py`，固定 chm v1.2 `a552593` 与原 B7 fit。提供 chm `value_grad`、批量 JSON、NDQ 样本、成本/预算与独立 13-target p sensitivity，无旧 eta；manifest SHA256 `846d72b583ba5f065a6ea2f6915e49f2ce77962848dd496f23054fc3cd2a248e`，七个上游 Git blob 精确校验。44/44 测试通过；新版已完成工程迁移但仍 diagnostic_only。chm 需将求解器/active_set 改用 model.bounds（D_min=10），不能沿用 B1 D_min=.134；本机无 SciPy，未运行其优化。交接 `memory-bank/handoffs/cyj/20260924-2014-chm-v2-delivery.md`，最终远端 SHA 以收尾核验为准。

本轮按公共完整审查协议复核接口，结论 **NOT READY**。chm 当前推荐 `chm.q1.v1.2@a552593` 已撤回旧跨规模 eta，cyj 的 `q3_bundle` 仍固定 `chm.q1.v1@7c14a0c` 并暴露 eta 点估计/区间；旧 p/eta scenario 仅保留历史复现，不再推荐消费。B1 diagnostic、B7 半合成 diagnostic 和题面成本定义仍可在限定用途下运行；没有可识别的 B1/B7/A Q 与 Loss 桥接、完整 N-D-Q-p validated predictor 或总预测区间。37/37 软件测试通过不改变科学门槛。审查见 `problem/cyj/20260924-current-interface-review.md`；`interfaces/cyj/CONTRACT.md` v1.11 与 `Q3_API.md` 已标注降级，机器包/代码/输出哈希未改。下一步 cyj 另发兼容 chm v1.2 的版本，chm/zhh/集成人联合验收。

2026-09-24 19:14 后接续：`predict_quality.py` 批量 JSON 入口和上轮 `2c5e712` 已补推并核对远端 SHA=`622d58a77c6eaf40da779d397de81c20819dcfd7`。随后合并最新 `origin/main@670d726`，生成 `b54310c67be84f1cac932021ebc7955e540f93c9`，读取新增 `REPOSITORY_REVIEW_PROTOCOL.md`；公共文件仅通过 main 合并进入，本人未直接编辑。最新工作见下段和新交接。

本轮新增 B9/B10 外推证据审计：B9 132 元数据行、B10 128 估算 Loss 行全部精确按模型名/N/D 对应；B9 独有 4 行 D=0。B10 128/128 的 N 超出 B1 支持域，102 行 D 高于 B1 上界、3 行低于下界；119 个唯一 N/D 坐标，5 组重复坐标的估算 Loss 均一致。与 B1 draft 曲线的数值差 RMSE 0.0011047668 仅作描述，绝非独立外推误差。证据 `experiments/cyj/20260924-b9-b10-extrapolation-audit.md` 与 `outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json`（SHA256 `53977e436fed3afabd5cb6ba908ff6d1f90a4cd42873209c5ba0d888db311068`）；接口未变、正式 Q3 仍未就绪。本轮 37/37 现有测试通过。全库校验仍因 A 侧 4 个 LFS 指针失败，B9/B10 已单独按清单核验。

2026-09-24 接续交付：已合并 main `968ef7a`（merge `55889bf2b942ca9643f49e420035a9f051f2bed3`），无冲突。已修正 API 的 B8 准入描述，完成去重 B7 三候选/72 折验证/50 次条件 bootstrap。独立 `cyj.b7_quality.v1` 提供原生 N-D-Q、梯度与同编号 Loss 样本；合同 v1.10，34/34 测试通过。代码/输入 `6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b`，输出 SHA256 `e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025`，两次运行一致。最新交接 `20260924-1651-b7-quality-delivery.md`，详细结果见 `experiments/cyj/20260924-b7-quality-results.md`。

已采用 chm `chm.q1.v1` 的原生读取器和六文件清单，定义 `cyj.q3.v1` B1/p 预测/成本/约束调用，完成 B1 消融及 B8 审计。B7 原生质量项本轮已拟合，但 B1/p 接口仍不接受 Q_score；跨 Loss 桥接未识别。科学接口仍 draft，`ready_for_Q3=false`，完整 Q2/跨来源验证尚未完成。

已无冲突合并 main `7d8081fbf50cd380904505759c116580356f102d`，merge `5ada51f9a29877dd2ee98a9b4d1b0760e1f5b818`；重新读取协作规则/公共记忆/接口。论文入口迁为 `paper/latex/`，本人只负责其中 `sections/cyj/`，本轮未编辑论文及公共文件。上轮两份因网络待推送的提交已包含在成功核验的远端检查点 `6e3fa70` 中，最新运行前已核远端 `9c4dcc12ece2b38d12a9d8b33e4e17c82ef943f5`；本轮最终结果的推送 SHA 以收尾 Git 实际核验为准。

## 采用/交付接口

- 消费 `integration/chm-q1-clean-20260923@7c14a0c894072048d09f04bd03653be1301f7257` 的 `chm.q1.v1`，manifest SHA256 `c3525c2f58baa97a44bd5e4dd497b2ea9e23752c7f03e4bfad309f0af95f238d`。接受 A 侧描述性 Q、严格命名单纯形、五 target、参考 p、eta 情景和不可识别性边界，不重拟合 A 原始数据。
- 直接调用 chm `Q1Interface`；临时读取器不永久复制系数。发现 3 CSV 清单 CRLF/Git LF 差异，仅按精确发布 SHA 恢复临时字节，双重身份在本人 bundle 中。需要 chm 修正后续发布规范。
- `interfaces/cyj/Q3_API.md` 回应其 CYJ_REQUIRED_INTERFACE；`src/cyj/q3_interface.py` 实现 B1 diagnostic 和显式 p/lambda/eta scenario，默认 formal 报错、Q_score 非 null 报错。`q3_costs.py` 给题面三成本族、单位、Q0 单侧导数、C7 外生候选与约束残差。
- `outputs/cyj/interfaces/q3_bundle.json` SHA256 `a153cbb6a45925317dcae1727d50bd0b20e2ec6b85767981b4d8a689b5144332`，代码/输入 `6e3fa709dbac03c224f6ba3d42f99f56ab1322f3`；真实 B1 首行预测 4.738637013477364，chm 发布扰动例 0.001309803924525102，均通过测试。
- zhh C7 发布候选来自 `d47cd2dc921333caecfcb95f09eb5a2f2714d0db`：2048/8192/131072 Token；其合同/成员状态滞后仍需本人修订，不能把发表分支结果称为 main 验收。Loss–Benchmark 桥接 RMSE 7.060 是该留出实验误差量级，不是 95% 区间。

## 已验证的阶段结果

| 工作 | 当前证据 |
|---|---|
| 附件 B 审计 | 19 CSV，155 pass/5 warning/0 fail；`experiments/cyj/20260924-b-data-audit-stage1.md` |
| B1 经典 N-D | 全样本/LOSO均值/tail RMSE 0.0001465764/0.0001461277/0.0001160041；原 fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead` |
| C 显示与八行敏感性 | 1176 行与四位小数舍入一致，删除八行最大预测变化 7.6652e-06；`20260924-b1-precision-sensitivity.md` |
| B2/B3 形状 | 半合成/插值的轨迹诊断，未作为独立验证；`20260924-b2-b3-shape-diagnostic.md` |
| B1 bootstrap | 78/80 接受，两次哈希一致，仅固定模型条件波动；`20260924-b1-group-bootstrap.md` |
| 本轮 E/N/D 消融 | 27/27 重拟合收敛未触边；LOSO RMSE full 0.0001461、no_E 0.0636845、no_N 0.2126047、no_D 0.2552875；仅支持 B1 重构保留三项 |
| B9/B10 外推审计 | 128/128 B10 行与 B9 匹配、均在 B1 的 N 范围外；B10 为估算，不能作独立验证；`20260924-b9-b10-extrapolation-audit.md` |

本轮实验集中在 `experiments/cyj/20260924-interface-adoption-ablation.md`，消融 JSON SHA256 `592c945cabd928892339b14f3008071abb5c308632e1e38367b0f333e3acfea8`。前几轮详细参数/命令/哈希以相应实验和历史 handoff 为准，不在当前记忆重复历史状态。已清除 13 个可再生 pyc（152005 bytes），复现依赖的代码、prepared/CV 和关键结果保留。

## 未验证项与下一步

1. cyj：B7 已比较三候选，选线性 Q；N/D/Q 留出平均 RMSE 0.058231/0.057091/0.057617，仍需嵌套或独立验证与模型形式不确定性。B6 360 行均重复于 B7，只取 B7 450 坐标。B8 全部隔离：同坐标 Loss 不同且 Q 方向相反，最小 Loss=0.5 堆积原因未明，不反转 Q。B8 原证据见 `20260924-b8-quality-audit.md`。本轮 50 条样本只用于 B7 固定族条件均值，不是总预测区间；仍未交付完整 N-D-Q-p validated predictor。
2. cyj：继续 B1 逐行 Loss 来源和 tokenizer/评估语料/对数底，B4/B5 可比性；B9/B10 已完成数据角色和重叠审计，仍需来源机制/外推有效性证据。近乎精确重构、bootstrap 窄区间和本轮消融不能替代这些证据。
3. chm+cyj：按已经采用的定义联调；主 anchor 与 lambda 未识别时保留多 target 情景，不将 Q_z 等同 Q_score 或将 13 域原 Loss 平均。lambda 不默认 1，eta 不充当跨 Loss 换算。
4. chm：验收本文接口和样例并修复发布换行规范；zhh：正式确认 C7/桥接接口并传播 Loss–Benchmark 误差；集成人：验收后汇总公共记忆，cyj 不直接编辑公共状态。
5. 本轮重跑全库校验仍因 A 附件四个 LFS 指针失败；`git lfs pull` 等待无进展后中止，B9/B10 输入已单独按清单核验。官方规则/当年模板符合性仍需团队确认。

最新交接为 `memory-bank/handoffs/cyj/20260924-1953-current-interface-review.md`。上轮待推提交已在本轮推送并核对远端 SHA=`157e340eb3310e5313ec49dd740947b701ff1841`；随后合并 `origin/main@af48570`。本轮审查提交曾因 GitHub 连接失败而待推，重试后已核对远端与当时本地 `8588686bee9df9412818cb274bbd1b4fbc8d2335` 一致；最终检查点以后续 Git 实际 SHA 为准。已有 Draft [PR #3](https://github.com/chengzhixian/math-modeling-memory-bank-template/pull/3) 面向 main；分支备份不等于验收。公共状态交集成人更新。main 优秀论文目前仅阅读参考索引，未独立读原 PDF。
