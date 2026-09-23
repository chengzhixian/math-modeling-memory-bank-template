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


本地接力补记：已阅读并整合 cdffdd1 公共规则同步；保留本轮全量运行后的当前状态，取代远端此前尚在运行的描述。

## 2026-09-23 网页审查工程修复与待办

- 用户指定优先解决受污染祖先不能直接并入 main，以及配比旧结果与新版目录混用。审查其他数学、代码问题逐项登记于 problem/chm/20260923_web_review_open_issues.md，暂不修改模型。
- 三个配比生成脚本与 q1_figures.py 默认输入/输出均改为 outputs/chm/local_recheck_v1/；旧根目录配比表原样归档至 outputs/chm/archive/web_v0/。q1_verify_local.py 已同步新归档路径，默认命令复跑通过。
- clean integration 分支须从最新 origin/main 单独创建，只导入 chm 归属文件快照；不得将本分支直接 merge 进 main。该分支尚待建立与远端核验，成功后以交接追加实证。
