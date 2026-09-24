# 网页端审查待办（2026-09-23）

来源：用户粘贴的网页版审查。以下是待核查、待修改事项，**不是本轮已完成结果**。本轮仅修复两项工程问题：受污染祖先不能直接接入 `main`，以及配比结果的默认读写路径混用。

## 已处理的工程问题

1. **Git 历史**：`team/chm-data` 祖先可达已作废的 `6086964` 等提交，不能直接合并到 `main`。已从干净 `origin/main` 建立 `integration/chm-q1-clean-20260923`，首个干净提交为 `c57ec6916a03dce53734a1c5254f3f53d4f7b9f2`，唯一父提交是当前 main `a0932fd92b...`。远端比较为 ahead 1 / behind 0，69 个变更文件全部位于 chm 归属范围，且文件树与 `team/chm-data@c6aca3bdbe` 最终树一致。集成人仍须验收后决定是否进入 `main`，不得从旧 chm 分支做普通 merge。
2. **配比输出双版本**：三个配比生成脚本与绘图脚本默认使用 `outputs/chm/local_recheck_v1/`；旧根目录配比输出移到 `outputs/chm/archive/web_v0/`。重新运行默认命令并核对根目录没有混入旧版配比文件。

## 尚待处理，当前不改模型、代码或结论

| 编号 | 审查意见 | 后续核查或修改 | 负责人 |
|---|---|---|---|
| R01 | 两台环境的 Git 时间记录相差约 8 小时，页面时间不能用来判定提交先后 | 核对时区；协作判断统一使用父提交关系与 SHA | chm / 集成人 |
| R02 | 曾用逐文件复制同步 `main` 公共规则，导致文件内容一致但仍落后主分支 | 后续按团队流程 `fetch` 后合并 `origin/main`，检查冲突 | chm |
| R03 | **已解决**：已删除 `experiments/chm/20260923-q1-regmix-baseline.md` 中来自已作废历史的候选方法残留，并补充污染审查说明 | 后续若重新采用同名方法，必须以独立公开文献和当前数据重新建立证据链 | chm |
| R04 | `interfaces/chm/CONTRACT.md` 仍内嵌完整历史 v1.2，关键词检索可能读到旧状态、旧参数和路径 | 将历史版本另归档，现行合同只保留当前有效版本 | chm |
| R05 | **主规则已修正，数值待全量重跑**：部分 RPS 指标 pooled 相关接近 0 且跨域方向异质；旧主模型按正负号强制定向 | 已将 LOO 方向稳定准入写入 `q1_quality_analysis.py`：删除任一 A1 域后方向翻转的指标不进入主 Q；现有审查据此排除 `rps_lines_numerical_chars_fraction` 与 `rps_doc_frac_chars_top_3gram`。方向 bootstrap CI 尚未实现，canonical A1–A3 输出与论文数值须在取得 LFS 实体后重跑刷新 | chm |
| R06 | 三类指标各 1/3 权重是建模假设；当前只比了完全等权与列表压缩 | 在家族权重单纯形上抽样，报告高低质量域排序保持情况 | chm |
| R07 | A12–A15 的 10B/70B 共 63 个配方均来自 1M 训练配方 | 论文明确写作已见配方上的**尺度外推**，不得称新配方泛化 | chm |
| R08 | 经验衰减参数 η 的 1B 配方支持集与 1M/60M 不同 | 降低因果与纯规模弹性表述；注明配方支持集变化可能混入估计 | chm / cyj |
| R09 | η 的 bootstrap 仅重抽 13 个目标域，条件于 Ridge、配方及当前尺度校准 | 论文注明条件区间；时间允许时做配方、Ridge 与校准的嵌套重抽样 | chm |
| R10 | Q1 的 `Q_z` 与 B6–B8 的 `Q_score` 并非同一坐标；13 个验证域 Loss 与 B1 `val_loss` 未证明可比 | chm/cyj 联合冻结跨附件 Q 映射、p→Loss 的主锚点及敏感性；此前不发布 Q3 正式优化 | chm / cyj |
| R11 | Q、域映射、p 和 η 的不确定性需要传递到 Q3/Q4；桥接误差不可忽略 | 共同确认采样方式、可用域与区间报告口径 | chm / cyj / zhh |

