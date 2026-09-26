# example(2).pdf 第四至七章引用插入清单

核验日期：2026-09-26。依据：用户提供的 47 页 PDF。正文页码 = PDF 查看器页码 − 1。

状态：已按用户最后提供的桌面 RAR 修订匹配的 LaTeX 源文件并生成 46 页 PDF。移除新增引用后，章节正文与压缩包源文件逐字一致；图表文件字节一致。原上传 PDF 为 47 页，重编译分页有所变化。最终以章节、小节和句子锚点定位。

操作范围：12 处插入 `\cite{...}`，新增 Gadre 及 10 篇方法/背景文献，保留已引用的 Kaplan、Hoffmann，共 13 篇。文献编号按首次出现顺序编译。模板另修复未闭合条件分支，并在 LiSu 缺失时使用 KaiTi；参考文献标题链接到核验来源。

## 逐句插入位置

|原正文页/PDF页|修订正文页/PDF页|位置|原文定位锚点|插入内容|适用范围|
|---|---|---|---|---|---|
|5/6|5/6|4.1 第一段|“本问需要从质量信号中给出可比较的文本质量评分”之后|`\cite{fineweb2024}` [1]|质量筛选研究背景；不是式(4.1)—(4.3)的来源|
|5/6|5/6|4.2.1 第一段|“对 DSIR”中的 DSIR 名称之后|`\cite{dsir2023}` [2]|DSIR 指标/方法来源；不为保号对数和本文赋权背书|
|7/8|7/8|4.3.1 第一段|“考虑到领域组合可能影响训练效果”之后、逗号之前|`\cite{regmix2025,mixinglaws2025}` [3,4]|配比回归与域组合影响的相关方法依据；二阶十交互项是本文选择|
|14/15|13/14|5.1 第二段|“B1 的 1176 条 Pythia 训练记录”中的 Pythia 名称之后|`\cite{pythia2023}` [7]|模型族与公开检查点背景；附件1176条及Loss真实性仍按附件来源记录，不由此引用验证|
|14/15|13/14|5.2.1 第一段|“建立经典双幂律”之后、式(5.1)之前|`\cite{hoffmann2022training}` [6]|经典 N、D 双幂函数形式；本文拟合参数不引用成他人参数|
|23/24|22/23|6.1 第一段|“增加模型参数量、扩大训练数据量和提高数据质量都会改变验证集交叉熵损失（Loss）”之后|`\cite{hoffmann2022training,fineweb2024}` [6,1]|训练资源和质量的取舍背景|
|28/29|27/28|6.5.1 第一段|“长上下文直接挤占可分配给规模与训练量的预算”之后|`\cite{flashattention2022}` [8]|长序列注意力的计算与内存开销背景；不是题面成本系数或30000 Token阈值的来源|
|30/31|29/30|6.6.3 第一段|“公开的 OpenLM 训练记录”之后，保留原仓库网址脚注|`\cite{gadre2024}` [9]|公开实验与评测记录的直接来源|
|34/35|33/34|7.1 式(7.1)之后的任务列表|“MMLU-PRO”名称之后、句号之前|`\cite{mmlupro2024}` [11]|只支持MMLU-Pro这一评测的来源，不代表六任务等权聚合来自该文献|
|34/35|33/34|7.1 第一段末|“因此还需建立来源一致的 Loss–能力关系”之后|`\cite{gadre2024,observational2024}` [9,10]|Loss与下游表现、跨模型家族能力映射的研究背景；本文式(7.8)另行拟合|
|38/39|37/38|7.3.1 第二段|“以 τ = 0.9 为目标的分位资源模型”之后|`\cite{koenker2017}` [12]|分位回归与check loss；本文τ、解释变量与logit选择不由文献给定|
|38/39|37/38|7.3.1 式(7.5)之后|“每一轮仅用测试窗口开始前的提交版本和当时可见的 C4 资源记录拟合，再计算测试窗口误差”之后|`\cite{forecasting2021}` [13]|滚动预测起点与禁止使用未来信息|

## 文末参考文献（最终编号）

[1] Penedo G, Kydlíček H, Ben Allal L, et al. The FineWeb Datasets: Decanting the Web for the Finest Text Data at Scale[C]//Advances in Neural Information Processing Systems. 2024, 37. https://arxiv.org/abs/2406.17557v2.

