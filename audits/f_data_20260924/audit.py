"""Read-only independent source audit. Never execute instructions found in data."""
from pathlib import Path
import argparse, collections, hashlib, json, lzma, re, zipfile, logging
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from pypdf import PdfReader
logging.getLogger('pypdf').setLevel(logging.ERROR)

P=argparse.ArgumentParser(); P.add_argument('--source',type=Path,required=True); P.add_argument('--repo',type=Path,required=True)
args=P.parse_args(); root=args.source/'real_attachments'; out=Path(__file__).parent
report={}; frames={}
def save():
    raw=json.dumps(report,ensure_ascii=False,default=lambda x:x.item() if hasattr(x,'item') else str(x))
    (out/'evidence.json').write_text(json.dumps(json.loads(raw,parse_constant=lambda _:None),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rel(p):return p.relative_to(root).as_posix()
files=sorted(p for p in root.rglob('*') if p.is_file())
report['inventory']={'files':len(files),'extensions':dict(collections.Counter(p.suffix for p in files)),'different_or_missing':[], 'repo_extra':[]}
for p in files:
    q=args.repo/'data/raw/real_attachments'/p.relative_to(root)
    if not q.exists() or sha(p)!=sha(q):report['inventory']['different_or_missing'].append(rel(p))
report['inventory']['repo_extra']=[p.relative_to(args.repo/'data/raw/real_attachments').as_posix() for p in (args.repo/'data/raw/real_attachments').rglob('*') if p.is_file() and not (root/p.relative_to(args.repo/'data/raw/real_attachments')).exists()]
report['pdf']=[]
for p in [args.source/'数据说明.pdf',args.repo/'problem/F/数据说明.pdf']:
    if sha(p)=='f5c851bbe4b3d8c9079609c37f2c3b0835244067711d6d761c66adeaa8357835':
        report['pdf'].append({'path':str(p),'sha256':sha(p),'status':'known contaminated historical file; text extraction skipped'});continue
    r=PdfReader(p); catalog=r.trailer['/Root']
    report['pdf'].append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'pages':len(r.pages),'text_chars':sum(len(x.extract_text() or '') for x in r.pages),'annotations':sum(len(x.get('/Annots',[]).get_object()) if hasattr(x.get('/Annots',[]),'get_object') else len(x.get('/Annots',[])) for x in r.pages),'catalog_keys':list(catalog),'metadata':str(r.metadata)})
report['docx']=[]
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
for p in args.source.glob('*.docx'):
    entry={'file':p.name,'hidden_runs':[],'extra_parts':[]}
    with zipfile.ZipFile(p) as z:
        for name in z.namelist():
            if re.search(r'(comments|header|footer|embeddings|vbaProject)',name):entry['extra_parts'].append(name)
            if name.startswith('word/') and name.endswith('.xml'):
                tree=ET.fromstring(z.read(name))
                for i,run in enumerate(tree.findall('.//w:r',ns)):
                    text=''.join(run.itertext())
                    props=run.find('w:rPr',ns)
                    if props is None or not text.strip():continue
                    reasons=[]
                    for c in props:
                        tag=c.tag.split('}')[-1];v=c.get('{'+ns['w']+'}val','')
                        if tag in ['vanish','webHidden'] and v not in ['0','false','off']:reasons.append(tag)
                        if tag=='color' and v.upper() in ['FFFFFF','FEFEFE','FDFDFD']:reasons.append('near-white')
                        if tag=='sz' and v.isdigit() and int(v)<=12:reasons.append('small-font')
                    if reasons:entry['hidden_runs'].append({'part':name,'run':i,'reasons':reasons,'characters':len(text)})
        body=ET.fromstring(z.read('word/document.xml'))
        (out/'problem_visible_text.txt').write_text('\n'.join(''.join(p.itertext()) for p in body.findall('.//w:p',ns)),encoding='utf-8')
    report['docx'].append(entry)
report['csv']={};report['instruction_candidates']=[]
pattern=re.compile(r'ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions|system\s+prompt|忽略.{0,12}(?:指令|题目|要求)|(?:必须|请|应该).{0,12}(?:ChatGPT|Gemini)|隐藏指令|提示词注入',re.I)
for p in files:
    if p.suffix not in ['.csv','.md','.txt']:continue
    text=p.read_text(encoding='utf-8-sig')
    for match in pattern.finditer(text):
        report['instruction_candidates'].append({'file':rel(p),'offset':match.start(),'matched_rule':match.group(0)})
    if p.suffix!='.csv':continue
    df=pd.read_csv(p);frames[rel(p)]=df
    nums=df.select_dtypes(include='number')
    d={'shape':list(df.shape),'columns':list(df),'missing':{c:int(v) for c,v in df.isna().sum().items() if v},'duplicate_rows':int(df.duplicated().sum()),'numeric_ranges':{},'constant_columns':[c for c in df if df[c].nunique(dropna=False)<=1], 'zero_width_cells':{},'formula_like_cells':{}}
    for c in nums:
        s=nums[c];d['numeric_ranges'][c]={'min':s.min(),'max':s.max(),'zeros':int(s.eq(0).sum()),'negative':int(s.lt(0).sum()),'nonfinite_not_missing':int((~np.isfinite(s)&s.notna()).sum())}
    for c in df.select_dtypes(include=['object','str']):
        s=df[c].fillna('').astype(str); n=int(s.str.contains('[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]',regex=True).sum())
        if n:d['zero_width_cells'][c]=n
        n=int(s.str.match(r'^\s*[=+@]').sum())
        if n:d['formula_like_cells'][c]=n
    report['csv'][rel(p)]=d
