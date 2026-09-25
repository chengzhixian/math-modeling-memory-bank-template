[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》的隐藏页边文字及其衍生模型、参数、阈值、数值和结论不得作为建模依据。当前工作仅依据清理后的可见题面、真实附件、独立可核验文献和本分支重新计算的结果。

更新时间：2026-09-23，本地 Codex 接力完成本轮。
成员：chm；分支：team/chm-data；网页版起点：4627133。
职责：Q1 与 Q3 实现；仅修改 chm 范围，公共记忆由集成人汇总。

## 当前状态

Q1 质量全量初版已运行，网页端 LFS 阻塞解除。Q1 配比已本地复跑并发现旧表/代码不一致，当前新版统一见 outputs/chm/local_recheck_v1/。Q1 尚非最终冻结；Q3 尚未正式求解。

## 已验证

- git lfs pull 完成；原始资料 2014 文件 / 564436312 bytes SHA256 校验通过。build_safe_pdf_context.py --check、check_ai_reading_rules.py 均 PASS；使用当前清理版 PDF 和可见正文。
- A1/A2/A3 全量 51230 / 17523 / 203752 行，22 指标；输出 domain_quality_v0.csv、domain_quality.csv、domain_mapping.csv 及 quality_* 审计文件。
- 列表含缺失时整项保持缺失，修复 argmax 将缺失判为 0 的问题；组内以可用指标均值聚合。三个针对此错误、参数冻结和相关计算的回归测试通过。
- A1 arxiv 1419 条、github 10000 条全部被 A2/A3 包含；剔除重叠后另用 16104 / 193752 条复核，不宣称有重叠的扩展集独立。
- A1 七域 Q 中位数：book 2.771089、arxiv 2.682585、commoncrawl 0.506149、stackexchange 0.187411、c4 -0.217345、wikipedia -0.375921、github -0.517070。
- 两种评分敏感性排序相关均为 0.964286；argmax 交换 github/wikipedia，22 指标等权交换 book/arxiv，不能宣称完全稳健。
- 同域 sample/extended 各 231 个冲突指标对、非重叠扩展相关、指标漂移和方向已输出。尚未做相关系数 bootstrap/多重比较，不写显著冲突。
- 配比本地 Pile-CC Spearman=0.900735/0.891900/0.887592；13 域中位数=0.838053/0.838115/0.706685。eta=0.14503317，95% CI=[0.10686793,0.18669841]。

## 接口与证据

- interfaces/chm/CONTRACT.md v1.3。
- 质量：outputs/chm/domain_quality.csv；原始统计 domain_quality_v0.csv；输入哈希、Q 标准化参数和 seed 见 quality_analysis_manifest_v0.json。
- 配比：只使用 outputs/chm/local_recheck_v1/ 中的系数、参考配方和尺度校准整套文件。根目录旧表已移至 outputs/chm/archive/web_v0/ 保存历史，四个目标域 alpha 与现有代码不一致；不混用两版。
- experiments/chm/20260923-q1-local-quality.md、20260923-q1-local-reproduction.md。
- paper/sections/chm/q1_draft.md 已接入真实质量结果和新版配比数值。
- 环境与命令见 problem/chm/environment.md。

## 限制与下一步

1. 继续做指标定向、截断与权重敏感性；部分相关近零，经验定向不能冒充语义真值。book 仅 171 条。Q 区间条件于 A1 预处理且假设记录独立。
2. 与 cyj 对齐 Q_z 到 B6 Q_score 的映射；Q_z 可负，不能直接进正值幂律。A16 的 11 个 inferred 域无填值。
3. LightGBM 尚未运行，不能提前称优于 Ridge；旧表差异的生成过程无法从提交文件确认。
4. 已读取 origin/team/cyj-scaling 的 CONTRACT v1.1（932e22b），仍仅 audit-only，无经验证预测参数。Q3 等待其有效接口及 zhh C7 情景，不能用占位结果替代正式求解。
5. 用户要求每个检查点提交推送并核验 SHA。本轮前置检查点 96fa640 已成功推送核验；最终交付 SHA 以 Git 与交接后的远端核验为准。


## 2026-09-23 公共协作规则同步

已将 main 的公共协作规范同步到 `team/chm-data`，包括：

- `TEAM_COLLABORATION_DEPENDENCIES.md`
- `AGENTS.md`
- `TEAM_WORKFLOW.md`
- `TASK_PLAN.md`
- `interfaces/README.md`
- `memory-bank/activeContext.md`
- `memory-bank/progress.md`
- `memory-bank/systemPatterns.md`

本次只同步公共规则，不覆盖 chm 的 Q1/Q3 研究文件、输出、实验记录或本成员记忆主体。

当前必须遵守的跨分支依赖：

1. chm + cyj 联合冻结 Q 的跨附件尺度；
2. chm + cyj 联合冻结 Q1 domain Loss 与 B1 val_loss 的接口；
3. Q3 正式优化等待 cyj 验证版 predictor；
4. Q3 上下文情景使用 zhh C7；
5. Q4 能力解释必须传播 Loss–Benchmark 桥接误差。

开始任何跨成员工作前重新读取 `TEAM_COLLABORATION_DEPENDENCIES.md` 和 `interfaces/README.md`。

> 2026-09-24 LaTeX 同步：用户指定的第二十二届模板及整体分章节初稿已进远端 `main`，并合并到本 clean integration 分支。chm 后续只维护 `paper/latex/sections/chm/` 与 `paper/latex/figures/chm/`；集成人维护 `main.tex`、类文件、文献总表和最终 PDF。第一问 LaTeX 初稿对应 `q1.tex`，静态引用检查通过；本机无 XeLaTeX，尚未编译验证。

> 2026-09-24 图文与范文复盘：第一问初稿已嵌入 5 张自有数据图，并新增非重叠扩展集的冲突实例表；新图由 `src/chm/q1_paper_figures.py` 生成。依往届公开作品的论证与排版方式复盘 P0/P1 建模不足，记录在 `problem/chm/20260924_q1_paper_comparison_and_improvements.md`。全队参考入口在 `main` 的 `references/award_papers/README.md`，已核验国一索引与未核验奖项的 2023 版式样本分列。

> 2026-09-24 第一问初稿就绪：复核 A1–A15 质量、配比、敏感性和消融证据，修正论文草稿中过期的“待复跑”状态及未独立证实的公开基线数值对照；加入 1B 绝对 Loss 消融限制和双层 bootstrap 区间。结论与待办见 `problem/chm/20260924_q1_readiness_review.md`，可供集成人整合的初稿见 `paper/sections/chm/q1_draft.md`。Q1 的描述性结论已可写，Q/Loss 跨附件数值桥接仍待 cyj 接口与证据。


本地接力补记：已阅读并整合 cdffdd1 公共规则同步；保留本轮全量运行后的当前状态，取代远端此前尚在运行的描述。

## 2026-09-23 网页审查工程修复与待办

> 2026-09-24 官方字段再审：`Q_z` 是 A1–A3 22 信号的 chm 派生量，B6–B8 `Q_score` 是赛题文件自带字段但三文件均为半合成。B 侧建模应优先用原生 `Q_score`，A 分数仅供域描述/排序，不直接进入 B 预测器；A16 仅 6/17 域 direct/near_direct，不能补全 17 维 Q。接口已增机器可读禁止直接对接标志；证据和限制见 `interfaces/chm/OFFICIAL_DATA_REVIEW.md`。

> 2026-09-24 用户确定接口归属：chm 负责定义并发布 A 侧 Q/p，cyj 直接消费；cyj 负责 B 侧 Loss/标度律/Q3 理论，chm 直接消费。chm 已准备 `chm.q1.v1`（`interfaces/chm/CONTRACT.md`、`USAGE.md`、`q1_interface_v1.json`、`src/chm/q1_interface.py`），以及交给 cyj 的 `CYJ_REQUIRED_INTERFACE.md`。验收和剩余限制见 `memory-bank/handoffs/chm/20260924-q1-producer-interface-v1.md`。跨附件未识别映射不因职责划分而自动成立。

> 2026-09-24 消融/收敛：`src/chm/q1_ablation.py` 已复算 3 家族去一与配比输入去除；结果见 `experiments/chm/20260924-q1-ablation-and-cleanup.md`、`outputs/chm/ablation_v1/`。RPS 去除引起 4/7 域排序变化；无配比模型在 1M/60M 各 13/13 域较差，1B 完整模型仅 4/13 域 RMSE 改善。已删除旧网页输出副本和被替代的过程脚本；保留 Git `44e8db4` 审计快照。主 Q/p 定义不变，跨成员桥接待办不变。

> 2026-09-24 接续：已从远程拉取 clean integration 到独立 worktree，复核真实 A1–A3 与 Q1 代码、敏感性和图表。修复筛选后 DSIR 空家族中断、eta bootstrap 配方行未配对、图表脚本运行错误；新增产物和 cyj/zhh 增量接口判断见 `problem/chm/20260924_cross_branch_delta_review.md`。跨成员 Q/Loss 桥接仍待联合冻结；本轮仅推进 chm producer draft。

- 用户指定优先解决受污染祖先不能直接并入 main，以及配比旧结果与新版目录混用。审查其他数学、代码问题逐项登记于 problem/chm/20260923_web_review_open_issues.md，暂不修改模型。
- 三个配比生成脚本与 q1_figures.py 默认输入/输出均改为 outputs/chm/local_recheck_v1/；旧根目录配比表原样归档至 outputs/chm/archive/web_v0/。q1_verify_local.py 已同步新归档路径，默认命令复跑通过。
- clean integration 已建立并远端核验：`integration/chm-q1-clean-20260923`，首个干净提交 `c57ec6916a03dce53734a1c5254f3f53d4f7b9f2`，唯一父提交为当前 main `a0932fd92b...`；相对 main ahead 1 / behind 0，69 个变更文件全部属于 chm 归属范围。后续集成人应从该 clean integration 分支验收，禁止直接 merge `team/chm-data`。


## 2026-09-24 16:51 Q3 启动与上游复核

已全面重读 main、chm clean、cyj 最新个人分支和 zhh 个人分支的公共规则/成员记忆/接口/最新交接。

### 上游结论

- main 最新公共 HEAD：`968ef7a36f1503aa222a0b09c8a8cb5d0f535ecd`。
- cyj 最新 HEAD：`6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b`。已经提供 `cyj.q3.v1`、B1 N-D predictor、题面三成本、约束残差和显式 p scenario；机器包仍 `ready_for_Q3=false`。最新 B7 质量提交只有代码与运行前协议，尚无真实 fit 输出。
- zhh 最新 HEAD 仍为 `d47cd2dc921333caecfcb95f09eb5a2f2714d0db`；C7 CSV 存在，合同/成员记忆仍滞后。

### 本轮 chm 新增

- `src/chm/q3_preflight.py`：锁定精确 cyj/zhh ref 的 formal readiness gate。
- `src/chm/q3_nd_baseline.py`：B1 N-D 解析诊断。
- `src/chm/q3_solver.py`：gated solver scaffold；p 情景要求显式 target/lambda/eta，p 只从 A4 已观测 512 配方中选择。
- `outputs/chm/q3_nd_diagnostic.csv` 及 manifest。
- `outputs/chm/q3_preflight_snapshot.json`。
- `experiments/chm/20260924-q3-nd-diagnostic.md`。
- `problem/chm/20260924_q3_upstream_status.md`。
- `src/chm/test_q3_nd_baseline.py`。

诊断发现：1e19 三个上下文均内点；1e22/2048 已触 D 上界；1e24 三个上下文均 N/D 双上界且预算大量剩余。该现象只说明 B1 支持域不足，不能写成高预算正式最优结论。

### Q1 接口修订

cyj 指出的 CRLF/LF manifest 问题已修为新生产者版本 `chm.q1.v1.1`：
- 新 manifest：`interfaces/chm/q1_interface_v1_1.json`；
- `hash_mode=sha256_utf8_lf_normalized`；
- 旧 v1 保留追溯，不静默覆盖；
- 科学数值不变。

完整本地环境仍需复跑 v1.1 接口测试后再通知 cyj 切换。

### 当前正式阻塞

正式 Q3 仍等待：
1. cyj B7-native Q 模型实际运行与发布；
2. cyj 对 B1/B7 Loss 关系的正式处理；
3. p primary anchor / lambda_loss 的 validated 或正式 scenario-only 决策；
4. cyj `ready_for_Q3=true`；
5. zhh 更新 C7 合同/版本状态。

在此之前只发布 diagnostic/scenario，不发布正式最优配置。


## 2026-09-24 Q3 连续预算与配比选择验证

本阶段完成 diagnostic/scenario 层的 Q3 结构验证，不改变 formal_ready=false 的上游门禁。

新增结论：
- B1 N-D diagnostic 在每个 C7 上下文下随预算依次经历 N_min_bound、interior、D_max_bound、support_corner 四段。
- 2048 Token 的 N_min 释放、D_max 激活、支持域饱和预算约为 7.95e17、9.33e21、2.30e22 FLOPs；8192 为 9.47e17、1.11e22、2.74e22；131072 为 3.99e18、4.69e22、1.16e23。
- 25 起点数值验证与解析解一致，最佳 Loss 最大绝对差约 4.44e-16，N/D 相对误差约 4.23e-08。
- A4/A5 逐 target 代理用于 held-out 候选选择：全部 39 个 scale-target 检验中 25 次选中真实最优、34 次进入真实前 10%；五 target 主面板 11/15 精确最优、14/15 前 10%。
- 1B 的 target-dependent 风险明显：全部 13 target 仅 8/13 前 10%，hackernews 最大相对 regret 约 21.1%；主面板中 pile_cc 为第 10/64，relative regret 约 2.63%。
- 五个主 target 的 A4 训练支持候选最大单域占比中位数约 0.954，4/5 超过 0.9；因此不发布连续单纯形无约束 p optimum。
- 在线性 m_k(p) 且 lambda_loss>0 的当前模型中，固定 target 的 p 排序不随预算、上下文、N、lambda 或 eta 改变；当前 p 模型本身不能识别预算驱动的 p 结构切换。

正式 Q3 仍等待 cyj ready_for_Q3=true、B-native Q 性能项、B1/B7 Loss 处理、p anchor/lambda 正式状态及 zhh versioned C7。当前结果只用于 solver 验证、支持域判断和 scenario 设计。


## 2026-09-24 Q3 质量成本几何

在不假设任何 Q 性能收益的前提下，完成题面三种质量成本函数的纯成本分析与测试。

关键恒等式：
- attention/train = L_ctx / 30000；
- C_Q / (C_train + C_attn) = [g(Q)-g(Q0)] / {N_B [6e9 + 2e5 L_ctx]}。
因此质量成本相对基础计算的比例与 D 无关，随 N 增大按 1/N 下降。

曲率：
- exponential、power 为凸成本；
- logarithmic 为凹成本；
- Q=Q0 处因 max(.,0) 存在拐点，正式 KKT 必须使用右导数/次梯度，不能把双侧导数写成 0。

诊断 Q0=0.5→Q=1：
- 2048 Token、N=1B 时 exponential/power/logarithmic 的 C_Q/(train+attn) 约 0.598/0.731/0.189；
- N=10B 时约 0.0598/0.0731/0.0189。
这些只描述成本，不代表提高 Q 的净收益或正式最优 Q。

正式 Q 优化继续等待 cyj 的 B-native Q 性能模型和 ready_for_Q3=true。


## 2026-09-24 Q3 generic solver 与 readiness v2

第三阶段工程完成：
- 通用 N-D-Q loss callback + SLSQP 多起点；
- active-set/结构切换检测；
- KKT 内点边际比与上下界单侧条件；
- Q0 使用右导数；
- 8 个单元测试通过；
- 3 成本族 × 5 synthetic 预算点共 15 个 KKT 检查全部通过，自由变量边际比最大相对离散约 3.83e-7。

readiness 规则修订：
- 不要求 A Q_z 数值映射到 B Q_score；
- 正式 Q3 必须有同一 B-native Loss 坐标上的 validated 联合 N-D-Q predictor；
- p 可为 validated_bridge（唯一 p）或 sensitivity_only（NDQ 主结果 + 多 target p 敏感性）；
- 当前 cyj.q3.v1 仍不满足，formal_ready 保持 false。

synthetic quality 模型只用于软件验证，其数值最优解不得进入论文结果。


## 2026-09-24 Q3 数值章节阶段初稿

已补齐 `paper/latex/sections/chm/q3_numerical.tex`，修复 main.tex 已引用但文件缺失的 chm Q3 数值章节入口。章节只写已验证的 diagnostic/scenario 方法和结果，不填 formal 最优配置。

内容覆盖 N-D 连续预算相位、质量成本几何、p held-out 选择验证、generic solver/KKT 软件验证，并在末尾保留 cyj formal predictor 到位后的正式结果 TODO。

章节自身静态检查：10 label 无重复、3 ref 全部有定义、无额外 input/citation。完整 XeLaTeX 编译待本地或集成人执行。


## 2026-09-24 Q3 正式结果发布接口

第五阶段完成正式结果 schema 与发布器：
- 主配置 optimization.csv；
- sensitivity-only 的 p_sensitivity.csv；
- uncertainty_summary.csv；
- manifest.json；
- 只允许 formal_validated 进入 zhh 下游。

发布器强制检查 readiness、成本分项和、预算、KKT、Loss 坐标、支持/外推状态、p policy 与不确定性；5 个软件测试全部通过。

至此，chm 在 cyj formal predictor 到位前能独立完成的 Q3 主工程已基本就绪。后续优先等待/验收上游，而不是继续增加无关代理模型。


## 2026-09-24 Q3 连续预算与结构转移

在 cyj 正式 `ready_for_Q3=true` 前，继续完成不依赖 Q/p 最终桥接的 Q3 诊断骨架。本阶段只使用 cyj 已交付的 B1 N-D 基线与题面成本，不发布正式最优配置。

已推导并数值扫描验证固定上下文下的活跃约束转移：
1. 预算低于最小支持成本：不可行；
2. `N=N_min` 边界；
3. N-D 内点；
4. `D=D_max` 边界；
5. `N=N_max,D=D_max` 支持域角点，继续增加预算只能产生预算松弛。

内点预算弹性：
- `d log N*/d log C = 0.451528388895`；
- `d log D*/d log C = 0.548471611105`。

上下文只通过 `6e18*(1+L_ctx/30000)` 改变有效单位成本，因此 30000 Token 是 attention/train 成本相等的解析临界长度；它不是 C7 新观测情景。

精确转移阈值见 `outputs/chm/q3_budget_transitions.csv`，方法与解释见 `experiments/chm/20260924-q3-budget-transitions.md`。2001 点对数预算扫描能在网格分辨率内恢复全部解析转移，无额外伪转移。

该阶段结果是 solver/结构判据验证，不解除 cyj Q、lambda、anchor 和 zhh 正式接口的阻塞。


## 2026-09-24 Q3 质量成本函数敏感性

继续完成不依赖 cyj 最终 Q 性能模型的成本侧分析。题面三类质量成本均按
`C_Q=1e9*D_B*max(g(Q)-g(Q0),0)`，本阶段只研究成本曲率、单侧导数和与训练/注意力成本的量级关系，不发布最优 Q。

解析结果：
- exponential 与 power 为凸成本，log 为凹成本；
- `Q=Q0` 处左导数为 0、右导数为 `1e9*D_B*g'(Q0)`，存在 kink；
- `C_Q/C_train = Δg/(6e9*N_B)`，与 D 无关；
- `C_Q/C_attn = Δg/(2e5*N_B*L_ctx)`，与 D 同样无关。

仅作可复核示例的 `Q0=0.5`：
- 增量 exp 与 log 在 `Q≈0.7491088` 交叉；
- log 与 power 在 `Q≈0.5767453` 交叉；
- 但 power 在整个 `0.5<Q<=1` 都不是最低增量成本族；
- Q=0.8 时，使质量成本=训练成本的 N_B 阈值分别约 exp 0.169、power 0.289、log 0.135。

输出见 `outputs/chm/q3_quality_cost_sensitivity_q0_0p5.csv` 与 `outputs/chm/q3_quality_cost_crossings_q0_0p5.json`。该示例的 Q0=0.5 来自 cyj 接口算例，不代表官方固定基准；正式 Q3 必须使用上游定义的 Q0。


## 2026-09-24 Q3 配比支持域与稳健候选

完成 p 的 A4 训练支持域诊断。当前 Ridge 的 target-specific 配比效应对 p 线性，因此在 A4 配方凸包内优化与在 512 个观测配方上取最小值等价；lambda>=0 且 eta 固定时，单 target 最优 p 的排序不随 N、预算或上下文变化。

单 target 最优观测配方高度极端：
- pile_cc best index 291，约 98.8% pile_cc；
- wikipedia_en best index 171，约 70.9% wikipedia；
- arxiv best index 300，约 90.2% arxiv；
- stackexchange best index 389，约 99.8% stackexchange；
- github best index 292，约 95.4% github。

因此单 target p 不宜直接当总体最优配比。

对五 target 面板分别按 A4 横截面标准差归一化后：
- standardized minimax 最佳为 index 139；
- standardized mean 最佳为 index 326；
- mean-rank 最佳为 index 177。
其中 index 139 有 14 个非零域，有效域数约 8.824，最大权重仅 0.201，五个 target 的 m_k 均为负。

512 个 A4 配方中只有 3 个（35、99、139）在五 target 上都严格优于 p_ref；index 139 位于五目标 Pareto 前沿。该“全改善”只是当前五个 A-side Ridge 代理的预测，不是 B1 Loss 的已验证改善。

正式 Q3 若 cyj 仍无法识别 primary anchor/lambda，应优先把这些稳健候选作为 p 情景面板，而不是伪造唯一 B1 最优配比。


## 2026-09-24 Q1 冲突跨扩展集复制性

利用已由完整 A1–A3 本地运行生成的 `quality_conflict_extended_v0.csv` 与 `quality_conflict_nonoverlap_v0.csv`，补做不依赖原始 LFS 正文的复制性汇总。

- arxiv：A1 样本中 96 个负相关指标对，其中 92 个在完整 A2 扩展集和去除 A1 重叠后的 A2 子集仍为负，复制率 95.83%。
- github：A1 样本中 91 个负相关指标对，91 个在完整 A3 和去重 A3 子集仍为负，复制率 100%。
- 样本与完整扩展集符号一致率：arxiv 96.10%，github 99.13%。
- 样本与去重扩展集符号一致率：arxiv 95.67%，github 99.13%。
- arxiv/github 两域共同存在 56 个“三层均为负”的指标对。
- 最稳共同冲突：`rps_lines_uppercase_letter_fraction` vs `rps_lines_ending_with_terminal_punctution_mark`，六个相关系数中最弱绝对值仍为 0.73929。

该结果说明部分指标冲突并非由 A1 与扩展集的样本重叠单独造成，但当前仍是复制性/效应量证据，不宣称通过 bootstrap CI 或 FDR 显著性控制。后两项需完整 LFS 环境重跑逐记录分析。

## 2026-09-24 Q1 可识别性与多维 Loss 重构（已融合至 clean 分支）

用户要求重新审查第一问，并明确以后所有 chm 工作继续维护在 \`integration/chm-q1-clean-20260923\`，不再另开 Q1 临时分支。本轮对附件 A 的可识别性重新核对后：

- A4--A15 的配比/Loss 实验没有与每个配方实验对应的训练数据量 \(D\) 字段；
- 真实检验规模仅有 1M、60M、1B 三个离散位置；
- 1M/60M 使用相同 256 个配方，1B 使用另一组 64 个配方；
- 因此旧的 \(b_k(N)\) 与公共 \(\eta\) 只保留历史审计，不再属于 Q1 主模型或正式生产者接口；
- Q1 正式交付改为 A4+A5 的 13-target 1M Ridge 对比
  \[
  m_k(\mathbf p)=\hat{\boldsymbol\beta}_k^\top(\mathbf p-\mathbf p_{\rm ref}),
  \]
  并用 A6--A11 做冻结模型的排序验证；
- 13 个 target 不先强行平均，而统一写成
  \[
  \widehat{\mathbf L}_{1M}(\mathbf p)
  =
  \widehat{\boldsymbol\alpha}
  +\mathbf B(\mathbf p-\mathbf p_{\rm ref}),
  \quad
  \mathbf B\in\mathbb R^{13\times17},
  \]
  决策层按已知权重、等权情景、minimax、保护约束或 Pareto 口径处理；
- 第一问的配比优化支持域限定为 A4 的 512 个观测配方凸包，避免在线性代理上跑到未观测单纯形顶点；
- Data Mixing Laws、BiMix、DoReMi 只作为“逐维建模 + 多目标决策”的文献依据，不直接照搬其需要附件 A 未提供变量的尺度律；
- clean 分支新增的 Q1 冲突复制性证据同时保留：arxiv 92/96、github 91/91 个样本负相关在完整扩展与 non-overlap 扩展中继续为负；两域共有 56 个三层稳定负相关指标对。该证据仍不宣称 bootstrap/FDR 显著性。

当前正式 Q1 论文源以 \`paper/latex/sections/chm/q1.tex\` 为准；机器接口升级为 \`chm.q1.v1.2\`，明确 \`scale_transfer_status=not_identified_from_attachment_A\`。

## 2026-09-24 可识别性错误复盘与审查规则升级

Q1 曾把 1M/60M/1B 三个实验组上的经验配比幅度差异进一步解释为纯模型规模 \(N\) 的连续衰减律，并拟合公共 \(\eta\)。该结果数值可算、代码可复现，但附件 A 没有与配方实验对应的 \(D\)，真实规模位置只有三个，且 1B 配方支持集与 1M/60M 不同，因此该结构解释不可识别。

本次将此错误明确归类为 identifiability error，而不是一般计算错误。以后任何公式进入代码或论文前，必须先通过 variable provenance、identifiability、dataset-role、support/leakage、claim-level 五类 gate。必须永久记住：

\[
\text{参数可估计}\neq\text{参数可识别},
\qquad
\text{拟合稳定}\neq\text{科学解释成立}.
\]

完整复盘见 problem/chm/20260924_q1_identifiability_failure_postmortem.md。用户要求把完整仓库审查流程同步到 main，作为所有成员和 AI 的公共强制规则：以后收到“审查远程分支/本地仓库/代码/数学模型/问题”等请求时，必须执行全流程，不能只做代码 lint、diff 或数值复算。

## 2026-09-24 Q1 LaTeX 编译快照同步

Q1 LaTeX 源文已按可识别性修正撤出连续配比尺度律；本次重新运行 XeLaTeX/BibTeX/XeLaTeX 两次，形成 18 页 paper/latex/output/chm-q1-draft-20260924.pdf。PDF 已核对包含可识别性边界、冻结 1M 代理排序验证与跨实验组限制；旧 10 页快照从 Git 移除。main 仍只保留空白模板。

## 2026-09-24 cyj 接口复核与 Q3 推进

cyj 远端 ad1d312 已将旧 p/eta 情景降级，正式 ready_for_Q3=false；B7 原生 N-D-Q 只允许半合成条件诊断。本轮新增 B7 三预算、三上下文、三成本族扫描及实验记录，27 组合中 24 个在声明支持域可行；不把结果接到附件 A 配比或 B1 Loss。Q1 论文遗漏的 13x17 作用热力图已补，Q1 接口八项测试、B7 诊断三项测试及 LaTeX 静态检查通过，19 页 PDF 重新编译。完整交接见 memory-bank/handoffs/chm/20260924-q3-b7-interface-diagnostic.md。

## 2026-09-24 Q3 数值验收修复（第一检查点）
发布接口 v2 撤出 eta/lambda_scenario，A 配比敏感性限定 A4/A5 1M 坐标；通用求解器强制显式模型支持域，预算约束归一化，使用解析梯度及可达 Q 端点，只接受收敛可行解。KKT 改为相对边际残差并检查原始可行性、对偶及互补松弛。32 项 Q3 回归通过。B7 全局误差界、连续预算与转移扫描仍在实施；旧人工模型 KKT 统计待新结果替换，不能作为正式验收依据。


## 2026-09-24 Q1 方向稳定性主规则升级

用户复核指出旧主模型把极接近 0 的 pooled Spearman 也按正负号强制定向。回查 `quality_review_v1` 后确认：`rps_lines_numerical_chars_fraction`（full pooled rho 约 8.03e-05，LOO 约 [-0.0275, 0.0274]）和 `rps_doc_frac_chars_top_3gram`（rho 约 -0.0181，LOO 约 [-0.0631, 0.0181]）会在 leave-one-domain-out 中翻转方向。

现已把 `stable_loo` 从 review-only 敏感性规则提升为 `src/chm/q1_quality_analysis.py` 的主方向准入规则：8 个语义模型锚点固定保留；其余指标只有在删除任意一个 A1 域后 pooled 方向均不翻转才进入主 Q_A；不稳定指标 orientation=0，并在家族聚合前置为缺失，避免把“0”当成真实指标值稀释均值。更严格的 `stable_consensus_075` 会删除全部 DSIR 家族，继续仅作压力测试。

已同步方法设计、Q1 LaTeX 方法段和审查清单；新增回归测试覆盖“不稳定指标应被排除而非乘零”。当前远端执行环境只能读取 Git LFS pointer，无法取得 A1--A3 实体，因此 canonical `domain_quality.csv`、bootstrap 区间、扩展集复核和图表尚未按新规则全量重跑。旧数值只能作为 sign-only 历史结果，不得与新主规则混写。方向 bootstrap CI 仍是 R05 未完成增强项，不能声称已经实现。

历史判断：R05 原待办明确要求先做“剔除不稳定指标的 Q 敏感性版”，但没有单列“敏感性验证通过后回写主模型”的验收项；`quality_review_manifest_v1.json` 因而明确写 `review_sensitivity_not_primary` / `primary_quality_definition_unchanged=true`。该缺口现已补成显式两阶段闭环：主规则代码先升级；随后必须在有 LFS 实体的本地环境全量重跑、刷新 canonical 输出和论文数值后再冻结。

## 2026-09-24 Q1 22 信号主模型修正

根据用户提供的讨论稿复核后，撤销上述 stable-LOO 主准入设计。A1 全量 Spearman 符号用于 14 个统计字段定向，8 个模型字段固定正向，全部 22 项进入主 Q。七域和 LOO 只作诊断；本机 A1--A3 实体全量重跑并刷新 canonical 输出、图表、第一问正文及 `chm.q1.v1.3` 接口。旧 20 项口径和旧评分数值仅为历史，不得继续作为当前 Q1 结论。复现和风险见 `memory-bank/handoffs/chm/20260924-q1-all22-global-orientation.md`。

## 2026-09-24 Q1 全量 22 信号论文编译验收

已找到并获准执行本机 MiKTeX；修复语义锚点公式的悬空引用，新增自动构建脚本和包含公式引用的静态检查。当前工作树生成 `paper/latex/output/chm-q1-all22-latest.pdf`，21 页，全部页面渲染检查通过；新方法与质量结果位于第 5--8 页。构建清单保存源文件和 PDF 哈希。详见 `memory-bank/handoffs/chm/20260924-q1-all22-pdf-build.md`；Q2/Q4 占位和 Q3 尚未提交的来源边界已注明。

## 2026-09-25 Q3 工程闭环与 CYJ v4 所有者验收

已审查 CYJ 最新 2c237b3，按 P0 接口消费→P0 当前模型数值验收→P1 扫描/转移/敏感性→论文交接的顺序完成接续。精确消费 v4 3471530，三个批量 fixture、330 场景（321 可行）通过，33 个独立可行情景的全局目标值误差界 <=1e-7；1609 点预算扫描、41 个转移括区、54 组支持域敏感性及独立 DE 结果对照均落盘。旧恒定 G 仅历史基线。CHM owner acceptance 阻塞解除，但半合成来源、独立外测、区间校准与跨源桥接仍使 ready_for_Q3=false。Q1 v1.3 与 v4 固定 v1.2 的配比系数/参考相同，A 质量已更新，要求 CYJ 下一版同步元数据。详见交接 20260925-cyj-v4-owner-acceptance.md；当前论文输出为 chm-q1-all22-latest.pdf。

## 2026-09-25 Q1 第二小问冲突感知分析

已按用户修改意见新增 `src/chm/q1_conflict_aware.py`，保留 Q_A 主评分与 22 指标定向，在 A1 及 A2/A3 去重扩展集做 231 对 Spearman、分家族 BH-FDR 0.05、跨域成因模式与复制性冲突图。初轮输出显示总体 66 对显著负相关、55 对在去重扩展集复现；新增样本级 `(Q_A,D)`、七域汇总及图，论文草稿与 LaTeX 已补。数据在附件 A 坐标内，不向 B 侧假定质量映射。最终极端值诊断与全量复跑状态见本次交接及实际 manifest；未完成复跑前不视为最终冻结。

## 2026-09-25 Q1 前两小问证据补链

用户明确要求按审查任务书继续完善质量评价与冲突消解，但第三点配比建模改动前先讨论方案。本轮未修改 A4--A15 配比模型。质量主评分、22指标和 `chm.q1.v1.3` 保持原样；新增按域 70/30 固定留出、训练集 100 次分层方向重抽样及统一规则排名面板。训练集重抽未改变七域方向与排名，但 LOO 仍有5项翻号，方法规则面板部分域排名变化；两类不确定性分别报告。

冲突处理新增冻结的 A1 阈值、非惩罚性标记与缺失回退；27条按域/Q-D四象限固定哈希选样，以原文行号和SHA本地核查，仓库不提交原文。去重 A2/A3 用冻结阈值复核触发率，不能解读为准确率。论文已补真实结果，PDF构建通过。细节见 `experiments/chm/20260925-q1-quality-conflict-evidence.md` 与本轮交接。当前仍无独立人工质量真值；案例语义需参赛者复核，Q1完整最终冻结及v1.4发布尚未完成。

## 2026-09-25 配比最终审计第一检查点

用户已授权继续第三小问及 CYJ 一次性上游交付，并明确目前无人工真值/盲评条件，可跳过该可选项且如实注明。新增 `src/chm/q1_mixture_final_audit.py` 对 A4--A15 一对一索引/列序/原始SHA、逐目标误差与基线、A4凸包、A6/A8配对、训练内交互候选做独立审计。初轮运行：A10 1B 64配方中17个在A4凸包内、47个超出；主Ridge 1B绝对RMSE 4/13优于训练均值基线；交互候选在三个真实检验组RMSE改善，但尚未更改正式13x17 Ridge接口。详见 `experiments/chm/20260925-q1-mixture-final-audit.md`。此为检查点，Q1完整发布与新接口仍待完成。

## 2026-09-25 Q1 第三小问验收候选

已在本人 clean integration worktree 对 cyj `86526a1` 的两个 Q1 派生包进行原始 A4/A5、逐行归一化、冻结 `chm.q1.v1.3` 五表和交互定义复核。数值身份通过：512 行归一化最大差 `2.22e-16`，13 目标交互 CV 与本人 `2450971` 审计最大差 `3.33e-16`；四个交互实质文件跨 NumPy 环境哈希相同。发现 `qa_mapping.json` 的 arxiv/github 使用 A2/A3 扩展分数，而 v1.3 主 `Q_A` 使用 A1 sample；已分别重算质量约束场景，不能无条件签收 v1 的质量政策语义。第三小问多目标、覆盖与模型形式敏感性及论文验收 PDF 已就绪，主 Ridge v1.3 暂不变，交互候选只用于敏感性。用户要求先验收再进入正式模型；详见 `memory-bank/handoffs/chm/20260925-q1-third-part-export-owner-review.md` 与 `paper/sections/chm/q1_third_part_acceptance_candidate.md`。Q2/Q3 的正式版本切换与第三问重算待验收后执行。

## 2026-09-25 Q1 模型比较与稳定性补证

用户要求继续完成同条件 Ridge/交互对照、配方选择稳健性及 Q2 质量映射更正情景。本轮训练内嵌套五折中交互 13/13 目标 OOF RMSE 优于 Ridge；A6--A11 同条件检验中 1B 凸包内 17 与外 47 条各为 13/13 目标交互 RMSE 较低，但全 1B 仅 11/13 目标优于常数且 Spearman 仅 7/13 高于 Ridge。214 权重扫描下无质量约束两模型选方一致 77.1%，加 direct 52.6%、direct+near 63.6%；真实检验候选内部的决策压力结果不支持“所有指标上交互最优”。chm 侧独立复现 cyj 两项旧条件 Q2 政策，并以 A1 主评分重算，损失变化量很小但最优混合权重变化。交互现是 Q1 支持域内优先预测候选，正式 `v1.3` 仍为 Ridge，等待用户验收后才切换接口。详细见 `memory-bank/handoffs/chm/20260925-q1-comparison-stability-q2-remap.md` 与 `experiments/chm/20260925-q1-third-part-model-comparison.md`；`ready_for_Q3=false`。

## 2026-09-25 Q1 主要矛盾形式化

用户最新要求暂缓论文 PDF，优先完成模型与问题主要矛盾。已在实验记录和 Q1 LaTeX 源码写明三项识别边界：13 目标外生权重缺失导致配方条件最优；A16 的 11 个 inferred 域无 Q_A 数值使全配方质量不可求；A/B 无成对配比与 B 侧 Loss，故 cyj 条件公式的 lambda/eta 无法由现有数据估计，其中 N=1B 单点使 eta 完全消失。已有比较和 Q2 重算只支持条件预测，不解除此边界。论文 PDF 暂缓。

## 2026-09-25 用户授权交互主模型升级（进行中检查点）

用户明确要求直接以二阶交互替换 Q1 配比主模型并重做配方和下游接口。已新增 chm.q1.v2.0 冻结包、默认 Q1 读取器、512 A4 配方精确枚举与 A1 质量政策决策、chm 侧 cyj B7 条件重算，并将 Q3 的 p 支持诊断改用 v2。Ridge 读取器复制为 v1.3 历史版，旧测试已显式固定。当前 Q1 30 项测试通过。仍需完成旧 Q3 选择验证入口迁移、论文余下口径核对和全量回归；本检查点不是最终交付。
Q1 v2 主模型后续补足连续凸包空间分支定界的数值上下界（四个主情景间隙均 <0.001）、Q2 三质量政策连续情景及 Q3 p 选择验证 v2。完整接口见 interfaces/chm/Q1_V2_DOWNSTREAM.md，实验记录见 experiments/chm/20260925-q1-v2-primary-interaction.md；旧 Ridge 与旧 cyj v6 均仅保留原版本复现。Q1 32 项、Q3 38 项测试、安全阅读两门禁、原始 2014 文件哈希核验均通过。用户要求论文 PDF 暂缓。

## 2026-09-25 Q1 v2 证据措辞与数值签核

按用户最新要求仅处理证据口径、数值界与旧入口，暂不制作论文 PDF，也不代替 CYJ 发布新版。A6--A11 已参与模型形式选择，当前仅称同条件比较，不称未触碰最终盲测；1B 47/64 超 A4 凸包、绝对 Loss 与质量无人工真值边界均保留。新增 audit_q1_v2_signoff.py 重算四份配方总量、非负性、凸包重构、质量松弛、目标值和间隙，全部通过，最大间隙 0.0009955585，界只按浮点数值结果陈述。当前 q1_draft.md 改为 v2 取数摘要，Ridge 草稿和 v1.3 合同归档。详见本轮 handoff 和 outputs/chm/q1_v2_signoff/audit.json；参赛者终稿仍需据此核对表达，PDF 仍暂缓。

## 2026-09-25 Q1 v2 外推估算与重拟合压力

按用户要求补齐 Q1 自身题面闭环，冻结 v2 后复核 A12--A15 两组外推估算表：各 63 个配方均为 A4 已见配方。v2 与 10B/70B 估算 Loss 的逐目标 Spearman 中位数为 0.4915/0.3941，略低于旧 Ridge 的 0.5136/0.4148；同候选等权选择在估算表均排第 61/63。明确这是估算表的负向压力证据，不是大模型实测，不能回头调 v2。另作 30 次 80% A4+A5 无放回重抽、重选交互域及逐目标正则后重新拟合，在 512 个已观测候选中，原等权无约束 index 136 被选 29 次，direct 10 次，direct+near 13 次，minimax 7 次；后面三种政策的具体候选更敏感。这不是连续凸包最优解置信区间。代码、原始输入哈希、明细与限制见 experiments/chm/20260925-q1-v2-estimated-and-refit-stress.md 及本轮 handoff。

## 2026-09-25 Q1 自身答案定型

用户明确要求直接定型并判断 Q1 是否解决。已将附件 A 条件下的完整答案冻结为 outputs/chm/Q1_FINAL_ANSWER_V2.md，逐项汇总质量评分、冲突感知处理、配比交互模型、四情景数值决策、真实检验组、估算压力和重拟合敏感性；当前 q1_draft.md 与合同指向此唯一结论入口。Q1 自身可宣称解决，但结论是指定评分规则、权重、质量政策与 A4 支持集下的条件性数值解，不宣称人工质量准确率、无条件唯一最优或真实 10B/70B 实测验证。正式生产者仍为 chm.q1.v2.0，原清单 SHA 不变。详见本轮 handoff。
