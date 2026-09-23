# chm → cyj Q1 生产者接口 v1.5

日期：2026-09-24；版本：`chm.q1.v1`；生产者：chm；消费者：cyj（Q2/Q3）、zhh（需要 Q1 证据时）。状态：**A 侧描述与配比证据可消费，跨 A/B 数值接口未就绪**；尚非 cyj 预测器或 `main` 集成成果。官方数据与派生量的资格审查见 [OFFICIAL_DATA_REVIEW.md](OFFICIAL_DATA_REVIEW.md)。

唯一机器入口：`interfaces/chm/q1_interface_v1.json`，指向已审核的六个文件及 SHA256/行数。可调用入口：`src/chm/q1_interface.py` 的 `Q1Interface`。消费者用法、输入校验、返回字段、单位与示例见 [USAGE.md](USAGE.md)；需 cyj 定义的 B 侧接口见 [CYJ_REQUIRED_INTERFACE.md](CYJ_REQUIRED_INTERFACE.md)。

| chm 交付 | 数据/算法 | 状态与边界 |
|---|---|---|
| 质量 Q | 官方 A1–A3 提供 22 个质量信号，但**没有提供 `Q_z`**；chm 按稳健定向与三家族等权计算 7 域 `Q_z` 中位数及条件 bootstrap 95% 区间 | 自定义派生坐标，可为负；仅作 A 侧质量描述/排序，不是 B6–B8 官方提供的 `Q_score`；不能直接输入 B 模型 |
| 17 域映射 | `direct` 3、`near_direct` 3、`inferred` 11 | `inferred` 不填 Q；`near_direct` 是代理，不是同总体观测 |
| 配比 p | 17 个命名非负权重，和为 1；A4 平均归一化配比作 `p_ref` | 调用时拒绝缺维/多维/非法和；系数是 Ridge 相对效应，不作因果解释 |
| 逐目标域效应 | 13 个目标域各有 `m_k(p)=Σβ_kj(p_j-p_ref,j)`，单位为 A 侧目标域交叉熵变化 | 不是绝对 Loss、B1 `val_loss` 或唯一总体 Loss；A6–A11 验证和逐域结果见清单 |
| 跨规模情景 | `(N/10^6)^(-η)`，`N` 是参数个数；η 点估计 0.14503317 | 1M/60M/1B 是已见规模，**60M/1B 的本函数返回值仍只是条件 η 情景**；其他规模再增加外推。1B 配方支持集不同，η 与区间均条件于固定 A4+A5 Ridge |

η 的目标域 bootstrap 95% 区间为 `[0.10686793, 0.18669841]`；目标域加校准行配对重抽样区间为 `[0.09756180, 0.20097672]`。质量域排序、CV、消融和图表证据分别见 `outputs/chm/quality_review_v1/`、`outputs/chm/local_recheck_v1/q1_regmix_cv_split_sensitivity.csv`、`outputs/chm/ablation_v1/` 和 `paper/sections/chm/figures/`。

**官方字段优先与职责边界：**cyj 的质量项应首先使用赛题 B6–B8 自带的 `Q_score` 字段，并保留其**半合成**来源标签；chm `Q_z` 仅作独立的 A 侧描述与定性/排序敏感性。chm 维护上述 A 侧数值、配比域顺序、目标域面板、参考配比及验证范围。cyj 定义 B 侧质量项、B1 Loss 口径和 target anchor、跨 Loss 系数、最终预测器及 Q3 成本理论。无成对数据时不能把 `Q_z` 数值转成 `Q_score`，也不能用讨论结论替代标定。完整限制见 [Q2_BRIDGE.md](Q2_BRIDGE.md) 与 [UNCERTAINTY.md](UNCERTAINTY.md)。

消费者应记录精确分支/提交 SHA、接口版本、manifest SHA、target、η 情景及是否外推。旧 `team/chm-data` 带有作废祖先，不得直接合并；只读取 clean integration 分支。历史 v1.2 在 `archive/` 仅供审计，不能作当前接口。