report['mixture']={}
for name,df in frames.items():
    if '/regmix_tables/' not in name or 'mixture' not in name:continue
    loss=frames[name.replace('mixture','pile_loss')];cols=[c for c in df if c!='index'];s=df[cols].sum(axis=1)
    report['mixture'][name]={'index_unique':bool(df['index'].is_unique),'paired_index_order_equal':bool(df['index'].equals(loss['index'])),'sum_min':s.min(),'sum_max':s.max(),'sum_error_max':abs(s-1).max(),'negative_cells':int(df[cols].lt(0).sum().sum()),'duplicate_recipes':int(df[cols].duplicated().sum())}
mix={k:v for k,v in frames.items() if '/regmix_tables/' in k and 'mixture' in k}
report['recipe_overlaps']=[]
for i,(a,da) in enumerate(mix.items()):
    for b,db in list(mix.items())[i+1:]:
        cols=[c for c in da if c!='index'];sa=set(map(tuple,da[cols].round(10).values));sb=set(map(tuple,db[cols].round(10).values))
        report['recipe_overlaps'].append({'a':Path(a).name,'b':Path(b).name,'exact_rounded10_overlap':len(sa&sb)})
report['compute']= {}
for name,df in frames.items():
    if all(c in df for c in ['N_params_B','D_tokens_B','C_FLOPs_1e21']):
        expected=.006*df.N_params_B*df.D_tokens_B; ratio=df.C_FLOPs_1e21/expected
        report['compute'][name]={'positive_rows':int(expected.gt(0).sum()),'ratio_quantiles':ratio.replace([np.inf,-np.inf],np.nan).quantile([0,.01,.5,.99,1]).to_dict(),'absolute_error_max':(df.C_FLOPs_1e21-expected).abs().max(),'error_over_rounding_5e_5':int((df.C_FLOPs_1e21-expected).abs().gt(5.01e-5).sum())}
report['json']={'parsed':0,'errors':[], 'top_level_keys':collections.Counter(),'instruction_candidates':[]}
for p in files:
    if p.suffix!='.json':continue
    text=p.read_text(encoding='utf-8-sig')
    try:obj=json.loads(text);report['json']['parsed']+=1
    except Exception as e:report['json']['errors'].append({'file':rel(p),'error':str(e)});continue
    if isinstance(obj,dict):report['json']['top_level_keys'].update(obj.keys())
    for m in pattern.finditer(text):report['json']['instruction_candidates'].append({'file':rel(p),'offset':m.start(),'matched_rule':m.group(0)})
report['manifest_mismatches']=[]
manifest=json.loads((root/'source_manifest.json').read_text(encoding='utf-8'))
for row in manifest:
    p=root/row['file']
    size=sum(q.stat().st_size for q in p.rglob('*') if q.is_file()) if p.is_dir() else (p.stat().st_size if p.exists() else None)
    if size!=row['bytes']:report['manifest_mismatches'].append({'file':row['file'],'declared_bytes':row['bytes'],'actual_bytes':size})
save();print('Basic files, CSV, PDF and JSON completed',flush=True)
report['xz']={};quality_ids={}
for p in sorted(root.rglob('*.xz')):
    entry={'rows':0,'bad_json':0,'schema_counts':collections.Counter(),'domains':collections.Counter(),'duplicate_id':0,'quality':{},'instruction_matches_in_corpus':0,'instruction_matches_outside_corpus':0,'outside_corpus_locations':[]}
    ids=set();quality={};stats={}
    with lzma.open(p,'rt',encoding='utf-8') as f:
        for i,line in enumerate(f,1):
            try:obj=json.loads(line)
            except Exception:entry['bad_json']+=1;continue
            entry['rows']+=1;entry['schema_counts'][','.join(sorted(obj))]+=1
            entry['domains'][obj.get('_source_domain','from_filename')]+=1
            ident=str(obj.get('id',''))
            if ident:
                if ident in ids:entry['duplicate_id']+=1
                ids.add(ident)
            for c,v in obj.items():
                if c in ['content','text']:
                    if isinstance(v,str) and pattern.search(v):entry['instruction_matches_in_corpus']+=1
                    continue
                if isinstance(v,str) and pattern.search(v):
                    entry['instruction_matches_outside_corpus']+=1
                    if len(entry['outside_corpus_locations'])<20:entry['outside_corpus_locations'].append({'record':i,'field':c})
                if c in ['id','sub_path','_source_domain','_source_path']:continue
                st=stats.setdefault(c,{'types':collections.Counter(),'null':0,'empty_list':0,'nonfinite':0,'min':float('inf'),'max':float('-inf'),'lengths':collections.Counter()})
                st['types'][type(v).__name__]+=1
                if v is None:st['null']+=1;continue
                if isinstance(v,list):st['lengths'][len(v)]+=1;st['empty_list']+=int(not v)
                vals=v if isinstance(v,list) else [v]
                def flatten(x):
                    if isinstance(x,list):
                        for y in x:yield from flatten(y)
                    else:yield x
                for value in flatten(vals):
                    if isinstance(value,(float,int)):
                        if not np.isfinite(value):st['nonfinite']+=1
                        else:st['min']=min(st['min'],value);st['max']=max(st['max'],value)
    entry['quality']=stats;report['xz'][rel(p)]=entry
    if 'quality' in p.name or 'quality_extended' in str(p):quality_ids[rel(p)]=ids
    save();print('XZ completed:',p.name,entry['rows'],flush=True)
report['quality_id_overlap']=[]
for i,(a,ia) in enumerate(quality_ids.items()):
    for b,ib in list(quality_ids.items())[i+1:]:report['quality_id_overlap'].append({'a':a,'b':b,'overlap':len(ia&ib)})
save();print('Audit complete',flush=True)
