# B1 按模型规模整组重抽样：经典 N-D 基线条件波动

日期：2026-09-24（北京时间）。状态：已运行的 B1-only 诊断，不是 calibrated prediction interval、独立泛化验证或 Q3 validated predictor。代码/输入提交 `8dd672eb53571325f27342f4e545c0fa7bf06f24`，公共 main 在本轮 fetch 时为 `a0932fd92b3a46cef8eb0bf563df1e6abc9396ef`。

## 输入身份、环境与复现命令

- 原始输入：附件 B1 `pythia_training_log_existing.csv`，运行时按 `data/raw/real_attachments/F_MANIFEST.json` 校验字节数/SHA256；脚本与依赖文件按 `--input-version` 指定提交核对。另核对 `outputs/cyj/classic/prepared_b1.csv` 与基线结果内部记录的 SHA、`outputs/cyj/classic/classic_fit.json` 的 SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead`。结果 JSON `provenance` 存完整文件身份及 Python/NumPy 版本。
- Windows 本机使用 Python 3.12.14（`C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`）。在仓库根目录运行 `& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' src/cyj/diagnose_b1_group_uncertainty.py --input-version 8dd672eb53571325f27342f4e545c0fa7bf06f24`；默认 `--replicates 80 --starts 8 --max-iterations 1200 --seed 20260924`。相同命令实际运行两次，输出 SHA256 均为 `e105dfd6b4ffc28f6d6fdf116173b0602b5d7ea5c2ec156f333be113ebeaadef`，94,180 bytes，LF。
- `& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s src/cyj/tests -p 'test_*.py' -q`：21/21 PASS；`-m py_compile src/cyj/diagnose_b1_group_uncertainty.py` 通过。无 SciPy，使用项目 NumPy 确定性多起点 Nelder–Mead 与原基线同一 Huber 目标。

## 协议与结果证据

B1 为 8 个 N 规模组、各 147 checkpoint。每次有放回抽 8 条整轨迹，重复抽中者赋不同 draw ID，使组等权目标保留抽样次数，而不是只留唯一 N；绝不随机拆 1,176 行。保留每次抽样的组、distinct 组数、拟合参数、收敛与触边状态。只把收敛且不触优化边界的重复纳入分位数：78/80 接受，2 个未收敛（第 5、59 次），无触边接受。结果文件：`outputs/cyj/diagnostics/b1_group_bootstrap.json`，schema v1，SHA256 `e105dfd6b4ffc28f6d6fdf116173b0602b5d7ea5c2ec156f333be113ebeaadef`。

条件于该 B1 数据/模型/优化筛选的参数 2.5%–97.5% 经验分位数：E `[1.689745706,1.689980083]`；A `[0.353863428,0.354069416]`；B `[1.240145710,1.240354213]`；alpha `[0.339867769,0.340099539]`；beta `[0.279852351,0.279949026]`。在 N=1.416184 B 参数、D=100 B token 的网格点，基线点预测 2.346082172，重抽样经验分位数 `[2.346068389,2.346096456]`。其余 8 个 N/D 组合及全部抽样在 JSON 中；网格点只演示原 B1 模型内的条件波动，不是新的观测或跨来源验证。

## 解释限制与下一步

仅 8 个规模簇、80 次重抽样且 2 次因优化未收敛而剔除；百分位端点不具备校准覆盖保证。即使极窄，也可能只反映同源确定性构造或强预处理；B1 `val_loss` 的逐行生成/预处理仍未知。该层不含模型形式、原始数据来源、B2/B4/B5 Loss 可比性、Q/p、13 域 Loss anchor、外推、C7、Loss–Benchmark 桥接不确定性。不得将这些分位数作为 Q3 正式预测区间或 Q4 总误差条。

cyj 下一步查 B1 Loss 来源与 B4/B5 同尺度证据，并与 chm 联合确定 Q 情景/映射、Loss 口径与 anchor/p；若不可识别则维持情景与 `ready_for_Q3=false`。zhh/集成人应在自有接口验收后消费，不得将本 JSON 自动并入公共结论。
