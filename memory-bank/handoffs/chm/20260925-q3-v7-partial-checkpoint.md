# CHM Q3 v7 条件答案阶段性交接（2026-09-25）

## 当前状态

本检查点按用户要求封存当前工作，Q3 **尚未最终完成**。题面原文与仓库 DOCX 字节一致，SHA256 为 `bc99a72460fa3d947a442d502969a13212ce0ea092d827afdbbf3b55339da4c4`。Q1 v2 保持冻结，CHM 只消费 CYJ v7 的固定提交 `895ad42de670ece04ba7e781817a2126ec34327e`，没有修改 CYJ 源码。

用户确认的主口径是：沿用第一问声明的配比策略，在第三问的预算约束下配置 B 侧 `N,D,Q`；程序再给出联立配比的**条件性**检查。CYJ 的跨附件公式 `L_B7 exp(r_w(p))` 没有 A/B 成对实验标定，故不能称为经验识别的配比最优或有联合 95% 置信区间。正式 Q3 发布门禁仍关闭。

## 已封存文件与数值

- `src/chm/q3_v7_inputs.py`：核对 CYJ 提交、Q1 清单/凸包界、B7 系数哈希后才加载 v7。Q1 清单 SHA256 `c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`。
- `src/chm/q3_conditional_grid.py`：B7 声明支持域内优化，逐项核算训练、质量、注意力 FLOPs，使用 B7 降维浮点目标界及 KKT 检查；预算不可行时写显式状态。
- `outputs/chm/q3_conditional_v1/optimization.csv`：`1e19,1e20,1e22,1e24` 四档预算、2048/8192/131072 Token、三种质量成本，共 36 行；33 行可行。`1e19`/131072 Token 的三行不可行，B7 支持域最小成本 `2.255008e19` FLOPs。
- 同目录 `budget_scan.csv`、`transitions.csv`、`resolution_check.csv`：3849 个预算扫描点、42 个结构转移括区；最大括区相对宽度 `8.783704e-6`。161 点初扫后用所有区间中点复核，必要时加密至 641 点；发现短暂中间状态则拆成两个转移，支持域角点的瞬时预算等式合并为同一稳定状态。原始活跃集仍保留用于 KKT。
- 可行主网格最大浮点全局目标间隙 `9.999963e-8`，最大 KKT 相对违反量 `3.679868e-7`，最大相对超预算 `2.22e-16`。这些只衡量所声明 B7 模型内的数值求解误差，不覆盖模型、参数或 A/B 桥接不确定性。
- `src/chm/q3_joint_v7_check.py`：已重放 Q1 等权连续凸包、observed-512、direct 与 direct+near 配比候选；桥接强度为零时将配比标为未识别。**尚未**产出配比策略表、联立数值检查或桥接敏感性结果。

## 复现与验收

在仓库根目录，Python 3.12.14、NumPy 2.5.3、SciPy 1.18.1：

```powershell
& '.venv\Scripts\python.exe' -B -m unittest discover -s src/chm -p 'test_q3*.py' -q
& '.venv\Scripts\python.exe' -B src/chm/q3_conditional_grid.py
```

Q3 单测 55 项通过；CYJ v7 的 21 个冻结 fixture 通过。`.venv` 与 `.upstream/cyj-v7` 是本地忽略目录，后者需从上述 CYJ 精确提交重新建立只读依赖工作树。原始附件 2014 项 / 564436312 bytes 的仓库校验已通过。输出 CSV 由脚本重算；当前尚无完整输出 manifest，不能将这些文件冒充最终发布包。

## 下一步与限制

1. 以已签核的 Q1 四类候选填 `policies.csv`，对可行主网格逐一调用 CYJ v7，输出独立的 B-native Loss 与条件桥接 Loss；完成若干代表情景的直接联合 `N,D,Q,p` 检查、桥接强度/规模衰减/模型形式敏感性。
2. 写校验型条件发布器和 SHA 清单，更新 `paper/latex/sections/chm/q3_numerical.tex`。正文必须说明题面三种成本、三档预算、结构转移、`L_crit=30000` Token、C7 外部情景、不可行行与跨附件边界；旧 B1 诊断不能代替新 B7 结论。
3. 重跑题面与原始数据门禁、CYJ fixture、CHM Q3 测试、论文静态与可用的 XeLaTeX 验收。Q1 不改，Q2/Q4 只读。

## 远端同步

此前已核对远端 CHM 分支 `integration/chm-q1-clean-20260923` 与本地提交 `0a905a6f3d3dbf7080e0501e42e848cdc1e08857` 一致。之后的本地提交包含 `846d0b8` 和 `3c51abc`，**尚未确认上传**。HTTPS `github.com:443` 连接重置或超时；`ssh.github.com:443` 可达但本机 SSH 公钥未获授权。恢复网络后先 `git fetch origin integration/chm-q1-clean-20260923`，确认无远端分叉，再 `git push origin HEAD:refs/heads/integration/chm-q1-clean-20260923` 并用 `git ls-remote` 与 `git rev-parse HEAD` 比较；不得强推。
