# CYJ Q3 v8 联合验收清单交接

日期：2026-09-26（北京时间）。任务类型：仅修订任务清单；未执行 Q3 联合验收。

## 本次变更

- 新增 `problem/cyj/CYJ_Q3_V8_JOINT_ACCEPTANCE_TASKS.md`，明确 CYJ 对已发布 CHM Q3 v8 的版本锁定、Q2 生产者复核、数学与代码交叉核对、36 格／模式独立消费者复现、敏感性、论文对照及本人签收职责。
- 更新 CYJ 成员记忆；本机 Downloads 的原联合清单已修正“CHM v8 待发布”的过时说法（该文件不在仓库内）。

## 证据与核验

- `git -c http.sslBackend=openssl ls-remote origin refs/heads/integration/chm-q1-clean-20260923` 返回 `c052b6918c3f77a2285622521d8abb1b429513be`；只读 fetch 后检查该提交文件树，确认 `src/chm/q3_conditional_v8.py`、`src/chm/q3_v8_assumption_sensitivity.py`、`outputs/chm/q3_conditional_v8/manifest.json` 和 Q3 数值章节存在。
- CHM manifest 自述消费 CYJ v8 文件树 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6` 和 Q1 v2 manifest SHA256 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`；这些身份仍须在正式验收时逐文件复核。
- 本次只核对发布状态与计划文本，没有运行 fixtures、模型脚本或优化复算；清单复选框均保留未完成。

## 未解决问题与下一步

- CYJ 尚未独立签收 CHM Q3 v8；A/B 质量与 Loss 跨源映射仍未实证识别，完整 Q3 没有联合预测区间。这些科学边界不因 CHM 已发布而改变。
- CYJ：按新清单执行完整审查、记录独立数值差异与论文口径，在本人目录签收或列阻塞；发现 CHM 文件问题交 CHM 修复。
- CHM：保持 Q3 数值产物所有权，并对 CYJ 发现的问题重新发布与签署 owner acceptance。
- 已确认的集成人：待双方签收后核验合并与公共状态；不得提前记为联合通过。

当前提交及远端同步状态以本次实际 Git 检查点为准，不预填 SHA。
