# CYJ Q1→Q2 派生导出第一检查点

## 变更

遵照用户 V3 任务书的单独 Q1 生产阶段，在 CYJ 分支新增 `src/chm/export_q1_q2_bundle.py`，读取 A4 仅为发布 Q1 派生的完整 512×17 归一化候选配方。沿用 CHM `q3_p_support.load_a4` 的逐行归一化语义；无新拟合。复制 CHM 固定 v1.3 五表及 CHM 后续配比审计派生指标，生成 `outputs/chm/q1_exports/q1_q2_bundle_v1/` 14 个文件（13 个派生文件加 manifest）。输出包状态明示 `Q1_derived_export_pending_CHM_owner_signoff`；这不覆盖原 v1.3。

## 输入、证据与复现

- 冻结 Q1 `cdda1ad62c5c7eb72b413c4228caeff87d2bad30`，后续 CHM 审计 `2450971d15b7f6516d6db408759bf1b22f497808`。
- A4 原始 `train_mixture_1m.csv` SHA256 `04a32ef4ab594376bf90e11404c033668f887c351d6a03ad3744824c7296a2d8`，仅由 `src/chm` 导出程序读取；全部 512 行、17 域名及顺序、index 唯一性与正性检查通过。
- 命令：`python -B src/chm/export_q1_q2_bundle.py`；导出 manifest SHA256 `b0dda7caac30513c0f37e74ccb143064606847fdc35fd7607c999ac2f8647ecb`，各产物 SHA 和代码 SHA 见该 manifest。输出包含 512 配方、质量/映射、13 目标 Ridge/参考、A held-out、1M/60M 配对与交互候选比较；完整二阶系数不存在，明确不发布。

## 未解决与下一步

CHM 须复核并签收此 Q1 增量导出包的来源、归一化与版本；CYJ 继续实现只消费派生包和 B 附件的 Q2 优化及 v6。此检查点未运行 Q2 数值，不能视为 C1–C8 验收。论文核心建模和论证仍由队员自行确认，AI 辅助按题面披露。
