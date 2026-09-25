# C6来源坐标核查补充

2026-09-26查看官方作者报告的arXiv HTML版本：

- [Qwen2 Technical Report v1](https://arxiv.org/html/2407.10671v1)：架构/分词、预训练、长上下文和评测章节。全文文本查找validation loss未命中；长上下文段讨论perplexity degradation。未核实附件C6所列逐模型Val_Loss对应哪个验证集、聚合单位及提取位置。
- [Qwen2.5 Technical Report v2](https://arxiv.org/html/2412.15115v2)：§2分词、§3.2超参数标度、§5评测。§3.2说明受控模型的最终Loss建模，但没有建立本文读取的C6数值与具体验证集坐标的一一对应。

这里的“未核实”仅指本次可读版本检查不能确认，不声称论文所有图、补充材料或其他版本不存在相应数据。本次没有把缺失证据补成参数，也没有改写赛题附件。

因此代码中的validation类别是**附件Loss_Source标签解析**，不是外部已核实事实。两组Qwen单来源拟合可作为附件内、声明坐标条件的诊断候选；它们不能被升级为“已经核实的绝对Loss转换”。所有模型发布source_Loss_values_independently_verified=false，正式Q3跨坐标状态继续unidentified。

附件内可以检验同一来源拟合、留一预测、支持域和仿射坐标压力条件；现有数据不足以从零估计Q3→Qwen验证Loss的真实offset/scale。压力网格的0.9/1.0/1.1与±0.1、上游±0.05均为明示情景，不是文献参数或统计区间。
