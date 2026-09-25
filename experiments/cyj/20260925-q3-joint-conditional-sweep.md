# Q3：joint B7 条件资源配置扫描

本实验只回答「若 B7 半合成 Loss 候选及题面成本函数成立，支持域内数值解怎样变化」。它不声称真实大模型的最优配置。输入模型 SHA256 `c7426036164238d41b92ca08e9ca9087224aeb0c74554478b66093774a5b5b1a`；B7 原始文件 SHA256 `880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`。CHM 求解器固定为 `92e0592000cba58fca355a881dc59caadbd446b2` 的三个源码文件，逐文件哈希见 `q3_sweep_manifest.json`。随机种子 `20260925`，20 起点，30 点对数预算转变扫描及每个检测到的边界变化六次对数二分。

运行：使用 Python 3.12.14、NumPy 2.3.5、SciPy 1.18.1、Matplotlib 3.11.2，`python -B src/cyj/q3_joint_sweeps.py --starts 20 --transition-points 30`。Windows 本机 SciPy/Matplotlib 运行目录见 `problem/cyj/environment.md`；`q3_sweep_manifest.json` 记录精确脚本参数、数据和 CHM 模块身份。输出范围仅为 N∈[0.07,11.97] 十亿参数、D∈[10,600] 十亿 token、Q∈[Q0,1]，本次 Q0=0.5。2048/8192/131072 来自先前 C7 情景；其余上下文长度是 CYJ 外生敏感性网格，不能称为 C7 新测量。

## 数值结果

11 档预算 × 10 档上下文 × 3 成本族共 330 个网格点：321 个可行收敛、9 个因支持域最低成本高于预算而不可行。321 个解均通过记录的可行性与 KKT 相对残差检查；其中 237 个预算激活且至少一变量在界，3 个预算激活内点，81 个三变量上界饱和且预算未用尽。最后一类是 B7 支持域截断，不是预算足够后的真实最优饱和。条件预测区间按 joint 参数簇 bootstrap 加 N 轴 nested OOF 残差形成；该具体构造未独立校准覆盖率。

在 30000 token、指数质量成本族下，预算从 `1e19` 到 `1e24` 增加时：`1e19` 解约 N=0.07728、D=10、Q=0.55144；`1e22` 解约 N=4.51727、D=172.29308、Q=1；`1e23` 解达到 N=11.97、D=600、Q=1，实际成本约 `8.8484e22`，预算利用率 0.88484。固定预算 `1e22`、同族时，24576/30000/32768 token 对应 N 约 4.7450/4.5173/4.4129，D 约 179.77/172.29/168.83，Q 均为 1。题面 attention 与训练 FLOPs 相等的 30000 token 是成本项比例的代数点，并非这些配置的突变点。

检测 180 个活跃集变化括区；其中 `D_lower_active`、`D_upper_active`、`N_upper_active`、`Q_upper_active`、`support_saturated` 各 30 个，`Q_lower_active` 22 个、`N_lower_active` 8 个。部分情景从最低可行预算附近就已离开 Q0，故没有可识别的内部 Q0 离界转变点；不可补造阈值。30000 token、指数族的 Q 上界激活括区约 `(1.1615,1.1688)e20` FLOPs，完全支持域饱和括区约 `(8.7998,8.8554)e22` FLOPs。括区比约 1.0063；这只是按当前活跃标记容差的数值过渡，不是解析相变或真实系统阈值。

## 可复核文件与限制

`outputs/cyj/q3/q3_budget_sweep.csv` SHA256 `baa0ce59ddf5e69b603c4f07fcc15bf5da0076ea0a931c1e51c568162d586ce2`；带非有限值拒绝与机器精度级边界处理的重跑 `q3_transition_points.json` SHA256 `795f41180b67af81c840b59d4a2b7ae042e38c338a038a2a890e712023c6101a`，诊断脚本 SHA256 `37dd17f04086bfad4073dce1d1dea95395db96f0da61e442a47d8c87002dd958`。运行时仓库基线 commit 为 `c11629a032fdca8c0a366b732227711410b305d9`；本轮脚本增量由该 SHA256 和本轮后续 Git 提交共同固定。`q3_context_sweep.csv` 与 `q3_regime_map.csv` 是同一网格的视图，图见 `figures/cyj/q3_*`，不是新增独立数据。条件实验没有跨 A/B Loss 桥接，也没有新真实训练外测；`ready_for_Q3=false`。成本/偏导/KKT 证明见本人论文 `q3_theory.tex`，求解器数值 KKT 是必要条件检查，不是全局最优证明。
