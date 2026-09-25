# cyj / P20 跨分支审查与 B1 组级 bootstrap 运行前交接

时间：2026-09-24 09:59 北京时间。状态：运行前检查点；不能称 bootstrap 结果完成或预测接口 validated。分支 `team/cyj-scaling`，本轮起点及此前已核远端 `9a2d4357351afb11c59dff474cc82350a496eb7e`，公共 `origin/main=a0932fd92b3a46cef8eb0bf563df1e6abc9396ef` 是祖先。

## 变更、版本和证据

- 只读比较 chm 清洁集成分支 `7a958d7b5760bce4e7136a5c80e6b9275de60eaf`、zhh 个人分支 `d47cd2dc921333caecfcb95f09eb5a2f2714d0db`，文件 SHA 和逐项冲突/借鉴写入 `problem/cyj/20260924-cross-branch-interface-review.md`。未合并其他分支，未从禁用 Gemini 历史提交取材。
- 新增 `src/cyj/diagnose_b1_group_uncertainty.py` 与对应测试，代码提交 `8dd672eb53571325f27342f4e545c0fa7bf06f24`。执行 `python -m unittest discover -s src/cyj/tests -p 'test_*.py' -q` 得 21/21 PASS，Python 编译通过；正式数据运行尚未执行。
- 拟使用 B1 `pythia_training_log_existing.csv`、提交内 `F_MANIFEST.json`，已审 `prepared_b1.csv`、`classic_fit.json`（SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`）。程序运行时将再次核对代码/输入与版本；默认 80 次按 8 个 N 轨迹整组重抽样，每次 8 starts，seed 20260924。
- 复查命令：`git status --short --branch`；`git fetch origin --prune`；`git rev-parse origin/main`；`git show <ref>:<path>`；`python -m unittest discover -s src/cyj/tests -p 'test_*.py' -q`。结果命令待检查点推送后：`python src/cyj/diagnose_b1_group_uncertainty.py --input-version 8dd672eb53571325f27342f4e545c0fa7bf06f24`。

## 接口、未验证项与合作

- 本次没有改变数学预测接口，`interfaces/cyj/CONTRACT.md` 仍为 v1.6 draft，`ready_for_Q3=false`。组级 bootstrap 即使完成，也只覆盖 B1 经典模型的条件不确定性，不能替代 Q/p 定标、Loss anchor、跨附件可比性或 Loss–Benchmark 传播。
- chm 清洁分支的 `Q2_BRIDGE.md` 表明当前无 `Q_z`↔`Q_score` 配对标定；其 p target panel 与 centered p、显式 `lambda_k(N)` 可用于结构联调，但 Q1 13 域 Loss 不可等同 B1 `val_loss`。chm+cyj 需共同冻结可识别的 Q 情景/映射及 Loss 口径、anchor、p 接法，无法识别则明确情景状态。
- zhh 的 C7 情景是外生 2048/8192/131072 Token，桥接实验留出 RMSE 7.060 不是 95% 区间。zhh `RESULTS.md` 与其旧 `CONTRACT.md`/成员记忆状态不一致，须 zhh 本人修订、集成人验收后消费。
- B1 near-exact Loss 来源、B2/B4/B5 与 B1 同尺度、A 附件 LFS 全库校验、chm/zhh 独立复现均未验证。公共记忆和 `interfaces/README.md` 如需更新交由集成人，不由 cyj 改写。

## 下一步

cyj 先按明确文件暂存本交接、本人记忆和审查文件，提交推送并核对 `git rev-parse HEAD` 与 `git ls-remote origin refs/heads/team/cyj-scaling`；再执行 80 次 bootstrap，检视接受/拒绝率、区间稳定性和参数边界，生成本人实验记录与接口草案更新；结果若不足以支持区间则如实标注。随后再审 B1 Loss 来源及 B4/B5 可比性。chm+cyj 联合做 Q/p/Loss 决定；zhh 修正其接口；集成人验收并汇总公共状态。
