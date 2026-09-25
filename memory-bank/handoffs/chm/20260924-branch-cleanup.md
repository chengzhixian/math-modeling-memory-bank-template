# chm 分支清理判断（2026-09-24）

当前长期维护分支：`integration/chm-q1-clean-20260923`。

## audit/f-data-20260924

该分支相对 clean 只有 1 个独立审计提交。直接树比较显示其真正独有内容为 8 个文件：`audits/f_data_20260924/` 下 7 个审计报告/证据/脚本，以及 `memory-bank/handoffs/audit/20260924-original-data-audit.md`。这些文件已以提交 `77037e8fe625fa1227fe64862fbf551ab908b73d` 复制进 clean 分支；审计分支相对 clean 已无独有路径。审计分支上的 Q1/Q2/Q3/LaTeX 文件均是较旧快照，不应覆盖 clean 当前版本。因此该 audit 分支在合并完成后可以删除。

## team/chm-data

该分支是旧 legacy 分支，历史提交中已明确记录 `mark legacy branch non-integrable` 与 `remove contaminated method names`。相对当前 clean，它仍有 12 个只存在于 legacy 分支的路径：

- 9 个 `outputs/chm/archive/web_v0/` 历史网页输出；
- `outputs/chm/local_recheck_v1/web_local_cv_comparison.csv`；
- `src/chm/q1_regmix_baseline.py`；
- `src/chm/q1_verify_local.py`。

这些内容均不应并入当前主工作流：web_v0 是已知与本地确定性复跑不一致的历史结果；`q1_regmix_baseline.py` 把 13 个 target Loss 直接求均值，已不符合当前 13 维 Loss 主模型；`q1_verify_local.py` 和 comparison CSV 仅服务于旧网页结果与 local_recheck 的差异审计。当前 clean 已保留新版 Ridge、消融、接口、论文和必要审计结论。

因此 `team/chm-data` 不应再 merge，也没有继续保留为活动分支的必要；可以删除。若未来需要追溯，其最终 HEAD 为 `867e9eebe30bc3944b3eb27a47912bffae520368`，提交 SHA 可作为历史定位点。

## 规则

后续 chm 只向 `integration/chm-q1-clean-20260923` 推送。临时审计/实验分支在验收后，将必要文件择优合入 clean，再删除临时分支；不再让旧 legacy 分支参与集成。
