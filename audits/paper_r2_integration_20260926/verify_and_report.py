from pathlib import Path
import hashlib, json, html, difflib, re
import pypdfium2 as pdfium
from pypdf import PdfReader
from PIL import Image, ImageDraw

REV = Path(__file__).resolve().parent
ROOT = REV.parent
PDF = ROOT / 'output/pdf/论文_R2补充版.pdf'
changes = json.loads((REV/'changes.json').read_text(encoding='utf-8'))
extra = [
 ('example.tex', r'\documentclass[bwprint]{gmcmthesis}',
  '\\documentclass[bwprint]{gmcmthesis}\n\n% 在未安装隶书的机器上使用楷书，保证标题与摘要可编译。\n\\IfFontExistsTF{LiSu}{}{\\renewcommand{\\lishu}{\\kaishu}}',
  '编译兼容：主文件导言区', '缺少隶书字体时使用楷书回退'),
 ('chapter6.tex',
  r'''若 $C_{\max}<C_{\min}$，该配方在给定情景下不可行。否则令 $x=\ln N$，只需搜索
$x\in[\ln N_{\min},\,\ln\min\{N_{\max},(C_{\max}/D_{\min}-h)/c\}]$；''',
  r'''若 $C_{\max}<C_{\min}$，该配方在给定情景下不可行。否则令 $x=\ln N$，只需搜索以下区间：
\[
x\in\left[\ln N_{\min},\,
\ln\min\left\{N_{\max},\frac{C_{\max}/D_{\min}-h}{c}\right\}\right].
\]''', '6.3 模型求解：搜索区间', '将原有超宽行内公式改为独立公式，数学内容不变'),
 ('gmcmthesis.cls', '\t\\makenametitle', '\t\\fi\n\t\\makenametitle',
  '编译修复：模板封面条件', '闭合模板已有的条件，消除 incomplete iftrue 提示')]
for name, before, after, location, purpose in extra:
    if not any(x['location']==location for x in changes):
        changes.append(dict(id=len(changes)+1, file=name, location=location,
                            purpose=purpose, before=before, after=after))

reader = PdfReader(PDF)
pages = [p.extract_text() for p in reader.pages]
normalized = [re.sub(r'\s+', '', s).replace('\x00','-') for s in pages]
markers = {
 1: ['R2中位数由0.6056'], 2: ['后训练组短期回测'],
 3: ['平均绝对百分比误差'], 4: ['对应的折外预测'],
 5: ['绝对Loss的直接迁移失效','冻结1M配比模型的绝对Loss迁移诊断'],
 6: ['本问建立了A1'], 7: ['0.999999816'],
 8: ['0.9793、0.9791','0.9793', '折外RMSE分别'],
 9: ['二者均不构成四变量'], 10: ['不报告四变量预测'],
 11: ['决策后悔值约为2.51'], 12: ['降低约41.1'],
 13: ['四窗口滚动预测RMSE'], 14: ['0.2071和0.9508'],
 15: ['后训练主模型在短期回测'], 17: ['只需搜索以下区间']}
for c in changes:
    text=(ROOT/c['file']).read_text(encoding='utf-8')
    assert c['after'] in text, (c['id'], c['file'])
    c['line']=text[:text.index(c['after'])].count('\n')+1
    hits = sorted({i+1 for i,p in enumerate(normalized)
        if any(re.sub(r'\s+','',m) in p for m in markers.get(c['id'],[]))})
    if c['id'] == 1: hits = [2]
    if c['id'] == 7: hits = [15]
    if c['id'] == 12: hits = [38, 39]
    c['pdf_physical_pages']=hits
    c['printed_pages']=[i-1 for i in hits if i>1]

log=(REV/'build/paper-r2.log').read_text(encoding='utf-8', errors='replace')
for bad in [r'Overfull \\[hv]box',r'Missing character:',r'There were undefined',
            r'(Reference|Citation) .+ undefined',r'Label\(s\) may have changed',
            r'\(\\end occurred when']:
    assert not re.search(bad,log), bad
assert not any('??' in p for p in pages)
assert all(any(s in p for p in normalized) for s in
           ['0.6703','0.6710','8.3331','506.7317','0.999999816','0.9794','12.2321','1.1865'])
manifest = dict(pdf=str(PDF), pdf_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),
    physical_page_count=len(pages), science_changes=15, compilation_changes=3,
    source_model_sha='c6b36c08b5a85c81a3889d48d50c26ac136a048b',
    checks='No overfull boxes, missing glyphs, unresolved references/citations, changed labels, open conditionals or ?? markers',
    sources={name:dict(before_sha256=hashlib.sha256((REV/'original'/name).read_bytes()).hexdigest(),
      after_sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
      for name in sorted({c['file'] for c in changes})})
