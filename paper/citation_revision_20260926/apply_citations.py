"""Add citations to the user supplied source, checking exact body preservation."""
from pathlib import Path
import hashlib, json, re

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / 'archive_input/Huawei_Cup_2026_Mathematical_Modeling_latex-main/Huawei_Cup_2026_Mathematical_Modeling_latex-main'
PROJECT = ROOT / 'revised_project'
CHANGES = {
 'chapter4.tex': [
  ('本问需要从质量信号中给出可比较的文本质量评分', 'fineweb2024'),
  ('对 DSIR', 'dsir2023'),
  ('考虑到领域组合可能影响训练效果', 'regmix2025,mixinglaws2025'),
 ],
 'chapter5.tex': [
  ('B1 的 1176 条 Pythia', 'pythia2023'),
  ('建立经典双幂律', 'hoffmann2022training'),
 ],
 'chapter6.tex': [
  ('增加模型参数量、扩大训练数据量和提高数据质量都会改变验证集交叉熵损失（Loss）', 'hoffmann2022training,fineweb2024'),
  ('长上下文直接挤占可分配给规模与训练量的预算', 'flashattention2022'),
  ('公开的 OpenLM 训练记录', 'gadre2024'),
 ],
 'chapter7.tex': [
  ('因此还需建立来源一致的 Loss--能力关系', 'gadre2024,observational2024'),
  ('MUSR 和 MMLU-PRO', 'mmlupro2024'),
  ('以 $\\tau=0.9$ 为目标的分位资源模型', 'koenker2017'),
  ('每一轮仅用测试窗口开始前的提交版本和当时可见的 C4 资源记录拟合，再计算测试窗口误差', 'forecasting2021'),
 ],
}

EXTENDED_CHANGES = {'chapter4.tex': [('（MAD）进行稳健标准化', 'robust2018'), ('Spearman 秩相关', 'spearman2018'), ('Bootstrap 重抽样', 'islr2021'), ('Benjamini--Hochberg 方法', 'fdr2019'), ('记 The Pile', 'pile2022'), ('岭回归模型和训练均值预测作为对照', 'islr2021'), ('采用五折嵌套交叉验证比较模型', 'hpo2023'), ('凸包为搜索区域', 'wright2022'), ('McCormick 松弛与空间分支定界求解', 'global2025')], 'chapter5.tex': [('Huber 损失', 'huber2020')], 'chapter6.tex': [('相应边际成本之比比较', 'wright2022'), ('按 C4、RedPajama 和 RefinedWeb 三种训练语料', 'c42020,redpajama2024,refinedweb2023'), ('同一 Paloma C4 验证集', 'paloma2024')], 'chapter7.tex': [('六项分别为 IFEval', 'ifeval2023'), ('、BBH', 'bbh2023'), ('、MATH Lvl 5', 'math2021'), ('、GPQA', 'gpqa2024'), ('、MUSR', 'musr2024'), ('以开发者为抽样块重复抽取', 'cluster2023'), ('设 $z_i=\\operatorname{logit}(S_i/100)$', 'islr2021'), ('对来源内每条记录依次留出、重拟合并预测', 'islr2021'), ('Qwen2 和 Qwen2.5', 'qwen22024,qwen252024')]}
for filename, additions in EXTENDED_CHANGES.items():
 CHANGES[filename].extend(additions)

evidence = {'body_unchanged': {}, 'insertions': [], 'source_pdf': 'example(2).pdf',
            'source_archive': 'Desktop/Huawei_Cup_2026_Mathematical_Modeling_latex-main.rar'}
for filename, additions in CHANGES.items():
 raw = (ORIGINAL / filename).read_bytes()
 original = raw.decode('utf-8')
 revised = original
 for anchor, keys in additions:
  assert revised.count(anchor) == 1, (filename, anchor, revised.count(anchor))
  revised = revised.replace(anchor, anchor + '\\cite{' + keys + '}', 1)
  evidence['insertions'].append({'file': filename, 'anchor': anchor, 'keys': keys,
                               'line': revised[:revised.index(anchor)].count('\n') + 1})
 recovered = revised
 for anchor, keys in reversed(additions):
  recovered = recovered.replace(anchor + '\\cite{' + keys + '}', anchor, 1)
 assert recovered.encode('utf-8') == raw, filename
 (PROJECT / filename).write_bytes(revised.encode('utf-8'))
 evidence['body_unchanged'][filename] = True
 evidence.setdefault('original_sha256', {})[filename] = hashlib.sha256(raw).hexdigest()

# Preserve original bibliography and citation keys; append only new works.
verified = (ROOT / 'references_verified.bib').read_text(encoding='utf-8')
new_entries = verified[verified.index('@article{gadre2024,'):] + '\n' + (ROOT / 'extension_verified.bib').read_text(encoding='utf-8')
original_bib = (ORIGINAL / 'reference.bib').read_bytes()
(PROJECT / 'reference.bib').write_bytes(original_bib + b'\r\n' + new_entries.encode('utf-8'))

# Minimal template build fixes; no manuscript wording is altered.
cls = (ORIGINAL / 'gmcmthesis.cls').read_bytes().decode('utf-8')
anchor = '\t\\makenametitle\n\t}'
assert cls.count(anchor) == 1
cls = cls.replace(anchor, '\t\\fi % Close the optional cover branch.\n' + anchor)
cls = cls.replace('\\endinput',
 '% Use installed KaiTi only when the original cover font is unavailable.\r\n'
 '\\AtBeginDocument{\\IfFontExistsTF{LiSu}{}{\\setCJKfamilyfont{zhli}{KaiTi}\\renewcommand{\\lishu}{\\CJKfamily{zhli}}}}\r\n'
 '\\endinput')
(PROJECT / 'gmcmthesis.cls').write_bytes(cls.encode('utf-8'))

for name in ['example.tex', 'chapter1.tex', 'chapter2.tex', 'chapter3.tex', 'chapter8.tex']:
 assert (PROJECT / name).read_bytes() == (ORIGINAL / name).read_bytes(), name
 evidence['body_unchanged'][name] = True

# Retain the original numbered style and make titles link to verified sources.
bst = (ORIGINAL / 'gmcm.bst').read_bytes().decode('utf-8')
assert "#0 'link.title :=" in bst
bst = bst.replace("#0 'link.title :=", "#1 'link.title :=")
(PROJECT / 'gmcm.bst').write_bytes(bst.encode('utf-8'))

evidence['template_fixes'] = ['close optional cover conditional', 'LiSu to KaiTi fallback when missing']
evidence['bibliography_style'] = 'clickable titles to verified URL or DOI; retain original numbered style'
evidence['citation_insertions'] = len(evidence['insertions'])
(ROOT / 'CHANGE_MANIFEST.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'insertions': len(evidence['insertions']), 'body_unchanged': all(evidence['body_unchanged'].values())}))
