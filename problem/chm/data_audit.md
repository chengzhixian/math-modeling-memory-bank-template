# Q1 附件 A 首轮数据审计

日期：2026-09-23（北京时间）
角色：chm
工作起点：`0bf6caf723d096c3393577b9caef668b6d3ff816`
状态：进行中

## 已核对范围

本轮直接读取 `team/chm-data` 的 A4–A17 普通 Git 文件，并核对 A1–A3 的 Git LFS 指针。没有读取、恢复或引用任何已作废隐藏文字及其衍生结论。

## A1–A3 LFS 对象

| 文件 | LFS SHA256 | LFS 声明大小 |
|---|---|---:|
| A1 `slimpajama_quality_signal_sample.jsonl.xz` | `14a4eeec4c7d98efd78942ddd9c1329640527f2108e73227be449bc1a8dbe579` | 103,349,792 B |
| A2 `arxiv_part-6777d8857c6e-000486.jsonl.xz` | `ae1e3399f84f605d994fc60b46984d742e14abb3355d8e7a91822eae1b99e16a` | 3,652,724 B |
| A3 `github_part-6777d8857c6e-000275.jsonl.xz` | `7af069c71c6027a10f2013cc14dd9d5d17855c264734f69c955544ff6cff7382` | 37,618,172 B |

当前读取环境只能得到 LFS pointer，不能在本轮环境中解压全文。因此 A1–A3 的 22 维质量评分、相关矩阵和域级 Q 尚未运行；必须由本地完整 clone 后执行 `git lfs pull` 再继续。此项为明确阻塞，不得写成已完成。

## A4–A15 配比/Loss 成对审计

| 数据组 | 配比行数 | Loss 行数 | 配比维数 | Loss 维数 | index 成对数 | Loss 缺失 | 配比和最大绝对偏差 |
|---|---:|---:|---:|---:|---:|---:|---:|
| train 1M | 512 | 512 | 17 | 13 | 512 | 0 | 0.004 |
| test 1M | 256 | 256 | 17 | 13 | 256 | 0 | 0.003 |
| test 60M | 256 | 256 | 17 | 13 | 256 | 0 | 0.003 |
| test 1B | 64 | 64 | 17 | 13 | 64 | 0 | 0.002 |
| est 10B | 63 | 63 | 17 | 13 | 63 | 0 | 0.002 |
| est 70B | 63 | 63 | 17 | 13 | 63 | 0 | 0.002 |

配比行和均接近 1，偏差为千分位级舍入误差。后续建模应在读取时检查并记录是否重新归一化，但原始文件不得改写。

另外已观察到：
- `test_mixture_1m.csv` 与 `test_mixture_60m.csv` 的 Git blob SHA 相同，说明两种模型尺度使用同一组 256 个测试配方；
- `est_mixture_10b.csv` 与 `est_mixture_70b.csv` 的 Git blob SHA 相同，说明两个外推尺度使用同一组 63 个配方；
- 17 个训练域只有 13 个直接验证 Loss，缺少 `nih_exporter`、`enron_emails`、`europarl`、`philpapers` 的同名验证 Loss。

## A16 域映射审计

17 个配方域中：
- direct：3 个（arxiv、github、stackexchange）；
- near_direct：3 个（wikipedia_en→wikipedia、gutenberg_pg_19→book、pile_cc→commoncrawl）；
- inferred：11 个，无同名质量域。

这意味着质量侧 7 域不能被简单“一对一复制”到 17 域。最终 `domain_quality.csv` 必须带映射类型和可信度；11 个 inferred 域若缺乏独立证据，不应伪造精确 Q 值。

## A17 域文本摘要

A17 的每域抽样行数差异很大，例如 ubuntu_irc 仅 16 行、philpapers 67 行，而 stackexchange 30,378 行、pubmed_abstracts 29,895 行。`avg_text_chars` 也跨越多个数量级。因此 A17 更适合用于域特征和映射辅助，不适合不加权地当作17域质量真值。

## 下一步

1. 本地 LFS 完整后，流式处理 A1–A3，核对 22 指标的数据类型、缺失、极值和列表型字段长度；
2. 对列表型指标设计统一标量压缩，建立稳健标准化；
3. 输出 Spearman 相关矩阵、冲突指标对和质量潜变量；
4. 对 arxiv/github 比较 A1 抽样与 A2/A3 扩展集，量化抽样偏差；
5. 结合 A16 构造 7 质量域到 17 配方域的映射及可信度；
6. 配比建模采用“规模效应先剥离、配比效应后建模”的方向，避免将 1M 固定线性系数直接外推。
