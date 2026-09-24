# cyj / P20 跨分支审查与 B1 组级 bootstrap 结果交接

时间：2026-09-24 10:11（北京时间）；分支 `team/cyj-scaling`。状态：本人生产者侧诊断完成，未获 chm/zhh/集成人验收，Q3 `ready_for_Q3=false`。公共 `origin/main=a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`；运行前个人远端核验 `65b3a722d83b7206290acec12474fd2dabafe796`。本交接提交/推送后的最终 SHA 须以实际核验为准。

## 本次变更及版本

- 新增 B1 整组重抽样脚本、测试、结果 JSON 与实验记录；本人接口 `interfaces/cyj/CONTRACT.md` 从 v1.6 到 v1.7，仅追加条件诊断。跨分支审查见 `problem/cyj/20260924-cross-branch-interface-review.md`（含 fetch 后 chm 新提交增量），本次未修改公共记忆或其他成员目录，也未合并任何分支。
- B1 脚本/依赖与输入锁定提交 `8dd672eb53571325f27342f4e545c0fa7bf06f24`；源 CSV 按提交内 `F_MANIFEST.json` 身份核验；prepared B1 对照原基线 provenance；经典结果 SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。环境 Python 3.12.14，NumPy 版本和输入文件身份详见结果 JSON。不得使用历史隐藏 PDF 文本或作废 Gemini 提交作依据。
- chm 清洁集成分支先读 `7a958d7b5760bce4e7136a5c80e6b9275de60eaf`，再次 fetch 后已到 `3f237910bc4b7ebfc7d4408d65572c134fed59c5`；zhh 分支 `d47cd2dc921333caecfcb95f09eb5a2f2714d0db`。各接口文件 SHA、限制与利益点在本人审查记录中。其他个人分支状态不是 main 验收结论。

## 命令与结果证据

- `git fetch origin --prune`；`git rev-parse origin/main`；`git diff --name-status 7a958d7..origin/integration/chm-q1-clean-20260923`；`git show <ref>:<path>` 用于只读核对。先做本人运行前 commit/push，再以 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/team/cyj-scaling` 核实 SHA 一致。
- 在仓库根目录两次执行 `& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' src/cyj/diagnose_b1_group_uncertainty.py --input-version 8dd672eb53571325f27342f4e545c0fa7bf06f24`；两次均报告 78/80 accepted，结果 `outputs/cyj/diagnostics/b1_group_bootstrap.json` SHA256 均 `e105dfd6b4ffc28f6d6fdf116173b0602b5d7ea5c2ec156f333be113ebeaadef`，94,180 bytes。
- `& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s src/cyj/tests -p 'test_*.py' -q` 得 21/21 PASS；`-m py_compile` 通过。80 次均整条 N 轨迹抽样，2 次未收敛剔除。五参数及 3×3 网格经验分位数见 JSON 和 `experiments/cyj/20260924-b1-group-bootstrap.md`，不写成正式 95% 预测区间。

## 接口冲突、未验证项与下一步

- chm 的 `Q_z` 与 B 侧 `Q_score` 无配对标定，Q1 13 域 Loss 与 B1 `val_loss` 不同口径；不能恒等映射、指定事实 anchor 或默认 `lambda=1`。chm 新增的 eta 配对条件区间及消融只能借鉴不确定性拆层和敏感性做法，不提供跨 Loss 换算。共同确定 B-native Q 情景可否满足交付、主/敏感性 target 与 p 中心化/尺度传递，并记录联合冻结版本。
- zhh 提供 C7 2048/8192/131072 Token 外生情景与分级桥接结果，但其合同/成员记忆仍过期；请 zhh 自行修订并经集成人验收。桥接留出 RMSE 7.060 不是可直接套用的 95% 误差区间，Loss 不等于 Benchmark。
- B1 Loss 逐行来源、近乎精确重构机制、B2/B4/B5 同一统计尺度、Q/p/anchor、跨来源与外推验证、全库 A 附件 LFS 验证仍未完成。B1 bootstrap 极窄区间只覆盖固定 B1 数据/模型/优化筛选，不能作为 Q3 validated predictor 或 Q4 传播的总不确定性。
- cyj 下步优先审 B1 Loss 构造/来源与 B4/B5 同尺度证据，再与 chm 联合做 Q/p/Loss 决策；zhh 更新其自有合同，集成人复现验收后决定 main 与公共 memory-bank 更新。若无法确认映射和 Loss bridge，维持分层情景表述，不编造定标。

## 提交推送检查点

本交接随本人实验、结果、合同和记忆按明确文件暂存，执行 `git diff --check`、`git commit -m "cyj: record B1 group-bootstrap conditional uncertainty"`、`git push origin team/cyj-scaling`，最后比较 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/team/cyj-scaling`；未核对前不得称远端备份成功。
