"""Cross-file checks; descriptive evidence only, not a fitted contest model."""
from pathlib import Path
import argparse,json,re,collections,zipfile
import pandas as pd
import numpy as np
from pypdf import PdfReader
P=argparse.ArgumentParser();P.add_argument('--source',type=Path,required=True);a=P.parse_args()
r=a.source/'real_attachments';out=Path(__file__).parent;d={}
def read(n):return pd.read_csv(r/n)
def records(df):return json.loads(df.to_json(orient='records',force_ascii=False))
B='B_scaling_laws/';C='C_efficiency_evolution/'
d['quality_direction']={}
qframes={}
for p in (r/B).glob('supplementary_NQ*.csv'):
    df=pd.read_csv(p);qframes[p.name]=df;changes=[];groups=[]
    for key,g in df.groupby(['N_params_B','D_tokens_B']):
        g=g.sort_values('Q_score'); diff=np.diff(g.val_loss)
        changes.extend(diff.tolist());groups.append({'N':key[0],'D':key[1],'n':len(g),'increasing_steps':int((diff>0).sum()),'decreasing_steps':int((diff<0).sum()),'correlation':g.Q_score.corr(g.val_loss)})
    d['quality_direction'][p.name]={'rows':len(df),'Q_range':[df.Q_score.min(),df.Q_score.max()],'loss_range':[df.val_loss.min(),df.val_loss.max()],'groups':len(groups),'increasing_steps':sum(x>0 for x in changes),'decreasing_steps':sum(x<0 for x in changes),'all_increasing_groups':sum(x['increasing_steps']==x['n']-1 for x in groups),'all_decreasing_groups':sum(x['decreasing_steps']==x['n']-1 for x in groups),'examples':records(df.head(10)),'data_type_counts':df.data_type.value_counts().to_dict() if 'data_type' in df else None}
d['NQ_overlap']=[]
for i,(n,x) in enumerate(qframes.items()):
    for m,y in list(qframes.items())[i+1:]:
        z=x.merge(y,on=['N_params_B','D_tokens_B','Q_score'],suffixes=('_x','_y'))
        d['NQ_overlap'].append({'a':n,'b':m,'shared_design_rows':len(z),'different_loss_rows':int((z.val_loss_x-z.val_loss_y).abs().gt(1e-8).sum()),'max_loss_difference':(z.val_loss_x-z.val_loss_y).abs().max()})
x=read(B+'pythia_training_log_existing.csv');d['pythia_aux']={'run_id_unique':bool(x.run_id.is_unique),'models':x.N_params_B.nunique(),'precision_counts':x.precision.value_counts().to_dict(),'per_model':[],'ppl_exp_loss_relative_max':((x.ppl/np.exp(x.val_loss))-1).abs().max()}
for n,g in x.groupby('N_params_B'):
    d['pythia_aux']['per_model'].append({'N':n,'rows':len(g),'precision_values':g.precision.unique().tolist(),'wd_unique':g.wd.nunique(),'lr_unique':g.lr.nunique(),'step_time_unique':g.step_time_ms.nunique(),'D_monotonic_by_step':bool(g.sort_values('steps').D_tokens_B.is_monotonic_increasing)})
