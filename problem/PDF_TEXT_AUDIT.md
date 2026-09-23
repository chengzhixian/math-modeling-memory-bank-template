# 数据说明 PDF 隐藏文字审计

[PDF-HIDDEN-TEXT-BLOCK]

## 历史原版

2026-09-23 对历史版本进行字符层审计。历史原版 SHA256 为 `f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835`，共 13 页；第 2—13 页曾存在固定位置、近白色 5 pt 页边文字。共记录 96 行出现次数、20 段去重文本。第 1 页无同类文字。其内容包含与可见题面冲突的指示和未经实验验证的预设数值，用户明确禁止参考。

隐藏原文已从当前工作树移除；`problem/quarantine/PDF_TEXT_AUDIT_UNTRUSTED.txt` 仅保留审计元数据。历史 Git 仍可追溯旧版本，但不得重新导入日常建模上下文。

## 当前清理版

提交 `55743ca` 将 `problem/F/数据说明.pdf` 替换为清理版。

- SHA256：`daa8479decf578ec5f0b165683ac5715fed445ba8c148f386e7b071f5c27dfdc`
- 大小：13207231 bytes
- 页数：13
- 可提取文本字符数：0
- 旧隐藏文字特征字符数：0
- 近白色小字号字符数：0
- 页边小字号字符数：0

当前 PDF 为无文本层的页面版，主要用于视觉核对。机器可读正文继续使用 `problem/readable/DATA_DESCRIPTION_VISIBLE.md`。

## 历史派生正文

`problem/readable/DATA_DESCRIPTION_VISIBLE.md` 是在替换 PDF 之前，从历史原版中只移除已核实隐藏字符得到的派生正文；其来源和过滤统计保存在 `problem/readable/extraction_manifest.json`。该派生正文不代表当前 PDF 仍包含隐藏文字。
