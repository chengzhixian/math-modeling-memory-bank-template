# P20：B9/B10 大模型外推证据审计

状态：已运行的数据结构与来源角色审计；**不是**外部预测验证。执行于 2026-09-24（北京时间），分支 `team/cyj-scaling`，工作起点 `b54310c67be84f1cac932021ebc7955e540f93c9`（合并 `origin/main@670d726` 后）。

## 输入与用途

可信输入为当前 F 题 DOCX（SHA256 `bc99a72460fa3d947a442d502969a13212cebff3b55339da4c4`）、可见数据说明 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`、B9/B10 原始 CSV 与 `data/raw/F_MANIFEST.json`（SHA256 `3377a36c5f6fcabb79abca5fe5621047a3abd9be6dffd9491bc8c651b19f903f`）。当前清理版数据说明 PDF SHA256 `daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`，仅作视觉核对。历史隐藏文字及作废建模提交均不作依据。

| 题目需要 | 数据/变量 | 性质与角色 | 证据能力 |
|---|---|---|---|
| 大模型规模情景 | B9 `model_name,N_params_B,D_tokens_B` | 来源汇编的模型元数据；N/D 单位十亿；仅情景与支持域清单 | 描述性，不能提供实测 Loss |
| 大模型 Loss 外推参照 | B10 `family,N_params_B,D_tokens_B,val_loss` | 数据说明明确列作“估算”；压力/外推参考，不进入训练或独立测试 | 不能给出独立真实泛化误差 |
| B1 经典曲线比较 | `outputs/cyj/classic/classic_fit.json` | B1 draft 五参数曲线，SHA256 `9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead` | 只描述数值接近程度；无 B1↔B10 共同 Loss 定义证明 |

B9/B10 原始 SHA256 分别为 `ee794c1c586ed33c485a9eb9a2a3d993790402b63297e9b2765a1387930e940e`、`a240e210c5b37444356c28eea96c6cc36be79c29baae1621c2e08aff727ccfeb`。脚本先按完整性清单核对字节与哈希，检查列名、名称唯一、N/D/Loss 正有限以及 B9 的 D=0 合法缺省，再比较行。

## 实际执行

```powershell
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B src/cyj/audit_large_extrapolation.py
& 'C:\Users\muyehuangyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest discover -s src/cyj/tests -p 'test_*.py' -q
Get-FileHash outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json -Algorithm SHA256
```

Windows / Python 3.12.14；此审计仅用标准库，无随机步骤。首个命令连续两次得到同一输出 SHA256 `53977e436fed3afabd5cb6ba908ff6d1f90a4cd42873209c5ba0d888db311068`；脚本 SHA256 `d44ff78157aa535a3a1c334207a67deeef2566a601445b93b8d10544f88c9c16`。现有 cyj 测试 37/37 通过。结果 JSON 在 `outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json`，其中固定原始文件、manifest、B1 fit 与脚本哈希。

## 结果与可识别性

- B9 有 132 行，B10 有 128 行；B10 每行按原始模型名及 N/D 与 B9 唯一精确匹配。B9 独有四个模型的 D 均为 0，B9 有 11 行 FLOPs 缺失。
- B10 的 N=100–10000B，128/128 行超过 B1 的 11.965825B 上界。D=0.1–36000B，其中 102 行超过 B1 的 299.893B 上界，3 行低于其 0.134B 下界。即使某些 D 落在 B1 范围，所有 B10 点仍是 N 外推。
- B10 仅 119 个唯一 N/D 坐标；5 个坐标组共多出 9 行，组内预估 Loss 全部相同。这与仅按 N/D 构造的估算一致，但不能由此反推出精确生成公式。
- 把 B1 draft 曲线代入 B10 N/D，数值差的 RMSE=0.0011047668、MAE=0.0006301262、最大绝对值=0.0052006305。**这些只是两组估算/拟合数的差异，不是预测误差或独立验证分数。** B10 生成机制和 Loss 坐标未证实，数值接近也不建立它们的独立性。

变量可识别性：B9 的 N/D 是记录字段（个别缺省）；B10 的 `val_loss` 是估算结果，不是观察；B1 五参数仅在 B1 口径与支持域内条件估计。B10 没有数据可识别真实大模型 Loss 与 B1 Loss 的跨来源桥接，也不能识别 Q、p 或外推误差。当前结论等级仅 L1 描述性。反事实从零看 B9 表头没有 Loss，B10 的“估算”标签又未给逐模型独立评估记录，所以最多建立外推情景清单和估算一致性，不能形成 L2 绝对预测或 L5 外推有效性主张。

## 限制与交接

本轮没有改变 `cyj.q3.v1` 或 `cyj.b7_quality.v1` 接口；`ready_for_Q3=false` 继续保持。B10 不作模型选择、参数拟合、bootstrap、held-out 测试或论文中的“真实外部验证”；若需要图表，只能明确写“估算参考/外推压力情景”。B4/B5 的绝对 Loss 可比性仍为 `not_established`。

`git lfs pull` 本次等待后无进展，已中止；随后 `./scripts/verify_raw_data.ps1` 仍因 A 侧四个 LFS 指针报告 size mismatch。B9/B10 本次独立按清单哈希核对通过；全库 2,014 文件完整性**未通过**，由取得 LFS 实体数据的成员重跑。cyj 下一步继续核查 B1 行级评测来源及 B4/B5 可比性，并做 B7 选模后验证；chm/zhh 消费 B10 时保留 estimated 与 extrapolation 标签；集成人验收后再更新公共记忆。
