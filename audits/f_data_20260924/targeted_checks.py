from pathlib import Path
import argparse,collections,json,lzma,math
import pandas as pd
P=argparse.ArgumentParser();P.add_argument('--source',type=Path,required=True);a=P.parse_args();r=a.source/'real_attachments';out=Path(__file__).parent;d={}
d['quality_anomalies']={};sample={};qfields=None
paths=[r/'A_data_value/slimpajama_quality_signal_sample.jsonl.xz']+sorted((r/'A_data_value/slimpajama_quality_extended').glob('*.xz'))
for p in paths:
    res={'nonfinite_rows':[],'over100_counts':collections.Counter(),'over100_examples':[],'sample_overlap':0,'overlap_quality_disagreement':0,'corpus_instruction_matches':[]}
    with lzma.open(p,'rt',encoding='utf8') as f:
        for i,line in enumerate(f,1):
            obj=json.loads(line)
            fields=[c for c in obj if c not in ['id','sub_path','content','_source_domain','_source_path']]
            if p==paths[0]:sample[obj['id']]={c:obj[c] for c in fields}
            elif obj['id'] in sample:
                res['sample_overlap']+=1
                if json.dumps(sample[obj['id']],sort_keys=True)!=json.dumps({c:obj[c] for c in fields},sort_keys=True):res['overlap_quality_disagreement']+=1
            for c in fields:
                v=obj[c];vals=v if isinstance(v,list) else [v]
                if any(isinstance(x,(int,float)) and not math.isfinite(x) for x in vals):res['nonfinite_rows'].append({'record_1based':i,'id':obj['id'],'field':c,'nonfinite_elements':sum(isinstance(x,(int,float)) and not math.isfinite(x) for x in vals)})
                if ('frac' in c or 'fraction' in c) and isinstance(v,(float,int)) and v>100:
                    res['over100_counts'][c]+=1
                    if len(res['over100_examples'])<4:res['over100_examples'].append({'record_1based':i,'id':obj['id'],'field':c,'value':v})
    d['quality_anomalies'][p.name]=res
    print('Targeted quality complete',p.name,flush=True)
B=r/'B_scaling_laws';C=r/'C_efficiency_evolution'
q=pd.read_csv(B/'supplementary_NQ_experiment_large.csv');d['B8_floor']={'rows_at_0_5':int(q.val_loss.eq(.5).sum()),'duplicate_designs':int(q.duplicated(['N_params_B','D_tokens_B','Q_score']).sum()),'duplicate_experiment_id':int(q.experiment_id.duplicated().sum())}
lb=pd.read_csv(C/'leaderboard_cleaned.csv');avg=next(c for c in lb if c.startswith('Average'));bridge=pd.read_csv(C/'loss_benchmark_bridge_expanded.csv');d['bridge_row_matching']=[]
for i,row in bridge.iterrows():
    matches=lb[lb.Model.eq(row.Model)]
    d['bridge_row_matching'].append({'Model':row.Model,'candidate_rows':len(matches),'matching_average_rows':int(matches[avg].sub(row.LB_Average).abs().lt(1e-7).sum())})
ts=pd.read_csv(C/'leaderboard_extended_timeseries.csv');d['C3_zero_parameters']=int(ts.Params_B.le(0).sum())
d['C1_duplicate_model_names']=lb.loc[lb.Model.duplicated(False),'Model'].value_counts().to_dict()
x=pd.read_csv(B/'pythia_training_log_existing.csv');base=pd.read_csv(B/'scaling_baseline.csv');d['B4_nearest_B1']=[]
for _,row in base[base.family.eq('Pythia')].iterrows():
    nearest=x.iloc[((x.N_params_B/row.N_params_B).apply(math.log).abs()*10+(x.D_tokens_B-row.D_tokens_B).abs()/300).argmin()]
    d['B4_nearest_B1'].append({'N_B4':row.N_params_B,'D_B4':row.D_tokens_B,'Loss_B4':row.val_loss,'N_B1':nearest.N_params_B,'D_B1':nearest.D_tokens_B,'Loss_B1':nearest.val_loss,'delta_loss':row.val_loss-nearest.val_loss})
manifest=json.loads((r/'source_manifest.json').read_text(encoding='utf8'));d['manifest_directory_size']=[{'declared':x['bytes'],'actual':sum(p.stat().st_size for p in (r/x['file']).rglob('*') if p.is_file())} for x in manifest if (r/x['file']).is_dir()]
(out/'targeted.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
