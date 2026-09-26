"""Verify frozen provenance, export geometry and produce review-only contact sheets."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import pymupdf as fitz
from PIL import Image
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/nature'
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
report={'frozen_inputs':[],'exports':[],'quantitative_checks':{}}
for name,digest in manifest['inputs'].items():
    path=ROOT/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
    parts=path.relative_to(ROOT).parts
    if len(parts)<3 or parts[0]!='outputs' or parts[1] not in ['Q1','Q2','Q3','Q4']:continue
    frozen=json.loads((ROOT/parts[0]/parts[1]/'curated_manifest.json').read_text(encoding='utf-8-sig'))
    key='/'.join(parts[2:]);expected=frozen['sha256'].get(key)
    if expected:
        normalized=hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        assert expected in [digest,normalized],key
        report['frozen_inputs'].append({'file':name,'frozen_sha256_match':True})
    else:report['frozen_inputs'].append({'file':name,'manifest_coverage':'not-listed; actual input SHA recorded'})

preview=OUT/'qa/previews';preview.mkdir(exist_ok=True)
book=fitz.open()
for i,f in enumerate(manifest['figures']):
    stem=f['stem'];q=manifest['qa'][stem]
    assert q['alignment_verdict']=='PASS' and q['collision_exit']==0 and q['small_glyphs']==0,stem
    with fitz.open(OUT/f'{stem}.pdf') as pdf:
        width=pdf[0].rect.width/72*25.4;assert abs(width-183)<.01
        book.insert_pdf(pdf)
    with Image.open(OUT/f'{stem}.tiff') as tif:
        dpi=tuple(float(x) for x in tif.info.get('dpi'));assert min(dpi)>=599
    svg=(OUT/f'{stem}.svg').read_text(encoding='utf-8');assert '<text' in svg
    with Image.open(OUT/f'{stem}.png') as im:
        im.convert('RGB').resize((1400,round(im.height*1400/im.width))).save(preview/f'{stem}.jpg',quality=94)
    report['exports'].append({'stem':stem,'width_mm':width,'tiff_dpi':dpi,'editable_svg_text':True})
book.save(OUT/'figures.pdf',garbage=4,deflate=True)
book.close()
for i in range(0,len(manifest['figures']),2):
    ims=[Image.open(preview/(f['stem']+'.jpg')) for f in manifest['figures'][i:i+2]]
    canvas=Image.new('RGB',(1400,sum(im.height for im in ims)),'white');y=0
    for im in ims:canvas.paste(im,(0,y));y+=im.height
    canvas.save(preview/f'review_{i//2+1:02d}.jpg',quality=94)

q1=pd.read_csv(OUT/'source_data/Q1_recipe_target_loss.csv',index_col=0)
report['quantitative_checks']['negative_loss_diagnostic']=float(q1.loc['dm_mathematics','136'])
assert q1.loc['dm_mathematics','136']<0
d=pd.read_csv(ROOT/'outputs/Q3/observed_budget_scan.csv')
report['quantitative_checks']['all_power_recipe_categories']=sorted(d[d.quality_family=='power'].recipe_index.dropna().unique().tolist())
assert set(report['quantitative_checks']['all_power_recipe_categories'])=={172,368,459,477}
d=pd.read_csv(ROOT/'outputs/Q1/targetwise_validation.csv')
report['quantitative_checks']['Q1_improved_targets']={scope:int((g.interaction_rmse<g.ridge_rmse).sum()) for scope,g in d[d.support_group=='all'].groupby('scope')}
report['figure_count']=len(manifest['figures'])
report['status']='PASS'
(OUT/'qa/provenance_and_exports.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'figures':report['figure_count'],'checks':report['quantitative_checks']},ensure_ascii=False))
