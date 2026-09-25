# cyj 跨分支接口审查（2026-09-24，生产者侧观察）

状态：只读审查与合作建议；不是接口联合验收，也不将其他成员个人分支结果视为 main 事实。

## 版本和取证范围

- cyj 本人分支 `team/cyj-scaling` 起点 `9a2d4357351afb11c59dff474cc82350a496eb7e`；公共 `origin/main=a0932fd92b3a46cef8eb0bf563df1e6abc9396ef` 为其祖先。工作区开工时干净。
- chm 只读取清洁集成分支 `origin/integration/chm-q1-clean-20260923@7a958d7b5760bce4e7136a5c80e6b9275de60eaf` 的活动合同、`Q2_BRIDGE.md`、`UNCERTAINTY.md` 和审查状态。`origin/team/chm-data@867e9eebe30bc3944b3eb27a47912bffae520368` 的成员记忆明确禁止直接合并该受污染历史血缘；本审查不移植该分支的模型、参数或输出，也不读取作废历史内容。
- zhh 读取 `origin/team/zhh-frontier@d47cd2dc921333caecfcb95f09eb5a2f2714d0db` 的 `CONTRACT.md`、`RESULTS.md`、成员记忆、交接、C7 情景 CSV 与桥接结果摘要；该分支未进入 main。
- 精确读取文件 SHA256：chm `CONTRACT.md` `2252327f69c8a94e4e924161ee2c6c36f16e3ba60383221b4751f1ed70a96dec`、`Q2_BRIDGE.md` `d84710a0600a0a72f641d4489bb6d3609eba558c6e82b26d292e31ac3396e6d5`、`UNCERTAINTY.md` `2242de581a4acd32ffa655de97233927d847631263b123cf9868120de8516be6`；zhh `CONTRACT.md` `f349417f8196f3bd409eb5927daa9a11f85019cf3f1b618476fedaea3215b0c1`、`RESULTS.md` `132e7e1b1f79a2f654bfc46a9e894ab6fc7cb6ccc5a628ea87d61e8bd33a9f73`、`context_scenarios.csv` `b494a8949a74133e779b683c8a46021b5e16308970150bd18e033553c6fc8608`。这些是读入身份，不是验收结论。

## 本人当前进度和审查发现

cyj 已完成附件 B Stage 1 审计、B1 经典 N-D 拟合及按 N 组留出/token-tail、B1 显示计算量舍入与八行剔除敏感性、B2/B3 同源/半合成形状诊断，接口草案 v1.6。B4/B5 只输出未经 Loss 同尺度核实的描述性预测；没有 B1 组级参数区间、正式 Q/p、validated predictor。B1 三类误差几乎为零，Loss 行级来源仍无法独立追溯，不能将低误差称为真实独立泛化。Draft PR #3 尚待集成人验收。

| 对照点 | 从其他分支读到的状态 | 与 cyj 的关系及待办 |
|---|---|---|
| `Q_z` ↔ B6–B8 `Q_score` | chm `Q2_BRIDGE.md` v1.0：无配对标定；禁止恒等、MinMax 或手调线性平移 | 与 cyj 不直接等同的规则一致。公共协作文件要求共同冻结 mapping；目前证据只支持 B-native `Q_score` 情景和 A 侧相对排序，不支持可识别的数值 mapping。应由 chm+cyj/集成人明确“情景而非映射”是否满足正式交付，不能单方改成已冻结。 |
| 13 域 p→Loss ↔ B1 `val_loss` | chm v1.4 为生产者侧已核草案，建议 centered `m_k(p)` 和显式 `lambda_k(N)`，当前 anchor 是情景 | cyj 尚无 B1 validation set 与任一 Q1 target 同一口径的证据；不能选 pile_cc 作事实主 anchor，也不能默认 `lambda=1`。可借鉴 target panel 与中心化接口做结构联调，但正式 Q3 仍等待联合定口径。 |
| 不确定性层级 | chm `UNCERTAINTY.md` v1.0 区分 Q 定义、域映射、p target/CV、eta、跨附件桥接，并标记 conditional/scenario/unidentified | cyj 本次优先补 B1-only 按 N 组不确定性；只能称条件于 B1 模型/数据的区间，不能称 Q3/Q4 总预测区间。eta 区间不替代跨 Loss 的 lambda。 |
| C7 情景 | zhh `RESULTS.md`/CSV 给 2048、8192、131072 Token；high 仅 1 个支持模型 | 可作为 Q3 的外生情景边界，不是连续优化变量；当前 zhh `CONTRACT.md` 仍写“无结果”，成员记忆还写“未推送”，与同分支结果和实际远端冲突。请 zhh 自行更新合同、记忆与版本后再正式消费。 |
| Loss–Benchmark | zhh 的 75 条分级桥接在 Loss 排序留出集 RMSE 7.060、R² -1.376；高可比仅 7 条 | 与 cyj 不把 Loss 当能力分数的限制一致。7.06 是该留出实验误差量级，不是可直接用的 95% 区间；最终需 zhh 传播分级桥接误差和适用范围。 |

