# Q1 质量评价与冲突消解补充证据

日期：2026-09-25。原始数据入口仅为当前 A1--A3 实体文件；不引用历史 PDF 隐藏文字。主质量分 `Q_A` 和机器接口 `chm.q1.v1.3` 未更改。

## 质量评分：已有结果与本轮补验

A1 51,230 条及 A2/A3 17,523/203,752 条、22 指标变换与 A1 冻结标准化、七域主分及条件抽样区间已由既有 `q1_quality_analysis.py` 生成。新脚本 `q1_quality_robustness_final.py` 对 A1 按域固定划分 70% 训练、30% 评估；训练部分分层重抽 100 次，重拟合 14 个统计字段的方向，在固定评估集比较七域排序。100 次中七域排名均未改变，14 字段相对现行主方向的翻号率均为 0。此结果只说明固定分层抽样下的方向稳定，不能消除领域删除与方法选择风险。

现行 22 字段规则表 `quality_rule_22.csv` 将字段含义家族、方向来源、全局相关、各域同号比例、LOO 翻号、缺失率、名义家族权重及上述重抽翻号率放在一处。LOO 仍有 5 个字段翻号。已有八种评分规则的排名面板中，arxiv、book 为第 1--2，c4 为第 5--7，github 为第 5--7；这不是 95% 置信区间。特别是 book A1 只有 171 条，抽样区间不能解释为总体质量真值。

## 冲突：冻结处理动作与原文回读

保留已确认的 55 条复制性冲突边，A1 冻结 `Q_A` 中位数 0.02725594 和 `D` 第 75 百分位 2.04229706。高 `D` 触发 `FLAG_REVIEW`，不从 `Q_A` 扣分。低 `Q_A` 仅标记较低优先级，不自动删除。无可用冲突边时 `D` 缺失并复核，不能填零。A1 中 `RETAIN` 20,384、`RETAIN_FLAG_REVIEW` 5,231、`LOW_PRIORITY` 18,038、`LOW_PRIORITY_FLAG_REVIEW` 7,577。A1 七域无缺失 D；去重 A2 arxiv 的复核率 69.04%，去重 A3 github 为 47.08%，说明固定全局阈值的触发频率随领域分布变化，不应把它解释为错判率。

从七域和 A1 中位数 Q/D 四象限，按固定哈希顺序各取首条，共 27 条；book 缺少低 Q 高 D 组合。原文仅在本地以 `(domain,id,line)` 定向回读并验证 SHA；仓库只存索引、正文哈希/长度、22 个定向值与最高贡献冲突边，不提交全文。可用 `python src/chm/q1_text_case_review.py <domain> <id>` 本地复核。

初步语义核查中的支持与反例（非盲评、非真实质量标签）：

| 域与 ID | Q/D 动作 | 原文可复核观察 | 对规则的含义 |
|---|---|---|---|
| arxiv `BkiUdX3xK6wB9k0iLt8X` | 低 Q、高 D，复核 | 片段主要是 TeX 章节宏定义 | 格式与内容指标可能分歧，不能直接判为无价值 |
| c4 `BkiUc0HxaKgTvXx06dgF` | 低 Q、高 D，复核 | 片段为旅馆促销文案 | 标记广告样式有解释力，但非独立标签 |
| book `BkiUcKHxK6EuNCwyuQ3X` | 高 Q、高 D，复核 | 文本开头为版权信息，整条极长 | 高 Q 仍需查看结构；D 不自动扣分 |
| c4 `BkiUc_g4c3aisMwilqdm` | 低 Q、低 D，低优先级 | 片段是法院线上支付流程公告 | 低 Q、低 D 不等于无信息价值；优先级只是情景策略 |

这些观察仅是可追溯的语义案例核查。尚无盲化人工标签，不能计算准确率、误伤率或证明选择策略优于 Q-only。55 边由 A1 全样本筛选；各分析范围分别 BH-FDR 0.05，不等于最终跨范围边集拥有联合 5% FDR 保证。A2/A3 去重只能验证 arxiv/github 两域。所有 Q/D 阈值和版本见 manifest。

## 复现

在仓库根目录，使用已安装 pandas、numpy、scipy、matplotlib 的 Python：

```text
python src/chm/q1_quality_robustness_final.py
python src/chm/q1_conflict_resolution.py
python -m unittest discover -s src/chm -p test_q1_conflict_resolution.py
```

源哈希及运行配置见两个新输出目录的 manifest；数据只允许从 `data/raw/real_attachments/` 读取，原件不改写。
