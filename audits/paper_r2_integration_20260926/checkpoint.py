from pathlib import Path
import shutil, re
rev=Path(__file__).resolve().parent
paper=rev.parent
repo=Path(r'H:\研究生数模\review-main-metrics-20260926')
backup=repo/'audits/paper_r2_integration_20260926'
for folder in ['original','revised']:(backup/folder).mkdir(parents=True,exist_ok=True)
for name in ['chapter4.tex','chapter5.tex','chapter6.tex','chapter7.tex','gmcmthesis.cls']:
    shutil.copy2(paper/name,backup/'revised'/name)
    shutil.copy2(rev/'original'/name,backup/'original'/name)
for name in ['changes.json','paper-r2.diff','build_manifest.json','REVIEW.md','revise.py','verify_and_report.py','build.ps1','checkpoint.py']:
    shutil.copy2(rev/name,backup/name)
for name in ['R2修改对照表.html','R2修改位置.md']:
    shutil.copy2(paper/'output/pdf'/name,backup/name)
for part,source in [('original',rev/'original/example.tex'),('revised',paper/'example.tex')]:
    text=source.read_text(encoding='utf-8')
    text=re.sub(r'(?m)^\\(baominghao|schoolname|membera|memberb|memberc)\{.*$',
                r'\\\1{} % 封面个人信息未纳入公共远程检查点',text)
    (backup/part/'example.tex').write_text(text,encoding='utf-8')
handoff=repo/'memory-bank/handoffs/audit/20260926-paper-r2-integration.md'
handoff.write_text('''# 最新版本地论文 R² 整合检查点

用户授权在 Huawei_Cup_2026_Mathematical_Modeling_latex-main 中修改最新版论文，融合此前已复核的 R² 结论，并编译新 PDF、提供逐处原文/改文表格。

已完成 15 处指标与论证修改、3 处编译兼容和版式修复。对应摘要、Q1 同规模与跨规模诊断、Q2 同源与半合成验证、Q3 决策质量说明、Q4 四窗与来源内 LOO。所有数值来自 main@c6b36c08b5a85c81a3889d48d50c26ac136a048b 的已独立复算审计，未改模型和数据。

本地新 PDF：`H:/研究生数模/Huawei_Cup_2026_Mathematical_Modeling_latex-main/output/pdf/论文_R2补充版.pdf`，48 页。对应完整表格 `R2修改对照表.html` 和位置索引 `R2修改位置.md`。原件保存在同目录 `r2_revision_20260926/original/`，原 example.pdf 保留。PDF 已查看全篇总览和重点页；无溢出、缺字、未解引用、标签变化或未闭合条件。

远程检查点证据：`audits/paper_r2_integration_20260926/`，包含原/改章节、类文件、完整 diff、逐处 JSON、HTML 表格、哈希清单及审核报告。公共远端的原/改 example.tex 封面个人字段置空；完整论文 PDF 和未脱敏封面只保留在用户本机，未纳入公共上传。此检查点只推 audit 分支，不修改 main。

下一步为用户审阅新稿；官方格式、最终篇幅与参考文献真实性不在本次补指标任务的重新核验范围。来源限制和跨附件坐标未识别的事实仍保留。
''',encoding='utf-8')
print('Prepared checkpoint; cover personal fields removed from public source copies.')
