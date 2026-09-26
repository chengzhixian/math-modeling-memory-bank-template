# a19039b 评委视角审查整改与完整复核

日期：2026-09-26（北京时间）。对象：本地 `main`，起点 `a19039b5d11c91cf32e301dc85b2f4d50b5a75b7`，远端 `origin/main` 在开工时经代理核对为同一 SHA。用户桌面审查报告是待核的意见来源，不替代题面和原始附件。本文按 `REPOSITORY_REVIEW_PROTOCOL.md` 的 18 阶段记录。所有新增计算来自当前可见资料、main 代码和结果；未读取旧版 PDF 隐藏文字或复用作废 Gemini 工作。

## 分支与范围

| 留存分支 | 已核对远端提交 | 对本次问题的结论 |
|---|---|---|
| `team/cyj-scaling` | `d5e05ce` | 保存 B1/B7、v8 和验证的生产历史；正式 Q2 主输出已集成至 main。该分支仍把领域对统一标为 `model_based_not_causal_complementarity`，未给出固定补偿有限联合判据；下游接受状态仍是生产时快照。 |
| `team/zhh-frontier` | `ee23b20` | 保存 Q4 v3 设计、核心和图；main 当前核心数值与其一致。留存工作没有把规模/技术代理份额、q90 与最高值、Q3→能力代表换算整理为本报告要求的终稿答复。 |
| `integration/chm-q1-clean-20260923` | `c052b69` | 保存 Q1/Q3 的过程、条件格及验证；main 已集成其正式数据，独立质量模式在结果中已有，但论文章节未并列成决策表。 |

未做整分支合并或历史 cherry-pick。原工作区在切换前有 186 项暂存变更，已保存在原 integration 分支的 `stash@{0}`，未带入 main。`remote.origin.fetch` 改为抓取所有远端分支，main 现跟踪 `origin/main`。所有 GitHub 命令使用用户给出的 `http://127.0.0.1:7897` HTTP/HTTPS 代理。

## 18 阶段审查门禁

| 阶段 | 本轮证据与结论 |
|---|---|
| 1 Git 冻结 | 核实本地和远端 main 均为 a19039b；查看 status、diff、staged diff、log、三个分支及合并基点。变更仅在用户指定 main。 |
| 2 可信来源 | 题面 DOCX、`problem/readable/DATA_DESCRIPTION_VISIBLE.md`、校验过的附件及当前冻结接口优先；旧隐藏 PDF 与作废历史排除。 |
| 3 requirement→data | Q1 对 A1–A16，Q2 对 B1–B10，Q3 对 A/B/C7，Q4 对 C1–C8 的使用角色在四问正文和新数据利用表逐项说明。 |
| 4 变量追溯 | $N,D$ 均为十亿单位，成本 FLOPs；$Q_A$ 为 A 侧代理，$Q_B$ 是 B7 原生半合成坐标；$p$ 为 17 域配比，$S$ 为六任务百分制均分。Q4 的 $D$ 缺失单列假设。 |
| 5 可识别性 | B1 骨架、A4 域内相对效应、C2 同格变化可在声明范围内估计；A/B 质量、跨来源 Loss、纯技术因果份额和长期未来覆盖率不能由现有附件识别。 |
| 6 数据角色 | B1 真实轨迹；B2/B7 半合成、B3 插值；B6 与 B7 重叠；B10 和 A12–A15 estimated；C6 按 Loss 来源分层。未把这些当同等独立外测。 |
| 7 重叠/泄漏/支持移位 | Q1 A6–A11 参与模型判断，不能称最终盲测；B6 不能作为 B7 独立检验；C2 滚动回测逐截点去重，窗口重叠；Q3/Q4 超域行不算能力预测。 |
| 8 文献适用 | $N,D$ 幂律借用公开候选形式，系数只从 B1 估计；公开 Pythia、Leaderboard、Epoch 出处补引用，网站现行版不替代题面快照。 |
| 9 模型一致性 | Q2 有效配比扰动沿单纯形并经 A4 凸包检查；联合效应固定 donor，不能被读成纯两域因果交互。Q4 分解分母为共同支持标准化变化，允许负/超 100% 带符号份额。 |
| 10 公式↔代码 | Q2 用 `ConditionalV8.evaluate` 原接口逐格复算 28 个有限联合对照；Q3 表读冻结三模式格；Q4 q90/顶部与桥接表由当前 CSV 重算，脚本见 `evidence.py`。 |
| 11 单位/缺失/非有限 | 原始 2,014 文件 SHA256 校验通过；Q3 发布验证检查预算、支持、有限性；Q4 核心测试与 45 项哈希通过。脚本生成 JSON 禁止 NaN。 |
| 12 基线/消融/敏感性 | Q1 二阶对 Ridge、Q2 B1/B7 候选对照、Q3 九个单因素情景、Q4 四回测模型及格宽压力均沿用已有证据；新增 Q2 δ、质量斜率、配比强度共 28 行。 |
| 13 验证设计 | 原有真实、半合成、估算和诊断验证保持区分；新增联合效应是模型内操作性检验，不冒充真实干预。Q4 条件范围不是有覆盖率的预测区间。 |
| 14 结论阶梯 | 摘要和小结把“模型内条件决策、验证支持、未识别外推”分级。q90 为高分群稳健代理，不是绝对最高分；高预算未分配不表示现实无收益。 |
| 15 跨附件接口 | Q2 当前下游状态另立 `STATUS_CURRENT.md`，原冻结 acceptance 保持生产快照；Q3→Q4 已消费固定配方 36 行，但低预算联立配方 477、独立 $Q_B$ 尚未进入该桥，论文明确范围。 |
| 16 可复现 | `evidence.py`、`computed_evidence.json`、各问清单和本报告固定命令与路径；当前 main 的编辑版 Q3 manifest 及四问 curated manifest 已刷新并通过只读校验。 |
| 17 从零反证 | 检查“正曲率即互补”“q90 即最高上界”“113% 即纯技术因果”“高预算余量即无效投资”“Qwen 桥接即实测得分”等误读，并在正文对应处限定。 |
| 18 分支与 legacy | 三留存分支逐项比较；无现成完成的终稿补丁。原来源 manifest 与作废历史不改，当前 main 清单只更新本轮编辑文件哈希。 |

