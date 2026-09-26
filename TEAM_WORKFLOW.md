[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

本方案适用于三个人、三台电脑、不同 AI 工具。用户已指定 chm、cyj、zhh 分别承担原三个角色。每人在自己的成员记忆中填写机器与分支；不要求统一模型或硬件。默认建议 zhh 兼集成人，实际人选待团队确认。在确认前，不允许多个成员同时代行集成。

## 三条工作线

| 角色 | 主线 | 后续工作 | 不依赖别人即可先做 |
|---|---|---|---|
| chm 数据与求解 | Q1 全量质量、冲突、17 域配比 | Q3 求解实现、预算扫描、成本与上下文敏感性；写 Q1/Q3 章节 | 附件 A 审计、指标清洗、检验划分、配比基线 |
| cyj 标度律与理论 | Q2 拟合、跨来源验证、边际效用与替代条件 | 给 chm 提供 Q3 目标函数/约束/适用范围；核验优化与推导 | 附件 B 审计、B1 经典基线、B2–B5 验证；不等 Q1 全部完成 |
| zhh 评测与集成 | Q4 逐任务评测、技术贡献、桥接与预测 | 论文统稿、公共记忆和集成验收；写 Q4 与公共章节 | 附件 C 审计、C8 聚合、开放性与日期口径、桥接基线、C7 情景表 |

四问有真实依赖，不能完全互不等待。先交稳定的最小输入，再逐步替换为经过验证的版本；未取得正式输入时可开发接口和基础模型，但不得把占位参数产生的输出当作最终结果。Q3 在 chm 完成 Q1 后接手，避免 cyj 一人承担两整问；三人各写自己章节，zhh 不包办全文。

## 文件归属

集成人将验收后的 Q1–Q3 **main 发布副本**按问题收录于 `outputs/Q1`、`outputs/Q2`、`outputs/Q3` 和 `experiments/Q1`、`Q2`、`Q3`；下表的成员目录规则继续适用于个人分支的研究与完整生产日志。冻结清单中的原成员路径保留来源身份，main 的精简路径由问题目录索引说明。

| 文件或目录 | 唯一日常写入者 |
|---|---|
| src/chm/、outputs/chm/、experiments/chm/、problem/chm/、interfaces/chm/ | chm |
| src/cyj/、outputs/cyj/、experiments/cyj/、problem/cyj/、interfaces/cyj/ | cyj |
| src/zhh/、outputs/zhh/、experiments/zhh/、problem/zhh/、interfaces/zhh/ | zhh |
| paper/sections/chm/（Q1、Q3） | chm |
| paper/sections/cyj/（Q2、Q3 理论说明材料） | cyj |
| paper/sections/zhh/（Q4、摘要和公共章节） | zhh |
| paper/latex/sections/chm/、paper/latex/figures/chm/ | chm：Q1 与 Q3 数值章节及自有图 |
| paper/latex/sections/cyj/ | cyj：Q2 与 Q3 理论章节 |
| paper/latex/sections/zhh/ | zhh：摘要、问题重述、公共章节与 Q4 |
| paper/latex/main.tex、gmcmthesis.cls、references.bib、最终 PDF | 集成人：总装、类文件、文献与编译 |
| memory-bank/members/chm.md、cyj.md、zhh.md | 各自对应成员 |
| memory-bank/handoffs/chm/、cyj/、zhh/ | 各自对应成员；每次新建文件，不覆盖旧交接 |
| 六个公共记忆文件、TASK_PLAN.md、AGENTS.md、README.md、TEAM_WORKFLOW.md | 集成人 |
| 公共依赖清单、src/shared/、paper/outline.md、paper/main.*、最终 DOCX/PDF、interfaces/README.md | 集成人 |
| experiments/experiment-log.md、problem/problem-notes.md、problem/SOURCES.md 等公共索引 | 集成人 |

其他成员需要修改别人目录、公共接口或依赖时，在自己的交接文件写清建议，由文件负责人实施；紧急转交需明确新负责人和时间，原负责人暂停写入。暂不创建没有用途的空目录，首次工作时按归属创建即可。

2026-09-24 起统一以 `paper/latex/` 中的第二十二届华为杯模板源文件组织论文；其 2025 年封面与 2026 年正式要求的符合性须在提交前单独核验。三位成员只在本人分支修改各自 `sections/<成员>/`，不同时编辑总文件或他人的章节。集成人串行验收并合入，负责统一图号、符号、引用、摘要和最终 PDF。详细编译与模板差异见 `paper/latex/README.md`。

这些是协作约定，尚未配置 GitHub 强制分支保护或目录权限。不能保证 Git 自动阻止越界写入。评审时必须检查变更范围。

## 分支和电脑隔离

- 三台电脑分别 clone 同一仓库，使用各自本地目录。不要用网盘同时同步一个包含 .git 的工作目录。
- 建议固定个人分支：team/chm-data、team/cyj-scaling、team/zhh-frontier。每条分支同一时刻只有一个写入者；更换电脑或模型先交接并同步。
- main 是已集成版本，由一位集成人更新。成员推送自己的分支即完成备份，不必等 main 合并。
- 集成人做本人研究时仍用个人分支；做集成时使用干净的 main 工作目录。切换前先保存本人工作，或使用另一个 main worktree，避免把尚未验收的 zhh 研究改动带入主分支。
- 同一电脑同时运行两个会改文件的 AI 时，应使用不同 Git worktree 和不同子任务分支，并给出不重叠的文件范围；不能让两个 AI 共用同一工作目录。平时每人一个活跃写入会话即可。
- 当前仅写入分支命名方案，尚未创建三个成员远程分支，也未配置成员权限。

以下是通用 Git 命令。本机如默认 Git 不支持 HTTPS，使用 AGENTS.md 所述完整可执行路径；各电脑不复制他人的凭据或绝对路径。

首次加入（以 chm 为例；cyj/zhh 替换分支名）：

```sh
git clone https://github.com/chengzhixian/math-modeling-memory-bank-template.git
cd math-modeling-memory-bank-template
git fetch origin
git switch -c team/chm-data origin/main
git push -u origin team/chm-data
```

如果远端个人分支已经存在，使用 `git switch --track origin/team/chm-data`，不要再次创建同名分支。仓库已 clone 时跳过 clone；确认工作区干净后再切换。

每天开工，先查看状态；若有未提交改动，先在当前本人分支审查并提交备份，禁止为方便切换而丢弃。干净后：

```sh
git switch team/chm-data
git fetch origin
git pull --ff-only
git merge origin/main
```

其中 pull 更新本人分支，merge 接收已集成结果。命令失败或产生冲突即暂停后续命令，核对双方内容后解决；不要强推，不要用 reset --hard 或全选 ours/theirs 消除冲突。

完成一块任务：

1. 只更新本人代码、章节、成员记忆；新增本人交接记录。
2. 明确选文件暂存（不要不加检查地 git add .），检查暂存 diff 后 commit。
3. push 本人分支，即使是未完成工作也可用 wip 提交，记录尚未通过的检查。
4. 用 `git rev-parse HEAD` 和 `git ls-remote origin refs/heads/team/chm-data` 核对 SHA。
5. 达到接口验收或里程碑时发起面向 main 的 PR；未验收可先用 draft，备份成功不等于可以集成。

## 集成人如何接收

日常建议 12:00、18:00、21:30 检查待集成内容；到约定交接点立即处理，不让关键输入等到晚间。没有创建定时提醒。

1. 确认成员最新代码和记忆在同一次交付中，明确输入版本、接口变更和未验证项。
2. 检查是否改了别人的文件，按交接命令验证必要结果；不以“已经 push”作为验收依据。
3. 按依赖先后顺序串行合并，一次处理一个成员的变更。使用保留历史的 merge commit；固定个人分支不使用 squash/rebase merge，避免下次交付重复或历史分叉。
4. 更新公共 activeContext、progress，必要时更新其他公共记忆，标明采用的接口版本、实验路径与集成提交。
5. 推送 main 并核验远端 SHA；通知成员 fetch 并 merge origin/main。若依赖输入发生改变，下游记录需重跑的实验和论文图表。

推荐通过 PR 合并；没有 PR 工具时可由集成人在干净 main 上 fetch、pull --ff-only、merge --no-ff origin/成员分支，完成同等检查和公共记忆更新后再推送。无需为备份成员工作而把未完成代码合入 main。

## 全团队审查工作流（2026-09-24 起强制）

公共完整流程见根目录 `REPOSITORY_REVIEW_PROTOCOL.md`。用户已明确要求：以后任何成员与 AI 收到“审查一下远程仓库/我的分支/本地内容/代码/数学模型/问题/结果”等请求时，都必须走完整协议。

成员执行审查时：

1. 先冻结 branch / HEAD / merge base / diff，不先静默改代码；
2. 从题面和真实字段重新建立 requirement→data 与 variable provenance；
3. 在拟合前先过 identifiability Gate；
4. 固定 train / tuning / validation / test / extrapolated 角色；
5. 实查 overlap、泄漏和 support shift；
6. 检查文献方法条件是否真的由本题满足；
7. 对照数学公式与实际代码；
8. 做 baseline、消融、敏感性和 held-out 验证；
9. 按描述/预测/结构/因果/外推五级审查结论强度；
10. 做一次“忽略当前模型、只从题目和字段重新推导”的 red-team；
11. 若审查分支，做双向 diff、共同修改文件与最终文件树检查；
12. 发现按 BLOCKER / MAJOR / MINOR / NOTE 分级落盘。

完整审查不是“代码能运行”或“测试通过”的同义词。若存在 BLOCKER，必须先修复或降级结论，不能继续用复杂模型覆盖问题。

## 记忆怎样共享

- 公共六文件：已集成共识。由集成人维护；其他成员读取。
- 成员文件：该成员当前进度、使用版本、阻塞和下一步。由本人维护。
- 交接记录：每次工作块的证据与变更，按 `memory-bank/handoffs/chm/YYYYMMDD-HHMM-task-id.md` 新建。若重名加后缀。
- 已 push 但未合并的记忆在个人远端分支上。其他人先 fetch，然后可用 `git show origin/team/chm-data:memory-bank/members/chm.md` 读取，无需切换正在工作的分支。
- 正式计算默认使用已验收并进入 main 的接口版本。紧急提前使用个人分支产物时，记录精确 commit、哈希和“临时未集成”，不可把后续 main 结果混为一谈。
- 记忆不会自动进入另一个 AI 的对话。每次新会话、切换模型或接收重要更新后，显式要求 AI 重新读取文件。网页模型由本人上传/粘贴当前版本，产生的改动也由本人检查后回填。

交接至少含：角色/任务编号、状态、当前分支和工作起点 SHA、使用的输入版本/哈希、修改文件、运行命令、实际验证结果、输出路径、未知与阻塞、接口改动、需要谁在何时接收、下一步。当前提交包含交接记录时不要求把它自己的 SHA 写入文件；实际提交以 Git 历史为准，避免自引用。

## 不同机器和模型的最小共同约定

题面和附件已按用户要求迁入仓库，入口为 memory-bank/DATA_INDEX.md。每台机器安装 Git LFS，合并最新 main 后执行 git lfs pull，再运行 scripts/verify_raw_data.ps1，确认全部 2,014 个原始文件校验通过。每人用本地环境变量 F_DATA_ROOT 指向仓库 data/raw/real_attachments，代码不写死盘符；该环境变量是待实现的配置约定，当前还没有分析程序读取它。

各自维护 problem/chm|cyj|zhh/environment.md，记录实际 Python/库版本、系统、CPU/GPU、复现命令和随机种子。依赖版本先在本人范围提出，由集成人维护公共最小环境；不同机器对浮点结果允许经说明的数值容差，不要求二进制完全相同。能用 CPU 完成的统计任务不强制使用 GPU。

小型已允许共享的接口结果放 outputs/本人目录并随代码提交；大型文件留本地或团队存储，交接提供获取方式、大小和 SHA256，不把私人访问链接或密钥放公共仓库。模型聊天记录不是项目事实的唯一来源，证据必须落到文件。

## 可复制的开工提示词

> 我负责角色 chm（cyj/zhh 请替换），使用本人分支。先读 AGENTS.md、TEAM_WORKFLOW.md、公共 memory-bank、memory-bank/members/chm.md 和本任务相关接口约定。先报告当前分支、使用的输入版本和待验证项，再处理分配给我的任务。只修改归我负责的文件；涉及他人目录或公共文件时，在本人交接记录提出变更。结束时更新本人记忆并新增交接记录，将代码、证据与记忆一起提交并推送本人分支，核验远端 SHA。不要把未经验证的结果写成结论。

额度预留规则持续有效：任务结束和长任务开始前先备份，任一相关额度窗口剩余 ≤20% 时优先同步，≤10% 时先完成同步再开新重任务。本人分支和集成分支各自核验，不等待队友合并才备份。

## 跨分支依赖规范入口（2026-09-23）

三条工作线的详细依赖、当前接口冲突、合作顺序和 main 同步方式已冻结在：

`TEAM_COLLABORATION_DEPENDENCIES.md`

该文件属于公共协作规范，由集成人维护。成员每次开始新的跨成员工作块、接收上游接口或发现 main 有公共规则更新时，必须重新读取。

当前最重要的团队接口会议只处理四件事：

1. chm Q 与 B6–B8 `Q_score` 的共同尺度；
2. Q1 的 13 个 domain Loss 与 B1 `val_loss` 的可比性；
3. p 如何进入 cyj 的广义 Scaling Law；
4. chm/cyj/zhh 三层不确定性如何传递到 Q3/Q4。

在上述接口未冻结前：
- cyj 可以独立完成 B1 N-D 基线及 B2–B5 验证；
- chm 可以完成 Q1、Q3 求解器框架和接口检查，但不得发布 Q3 正式最优配置；
- zhh 可以继续 Q4 历史分析、C7 和桥接验证，但不得把异质 Loss 直接转换成最终能力结论。

### 公共规则如何进入个人分支

main 更新后，成员在本人的固定分支执行：

```powershell
git status
git fetch origin --prune
git pull --ff-only
git merge origin/main
```

执行前必须确认当前分支仍是本人的 `team/chm-data`、`team/cyj-scaling` 或 `team/zhh-frontier`。合并冲突时人工核对，不用 `reset --hard`、强推或整文件 ours/theirs。

若成员当前正在长实验且暂时不适合合并，也必须至少：

```powershell
git fetch origin --prune
git show origin/main:TEAM_COLLABORATION_DEPENDENCIES.md
git show origin/main:memory-bank/activeContext.md
```

这样可先读取最新公共共识，再在合适检查点合并 main。