chm 清洁分支审查状态中质量方向/家族权重/Qurater、CV 折分与 eta 二层重抽样仍有 LFS 完整环境重跑 pending 项；cyj 不把这些待跑结果写成已验证。zhh 分支结果与合同状态不一致，不能用过时合同替代 `RESULTS.md`，也不能因已有结果就称团队已验收。

## 对合作与本人下一步的影响

1. chm+cyj 优先进行简短接口决定：B-native Q 情景是否为当前唯一可辩护主线；若 Q3 必须连续优化 A 侧质量选择，需新增配对标定证据或将任务降级为情景比较。共同记录采用分支、SHA、文件 SHA、有效范围、状态。
2. chm+cyj 共同核对 B1 `val_loss` 评估口径并决定有无 Q1 target 主 anchor；未证实则保留 pile_cc、wikipedia_en、arxiv、stackexchange、github 为 target-specific 敏感性面板，`lambda` 只作情景参数。
3. cyj 独立完成 B1 按模型规模重抽样，标记仅覆盖 B1 参数不确定性与小组数限制；随后继续 B4/B5 同尺度证据和模型形式/来源审计。
4. zhh 自行修订 `interfaces/zhh/CONTRACT.md` 与成员记忆，使 C7/桥接接口状态、版本和实际结果一致；集成人验收后更新公共记忆与 `interfaces/README.md`。cyj 不修改这些他人/公共文件。

复查命令：`git fetch origin --prune`、`git rev-parse <ref>`、`git show <ref>:<path>`、`git diff --name-only origin/main...HEAD`。本文件的跨分支状态只对上述提交快照有效；新提交出现时须重读。

## 10:00 再次 fetch 后的 chm 增量（仅只读审查）

`origin/integration/chm-q1-clean-20260923` 已由 `7a958d7` 前进到 `3f237910bc4b7ebfc7d4408d65572c134fed59c5`（中间 `44e8db4`）；`origin/main` 未因此自动更新。本次重新读取 chm 合同 SHA256 `578ec40eafd1430917383c34806c9859abb99a4e0bf77c7e63e09675521225dd`、增量审查 `ce5aa055545617b779653a21ffad391b498df96c9dff4ea68fb4185c9a1f415a`、尺度清单 `b1e8a68ed277089cd7c5f2d72efef9097cecd614a0f70bc374392b765e08ba83`。

- chm 本地修复真实 A1–A3 严格筛选缺席家族导致的运行中断、eta 二层 bootstrap 的配对抽样单位，以及 Windows 无头绘图；增量文件报告 eta 点估计 0.145033、配对条件区间约 `[0.097562, 0.200977]`。这是 chm 分支的本地复核，不是 cyj 独立复现，也不覆盖 Q/p 和跨 Loss 桥接误差。
- 新消融报告域级排序对 RPS 家族更敏感，1B 配比对逐域 held-out RMSE 的改善仅 4/13；因此更不应将 1B 配比校准或 eta 点估计当作 B1 Loss 的现成 p 修正。主 Q/p 接口、`Q_z`↔`Q_score` 不可直接映射、13 域 Loss↔B1 `val_loss` 未证同口径等判断不变。
- chm 合同仍 v1.4 producer-validated draft，Q3 明确等待 cyj validated predictor 与 zhh 已验收 C7；增量不要求 cyj 修改现有 v1.6 合同字段。后续联合定标应引用 `3f23791` 及上述新文件哈希，不能再仅引用 `7a958d7`。