## 整改事项与判定

- **MAJOR 已处理：**Q4 两类代理的约定、D 的归属和格宽范围；q90 与同期/全期最高值及准确预测日；Q3 独立质量决策表和高预算未分配解释；Q2 固定 donor 的有限联合判据、反例与稳定性；Q3→Q4 中高预算四行能力换算及排序条件。
- **MINOR 已处理：**Q1 评分/冲突/配方摘要及中位数与 Q75 区分；Q2 质量替代和 B4/B5/B9/B10 数值用途；Q2 历史 pending 状态解释；浮点 fixture 容差；总摘要、数据利用清单和参考文献。
- **待提交前确认：**论文末尾已披露本项目可核实的 Codex 使用及作废 Gemini 历史；其他成员实际使用的 AI 工具与范围须由当事人补全。当前不是可宣称完整的人类提交版 AI 清单。
- **环境限制：**本机未发现 XeLaTeX/BibTeX，未做 PDF 编译与排版/匿名性目视验收。旧 `test_q4_complete.py` 的发布集成类查找已不在 main 精选包的 v2 路径，故以当前 v3 的 13 项核心测试及 45 项哈希门禁为正式 Q4 检查。

## 复核命令及已见结果

```powershell
.venv\Scripts\python.exe audits/review_followup_20260926/evidence.py   # 28 contrasts, 4 bridge rows
.venv\Scripts\python.exe -m unittest src.cyj.tests.test_verify_v8_fixtures src.chm.test_q3_conditional_v8 src.cyj.tests.test_ndqp_v8  # 22 tests OK
.venv\Scripts\python.exe src/cyj/verify_v8_fixtures.py              # 18 PASS
.venv\Scripts\python.exe src/chm/test_q1_v2.py                      # 7 OK
.venv\Scripts\python.exe src/zhh/test_q4_core_v3.py                 # 13 OK
.venv\Scripts\python.exe src/zhh/verify_q4_core_v3.py              # 45 hashes PASS
.venv\Scripts\python.exe scripts/refresh_main_manifests.py         # Q1–Q4 PASS
.venv\Scripts\python.exe scripts/check_paper_integrity.py          # 11 tex, 11 figures, 66 labels, 9 citations PASS
.venv\Scripts\python.exe scripts/check_ai_reading_rules.py         # 24 guarded entries PASS
./scripts/verify_raw_data.ps1                                      # 2014 files, 564436312 bytes, SHA256 PASS
```

上述结果只证明各命令的声明范围，不把数值门禁当作真实模型结论的外部验证。`git diff --check` 通过。用户审查报告的模拟 78 分不是官方评分，整改后不自行重新打分。