审查同时肯定：A1–A3 已全量读取；A1 的 arxiv/github 样本与扩展集重叠已识别并单独报告非重叠部分；Ridge 的 alpha 只在 A4/A5 内选择，未发现典型的检验集调参泄漏。这些肯定项不替代后续独立复核。

历史污染规则仍以仓库 `AI_READING_RULES.md` 为准。此清单只记录审查提出的问题，不从作废提交恢复任何模型或数据。


## 2026-09-24 主方案回写决策

此前清单只要求“构建剔除不稳定指标的 Q 敏感性版”，**没有单列“敏感性方案通过审查后同步回主模型”这一验收项**。`quality_review_v1` 也因此显式标成 review-only。现根据用户复核要求，将已经由真实 A1 数据验证过的 `stable_loo` 准入规则提升为主方向规则；更严格的 `stable_consensus_075` 因会删除全部 DSIR 指标并改变三家族结构，继续保留为压力测试。

当前回写分两阶段：第一阶段已完成源代码和方法定义的主规则切换；第二阶段必须在本地取得 A1–A3 Git LFS 实体后全量重跑，刷新 `quality_orientation_v0.csv`、`domain_quality_v0.csv`、`domain_quality.csv`、manifest、扩展集复核、图表和论文数值。第二阶段完成前，旧 canonical 数值只代表旧 sign-only 方向规则，不得与新主规则混写。

## 二次复核新增待办（ChatGPT，2026-09-23）

以下问题仅登记，未修改当前数学模型或结论：

| 编号 | 审查意见 | 后续核查或修改 | 负责人 |
|---|---|---|---|
| R12 | `Q_z` 的均值/标准差按 A1 全部记录估计，而七域样本量高度不均衡（book 171、arxiv 1419，其余多为约 1 万）；因此 Q 的数值尺度由大样本域主导。域排序不受最终仿射标准化影响，但跨附件映射到 B6 `Q_score` 时可能受影响 | 增加 domain-balanced 标准化或只使用未标准化 `S/Q_raw` 的敏感性，对比跨附件映射参数 | chm / cyj |
| R13 | A1/A2/A3 重叠判断依赖字符串 `_id` 集合，但代码未把“ID 非空且唯一”作为硬断言；当前 arxiv/github 的 unique ID 数等于行数，暂未发现实际重复 | 在读取后增加空 ID、重复 ID 检查，并把结果写入 manifest | chm |
| R14 | Ridge 当前固定 `KFold(n_splits=5, shuffle=False)`；公开来源只确认 5-fold CV，未独立确认“不打乱”这一具体折分。此前网页/本地 alpha 已因实现口径不同而变化，说明折分细节会影响选择 | 增加固定 seed 的 shuffled 5-fold 敏感性，比较 alpha、held-out Spearman 与接口系数；不利用 A6–A11 反向选方案 | chm |
| R15 | 若干活动说明文件仍含 local_recheck_v1 之前的旧数值：`experiments/chm/20260923-q1-regmix-domainwise.md` 的 Pile-CC/总体指标、`experiments/chm/20260923-q1-mixture-scale-transfer.md` 的 eta=0.14537、`problem/chm/q1_anchor_policy.md` 的旧 Pile-CC/eta 与根目录路径；当前论文草稿和 CONTRACT 顶部使用的是新版 | 后续统一从 `outputs/chm/local_recheck_v1/` 自动生成/刷新活动说明；历史 handoff 可保留旧值但须标记历史 | chm |
| R16 | `qurater` 的 4 个维度当前直接取原始算术平均，现有 argmax 敏感性并不会改变该聚合；公开数据卡将四维分别解释 | 增加“4 维分别标准化后等权聚合/作为四个子指标”的敏感性，检查七域排序 | chm |
| R17 | `q1_figures.py` 已切换到新版输出，但远程树中尚无 `paper/sections/chm/figures/` 生成图文件 | 正式写作引用图前从 local_recheck_v1 重新生成并核对图表数值，不使用旧本地图缓存 | chm |