(REV/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(REV/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
diff=''.join(''.join(difflib.unified_diff((REV/'original'/name).read_text(encoding='utf-8').splitlines(True),
    (ROOT/name).read_text(encoding='utf-8').splitlines(True),fromfile='original/'+name,tofile='revised/'+name))
    for name in sorted({c['file'] for c in changes}))
(REV/'paper-r2.diff').write_text(diff,encoding='utf-8')

rows=[]
for c in changes:
    loc=f"{c['file']}:{c['line']} · {c['location']}"
    if c['pdf_physical_pages']:
        loc += f"；PDF文件第 {','.join(map(str,c['pdf_physical_pages']))} 页（正文页码 {','.join(map(str,c['printed_pages']))}）"
    rows.append('<tr><td>'+str(c['id'])+'</td><td>'+html.escape(loc)+'<p>'+html.escape(c['purpose'])+'</p></td>'
                '<td><pre>'+html.escape(c['before'])+'</pre></td><td><pre>'+html.escape(c['after'])+'</pre></td></tr>')
report='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>论文 R² 修改对照</title>
<style>body{font-family:"Microsoft YaHei",sans-serif;margin:28px;color:#172435}h1{font-size:24px}table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{border:1px solid #c9d2de;padding:12px;vertical-align:top}th{background:#e9eff7}th:first-child{width:3%}th:nth-child(2){width:19%}th:nth-child(3),th:nth-child(4){width:39%}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;line-height:1.7;margin:0;font-family:Consolas,"Microsoft YaHei",monospace}p{line-height:1.7}.note{padding:14px;background:#f3f6fa}@media print{body{margin:0}pre{font-size:10px}thead{display:table-header-group}}</style>
<h1>论文 R² 修改对照</h1><p>以用户提供的本地最新版为底稿，共 15 处指标和论证修改、3 处编译兼容或版式修复。下表逐处保留准确的原文与改文（LaTeX 源码）；新 PDF 同时保留正、负 R²。</p>
<p class="note">PDF 文件页码从封面起算，正文页码从摘要起算。第 3、5 项是原位置插入的新增段落或表格，其“原文”列显示原插入点。R² 仅在对应的数据和评价口径下解释；Q3 使用优化和决策指标。数值来源为已独立复核的 main@c6b36c08b5a85c81a3889d48d50c26ac136a048b。</p>
<table><thead><tr><th>序号</th><th>位置与修改目的</th><th>原文</th><th>改文</th></tr></thead><tbody>'''+''.join(rows)+'</tbody></table></html>'
(ROOT/'output/pdf/R2修改对照表.html').write_text(report,encoding='utf-8')
md=['# 论文 R² 修改对照\n','完整逐字对照见 `R2修改对照表.html`；下表用于查找位置。\n',
    '|序号|源文件与行号|位置|PDF 文件页码|修改目的|','|---|---|---|---|---|']
for c in changes:
    md.append(f"|{c['id']}|{c['file']}:{c['line']}|{c['location']}|{','.join(map(str,c['pdf_physical_pages'])) or '导言/模板'}|{c['purpose']}|")
(ROOT/'output/pdf/R2修改位置.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

render=REV/'render'; render.mkdir(exist_ok=True)
doc=pdfium.PdfDocument(str(PDF))
thumbs=[]
for i in range(len(doc)):
    im=doc[i].render(scale=.55).to_pil().convert('RGB')
    canvas=Image.new('RGB',(350,515),'#d9dfe7')
    im.thumbnail((330,475)); canvas.paste(im,((350-im.width)//2,20))
    ImageDraw.Draw(canvas).text((12,493),f'PDF page {i+1}',fill='black')
    thumbs.append(canvas)
for start in range(0,len(thumbs),24):
    sheet=Image.new('RGB',(350*6,515*4),'white')
    for j,im in enumerate(thumbs[start:start+24]):sheet.paste(im,((j%6)*350,(j//6)*515))
    sheet.save(render/f'contact-{start//24+1}.png')
keypages=sorted({i for c in changes for i in c['pdf_physical_pages']})
for i in keypages:
    doc[i-1].render(scale=1.4).to_pil().save(render/f'page-{i:02}.png')
print(json.dumps(dict(pages=len(pages),changes=len(changes),keypages=keypages,checks='PASS'),ensure_ascii=False))
