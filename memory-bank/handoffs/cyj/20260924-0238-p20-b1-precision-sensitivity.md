# cyj / P20 B1 显示计算量精度与拟合敏感性交接

状态：已运行、待集成人验收；Q2 未完成，Q3 预测接口仍不可用。当前分支 `team/cyj-scaling`，工作起点/已核远端 SHA `768cc7d9f4ad2f71ad5852b18f469feec211e4af`，已包含 `origin/main=a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`；本轮诊断代码/输入 SHA `351ea0e0eaeab0226550311d8fcb9a855cebcc2d`。本交接所含最终提交及推送 SHA 以 Git 历史和远端核验为准。

## 本次变更与范围

- 新增 `src/cyj/diagnose_b1_precision.py`、`src/cyj/tests/test_b1_precision.py`，输出 `outputs/cyj/diagnostics/b1_precision_sensitivity.json`；更新 `problem/cyj/b_data_audit.md`、`problem/cyj/classic_scaling_baseline.md`、`experiments/cyj/20260924-b1-precision-sensitivity.md`、`interfaces/cyj/CONTRACT.md` v1.5 和本人成员记忆。
- 只修改 cyj 自有文件。原始 B1、公共记忆、其他成员目录、原 Stage 1 审计结果和原 classic_fit 均未改写。公共进度建议由集成人核验后写入：8 个 C 相对 warning 可由 B1 显示精度解释，但 B1 Loss 来源警报仍在。

## 输入版本与命令

- B1 CSV：111,459 bytes，SHA256 `529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2`；`F_MANIFEST.json` SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`；source_manifest SHA256 `34e81dabf46302eebaac8551fa18d2e72acd0833b1cf0276690bee897f1323db`。
- 原 prepared SHA256 `2eb418f022c414db13af89d2177b2b90c62d3ad3b29300adf7fb1de570927704`；原 classic_fit SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`，原代码/输入 SHA `cf297a4ad47e235acf5a9b6e890a5df5e05b07e5`。

```powershell
git status --short --branch
git fetch origin --prune
git pull --ff-only
git rev-parse origin/main
$py = 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m py_compile src/cyj/diagnose_b1_precision.py src/cyj/tests/test_b1_precision.py
& $py -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
& $py src/cyj/diagnose_b1_precision.py --input-version 351ea0e0eaeab0226550311d8fcb9a855cebcc2d
Get-FileHash outputs/cyj/diagnostics/b1_precision_sensitivity.json -Algorithm SHA256
```

最后两条诊断/哈希命令连续运行两次，输出哈希稳定。正式脚本在运行前核对代码版本、B1 清单身份、原 fit 固定哈希与 prepared 哈希。

## 实测结果与证据

- 16/16 单元测试 PASS，Python 编译 PASS；B1 1,176/1,176 行显示 C 与 `round(0.006*N*D,4)` 相同。8 个相对偏差 >5% 的 run_id：8、9、10、11、162、163、316、317；最大绝对差 `4.994688e-05`，落在四位小数半单位内。
- 剔除这 8 行重拟合（seed 20260924、24 starts、1600 最大迭代）收敛；原全部样本 RMSE `0.0001465764192`，重拟合在全部行 RMSE `0.0001466067481`，最大绝对预测变化 `7.6651953e-06`。这是同源敏感性，不是独立验证。
- 机器结果 JSON schema v1，7,010 bytes，SHA256 `c7c8b346e4cdbec6034aead4f959ea7f60aa14b52ad6cd00169ea98033356fd7`，固定 LF 换行。解释与运行环境见 cyj 实验记录和 `problem/cyj/environment.md`。

## 未验证项、接口变化与下一步

- 未验证：B1 逐条 `val_loss` 的真实评估日志、语料/分词器和 checkpoint 映射；未舍入 FLOPs 的来源；近乎精确重构的生成机制。官方 [EleutherAI Pythia 仓库](https://github.com/EleutherAI/pythia)及[模型卡](https://huggingface.co/EleutherAI/pythia-70m)仅提供背景核对（2026-09-24 访问），不等于本地行级 provenance。
- `interfaces/cyj/CONTRACT.md` v1.4→v1.5，仅新增诊断产物及限制，没有改变原经典基线 JSON，也没有 validated predictor。`ready_for_Q3=false`，chm 不得启动 Q3 正式优化；zhh 不得把 Loss 当 Benchmark。Q_A 与 B6–B8 Q_score、Q1 13 域 Loss 与 B1 val_loss 均未建立同一尺度。
- cyj 下一步：优先查 B1 Loss 独立来源；按规模 bootstrap/预测区间，再处理 B2/B3 和 B4/B5 分层可比性。chm+cyj：联合冻结 Q mapping、Loss 口径/anchor/p 接法与不确定性；消费前记录 chm clean 分支精确 SHA、文件哈希、接口版本及 draft/validated 状态。zhh：提供 C7 外生上下文情景并在 Q4 传播 Loss–Benchmark 桥接误差。集成人：验收本诊断后决定公共记忆更新，勿把当前同源 RMSE 写成独立泛化结论。
- 全库原始数据验证仍被附件 A 四个 LFS 指针阻塞；本轮只按清单核验 B1，未重跑全库 2,014 文件校验。官方提交规则仍待集成人核对。
