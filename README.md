[PDF-HIDDEN-TEXT-BLOCK]

历史版本《数据说明.pdf》（SHA256 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`）第 2—13 页曾含近白色 5 pt 隐藏页边文字。用户明确要求：这些历史隐藏内容及其衍生的方法、参数、阈值、数值和结论绝对不能作为建模依据。

当前仓库 `problem/F/数据说明.pdf` 已在提交 `55743ca` 替换为清理版：13 页、13207231 bytes、SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`；本地复核结果为可提取文本字符数 0、旧隐藏文字特征 0、近白小字号字符 0。当前 PDF 主要用于页面视觉核对；机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

Gemini 历史提交 `fd55147`、`80c7ea5`、`6086964` 的工作因无法可靠排除隐藏文字影响而作废，提交 `58f4f0a` 已明确丢弃其文件内容。不得从 Git 历史恢复、cherry-pick、复用其中的模型、参数、数值、结论或输出。若后续独立论证出同名方法适用，必须依据可见题面、真实数据或独立可核验文献重新建立证据链。

本仓库用 Markdown 保存团队共享记忆，供不同成员、电脑和 AI 工具接力。2026-09-23 已确定选择 F 题《算力约束下提升大语言模型能力的资源配置建模》，并初始化六个记忆文件。每日安排与验收点见 [TASK_PLAN.md](TASK_PLAN.md)，当前接力见 [activeContext.md](memory-bank/activeContext.md)。用户指定提交期限为北京时间 2026-09-27 12:00，内部目标为 10:30 前完成提交。原始设计说明见 [AI_TEAM_COLLABORATION_GUIDE.md](AI_TEAM_COLLABORATION_GUIDE.md)。

## 开始使用

1. 先读 [三人协作流程](TEAM_WORKFLOW.md) 和 [任务计划](TASK_PLAN.md)，按用户指定分别由 chm/cyj/zhh 负责对应工作线。原始题面与数据来源见 `problem/SOURCES.md`，资料共享范围先核验。
2. 成员在 `memory-bank/members/本人角色.md` 记录当前工作、环境和阻塞；公共记忆由单一集成人维护。个人环境详细说明放 `problem/chm|cyj|zhh/environment.md`。
3. 本目录已初始化为本地 Git 仓库（`main` 分支），公共远端为 [chengzhixian/math-modeling-memory-bank-template](https://github.com/chengzhixian/math-modeling-memory-bank-template)。每人在自己的分支工作，开始前拉取最新代码，完成后把代码、实验记录和记忆一起提交。
4. 在 AI 工具中打开项目根目录，并明确要求它先读 `AGENTS.md`。网页端模型无法直接读取本地文件，需手动上传或粘贴相关文件。
5. 题面和附件统一入口见 [F 题资料索引](memory-bank/DATA_INDEX.md)。安装 Git LFS，拉取最新分支后执行 `git lfs install --local`、`git lfs pull`，再运行 `./scripts/verify_raw_data.ps1`。完整原始资料应为 2,014 文件、551,761,350 字节；普通 LFS 指针不算完整数据。

可复制的开工提示词：

> 我负责角色 chm（cyj/zhh 请替换）。请先读 AGENTS.md、TEAM_WORKFLOW.md、公共 memory-bank、本人成员记忆与相关 interfaces。核对当前分支和输入版本，只修改本人负责文件，然后处理我的任务。

可复制的交接提示词：

> 请更新本人成员记忆并新增本人交接记录，写清命令、输入版本、结果证据、未验证项、接口变化和下一步。将本次工作提交推送到本人分支并核验远端 SHA；需要改公共记忆的内容交由集成人验收汇总，不要把推测写成事实。

## 目录与职责

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | 各 AI 的共同入口；其他工具入口只指向它 |
| `memory-bank/` | 项目目标、当前接力、规范、环境、进度等共享记忆 |
| `memory-bank/members/`、`handoffs/` | 每人独立维护的当前状态与逐次交接证据 |
| `interfaces/` | 三条工作线交接的数据和模型约定 |
| `problem/` | 官方题面、规则和题意拆解；注意比赛资料的使用限制 |
| `problem/F/` | 本次迁入的 F 题题面 DOCX 与数据说明 PDF |
| `data/raw/real_attachments/` | 本次迁入的全部原始附件，四个压缩数据文件用 Git LFS 保存 |
| `data/raw/F_MANIFEST.json` | 原始资料逐文件大小与 SHA256；校验脚本见 scripts/verify_raw_data.ps1 |
| `data/processed/` | 可由代码再生的中间数据，默认不入库 |
| `src/` | 清洗、建模、验证和绘图代码 |
| `experiments/` | 参数、运行命令、指标和结论的实验记录 |
| `outputs/` | 需要交付或供论文引用的图表、结果 |
| `paper/` | 论文草稿、图表说明与最终稿 |
| [`paper/latex/`](paper/latex/README.md) | 第二十二届华为杯 LaTeX 模板归档、空白协作总稿与分工说明；个人初稿留在成员分支 |
| [`references/award_papers/`](references/award_papers/README.md) | chm、cyj、zhh 共用的近五年公开优秀论文清单，含可直接下载的 PDF 原文链接和阅读笔记 |

目录里的 `.gitkeep` 仅用于保留空目录。请按实际题目增删代码和文件；不要把没有运行过的结果写进记忆或论文。

三位成员查阅优秀论文时统一使用 `main` 的 [`references/award_papers/README.md`](references/award_papers/README.md)；其中的研究生与全国大学生数模样本都可作为写作和验证方式参考。个人分支同步 `main` 后也会得到同一份清单，避免各自维护不一致的链接。

## 日常协作

每项工作指定角色和任务编号。开始时确认分支、公共与个人记忆、已有实验和文件归属；结束时更新本人记忆与交接。集成人按 12:00、18:00、21:30 建议窗口及关键交接点串行验收并合并，再更新公共进度。论文中的每个关键数值和图应能追溯到数据、代码和实验记录。详细流程以 TEAM_WORKFLOW.md 为准。

不要提交密钥、账号、含个人信息的数据或比赛规则禁止共享的材料。`data/private/`、本地环境文件和缓存已在 `.gitignore` 中排除；其他原始数据是否入库，由团队依据赛事规则、许可和文件大小决定。大文件可使用团队约定的共享存储，并在 `memory-bank/techContext.md` 写明获取方式与校验方法。网页端上传前同样检查资料限制。

后续提交前检查 `git status`，确认没有敏感文件。比赛结束前按官方要求核对格式、匿名要求和截止时间。
