# Q1 全量 22 信号主评分修订交接

分支：`integration/chm-q1-clean-20260923`。输入：清理版数据说明的可见正文与 A1--A3 实体数据；未使用历史 PDF 隐藏文字。外部修订讨论文件仅作为待核验的修改建议，数值均由本地数据重算。

## 本次变更

- 主方向改为 A1 全部有效记录上的 Spearman 符号；8 个模型型字段固定正向，14 个统计字段据符号取正反。主评分保留全部 22 个质量信号。七域 Spearman、LOO 翻号和删除脆弱指标仅作稳健性诊断。
- A1 51,230、A2 17,523、A3 203,752 条全量重跑；更新域级评分、条件 bootstrap 区间、冲突复制性、图表及论文第一小问。
- Q1 机器接口升级为 `chm.q1.v1.3`，质量数值发生改变；配比 Ridge 与排序证据沿用原接口。

## 证据与复现

- `outputs/chm/quality_analysis_manifest_v0.json` 记录输入哈希、行数、随机种子与冻结参数；`quality_orientation_primary_v1.csv`、`quality_orientation_by_domain_v1.csv`、`quality_orientation_robustness_v1.csv`、`quality_orientation_sensitivity_v1.csv` 区分主规则与诊断。
- 命令：`python src/chm/q1_quality_analysis.py --output-dir outputs/chm --bootstrap 1000`；随后运行 `src/chm/q1_quality_delivery.py`、`src/chm/q1_paper_figures.py`、`src/chm/q1_interface.py --build-manifest`。
- 新口径下 5 个统计指标 LOO 翻号；删除这些指标后的七域排序相关为 0.8929，主评分仍保留它们。

## 未解决与下一步

- 主方向基于自定义语义锚点，弱相关指标的方向仍有模型不确定性；条件 bootstrap 区间不覆盖规则选择。
- cyj/zhh 消费 Q1 时需更新到 v1.3 并核对下游依赖数值。负责人：chm 维护 Q1，cyj/zhh 复核各自下游接口。