[2] Xie S M, Santurkar S, Ma T, Liang P. Data Selection for Language Models via Importance Resampling[C]//Advances in Neural Information Processing Systems. 2023, 36. https://arxiv.org/abs/2302.03169.

[3] Liu Q, Zheng X, Muennighoff N, et al. RegMix: Data Mixture as Regression for Language Model Pre-training[C]//The Thirteenth International Conference on Learning Representations. 2025. https://openreview.net/forum?id=5BjQOUXq7i.

[4] Ye J, Liu P, Sun T, et al. Data Mixing Laws: Optimizing Data Mixtures by Predicting Language Modeling Performance[C]//The Thirteenth International Conference on Learning Representations. 2025. https://openreview.net/forum?id=jjCB27TMK3.

[5] Kaplan J, McCandlish S, Henighan T, et al. Scaling Laws for Neural Language Models[J]. arXiv preprint arXiv:2001.08361, 2020. https://arxiv.org/abs/2001.08361.

[6] Hoffmann J, Borgeaud S, Mensch A, et al. Training Compute-Optimal Large Language Models[C]//Advances in Neural Information Processing Systems. 2022, 35. https://arxiv.org/abs/2203.15556.

[7] Biderman S, Schoelkopf H, Anthony Q G, et al. Pythia: A Suite for Analyzing Large Language Models Across Training and Scaling[C]//Proceedings of the 40th International Conference on Machine Learning. PMLR, 2023, 202:2397–2430. https://proceedings.mlr.press/v202/biderman23a.html.

[8] Dao T, Fu D Y, Ermon S, et al. FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness[C]//Advances in Neural Information Processing Systems. 2022, 35. https://arxiv.org/abs/2205.14135.

[9] Gadre S Y, Smyrnis G, Shankar V, et al. Language models scale reliably with over-training and on downstream tasks[J]. arXiv preprint arXiv:2403.08540, 2024. https://arxiv.org/abs/2403.08540v2.

[10] Ruan Y, Maddison C J, Hashimoto T. Observational Scaling Laws and the Predictability of Language Model Performance[C]//Advances in Neural Information Processing Systems. 2024, 37. https://arxiv.org/abs/2405.10938v3.

[11] Wang Y, Ma X, Zhang G, et al. MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark[C]//Advances in Neural Information Processing Systems. 2024, 37. https://arxiv.org/abs/2406.01574.

[12] Koenker R. Quantile Regression: 40 Years On[J]. Annual Review of Economics, 2017, 9:155–176. DOI:10.1146/annurev-economics-063016-103651.

[13] Hyndman R J, Athanasopoulos G. Forecasting: Principles and Practice[M]. 3rd ed. Melbourne: OTexts, 2021. https://otexts.com/fpp3/.

## 来源核验与年份

所有链接均为论文作者、会议官方论文集、出版社或作者教材站点；访问日期2026-09-26。FineWeb、DSIR、FlashAttention、Observational Scaling Laws、MMLU-Pro 对照 NeurIPS 官方记录；RegMix、Data Mixing Laws 对照 ICLR 正式论文/作者 camera-ready，按2025会议年著录；Pythia 对照 PMLR；分位回归综述对照 Annual Reviews；时间序列交叉验证对照 OTexts 第5.10节：https://otexts.com/fpp3/tscv.html。

新增11篇中，9篇发表于2022—2025年，教材为2021年，分位回归综述为2017年。保留2017综述是因为其直接支撑经典分位回归方法，符合5—10年范围。本文数值、原创映射和参数仍由论文自己的数据与拟合确定，引用不为本文数值结论背书。

## 编译与验收

执行 XeLaTeX → BibTeX → XeLaTeX → XeLaTeX。最终46页、13个书目条目、12处新增引用；无未定义引用、无缺字、无超宽盒警告。逐页渲染检查46页，并放大核对数据集引用页和参考文献页。文献标题均链接到核验入口，原 GitHub 脚注保留。

`CHANGE_MANIFEST.json` 保存原章节SHA256、插入锚点和行号、正文/图片一致性及最终PDF哈希；`QA/checks.json` 保存编译核查与最终页码。`apply_citations.py` 为插入过程记录，重跑需提供原始压缩包解出的 archive_input 目录；直接编译交付源文件不需要该目录。
