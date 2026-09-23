# chm 官方 Q 字段与派生评分复核交接

日期：2026-09-24；分支：`integration/chm-q1-clean-20260923`。用户指出应优先关注赛题已提供的跨问题字段，要求复核 chm 派生 Q 与 B 官方 Q 的接口资格。

已核对可读说明、真实 B6/B7/B8 CSV 和官方 A16：B6/B7/B8 自带 `Q_score`，分别 360/450/1704 行，均标半合成；B8 有 calibrated 984 与 extrapolated 720。A1–A3 只提供 22 个质量信号，`Q_z` 是 chm 的描述性计算。A16 只有 3 direct、3 near_direct、11 inferred，不能为 17 个配比域补齐质量分数。详见 `interfaces/chm/OFFICIAL_DATA_REVIEW.md`。

结论：`chm.q1.v1` 的 A 侧质量与配比输出可作描述和敏感性，但尚不具备直接数值接入 B 预测器的资格。已在读取器返回中标记 `direct_B_predictor_input_allowed=False`、`direct_B1_addition_allowed=False`，60M/1B η 输出标为条件情景；合同、使用说明及给 cyj 的清单明确 B 侧优先使用原生 `Q_score`、保留半合成和外推分层。尚需 cyj 审计 B1/B6–B8 Loss 来源并定义质量与配比桥接，缺证据时维持未识别/情景状态。

复核：读取器 manifest 哈希及 `test_q1*.py` 测试；资料读取规则检查。未修改 B 原始附件或 cyj 文件。后续 chm 消费 cyj 正式接口时，逐字段核对来源、单位、实测/半合成状态及可识别性。
