# chm → cyj Q1 生产者接口 v1.5

日期：2026-09-24；版本：`chm.q1.v1`；生产者：chm；消费者：cyj（Q2/Q3）、zhh（需要 Q1 证据时）。状态：**chm 侧已在真实附件上复跑并校验，可直接消费的 A 侧接口**；跨 A/B 桥接尚未识别，也尚非 cyj 预测器或 `main` 集成成果。

唯一机器入口：`interfaces/chm/q1_interface_v1.json`，指向已审核的六个文件及 SHA256/行数。可调用入口：`src/chm/q1_interface.py` 的 `Q1Interface`。消费者用法、输入校验、返回字段、单位与示例见 [USAGE.md](USAGE.md)；需 cyj 定义的 B 侧接口见 [CYJ_REQUIRED_INTERFACE.md](CYJ_REQUIRED_INTERFACE.md)。

| chm 交付 | 数据/算法 | 状态与边界 |
|---|---|---|
| 质量 Q | A1 的 22 指标稳健定向，RPS/DSIR/model 家族内和家族间等权；7 域 `Q_z` 中位数及条件 bootstrap 95% 区间 | A 原生描述性坐标，可为负；不等于 B6–B8 `Q_score`；质量定义敏感性见 `outputs/chm/quality_review_v1/` |
| 17 域映射 | `direct` 3、`near_direct` 3、`inferred` 11 | `inferred` 不填 Q；`near_direct` 是代理，不是同总体观测 |
| 配比 p | 17 个命名非负权重，和为 1；A4 平均归一化配比作 `p_ref` | 调用时拒绝缺维/多维/非法和；系数是 Ridge 相对效应，不作因果解释 |
| 逐目标域效应 | 13 个目标域各有 `m_k(p)=Σβ_kj(p_j-p_ref,j)`，单位为 A 侧目标域交叉熵变化 | 不是绝对 Loss、B1 `val_loss` 或唯一总体 Loss；A6–A11 验证和逐域结果见清单 |
| 跨规模情景 | `(N/10^6)^(-η)`，`N` 是参数个数；η 点估计 0.14503317 | 1M/60M/1B 是已见规模；其他规模外推。1B 配方支持集不同，η 与区间均条件于固定 A4+A5 Ridge |

η 的目标域 bootstrap 95% 区间为 `[0.10686793, 0.18669841]`；目标域加校准行配对重抽样区间为 `[0.09756180, 0.20097672]`。质量域排序、CV、消融和图表证据分别见 `outputs/chm/quality_review_v1/`、`outputs/chm/local_recheck_v1/q1_regmix_cv_split_sensitivity.csv`、`outputs/chm/ablation_v1/` 和 `paper/sections/chm/figures/`。

**职责边界：**chm 定义和维护上述 A 侧数值、配比域顺序、目标域面板、参考配比及其验证范围。cyj 消费这套固定输入，并负责定义 B 侧 `Q_score` 的使用或跨坐标映射、B1 Loss 口径和 target anchor、跨 Loss 系数、最终 `N,D,Q,p→Loss` 预测器及 Q3 成本理论。无成对数据时这些映射应明确为情景或未识别，不能以讨论结论替代实测标定。完整限制见 [Q2_BRIDGE.md](Q2_BRIDGE.md) 与 [UNCERTAINTY.md](UNCERTAINTY.md)。

消费者应记录精确分支/提交 SHA、接口版本、manifest SHA、target、η 情景及是否外推。旧 `team/chm-data` 带有作废祖先，不得直接合并；只读取 clean integration 分支。历史 v1.2 在 `archive/` 仅供审计，不能作当前接口。
