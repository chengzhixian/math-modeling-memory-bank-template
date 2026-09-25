# chm 交接：Q1 可识别性错误复盘与公共审查流程建议

日期：2026-09-24

本轮已形成 Q1 结构性错误复盘，见：

- problem/chm/20260924_q1_identifiability_failure_postmortem.md

核心事故：此前把 1M/60M/1B 三个实验组上的经验幅度差异升级为纯 \(N\) 连续尺度律，并拟合公共 \(\eta\)。数值可算但数据不可识别，属于 identifiability error，而非一般代码错误。

永久规则：任何公式进入代码/论文前，先做 variable provenance、identifiability、dataset-role、support/leakage 与 claim-level gate；参数“能拟合”不等于“能解释”。

用户要求把完整审查流程升级为全团队公共规则，并同步 main。公共流程应由根目录 REPOSITORY_REVIEW_PROTOCOL.md 定义，并在 AGENTS.md、TEAM_WORKFLOW.md、公共 memory-bank 中建立强制入口。以后成员或 AI 收到“审查远程分支/本地仓库/代码/数学模型/问题”等请求时，都必须执行完整流程，不能只检查代码实现。
