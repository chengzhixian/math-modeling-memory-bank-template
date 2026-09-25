# CHM Q3 v8 迁移首个检查点（2026-09-25）

## 输入与决定

用户要求接续其他主机的 Q3 进度，并核查 CYJ v8 是否可直接使用。本人 `integration/chm-q1-clean-20260923` 工作树从 `0c5cf03` 快进至已远端核验的 `65bcb01f66d8b7359722e44266199ba025c9d5ef`，保留另一工作树的 v7 审查及未跟踪文件。CYJ 新分支为 `fd2dbb3b2002983430329cdb2ec6a275c2eed4f6`，其已核远端的 v8 验收主体为 `615c078517379284f6b0504c568790a7975c6eda`。Q1 v2 清单 SHA256 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`，B1 fit `9b0e381f...`、B7 质量项 `30819a59...`。默认数据说明只读 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`，不采用历史隐藏 PDF 文本及作废提交。

v8 的质量由 p 经未标定的 A→B 单调代理生成，v7 的独立 Q 自变量不再适合直接作为 v8 基准预测输入。v8 共同支持域 N∈[0.070542,11.965825]、D∈[10,299.893]（十亿单位），旧 v7 D 上界 600 的数值表和转移点不得改名沿用。Q1 无约束主配方在 v8 `direct_and_near` 映射下 Q 约 0.38578，低于本轮 Q3 `Q0=0.5` 情景；因此本轮主策略使用 CYJ Q2 v8 发布的 A4 已观测配方 172，Q 约 0.67136，且 Q1 质量约束成立。固定配比合法，因为题面允许由前两问决定 p；另作有限已观测配方联立选择检查。

## 本轮变更与复现

- 新 `src/chm/q3_v8_inputs.py` 核对精确 Git 对象、Q1/B1/B7 质量身份及 CYJ release record，然后加载 v8。当前 Windows Git worktree checkout 因未知 Git exit 5 失败，本机用 `git archive` 从精确提交导出最小只读派生包至被 Git 忽略的 `.upstream/cyj-v8/`；包不入库，未读取原始 A。
- 新 `src/chm/q3_conditional_v8.py` 在固定 p/Q 下降维：Loss 对 D 单调下降，按预算消去 D；在当前 B1 和 B7 参数符号条件下对 log N 凸，二分导数求全局固定 p 数值解。逐格调用 CYJ v8 predictor 复算并核对三项成本；报告浮点凸性下界，不作严格区间算术证明。
- `outputs/chm/q3_conditional_v8/fixed_policy_grid.csv` 有 36 格、30 可行；`observed_joint_grid.csv` 对满足 direct+near、Q≥Q0 的 87 个 A4 已观测配方逐一求解，36 格中 33 可行。`1e22` FLOPs、8192 Token、幂函数成本下配方 172 的 N=6.660655431、D=193.873531189、Q=0.671360765、条件 Loss=2.094421151，与 CYJ v8 固定配比 smoke 的 Loss 差在 1e-12 量级。低预算 4 格离散最佳为配方 477，其余可行格为 172。该“最优”只针对 87 个有限候选。
- 本机命令：`H:\研究生数模\math-modeling-memory-bank-template\.venv\Scripts\python.exe -B .upstream/cyj-v8/src/cyj/verify_v8_fixtures.py` 得 18/18；`... -B src/chm/q3_conditional_v8.py` 生成两表；`... -B -m unittest src.chm.test_q3_conditional_v8 -q` 得 5/5。测试包含精确导出文件篡改拒绝、Q1 原主配比 Q0 不兼容、v8 已发布 smoke 数值与另一 SLSQP 优化器一致。

## 科学状态与后续

v8 `acceptance.json` 为条件性工程验收，`q3_consumer_verified_by_CHM=false`，A/B 配对经验标定未完成。该输入没有识别质量代理函数、配比桥幅度与分离贡献；本轮没有联合 95% 预测区间或真实训练效果结论。继续在 v8 下重新扫描预算转移、验证支持域/数值界、添加结果清单并写本人 Q3 论文段。完整审查协议的 variable provenance、数据角色、claim ladder 和从零 red-team 仍需落盘。v7 历史输出保持版本化历史诊断，不作为 v8 主论文数字。本次提交和远端核验 SHA 以实际 Git 记录为准。
