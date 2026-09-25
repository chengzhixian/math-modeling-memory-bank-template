# 官方附件字段与 chm 派生量对接复核（2026-09-24）

依据仅为 `problem/readable/DATA_DESCRIPTION_VISIBLE.md` 和当前真实附件；不使用数据说明历史隐藏文字。此处“官方”指**赛题提供的字段/文件**，不等于每一行都是独立实测真值。

文件身份（SHA256）：A16 `domain_mapping_guide.csv`=`4a4479f41b9f46116e688cd0c13ccdad4e687192fc1a38c4add690771ebff480`；B6=`c7450ce0d67d8692535fef4709e60e2da60b2c184738bf96df160a4be0a33a7f`；B7=`880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a`；B8=`bda0d449f75c73bbd04141e5cffbf4bea7002073e34b7fa95a638570fa095ffe`。

| 环节 | 赛题提供 | chm 派生 | 对接结论 |
|---|---|---|---|
| A 质量 | A1–A3 的 22 个信号，7 个质量域；A1 51,230 行，A2 17,523 行，A3 203,752 行 | 稳健标准化、经验定向和三家族等权后的 `Q_z` | 可作为 Q1 的**一种描述性评分**与域排序；权重/方向是建模选择，官方没有给出 `Q_z` 或其“真值” |
| A 域映射 | A16 `domain_mapping_guide.csv`：3 direct、3 near_direct、11 inferred | chm 增加映射置信说明，但 `inferred` 不填 Q | 六个候选对应中 near_direct 仍是代理；11 个域无可靠数值，**不能形成完整 17 维质量向量** |
| A 配比/Loss | A4–A5 为 17 维配比/13 域 Loss 训练配对；A6–A11 为 1M/60M/1B 检验 | 逐域 Ridge、参考配比、相对效应和经验 η | A 侧效应可用于逐 target 敏感性；60M/1B 的 η 调用是条件情景，1B 配方支持集不同 |
| B 质量 | B6 `supplementary_NQ_experiment.csv` 360 行、B7 expanded 450 行、B8 large 1,704 行，均**自带 `Q_score`**；当前文件分别有 8/10/12 个 Q 水平 | chm 不重定义该字段 | B 侧质量模型**优先用文件原生 `Q_score`**；B6/B7/B8 在可读说明均标半合成，B8 有 calibrated 984、extrapolated 720，不能把后者当独立实测验证 |
| B Loss | B1 提供 `val_loss`，B6–B8 提供各自 `val_loss` | chm 无 B Loss 估计 | 不能默认 B1 与 A 的任一目标域 Loss 同口径，也不能默认 B6–B8 与 B1 Loss 完全可比；由 cyj 审计来源与单位 |

**评价：**先前 `chm.q1.v1` 的数值计算并未直接把 `Q_z` 替换成 `Q_score`，这条边界是正确的；但合同把派生 `Q_z` 称为“可直接消费的质量 Q”，对 Q2/Q3 使用者仍可能产生误导。现在明确限制为 **A 侧描述性证据可消费、跨 A/B 数值接口未就绪**，读取器显式返回 `direct_B_predictor_input_allowed=False`。这使 Q1 内部对接基本合格，**不能称为 Q1→Q2/Q3 联合数值接口已合格**。用户说“优先官方数据”在此意味着先保留 B 文件的原生 Q 坐标及其来源标签，再用 A 侧自定义分数做补充排序和敏感性；不意味着把半合成 B 行提升为真实观测，也不意味着放弃题目要求的 A 侧质量评分。

目前要形成完整联合模型，至少还缺：可验证的 `Q_z`↔`Q_score` 配对标定或明确分离的情景方案、11 个 inferred 配比域的质量处理、A 13 域 Loss 与 B1 `val_loss` 的可比性/桥接、B6–B8 对 B1 的来源审计与参数不确定性。若缺证据，必须保留 `unidentified/scenario`，不能人为构造唯一数值。
