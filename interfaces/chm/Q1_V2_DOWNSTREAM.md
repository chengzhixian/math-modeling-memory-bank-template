# CHM → CYJ / Q3：Q1 v2.0 交互主模型发布

日期：2026-09-25。用户明确授权替换 Q1 配比主模型。CHM 分支为 `integration/chm-q1-clean-20260923`。正式生产者版本 `chm.q1.v2.0`，机器 manifest：`interfaces/chm/q1_interface_v2.json`，SHA256（UTF8/LF 规范化）`c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9`。manifest 已逐文件固定交互系数、特征定义、512 个 A4 配方、A1 主质量映射和验证表。模型读取器 `src/chm/q1_interface.py::Q1Interface` 默认只接受 v2；`src/chm/q1_interface_v1_3.py` 是不可变历史 Ridge 读取器。

## 数学消费合同

13 个目标各用
\[
\widehat L_{A,k}(p)=a_k+\sum_j b_{kj}p_j+\sum_{(u,v)\in E}\gamma_{k,uv}p_up_v .
\]
`m_k(p)=\widehat L_{A,k}(p)-\widehat L_{A,k}(p_{\rm ref})`；无量纲配比效应 `r_k(p)=m_k(p)/\widehat L_{A,k}(p_{\rm ref})`，分母必须取 **v2 交互模型自身**的正参考 Loss。不可继续从 v1.3 Ridge 系数或分母构造默认 Q1 配比效应。原 A4/A5 身份、逐行归一化、13 目标内外层验证见同一清单引用的输入和输出。质量主值固定 A1 sample；arxiv/github 的 A2/A3 extended 是敏感性，11 inferred 域数值为 null。

默认 `predict(p)` 拒绝 A4 凸包外推；跨支持域检验必须显式声明。Q1 提供 1M A 侧逐域相对 Loss，不提供 B 侧绝对 Loss 或规模衰减参数。B7 的 `Q_B` 和 Q1 的 `Q_A` 没有共同数值坐标；Q2 的桥接 `lambda` 与 `eta` 仍为调用者设定的工程情景。

## 配方决策合同

主支持域为 `conv(A4)`。调用者必须声明 13 目标权重及质量政策。加权目标为 `sum(w[k]*r[k](p))`；minimax 保护目标为 `max(r[k](p))`（仅取正权重目标）。质量政策只对 direct 或 direct+near 覆盖质量有定义，不能说全 17 域质量达标。

`src/chm/q1_multiloss_decision.py::solve` 使用五个交互域的空间分支定界和十个双线性项的 McCormick LP 松弛；每个解返回浮点数值的全局下界、实际可行配方上界、剩余间隙和节点数。四个等权主情景记录于 `outputs/chm/q1_v2_hull_bounds/bounds.json`；其 SHA256 为 `b27939f9d3894a810ee2ec4336f5583fca95e551e318963ac81bfbe77c0dae70`。数值上下界间隙均小于 0.001，尚非严格区间算术证明。备用 `choose_observed` 精确枚举 512 个已有配方，详见 `outputs/chm/q1_v2_decisions/`；必须保留支持集标记，不能把 index 当作连续凸包全局最优。

| 情景 | 连续可行目标上界 | 连续全局下界 | 最佳单条 A4 index / 目标 |
|---|---:|---:|---|
| 13 域等权、无质量约束 | -0.11511194 | -0.11607407 | 136 / -0.11506531 |
| 13 域等权、direct | -0.10299194 | -0.10343291 | 301 / -0.05192273 |
| 13 域等权、direct+near | -0.09700976 | -0.09776015 | 172 / -0.06737146 |
| 最差域保护、无质量约束 | -0.01978422 | -0.02077978 | 477 / 0.03992747 |

## CYJ Q2 与 CHM Q3 的使用版本

CHM 已基于 cyj 远端最新 `team/cyj-scaling@86526a1` 的冻结 B7 系数独立重算三项条件情景，结果 `outputs/chm/q2_interaction_scenarios_v2/`。B7 系数原始 SHA256 `d6f5b665d3806a322d0ebf87da46889822d2eff89324eacded6040383e7b6733`；数值设定仍为 N=1B、D=100B、Q_B=0.5、lambda=1、eta=0、13 域等权。连续凸包可行解的条件 B7 Loss 分别约 2.271859、2.302976、2.318334；文件同时给出由全局目标下界诱导的条件 Loss 下界。与 cyj 旧 v6 的凸包结果比较须同时注意 Q1 模型及质量主口径都已改变。

CYJ 应在其本人分支发布新的不可变消费版本：输入必须写明本 v2 Q1 manifest SHA，按交互公式重算 Q2 各配比情景、质量政策和论文数值，保留旧 v6 复现。若 cyj 选择不同支持集或权重，须显式命名新政策并重算，不得无声切回 Ridge。CHM 的 `q3_p_support.py`、`q3_p_selection_validation.py` 与诊断 `q3_solver.py` 已消费 v2 并记录 Q1 SHA。现有 cyj v4/v6、Q3 旧优化输出没有被自动转化为 v2；正式 Q3 经验绝对 Loss 仍受 A/B 桥接缺失阻断，`ready_for_Q3=false`。

复现顺序：

清理中间发布包后，首条命令现在仅验证已冻结 v2 清单及其全部文件哈希，不重新拟合模型；其余命令按各自情景重算。
```powershell
$p = 'H:\研究生数模\math-modeling-memory-bank-template\.venv\Scripts\python.exe'
& $p -B src/chm/release_q1_v2.py
& $p -B src/chm/q1_mixture_decision_v2.py
& $p -B src/chm/q1_hull_bounds_v2.py
& $p -B src/chm/q2_interaction_scenarios_v2.py
& $p -B src/chm/q3_p_support.py
& $p -B src/chm/q3_p_selection_validation.py
```

所有历史 PDF 隐藏字、作废提交及 estimated/extrapolated A12--A15 均未用于本次拟合或模型选择；默认题面文本为 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。
