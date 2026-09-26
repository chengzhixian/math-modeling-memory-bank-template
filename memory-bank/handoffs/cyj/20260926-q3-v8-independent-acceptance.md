# CYJ → CHM / 集成人：Q3 v8 独立条件验收

日期 2026-09-26。CHM 发布对象 `integration/chm-q1-clean-20260923@c052b6918c3f77a2285622521d8abb1b429513be`，CYJ v8 冻结生产者文件树 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`，CYJ 本次起点 `team/cyj-scaling@74e678e319b58e2aab230a7b7233fa53f3053fa5`。完整 Gate、哈希、复现命令与限制见 `problem/cyj/20260926-q3-v8-independent-acceptance.md`。

## 本次变更与证据

- 新增 `src/cyj/q3_v8_independent_audit.py`、`q3_v8_sensitivity_audit.py`、`q3_v8_source_audit.py`；它们不调用 CHM 优化器。保存 41 文件哈希比对、108 格三模式独立数值差异、九情景 243 格复核、B/C 原始 CSV 重叠审计于 `experiments/cyj/20260926-q3-v8-acceptance/`。
- 18/18 冻结 fixtures、95/95 CYJ tests、9/9 CHM tests 通过；CHM 主网格、预算扫描、假设扫描重生文件哈希一致。三模式可行格 30/33/33；最大 Loss 差不超过 `2.31e-14`。九情景独立 Loss 最大差 `4.44e-16`，候选一致。CYJ Q3 理论节补 CHM 已发布事实、`q≥Q0` 的候选政策、87 配方范围和未识别边界；`interfaces/cyj/CONTRACT.md` 记 v8 条件可消费状态，旧版 `ready_for_Q3` 未改写。
- CHM 的 Q3 owner 交接 `memory-bank/handoffs/chm/20260925-q3-v8-conditional-answer.md` 已给条件签收。CYJ 生产者/消费者签收仅限冻结条件模型及有限候选数值，不是跨来源实证标定。

## 未解决问题、下一步与负责人

1. **科学 BLOCKER，CYJ+CHM+集成人共同保持边界：**缺同条件 A/B N/D/Q/p 配对观测，映射、桥系数、质量/配比重叠均无法识别；任何无条件真实最优或联合 95% 区间不得发布。
2. **MAJOR，CHM 数值负责人：**补 `direct` 与 `direct_and_near` 的完整 Q3 对照，并交 CYJ 复核；现仅签 `direct_and_near`。
3. **复现限制，CHM/CYJ：**外部 N/D 测试仓库 `.upstream/scaling-external@a003c491...` 未在本机，外测脚本本轮未重跑；其发布产物哈希一致。网络恢复后按原提交取源再运行。LFS 443 超时，本轮未重验 2014 文件；可用机器重新 `git lfs pull` 和 `scripts/verify_raw_data.ps1`。
4. **集成人：**`origin/main@0d1b511c014bc1558b1bfc226b72ba1b534a01da` 已选择性吸纳 Q1–Q3；将本次 CYJ 理论修订和审查结论择优迁入 main，重核精简 manifest、全稿编译与公共记忆。CYJ 个人分支未直接改公共六文件或 CHM 目录；分支尚未合并 main，以保留本次冻结消费和角色文件边界。

检查点主提交 `81f4651c656fdf48580dd375821716cf2c09c5cf` 已在本地创建。三次推送 `team/cyj-scaling` 均因 GitHub HTTPS 443 连接重置/无法连接失败；本地 `origin/team/cyj-scaling` 仍为 `74e678e319b58e2aab230a7b7233fa53f3053fa5`，**尚未完成远程备份**。网络恢复后先 fetch 检查分叉，再推送并用 `ls-remote` 核对 SHA。个人分支两遍 XeLaTeX 编译通过（29 页）；两处 overfull 在 CHM Q1 旧段落，非本次 CYJ Q3 理论变更。
