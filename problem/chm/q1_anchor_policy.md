# Q1→Q2 配比 anchor 与敏感性面板建议

日期：2026-09-23
状态：基于 A4–A11 已验证 Ridge 结果；供 cyj 选择 Q2 的 p 接口，不替代其 Loss 口径判断。

## 原则

不能仅按“预测相关最高”选一个目标域，也不能仅按“领域名称能直接映射质量 Q”选一个目标域。Q2 同时需要：
1. 配比效应在 1M/60M/1B 上具有稳定迁移；
2. 如果要与 Q 联合解释，目标域和 7 个质量域之间最好存在 direct/near-direct 映射；
3. 最终 Loss 口径必须和 cyj 的 Q2 模型定义兼容。

因此采用“主 anchor + 映射敏感性 + 高稳定性敏感性”的面板。

## A. 跨尺度最稳候选

按三种真实尺度的最小 Spearman 排序：

| target | min rho | mean rho | 说明 |
|---|---:|---:|---|
| pile_cc | 0.8811 | 0.8920 | 三尺度最稳；A16 为 near-direct → commoncrawl |
| pubmed_central | 0.7996 | 0.8283 | 高稳定，但质量侧为 inferred |
| wikipedia_en | 0.7913 | 0.8503 | 高稳定；A16 near-direct/direct-like → wikipedia |
| stackexchange | 0.7718 | 0.8078 | 稳定且 A16 direct |
| uspto_backgrounds | 0.7587 | 0.8141 | 稳定，但质量侧 inferred |

若只考虑 p 的跨尺度代理能力，Pile-CC 是首选候选。

## B. 与质量 Q 直接衔接的候选

A16 direct：
- arxiv；
- github；
- stackexchange。

对应三尺度最小 Spearman：
- arxiv ≈ 0.7446；
- github ≈ 0.6721；
- stackexchange ≈ 0.7718。

其中 stackexchange 在“直接映射 + 跨尺度稳定”两方面最均衡。

A16 near-direct 中：
- pile_cc → commoncrawl；
- wikipedia_en → wikipedia；
- gutenberg_pg_19 → book。

其中 pile_cc 与 wikipedia_en 的跨尺度稳定性较强。

## C. 推荐敏感性面板

建议 cyj 至少比较以下 5 个 target：
- pile_cc：性能稳定主 anchor 候选；
- stackexchange：direct 映射中最稳；
- arxiv：direct 映射，且 A2 有扩展质量数据；
- github：direct 映射，且 A3 有扩展质量数据；
- wikipedia_en：near-direct 映射且跨尺度稳定。

如果 Q2 篇幅允许，再加入 pubmed_central 作为“高稳定但 inferred 映射”的对照。

## D. 不建议的做法

- 不用 13 个原始 Loss 的简单平均；
- 不把 pile_cc 自动等同于“总体质量”；
- 不因 arxiv/github 有扩展质量数据就默认它们代表全部 p 效应；
- 不把目标域 Ridge 系数解释为独立因果贡献；
- 不在 Q2 未确认 Loss 口径前冻结唯一 anchor。

## E. cyj 接口使用方式

1. 先用 `mixture_effect_ridge_v0.csv` 读取目标域 k 的零和系数；
2. 用 `mixture_reference_v0.csv` 构造中心化效应
   [
   m_k(p)=\beta_k^\top(p-p_{ref});
   ]
3. 若需要规模传递，使用 `mixture_scale_calibration_v0.csv` 和公共 eta=0.14537（CI 0.10787–0.18686）；
4. 主结果与上述敏感性面板至少 3 个 target 比较；
5. 最终论文说明 anchor 选择依据和目标域敏感性。
