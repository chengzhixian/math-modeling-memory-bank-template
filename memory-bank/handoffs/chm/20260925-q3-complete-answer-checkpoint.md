# CHM Q3 完整答卷检查点（2026-09-25）

用户纠正先前过严门槛：赛题明确允许把独立 A/B 实验通过可检验假设统一，第三问不要求成对实验或联合 95% 区间。目标改为在本人仓库把 CYJ 正式 Q3 理论与 CHM 数值答案直接融合，完成假设稳健性，查权威公开真实实验验证可验证部分；暂不处理 Q4/集成人。CYJ `team/cyj-scaling@046abae` 只读 fetch 并读取 `paper/latex/sections/cyj/q2.tex`、`q3_theory.tex`；未修改 CYJ 分支或文件。正式模型仍锁定生产者 `fd2dbb3`、验收主体 `615c078`，Q1 v2 不变。

新增 `src/chm/q3_v8_assumption_sensitivity.py`，在 `q3_conditional_v8.py` 的固定配方求解中以原 CYJ v8 `evaluate` 敏感性模式实施质量映射斜率和配比桥强度，不修改 CYJ 生产者。九个单因素场景：主情景、Q0=0.45/0.55/0.60/0.65、质量映射斜率 0.5/1.5、配比桥 lambda=0/2。每场景官方 27 格，另 8192 Token/幂成本 161 点扫描及相对宽度 <1e-4 的转移括区。主情景 24/27 可行，各压力情景亦 24/27；Q0=0.60 后配方 477 失去质量资格，低预算改选 475，Q0=0.65 改选 172；斜率 1.5 低预算改选 97，lambda=0 时所有 24 可行格的配方均翻转。扫描数据和摘要在 `outputs/chm/q3_conditional_v8/assumption_*`，不是置信区间。

权威公开来源筛选见 `experiments/chm/20260925-q3-public-external-validation.md`：RegMix 官方表与附件 A 原始来源相同，不能再次当独立外测；Data Mixing Laws 与 DCLM 缺本题可对齐 Q/p/Loss 键。`mlfoundations/scaling@a003c4913793ac2ae7ef87b28ecb562955d026d5` 有 104 个作者公开真实训练模型，42 个落在 v8 共同 N/D 支持域，每 C4/RedPajama/RefinedWeb 训练语料 14 个。冻结 B1 对共同 Paloma C4 en Loss 的组内 Spearman=0.973626/0.986813/0.973626；训练成本代理真正限制候选的 1e20/1e21 六组，离散选择 5/6 与实际最佳一致，RefinedWeb 1e21 失败，实际 Loss regret=0.070515。只验证 N/D 排序与训练成本子结构；外部记录无 A4 17 域 p、同尺度 Q，不可宣称完整跨附件真实四变量最优。原作者 104 JSON 只读 clone 在忽略 `.upstream/scaling-external/`，逐模型与预算结果在 `external_nd_*`。

Q3 融合答卷已写 `outputs/chm/Q3_FINAL_ANSWER_V8.md`、`paper/latex/sections/chm/q3_numerical.tex` 与独立入口 `paper/latex/q3_final.tex`，涵盖 CYJ 映射、B1/B7 参数、边际条件、CHM 官方三预算表、转移、假设压力和公开外测。独立 PDF `paper/latex/output/chm-q3-v8-final.pdf` 为 8 页，XeLaTeX/BibTeX 引用、缺字、溢出门禁通过，已逐页渲染审查；仅 Q3，无 Q4 占位。新 CHM v8 单测 9/9 通过；manifest 需在本次最后代码/论文改动后重新发布并校验。此文件是额度同步检查点，后续若发现内容或排版缺陷再小批次修订；完整本轮提交与远端 SHA 以实际推送核验为准。
