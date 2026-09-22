# 研究生数学建模协作模板

本仓库用 Markdown 保存团队共享记忆，供不同成员、电脑和 AI 工具接力。2026-09-23 已确定选择 F 题《算力约束下提升大语言模型能力的资源配置建模》，并初始化六个记忆文件。每日安排与验收点见 [TASK_PLAN.md](TASK_PLAN.md)，当前接力见 [activeContext.md](memory-bank/activeContext.md)。用户指定提交期限为北京时间 2026-09-27 12:00，内部目标为 10:30 前完成提交。原始设计说明见 [AI_TEAM_COLLABORATION_GUIDE.md](AI_TEAM_COLLABORATION_GUIDE.md)。

## 开始使用

1. 比赛开始后，在 `memory-bank/projectbrief.md` 填写比赛、题目、截止时间和交付要求；把官方题面及规则放入 `problem/`，并记录来源。规则以官方发布版本为准。
2. 在 `memory-bank/techContext.md` 写下实际运行环境、安装命令和复现命令；在 `memory-bank/activeContext.md` 分配第一批比赛任务。
3. 本目录已初始化为本地 Git 仓库（`main` 分支），公共远端为 [chengzhixian/math-modeling-memory-bank-template](https://github.com/chengzhixian/math-modeling-memory-bank-template)。每人在自己的分支工作，开始前拉取最新代码，完成后把代码、实验记录和记忆一起提交。
4. 在 AI 工具中打开项目根目录，并明确要求它先读 `AGENTS.md`。网页端模型无法直接读取本地文件，需手动上传或粘贴相关文件。

可复制的开工提示词：

> 请先读取 AGENTS.md，再读取 memory-bank/activeContext.md、projectbrief.md、progress.md、systemPatterns.md 和 techContext.md。概括已确认的事实、待验证的假设、正在进行的任务以及我现在可以接手的下一步，然后处理我的任务。

可复制的交接提示词：

> 请依据这次实际完成的工作，更新 memory-bank/activeContext.md 和 progress.md；若方法、环境或题目理解有变化，同步更新相应记忆文件。写清文件路径、运行命令、结果证据、未验证项和下一步。不要把推测写成已证实结论。

## 目录与职责

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | 各 AI 的共同入口；其他工具入口只指向它 |
| `memory-bank/` | 项目目标、当前接力、规范、环境、进度等共享记忆 |
| `problem/` | 官方题面、规则和题意拆解；注意比赛资料的使用限制 |
| `data/raw/` | 允许共享的原始数据，不直接修改 |
| `data/processed/` | 可由代码再生的中间数据，默认不入库 |
| `src/` | 清洗、建模、验证和绘图代码 |
| `experiments/` | 参数、运行命令、指标和结论的实验记录 |
| `outputs/` | 需要交付或供论文引用的图表、结果 |
| `paper/` | 论文草稿、图表说明与最终稿 |

目录里的 `.gitkeep` 仅用于保留空目录。请按实际题目增删代码和文件；不要把没有运行过的结果写进记忆或论文。

## 日常协作

每项工作尽量指定负责人和任务编号。开始时确认分支、最新 `activeContext.md`、已有实验和自己要改的文件；结束时记录改动、可复现命令、结果位置、局限与下一步，并更新 `progress.md`。同一时间多人可能修改 `activeContext.md`，合并分支时应整合双方事实和待办，不要用其中一份覆盖另一份。论文中的每个关键数值和图应能追溯到数据、代码和实验记录。

不要提交密钥、账号、含个人信息的数据或比赛规则禁止共享的材料。`data/private/`、本地环境文件和缓存已在 `.gitignore` 中排除；其他原始数据是否入库，由团队依据赛事规则、许可和文件大小决定。大文件可使用团队约定的共享存储，并在 `memory-bank/techContext.md` 写明获取方式与校验方法。网页端上传前同样检查资料限制。

后续提交前检查 `git status`，确认没有敏感文件。比赛结束前按官方要求核对格式、匿名要求和截止时间。
