from pathlib import Path
import json, re, hashlib, html, difflib
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

REV=Path(__file__).resolve().parent
ROOT=REV.parent
PDF=ROOT/'output/pdf/论文_R2精简融合版.pdf'
reader=PdfReader(PDF)
pages=[p.extract_text() for p in reader.pages]
norm=[re.sub(r'\s+','',p).replace('\x00','-') for p in pages]
log=(REV/'build/paper-r2.log').read_text(encoding='utf-8',errors='replace')
for bad in [r'Overfull \\[hv]box',r'Missing character:',r'There were undefined',
            r'(Reference|Citation) .+ undefined',r'Label\(s\) may have changed',r'\(\\end occurred when']:
    assert not re.search(bad,log),bad
assert not any('??' in p for p in pages)
appendix_page=next(i for i,p in enumerate(norm) if '本附录检查未经规模校准' in p)
assert '506.7317' not in ''.join(norm[:appendix_page])
assert '506.7317' in ''.join(norm[appendix_page:])
q3=(ROOT/'chapter6.tex').read_text(encoding='utf-8')
assert 'R^2' not in q3 and '决策后悔值约为 2.51' in q3
abstract=(ROOT/'example.tex').read_text(encoding='utf-8').split('\\begin{abstract}')[1].split('\\end{abstract}')[0]
assert 'R^2' not in abstract
for s in ['0.6703','0.6710','0.999999816','0.9793','0.9791','0.9794','0.7500','12.2321','0.2071','0.9508','1.1865']:
    assert any(s in p for p in norm),s
assert 'B.1' in ''.join(norm[appendix_page:])
changes=json.loads((REV/'changes.json').read_text(encoding='utf-8'))
if not any(c['id']==14 for c in changes):
    before=(REV/'before/chapter5.tex').read_text(encoding='utf-8')
    after=(ROOT/'chapter5.tex').read_text(encoding='utf-8')
    changes.append(dict(id=14,file='chapter5.tex',location='5.8 本问结果与后续衔接',
        purpose='压缩已在前文交代的使用条件，消除小结末行单独占页',
        before=next(p for p in before.splitlines() if p.startswith('表\\ref{tab:q2-output}汇总')),
        after=next(p for p in after.splitlines() if p.startswith('表\\ref{tab:q2-output}汇总'))))
markers={1:['该模型在13个验证域上的嵌套交叉验证RMSE'],2:['在此基础上'],
 3:['以评价集均值预测为参照'],4:['在256个配方组成的同规模'],
 5:['本问建立了A1','跨规模应用限于排序比较'],6:['将每种留出方式的全部折外预测'],
 7:['本问以B1同源训练轨迹建立'],8:['6.6.2数值求解的复算'],
 9:['所选两组模型的测试','历史常数基线不同','RMSE降低约41.1'],10:['四窗口滚动预测RMSE'],
 11:['长期精度仍需进一步检验'],12:['本附录检查未经规模校准'],13:['本附录检查未经规模校准'],
 14:['汇总了本问输出'],15:['条件代理映射斜率变化对同一训练配方']}
for c in changes:
    source=(ROOT/c['file']).read_text(encoding='utf-8')
    if c['id']==7:
        c['after']=next(p for p in source.splitlines() if p.startswith('本问以 B1 同源训练轨迹建立'))
    if c['after']:
        assert c['after'] in source,c['id']
        c['line']=source[:source.index(c['after'])].count('\n')+1
    else:
        anchor='在此基础上' if c['id']==2 else '\\subsubsection{数值求解的复算}'
        c['line']=source[:source.index(anchor)].count('\n')+1
    c['pdf_pages']=sorted({i+1 for i,p in enumerate(norm) if i>=4 and any(m in p for m in markers.get(c['id'],[]))})
    if c['id'] in [1,2]:c['pdf_pages']=[2]
