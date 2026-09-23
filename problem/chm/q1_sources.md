# Q1 外部来源核验记录

核验日期：2026-09-23（北京时间）
角色：chm
用途：只记录独立公开方法依据和外部交叉验证；不替代题面附件上的实际计算。

## RegMix

论文：
Qian Liu, Xiaosen Zheng, Niklas Muennighoff, Guangtao Zeng, Longxu Dou, Tianyu Pang, Jing Jiang, Min Lin.
"RegMix: Data Mixture as Regression for Language Model Pre-training."
arXiv:2407.01492v2, 2025-01-23；arXiv 页面标注 ICLR 2025。

URL:
https://arxiv.org/abs/2407.01492
HTML:
https://arxiv.org/html/2407.01492

已核验公开正文要点：
- 512 个 1M 参数模型、每个训练 1B tokens，用于拟合配比回归；
- 测试包括 256 个未见 1M 配方、256 个未见 60M 配方和 64 个未见 1B 配方；
- 1B 模型训练 25B tokens；
- 论文使用 17 个可用 Pile 域；
- 目标变量在主实验中为 Pile-CC validation loss；
- 比较 L2 正则线性回归（Ridge）和 LightGBM；
- Table 2 的线性模型结果：
  - 1M: Spearman 90.08%, Pearson 87.78%;
  - 60M: Spearman 89.26%, Pearson 86.79%;
  - 1B: Spearman 88.01%, Pearson 72.57%;
- Table 2 的 LightGBM：
  - 1M: Spearman 98.45%, Pearson 98.57%;
  - 60M: Spearman 98.64%, Pearson 98.28%;
  - 1B: Spearman 97.12%, Pearson 94.36%;
- Appendix E：
  - Ridge 使用 5-fold CV；
  - L2 网格为 [1e-3, 1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3]；
  - LightGBM iterations=1000，learning rate=1e-2，其余为默认参数。
- 公开官方仓库 `sail-sg/regmix/regression_fitting/regression.ipynb` 当前主要展示 LightGBM 拟合，并未独立固定 Ridge 的 KFold 行顺序/是否 shuffle。因此本项目不再把 `shuffle=False` 描述成论文精确实现，而将其作为可复现主协议，并额外计算固定 seed 的 shuffled 5-fold 敏感性。

本项目的差异：
- 附件 CSV 的配比因十进制舍入使 sum(p) 偏离 1 最多约 0.002–0.004，因此本项目先严格归一化 p；
- 本项目除 Pile-CC 外，还对其余 12 个可观测验证域分别建立同类代理，用于目标域敏感性；
- 因此称 Pile-CC 结果为“对 RegMix 线性基线的近复现”，其余域是本项目扩展分析。

## SlimPajama-Meta-rater 数据卡

数据集：
opendatalab/SlimPajama-Meta-rater

URL:
https://huggingface.co/datasets/opendatalab/SlimPajama-Meta-rater

已核验 8 个列表型字段：
- fineweb_edu: 长度 1；
- ad_en: 长度 2，[has_ad_logit, no_ad_logit]；
- fluency_en: 长度 2，[not_fluent_logit, fluent_logit]；
- qurater: 长度 4，[Writing Style, Required Expertise, Facts and Trivia, Educational Value]；
- modernbert_professionalism/readability/reasoning/cleanliness: 各长度 6，对应等级 0–5 的 logits。

数据卡示例处理：
- ad_en / fluency_en 使用 argmax；
- 四个 ModernBERT PRRC 字段使用 argmax；
- qurater 拆成 4 个分量；
- fineweb_edu 取唯一元素。

本项目的建模选择：
- 主方案对二分类 logits 使用 softmax 后的正类概率；
- PRRC 6 级 logits 使用 softmax 期望等级；
- argmax 严格作为敏感性方案。
这是本项目为了保留连续置信信息作出的独立建模选择，不得写成官方数据卡的推荐方法。

## Meta-rater 论文

论文：
Xinlin Zhuang et al.
"Meta-rater: A Multi-dimensional Data Selection Method for Pre-training Language Models."
arXiv:2504.14194, 2025.

URL:
https://arxiv.org/abs/2504.14194

已核验：
- PRRC 对应 Professionalism、Readability、Reasoning、Cleanliness；
- Meta-rater 将这些维度与既有质量信号做多维整合；
- 使用 proxy models 和回归预测 validation loss 来学习质量组合。

在本项目中，Meta-rater 只用于说明“多维质量联合评价”和外部稳健性验证是合理方向；其学习权重不直接作为本题 Q 的主权重。