base=read(B+'scaling_baseline.csv');d['baseline_pythia']=records(base[base.family.str.contains('pythia',case=False)])
d['large_model_accessibility']=read(B+'supplementary_large_models.csv').accessibility.value_counts(dropna=False).to_dict()
lb=read(C+'leaderboard_cleaned.csv');ts=read(C+'leaderboard_extended_timeseries.csv');enh=read(C+'leaderboard_enhanced.csv')
cols=['IFEval','BBH','MATH Lvl 5','GPQA','MUSR','MMLU-PRO'];tcols=['IFEval','BBH','MATH_Lvl5','GPQA','MUSR','MMLU_PRO']
avg=next(c for c in lb if c.startswith('Average'))
d['leaderboard']={'unique_model':lb.Model.nunique(),'types':lb.Type.value_counts().to_dict(),'mean_disagreement':int((lb[avg]-lb[cols].mean(axis=1)).abs().gt(1e-6).sum()),'mean_max_diff':(lb[avg]-lb[cols].mean(axis=1)).abs().max(),'invalid_params_models':records(lb[lb['#Params (B)'].isna()|lb['#Params (B)'].le(0)][['Model','#Params (B)']]),'submission_range':[lb['Submission Date'].min(),lb['Submission Date'].max()]}
delta=ts.Average-ts[tcols].mean(axis=1)
d['timeseries']={'source_counts':ts.Source.value_counts().to_dict(),'years':ts.Year.value_counts().to_dict(),'duplicate_models':int(ts.Model.duplicated().sum()),'average_not_sixmean_count':int(delta.abs().gt(.01).sum()),'average_not_sixmean_rows':records(ts.loc[delta.abs().gt(.01)].assign(recomputed_mean=ts[tcols].mean(axis=1),difference=delta))}
join=lb.merge(ts,on='Model',suffixes=('_lb','_ts'))
d['timeseries']['matched_C1_rows']=len(join)
d['timeseries']['parameter_disagreements']=records(join[(join['#Params (B)']-join.Params_B).abs().gt(.001)|join['#Params (B)'].isna()][['Model','#Params (B)','Params_B']])
d['timeseries']['naive_name_join_score_disagreements_tolerance_00501']=int((join[avg]-join.Average).abs().gt(.00501).sum())
d['timeseries']['note']='Name-only joins are many-to-many; these discrepancies are not automatically source errors.'
keycols=['Model']+cols
for c in cols:lb[c+'_key']=lb[c].round(7)
for c,t in zip(cols,tcols):ts[c+'_key']=ts[t].round(7)
z=ts[ts.Source.eq('Open LLM Leaderboard')].merge(lb,on=['Model']+[c+'_key' for c in cols],suffixes=('_ts','_lb'),how='left',indicator=True)
d['timeseries']['score_key_unmatched']=int(z['_merge'].eq('left_only').sum())
d['timeseries']['score_key_average_mismatch']=int((z.Average-z[avg]).abs().gt(.00501).sum())
d['epoch_matches']={'dated_rows':int(enh.Epoch_AI_Publication_Date.notna().sum()),'unique_publication_dates':int(enh.Epoch_AI_Publication_Date.nunique()),'examples':records(enh[enh.Epoch_AI_Publication_Date.notna()].head(5))}
bridge=read(C+'loss_benchmark_bridge_expanded.csv');bc=['LB_IFEval','LB_BBH','LB_MATH','LB_GPQA','LB_MUSR','LB_MMLU_PRO']
z=bridge.merge(lb,on='Model');diffs={}
for c,e in zip(bc,cols):diffs[c]={'rows_different':int((z[c]-z[e]).abs().gt(1e-6).sum()),'max_diff':(z[c]-z[e]).abs().max()}
d['bridge']={'comparability':bridge.Loss_Comparability.value_counts().to_dict(),'matched_C1':len(z),'score_differences':diffs,'average_vs_sixmean_count':int((bridge.LB_Average-bridge[bc].mean(axis=1)).abs().gt(1e-6).sum()),'high':records(bridge[bridge.Loss_Comparability.str.startswith('High')])}
try:
    pq=pd.read_parquet(next((r/C/'data').glob('*.parquet')));d['parquet']={'shape':list(pq.shape),'columns':list(pq)}
except ImportError:
    pq=pd.DataFrame();d['parquet']={'status':'not parsed: pyarrow/fastparquet unavailable in bundled Python'}
if all(c in pq for c in ['Model']+cols):
    d['parquet']['name_join_before_normalizing']=len(lb.merge(pq,on='Model'))
    d['parquet']['fullname_equals_C1_row_order']=bool(lb.Model.reset_index(drop=True).equals(pq.fullname.reset_index(drop=True)))
    d['parquet']['score_mismatches_by_verified_row_order']={c:int((lb[c].reset_index(drop=True)-pq[c].reset_index(drop=True)).abs().gt(1e-8).sum()) for c in cols} if d['parquet']['fullname_equals_C1_row_order'] else None
    d['parquet']['flagged_counts']=pq.Flagged.value_counts(dropna=False).to_dict()
    d['parquet']['example_raw_vs_processed']={c:{'raw':pq[c+' Raw'].iloc[0],'processed':pq[c].iloc[0]} for c in cols}
epoch=read(C+'epoch_all_ai_models.csv');d['metadata_keyword_context']=[]
for c in epoch.select_dtypes(include=['str','object']):
    for i,v in epoch[c].items():
        if isinstance(v,str) and re.search(r'system prompt',v,re.I):
            d['metadata_keyword_context'].append({'row_1based':i+2,'field':c,'context':v[:700]})
d['json_detail']={'directories':0,'parseable_directories':0,'system_instruction_nonempty':0,'chat_template_nonempty':0,'latest_parseable_examples':[],'task_counts':collections.Counter()}
for folder in (r/C/'detailed_results').iterdir():
    if not folder.is_dir():continue
    d['json_detail']['directories']+=1;parsed=[]
    for p in sorted(folder.glob('*.json'),reverse=True):
        try:o=json.loads(p.read_text(encoding='utf8'))
        except json.JSONDecodeError:continue
        parsed.append((p,o))
        d['json_detail']['system_instruction_nonempty']+=int(bool(o.get('system_instruction')))
        d['json_detail']['chat_template_nonempty']+=int(bool(o.get('chat_template')))
    if parsed:
        d['json_detail']['parseable_directories']+=1
        p,o=parsed[0];d['json_detail']['task_counts'].update(o['results'].keys())
        if len(d['json_detail']['latest_parseable_examples'])<2:d['json_detail']['latest_parseable_examples'].append({'file':str(p.relative_to(r)),'model':o.get('model_name'),'results':o['results'],'config':o.get('config')})
d['pdf_after']={'sha256':__import__('hashlib').sha256((a.source/'数据说明.pdf').read_bytes()).hexdigest(),'text_chars':sum(len(p.extract_text() or '') for p in PdfReader(a.source/'数据说明.pdf').pages)}
(out/'crosschecks.json').write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf8');print('Crosschecks complete')
