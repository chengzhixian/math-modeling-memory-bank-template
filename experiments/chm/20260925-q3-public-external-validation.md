# Q3 公开真实实验筛选与外部检验（2026-09-25）

## 检验目标与选择标准

用户要求查找权威公开数据，尽可能验证跨附件最优配置。完整检验至少需要同一可比实验体系中记录模型参数量 $N$、训练 token $D$、可映射到 A4 17 域的配比 $p$、与 B7 同尺度或可标定的质量 $Q$，以及相同验证口径的 Loss；并在预算下有多个竞争候选。缺字段或损失口径不同，只能验证相应子结构，不能把跨项目数值强行拼接。

| 作者公开来源 | 可核实内容 | 与 Q3 的关系 | 决定 |
|---|---|---|---|
| [RegMix 官方仓库](https://github.com/sail-sg/regmix) | 1M/60M/1B 配比及验证 Loss；17 域 | 正是赛题 A4–A11 的原始来源，`data/raw/real_attachments/source_manifest.json` 可核 | 不当作新外测；A6–A11 已用于 Q1 模型形式选择 |
| [Data Mixing Laws 官方仓库](https://github.com/yegcjs/mixinglaws) | 多域配比与不同规模训练的实验数据 | 配比域集合、质量定义、验证坐标与 A4/B7 不一致 | 可作方法背景，不可数值宣称验证本题配方 172/477 |
| [DataComp-LM 官方仓库](https://github.com/mlfoundations/dclm) | 标准化规模档次与数据筛选/混合后的评测 | 公开档次有 $N,D$，质量是具体筛选方案或下游评测，未给本题 Q1/B7 同尺度代理和 A4 配比 | 无完整 Q3 对齐键，不据此拼出“真实最优” |
| [Language models scale reliably with over-training 官方仓库](https://github.com/mlfoundations/scaling) | 104 个实际训练模型，C4/RedPajama/RefinedWeb 三训练语料；每模型规模、训练 token 与同一 Paloma C4 验证 Loss | 可在同一语料族内独立检查 B1 的 $N,D$ 排序与离散预算选择；没有 17 域配比和本题质量坐标 | 执行有限的真实 $N,D$ 外部检验，明确不能检验跨源桥 |

数据引用的是作者仓库及仓库内实验记录，不重新拟合 v8，不从文献图估读数字，也不下载大文本语料。公开元数据固定在 `mlfoundations/scaling@a003c4913793ac2ae7ef87b28ecb562955d026d5`，本机只读 clone 保存在忽略目录 `.upstream/scaling-external/`。其 README 明示 104 个、三个训练集和 8 个 Loss 评测；原始模型 JSON 中 `hyperparameters.params/tokens` 和 `results[].val_data/loss` 逐行可核。

## 实施方法与结果

`src/chm/q3_external_nd_audit.py` 固定作者提交、文件数与共同 Paloma C4 en 验证键，仅保留 CYJ v8 的 $N\in[0.070542,11.965825]$ B、$D\in[10,299.893]$ B，共 42 个实际训练模型，每语料 14 个。用冻结 B1 五参数分别计算 $L_0(N,D)$，只比较同一训练语料内的排序；Pythia 和 OpenLM 的绝对 Loss 坐标不相减或报告 RMSE。三语料的 Spearman 依次为 C4 `0.973626`、RedPajama `0.986813`、RefinedWeb `0.973626`。

成本只取可比较的训练代理 $6ND$ FLOPs。诊断预算 $10^{20}$、$10^{21}$ FLOPs 在每语料的 14 个候选中分别留下 9、13 个；按 B1 最小 Loss 选择与同一验证集实际最小 Loss 选择，共 **5/6 组一致**。例外为 RefinedWeb 的 $10^{21}$ FLOPs：B1 选 `rw_original-d=1024_l=24_h=8-32.0`，实际最优为 `rw_original-open_lm_1b-1.0`，观测 Loss regret `0.070515`，不得隐藏。$10^{22}$ FLOPs 下 14 个候选均在预算内，三语料选择 3/3 一致，但预算已不筛选候选，不能增加预算最优的强证据。$10^{19}$ 每语料仅 1 个候选，亦不具辨别力。完整逐模型、预算表与哈希见 `outputs/chm/q3_conditional_v8/external_nd_audit.json`。

## 结论限制与下一可检验条件

此检验支持“B1 参数/Token 效应在另一个公开真实训练体系中有较好的**排序迁移**”，同时 1/6 的预算选择失败显示迁移并非无误。它**没有验证** CYJ 的 $Q_A\mapsto Q_B$、A 侧相对配比乘子、三种质量投入成本、注意力成本，也没有证明 Q3 配方 172 或 477 在真实训练中最优。若要检验完整主张，公开实验必须提供可比的 17 域配比或可明确映射的训练域、质量观测与相同口径的验证 Loss，并有预算内多候选；目前核查的权威来源未同时满足这些字段。赛题允许明示假设，因此完整经验外测不是交出 Q3 条件模型解的前提。
