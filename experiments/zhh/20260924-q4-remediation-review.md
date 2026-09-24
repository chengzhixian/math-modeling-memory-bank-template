# zhh Q4 审查与整改复核（2026-09-24）

## A. 范围与 Git 冻结

本地仓库 `math-modeling-memory-bank-template`，分支 `team/zhh-frontier`；整改前 HEAD 为 `ec275f8908329d40b15ba153f6d7b1f3ebacde0c`，本地跟踪 `origin/main` 为 `af4857045e5df62afc9815bce4b98dbbb8867253`，merge base `968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd`，相对 main 15 behind/6 ahead。整改前工作区干净，`origin/team/zhh-frontier` 与 HEAD 一致。仅审查和修改 zhh 文件；chm/cyj 发现及跨成员正式接口不在本轮修改范围。GitHub fetch 因连接失败，远端 SHA 只能在恢复网络后再核验。

可信来源：当前 F 题题面、清理版 `problem/F/数据说明.pdf`、`problem/readable/DATA_DESCRIPTION_VISIBLE.md`、原始 C 附件、本分支实际代码和输出、main 的 `REPOSITORY_REVIEW_PROTOCOL.md`。`leaderboard_enhanced.csv` SHA256 `D8AE5B1E00F36BF17ADB0C3FBF88C60EDD54298625D2DB1AA744B2B001202799`；`loss_benchmark_bridge_expanded.csv` SHA256 `E175462233C2B856E2878C603055B4ED70135F021300F912852AF1BB485BA4FD`。禁止来源：历史隐藏 PDF 页边文字、已作废 Gemini 工作、旧预测日志、未验收跨成员模型。

## B. 需求—数据与变量追溯

| Q4 要求 | 变量与字段 | 单位/性质 | 充分性 |
|---|---|---|---|
| 能力指标/趋势 | C1/C2 六项得分、`Submission Date` | 分数与日期，榜单观测 | 可做短窗描述与留出关联；提交日非训练完成日 |
| 规模/非规模分解 | C1/C2 `#Params (B)`、`Type`、六项分数 | 十亿参数、类别、等权派生分数 | OLS 条件关联可估；技术贡献因果份额不可识别 |
| 开放模型 | C1/C2 `Epoch_AI_Open_Weights`、`Hub License` | 状态与许可证代理 | 严格 yes 可观测；许可证不能证明权重可获取 |
| 算力放缓 | C4 `Training compute (FLOP)` | FLOPs，汇编观测 | 历史算力前沿可述；算力到参数及能力映射未识别 |
| Loss 到能力 | C6 `Val_Loss`、`Loss_Source`、六项评测 | 不同来源 Loss 与分数 | 高可比仅 7 行；跨来源数值换算未识别 |
| 逐任务和上下文 | C8 JSON 子任务；C7 `max_position_embeddings` | 准确率、token | 聚合与外生容量情景可复现 |

核心式 $S=\beta_0+\beta_N\log_{10}N+\beta_t t+\beta_I I+\epsilon$：$S$ 是六项完整案例等权派生分数，$N$ 来自 C1/C2 参数量，$t$ 由提交日与 2024-06-01 的差派生，$I$ 由 `Type` 派生。系数是当前样本及函数族下的条件估计，不是结构技术效应。C4 的算力、C6 的 Loss 与此式没有经过验证的共同坐标；相应能力预测与桥接判定 `not identified`。

数据角色：C1/C2 全体用于描述/主回归，按提交时间 80%/20% 分作时间留出诊断；严格/扩展开放集、分类型、交互项、最新模型行均为敏感性而非独立外部测试。C6 Loss 排序及来源留出仅用于桥接失败诊断。C3 历史行只作外部背景，不与 C1/C2 拼接。C8、C7 只作描述和外生情景。选择这些敏感性口径后，其时间留出不能再称无偏最终测试。

## C. 发现、影响与处理

### BLOCKER：旧 Markdown 算力放缓预测

整改前 `paper/sections/zhh/q4.md` 发布与当前代码相矛盾的两组点值及 Bootstrap 区间；其公式把算力对数增长直接加到参数对数增长，没有配对映射，系数重采样也未校准未来观测误差。影响第 5 节、接口摘要与最终论文。已撤回数值，Markdown/LaTeX/接口统一 `not_identified_for_compute_slowdown`，旧日志改名并标记撤回；重跑 `q4_results.json`，预测数组仍为空。未来若要正式预测，需独立配对数据与支持域外误差校准。

### MAJOR：开放性代理和模型类型组成

原 `isOpenModel` 将 Epoch 明确 no 但有许可证的 6 行纳入，且把许可证当作开放代理。改为明确 no 优先排除；扩展集 2,672 行，严格 Epoch-yes 集 424 行。严格集与扩展集的规模绝对份额分别为 48.97% 与 43.85%，类型系数 6.671 与 3.648；分组时间斜率 pretrained 0.431、non-pretrained 1.115 分/月。交互模型样本内 $R^2=0.531$，最新模型行回归时间斜率 1.080。差异说明单一共同时间斜率、43.9%/56.1% 不能被当作开放权重总体稳健技术份额。已重跑主回归、分解、时间留出并同步两种论文稿。

### MAJOR：桥接 RMSE 被写成区间

旧 `interfaces/zhh/RESULTS.md` 建议加减 7.06 分。该值为一次 Loss 排序留出 RMSE，按来源留出 RMSE 9.887；两者均非 95% 半宽。接口已删除加减建议并保持 `unidentified`。C1 模型名重复、C6 按名称连接可扩行，C3 历史 `Average` 与六项均值不总一致；本轮代码没有做这些危险连接，论文明确禁止未经版本/日期校验地拼接。

### MINOR：文档与产物漂移

更新了成员记忆、实验记录、合同、结果摘要、Markdown 与 LaTeX；旧运行文本保留为带撤回标记的历史证据。`frontier_forecast.csv` 仍为空预测字段。输出中保留的固定参数前沿 12 个月时间项 46.63 分只是超出约九个月观测窗的代数算例。

## D. 独立反向审查与复现边界

从题面与 C 表头重新看，六项完整案例可定义能力代理，参数量、类型和提交日期支持短窗关联；C8 支持子任务聚合；C7 支持观测容量档位。原表没有同时提供训练算力、参数、同尺度 Loss 与 Benchmark 的配对纵向样本。模型类型、后训练、评测版本和选择机制均可替代解释时间相关变化，因此无法识别算力放缓对未来能力的效应。模型复杂度未带来结构识别；简单的分组回归已显示共同斜率不稳定。没有独立未来样本或来源独立的桥接区间校准。

复现命令：`node src/zhh/q4_analysis.test.js`。它先重跑 `q4_analysis.js`，再核验排除冲突行、两类样本、类型斜率和空预测。`python scripts/build_safe_pdf_context.py --check` 与 `python scripts/check_ai_reading_rules.py` 已用 Codex bundled Python 通过。`verify_raw_data.ps1` 因四个 A 附件仍是 LFS 指针失败；本轮使用的 C 附件实际可读，不能据此宣称全量原始资料校验通过。OCR 工具因未配置 LLM endpoint 未运行。此报告不宣称正式外部预测验证。

## E. 判断

**VALIDATED FOR STATED SCOPE**：C8 聚合、C7 观测情景、C1/C2 短窗口描述与条件关联，以及开放性和模型类型敏感性可作为带限制的 Q4 稿件依据。算力放缓能力预测和跨来源 Loss→Benchmark 换算仍为 **NOT READY**；点值、区间与正式下游接口不得发布。