(REV/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
names=sorted({c['file'] for c in changes})
diff=''
for n in names:
    before=(REV/'before'/n).read_text(encoding='utf-8').splitlines(True) if (REV/'before'/n).exists() else []
    diff+=''.join(difflib.unified_diff(before,(ROOT/n).read_text(encoding='utf-8').splitlines(True),fromfile='before/'+n,tofile='after/'+n))
(REV/'refinement.diff').write_text(diff,encoding='utf-8')
manifest=dict(pdf=str(PDF),physical_pages=len(pages),pdf_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),
    appendix_B_physical_page=appendix_page+1,checks='PASS: stable references, no missing glyphs/overflow/open conditional; Q3 and abstract contain no R2; negative Q1 transfer diagnostics only in appendix; retained evidence and B.1 numbering',
    source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
(REV/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
rows=[]
for c in changes:
    loc=f"{c['location']} · {c['file']}:{c['line']}"
    if c['pdf_pages']:loc+='；PDF文件第 '+','.join(map(str,c['pdf_pages']))+' 页'
    rows.append('<tr><td>'+str(c['id'])+'</td><td>'+html.escape(loc)+'<p>'+html.escape(c['purpose'])+'</p></td><td><pre>'+html.escape(c['before'])+'</pre></td><td><pre>'+html.escape(c['after'] or '（删除，不新增替代说明）')+'</pre></td></tr>')
report='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>R² 精简修改对照</title>
<style>body{font-family:"Microsoft YaHei",sans-serif;margin:28px;color:#172435}h1{font-size:24px}p{line-height:1.7}table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{border:1px solid #c9d2de;padding:12px;vertical-align:top}th{background:#e9eff7}th:first-child{width:3%}th:nth-child(2){width:19%}th:nth-child(3),th:nth-child(4){width:39%}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;line-height:1.7;margin:0;font-family:Consolas,"Microsoft YaHei",monospace}@media print{thead{display:table-header-group}pre{font-size:10px}}</style>
<h1>R² 精简修改对照</h1><p>本表对照上一版 R² 补充稿与本次精简融合稿，共 15 处编辑。原文与改文为准确 LaTeX 源码；PDF 文件页码从封面起算。删除项的行号指向所在段落或小节，新增附录的行号从附录源文件起算。</p>
<p>主文保留与实际任务匹配的验证指标；Q1 跨规模绝对输出诊断完整移至附录 B，Q3 删除“不报告 R²”的说明，Q4 的必要回测限制保留在验证讨论。摘要与小结减少指标重复。此前原稿到补充稿的对照仍保存在 R2修改对照表.html。</p>
<table><thead><tr><th>序号</th><th>位置与目的</th><th>上一版原文</th><th>本次改文</th></tr></thead><tbody>'''+''.join(rows)+'</tbody></table></html>'
(ROOT/'output/pdf/R2精简修改对照表.html').write_text(report,encoding='utf-8')
md=['# R² 精简修改位置\n','相对上一版补充稿的 15 处编辑；完整原文/改文见 R2精简修改对照表.html。\n',
    '|序号|位置|源文件与行号|PDF文件页码|目的|','|---|---|---|---|---|']
for c in changes:md.append(f"|{c['id']}|{c['location']}|{c['file']}:{c['line']}|{','.join(map(str,c['pdf_pages']))}|{c['purpose']}|")
(ROOT/'output/pdf/R2精简修改位置.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
render=REV/'render';render.mkdir(exist_ok=True)
doc=pdfium.PdfDocument(str(PDF))
thumbs=[]
for i in range(len(doc)):
    im=doc[i].render(scale=.55).to_pil().convert('RGB');im.thumbnail((330,475))
    canvas=Image.new('RGB',(350,515),'#d9dfe7');canvas.paste(im,((350-im.width)//2,20))
    ImageDraw.Draw(canvas).text((12,493),f'PDF page {i+1}',fill='black');thumbs.append(canvas)
for start in range(0,len(thumbs),24):
    sheet=Image.new('RGB',(2100,2060),'white')
    for j,im in enumerate(thumbs[start:start+24]):sheet.paste(im,((j%6)*350,(j//6)*515))
    sheet.save(render/f'contact-{start//24+1}.png')
key=sorted({p for c in changes for p in c['pdf_pages']})
for i in key:doc[i-1].render(scale=1.4).to_pil().save(render/f'page-{i:02}.png')
print(json.dumps(dict(pages=len(pages),appendix_page=appendix_page+1,key_pages=key,checks='PASS')))
