# CHM Q3 v8 条件解交接（2026-09-25）

## 接续与所有权

本人分支 `integration/chm-q1-clean-20260923` 已从远端 `65bcb01` 接续 v7 半成品；CYJ `team/cyj-scaling` 的 v8 精确生产者提交 `fd2dbb3`、验收主体 `615c078` 仅作只读导出到忽略目录 `.upstream/cyj-v8/`，CYJ 分支和跟踪文件未改。此前的迁移检查点为 CHM 已推送并核验的 `0358def`。v8 以后 CYJ 新增 `79a595a`、`046abae` 只涉及论文和交接，未改变本轮锁定模型输入。Q1 冻结生产者 `chm.q1.v2.0` 不动。公共六记忆、CYJ/Q4 文件均未由本人更新。

## 题面条件答案与主要数字

Q3 按原题三预算 `1e19/1e22/1e24` FLOPs、三种质量成本、C7 三上下文 `2048/8192/131072` Token 实施，附加 `1e20` 过渡预算。主质量代理 `Q_B_proxy=phi(Q_A(p))` 是 v8 未实证标定跨源情景，不是独立的真实 B 质量控制。因 Q1 无约束主配方 136 的代理质量约 0.38578 < 本轮假设 `Q0=0.5`，固定策略合法改用 CYJ Q2 v8 已发布且满足 Q1 direct+near 政策的 A4 配方 172，质量代理 0.671360765。进一步对合格的 87 个 A4 已观测配方离散枚举，各配方的 N/D 子问题通过成本消元与 `log N` 数值凸性下界求解；不能把该有限枚举称为连续配比全局最优。

`outputs/chm/q3_conditional_v8/` 已有固定策略、离散联立、独立原生 B 质量敏感性三张 36 格表。分别 30/36、33/36、33/36 可行。`1e19`、131072 Token 在三种质量成本下不可行；低预算四个可行离散联立格选择配方 477，其余可行格选择 172。主展示的 `1e22`、8192 Token、幂成本选 p172、N=6.660655431 十亿参数、D=193.873531189 十亿 Token、Q 代理=0.671360765、条件 Loss=2.094421151；`1e24`、8192 Token 已到共同支持域角点，预算利用约 2.762%，不得外推继续增加 N/D 的收益。独立原生 B `Q` 敏感性在上述中预算格取 Q=1、N=5.258740894、D=222.936279965、条件 Loss=2.023222216，不解释为真实干预收益。

预算扫描对每个上下文/成本组合取 161 个对数点，固定和联立各 1449 行，数值细化得到 33 和 49 个状态转移括区，最大相对宽度 <1e-4；8192 Token、幂成本配方 477→172 位于 `[1.610535,1.610648]e19` FLOPs。131072 Token 的短暂配方状态被 81 点粗扫描漏过，故 161 点扫描亦不宣称穷尽更窄状态。题面代理成本给 `C_attention/C_train=L/30000`，临界 30000 Token 只表示两项成本相等，不是能力实测阈值。

## 产物与复核

- `src/chm/q3_conditional_v8.py`、`q3_v8_transition_scan.py`、`q3_v8_publish.py`、`plot_q3_v8.py` 和 `test_q3_conditional_v8.py`；精确输入装载 `q3_v8_inputs.py` 在首个检查点提交。`manifest.json` 封存 CYJ/Q1/B1/B7 身份、输出/代码/论文图文哈希、单位、数据角色和未校准状态。
- `paper/latex/sections/chm/q3_numerical.tex` 与 `paper/latex/figures/chm/q3_v8_power_8192.png` 已写为条件性 Q3 数值答案。审查记录 `experiments/chm/20260925-q3-v8-problem-answer-audit.md` 完成题面逐项字段追溯、数据角色、识别边界、数值审查和从零反证。v7 只留历史，不再作为 v8 主论文数字。
- CYJ v8 冻结 18/18 fixture 通过；CHM Q3 v8 新检查 7/7 通过，其中独立 SLSQP 对主中预算 Loss 差 <1e-8。`build_safe_pdf_context.py --check`、`check_ai_reading_rules.py`、原始 2014 文件 SHA256 验证通过。当前全稿 XeLaTeX/BibTeX 22 页引用/缺字/溢出门禁通过，Q3 第 19–22 页渲染审查通过；诊断 PDF 只存忽略 `.build/`，因 CYJ Q3 理论与 ZHH Q4 仍有占位段，不作为终稿。旧 `paper/latex/check_draft.py` 硬编码 Q1 五图，而冻结 Q1 已七图，故此共享静态检查失败，与本次 Q3 无关，未擅自改它。

## 结论等级与交给集成人的事项

本产物是题面代理成本、CYJ v8 半合成质量扩展、指定 Q0/映射和有限配方集内的**条件数值解**。A/B 没有成对干预观测，无法识别质量映射、配比桥幅度及二者重叠贡献；没有联合 95% 预测区间、真实大模型训练最优、Benchmark 因果收益。B7 同源 CV 不是独立外测，C7 131072 Token 支持稀疏。集成人可引用本轮官方三预算的表和条件结论，须从 CYJ 最新分支接入正式 Q2/Q3 理论、从 ZHH 接入 Q4 后重编全稿，并复核全稿措辞与篇幅。本人不修改他人段落和公共六记忆。

复现顺序：精确导出 CYJ `fd2dbb3` 派生文件至忽略 `.upstream/cyj-v8/`，运行 `python -B src/chm/q3_conditional_v8.py`、`python -B src/chm/q3_v8_transition_scan.py`、`python -B src/chm/plot_q3_v8.py`、`python -B src/chm/q3_v8_publish.py`，最后 `python -B -m unittest src.chm.test_q3_conditional_v8 -q`。提交 SHA 和远端一致性以本轮实际推送校验记录为准。
