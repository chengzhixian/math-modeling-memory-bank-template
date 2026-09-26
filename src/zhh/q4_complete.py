"""Q4 conditional answer. No hidden-PDF extraction; only current C attachments.
Run: python -B src/zhh/q4_complete.py. Requires numpy and pandas.
"""
from __future__ import annotations
import csv
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/raw/real_attachments/C_efficiency_evolution'
OUT = ROOT / 'outputs/Q4/prepared'
SEED = 20260926
Q3_REF = 'c052b6918c3f77a2285622521d8abb1b429513be'
TASKS = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO']
BTASKS = ['LB_IFEval', 'LB_BBH', 'LB_MATH', 'LB_GPQA', 'LB_MUSR', 'LB_MMLU_PRO']
PERMISSIVE = {'apache-2.0', 'mit', 'bsd-3-clause', 'bsd-2-clause', 'cc0-1.0'}
GIT = 'git'


def read(name):
    return pd.read_csv(DATA / name, keep_default_na=False)


def numeric(s):
    return pd.to_numeric(s.replace(r'^\s*$', np.nan, regex=True), errors='coerce')


def json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def dump(name, obj):
    (OUT / name).write_text(json.dumps(json_safe(obj), ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output([GIT, '-C', str(ROOT), *args], text=True, encoding='utf-8').strip()


def sigmoid(z):
    return 100 / (1 + np.exp(-np.clip(z, -40, 40)))


def logit(s):
    p = np.clip(np.asarray(s, dtype=float)/100, 0.001, 0.999)
    return np.log(p/(1-p))


def ols(x, y):
    x = np.asarray(x, dtype=float)
    x = np.column_stack([np.ones(len(x)), x])
    coef, _, rank, singular = np.linalg.lstsq(x, y, rcond=None)
    if rank != x.shape[1]:
        raise ValueError('rank deficient design')
    return coef


def metric(y, pred):
    y, pred = np.array(y), np.array(pred)
    return {'n': len(y), 'rmse': np.sqrt(np.mean((y-pred)**2)),
            'mae': np.mean(np.abs(y-pred)),
            'r2': 1-np.sum((y-pred)**2)/np.sum((y-y.mean())**2) if np.std(y)>0 else None}


def leaderboard():
    raw = read('leaderboard_enhanced.csv')
    raw['source_row'] = np.arange(2, len(raw)+2)
    raw['date'] = pd.to_datetime(raw['Submission Date'], errors='coerce', utc=True)
    raw['N'] = numeric(raw['#Params (B)'])
    for c in TASKS:
        raw[c] = numeric(raw[c])
    raw['open_status'] = raw.Epoch_AI_Open_Weights.str.strip().str.lower()
    raw['license'] = raw['Hub License'].str.strip().str.lower()
    raw['type'] = np.where(raw.Type.str.lower().str.contains('pretrained'), 'pretrained', 'non_pretrained')
    raw['type_detail'] = raw.Type
    raw['model_class'] = np.select([
        raw.Type.str.contains('continuously pretrained'), raw.Type.str.contains('pretrained'),
        raw.Type.str.contains('chat models'), raw.Type.str.contains('fine-tuned'),
        raw.Type.str.contains('merges'), raw.Type.str.contains('multimodal')],
        ['continued_pretrained','pretrained','chat','domain_finetuned','merge','multimodal'], default='unknown')
    valid = raw.date.notna() & (raw.N > 0) & np.isfinite(raw.N) & raw[TASKS].notna().all(axis=1) & raw[TASKS].ge(0).all(axis=1) & raw[TASKS].le(100).all(axis=1)
    license_proxy = ~raw.license.isin(['', 'unknown', 'other', 'n/a', 'nan'])
    expanded = valid & (raw.open_status != 'no') & ((raw.open_status == 'yes') | license_proxy)
    rows = raw[expanded].copy()
    rows['S'] = rows[TASKS].mean(axis=1)
    all_versions = rows.copy()
    # Stable ties preserve the last CSV row; same-name revisions never enter twice.
    rows = rows.sort_values(['date', 'source_row']).drop_duplicates('Model', keep='last').copy()
    rows['logN'] = np.log10(rows.N)
    rows['t'] = (rows.date-pd.Timestamp('2024-06-01', tz='UTC')).dt.total_seconds()/(86400*365.25/12)
    rows['z'] = logit(rows.S)
    rows['month'] = rows.date.dt.strftime('%Y-%m')
    rows['developer'] = rows.Model.str.split('/').str[0]
    rows['license_research_status'] = np.where(rows.license.isin(PERMISSIVE), 'permissive_license_label_not_repository_verified', 'custom_or_unknown_manual_review_needed')
    rows.to_csv(OUT/'leaderboard_sample.csv', index=False, lineterminator='\n')
    all_versions.to_csv(OUT/'leaderboard_all_versions.csv', index=False, lineterminator='\n')
    leaderboard.all_versions = all_versions
    return rows, {'raw_n':len(raw), 'expanded_before_dedup':int(expanded.sum()), 'expanded_latest':len(rows),
        'strict_latest':int((rows.open_status=='yes').sum()), 'permissive_latest':int(rows.license.isin(PERMISSIVE).sum()),
        'invalid_numeric_or_date':int((~valid).sum()), 'explicit_no_excluded':int((valid & (raw.open_status=='no')).sum()),
        'minimum_date':rows.date.min().strftime('%Y-%m-%d'), 'forecast_origin':rows.date.max().strftime('%Y-%m-%d'),
        'join_policy':'No C2-C4 or C2-C6 name-only join. C4 allocation transfers only by declared scenario.',
        'logit_floor':0.001, 'license_policy':'Permissive whitelist is a label sensitivity, not verified weights or a legal conclusion.'}


def audit_resources(cutoff):
    r = read('epoch_all_ai_models.csv')
    r['source_row'] = np.arange(2, len(r)+2)
    r['date'] = pd.to_datetime(r['Publication date'], errors='coerce', utc=True)
    for old, new in [('Parameters','N'), ('Training compute (FLOP)','C'), ('Training dataset size (total)','D')]:
        r[new] = numeric(r[old])
    reasons = []
    for _, x in r.iterrows():
        why = []
        if x['Domain'].strip().lower() != 'language': why.append('not_text_only_language_domain')
        if not re.search(r'language modeling|language generation|text autocompletion|code generation', x['Task'], re.I): why.append('not_generative_language_task')
        if x['Open model weights?'].strip().lower() != 'yes': why.append('not_explicit_open_weights')
        if pd.isna(x.date): why.append('missing_date')
        elif x.date > cutoff: why.append('after_forecast_origin')
        elif x.date < pd.Timestamp('2019-01-01', tz='UTC'): why.append('before_resource_window')
        if not all(np.isfinite(x[v]) and x[v]>0 for v in ['N','C','D']): why.append('missing_or_invalid_N_C_D')
        notes = x['Dataset size notes']
        if not re.search(r'\btokens?\b', notes, re.I): why.append('no_explicit_token_evidence')
        if re.search(r'\bwords?\b|\bimages?\b|\bexamples?\b|\bsentences?\b', notes, re.I): why.append('mixed_or_ambiguous_dataset_unit')
        if x['Base model'].strip(): why.append('base_model_or_continued_training')
        architecture_text = ' '.join(str(x[c]) for c in ['Model','Parameters notes','Training compute notes','Abstract'])
        if re.search(r'\bMoE\b|mixture.of.experts|sparse.*expert|active parameters|activated parameters', architecture_text, re.I): why.append('sparse_architecture_coordinate')
        if x['Confidence'].strip().lower() not in {'confident','likely'}: why.append('low_or_unknown_confidence')
        if re.search(r'benchmark|performance', x['Training compute estimation method'], re.I): why.append('compute_imputed_from_benchmark')
        reasons.append(';'.join(why))
    r['exclusion_reasons'] = reasons
    r['candidate'] = r.exclusion_reasons.eq('')
    r['C_over_6ND'] = r.C/(6*r.N*r.D)
    r['primary'] = r.candidate & r.C_over_6ND.between(0.5, 2)
    r['loose_ratio'] = r.candidate & r.C_over_6ND.between(0.1, 10)
    audit_columns=['source_row','Model','Domain','Task','Publication date','Parameters','Parameters notes',
        'Training compute (FLOP)','Training compute notes','Training dataset size (total)','Dataset size notes',
        'Training compute estimation method','Confidence','Base model','Open model weights?',
        'exclusion_reasons','candidate','primary','loose_ratio','C_over_6ND']
    def export_resource(frame, name, columns):
        export=frame[columns].copy()
        # Source notes have trailing spaces inside multiline quoted cells.
        # Normalize only display whitespace in derived audit tables; source row
        # IDs and the raw-file SHA retain the exact original evidence.
        for col in export.select_dtypes(include=['str','object']).columns:
            export[col]=export[col].map(lambda v:'\n'.join(line.rstrip(' \t') for line in v.splitlines()) if isinstance(v,str) else v)
        export.to_csv(OUT/name,index=False,lineterminator='\n')
    export_resource(r,'c4_resource_audit.csv',audit_columns)
    useful = r[r.primary].copy().sort_values(['date','source_row']).drop_duplicates('Model', keep='last')
    export_resource(useful,'c4_usable_resources.csv',audit_columns+['date','N','C','D'])
    if len(useful)<10: raise ValueError('insufficient audited resource samples')
    useful['year'] = useful.date.dt.year
    annual = []
    for year, g in useful.groupby('year'):
        annual.append({'year':year,'n':len(g),'q90_logC':np.quantile(np.log10(g.C),.9),
            'q90_logN':np.quantile(np.log10(g.N),.9),'q90_logD':np.quantile(np.log10(g.D),.9),
            'median_tokens_per_parameter':np.median(g.D/g.N), 'partial_year':year==cutoff.year})
    pd.DataFrame(annual).to_csv(OUT/'c4_annual_resources.csv', index=False, lineterminator='\n')
    a = pd.DataFrame(annual)
    fit_years = a[(a.year>=2020)&(a.year<cutoff.year)&(a.n>=3)]
    if len(fit_years)<3: raise ValueError('insufficient complete resource years')
    slope = ols((fit_years.year-2020).to_numpy()[:,None],fit_years.q90_logC)[1]
    regression = ols(np.column_stack([np.log10(useful.N),np.log10(useful.D)]),np.log10(useful.C))
    allocation = ols(np.log10(useful.C).to_numpy()[:,None],np.log10(useful.N))
    detail = {'raw':len(r), 'numeric_complete':int((r[['N','C','D']].gt(0)&np.isfinite(r[['N','C','D']])).all(axis=1).sum()),
        'candidate_n':int(r.candidate.sum()),'primary_n':len(useful), 'loose_ratio_n':int(r.loose_ratio.sum()),
        'reason_counts':dict(pd.Series(';'.join(reasons).split(';')).value_counts().drop('',errors='ignore')),
        'annual':annual,'complete_years_used':fit_years.year.tolist(), 'gC_log10_per_year':max(0,float(slope)),
        'unclamped_gC':float(slope), 'C_regression_intercept_logN_logD':regression,
        'descriptive_N_on_C_elasticity':allocation[1],
        'ratio_quantiles':np.quantile(useful.C_over_6ND,[.05,.5,.95]),
        'support':{k:[useful[k].min(),useful[k].max()] for k in ['N','D','C']},
        'architecture_status':'No independent architecture column. Text screening cannot guarantee all surviving models are dense.',
        'stage_status':'Base-model rows excluded; absent base-model field is no proof of no posttraining.',
        'unit_status':'Only token-explicit Dataset size notes without conflicting unit terms retained; no general words-to-token conversion.',
        'circularity':'Operation-counting C often derived from N,D. Ratio gate is coordinate QC, not independent validation of 6ND.',
        'future_policy':'All resources after the C2 origin excluded; annual 2025 treated partial, not growth-training target.'}
    return useful, detail


def fit_frontier(rows):
    return ols(rows[['logN','t']].to_numpy(), rows.z)


def anchor(rows, end=None, q=.9, window=2):
    end = rows.t.max() if end is None else end
    recent = rows[rows.t>=end-window]
    f = float(recent.S.quantile(q))
    high = recent[recent.S>=f]
    return {'S':f,'N_B':float(10**high.logN.median()),'t':float(end),'recent_n':len(recent),'high_n':len(high)}


def shapley(z0, dn, dt):
    # Exact two-component decomposition of the bounded score change.
    a = .5*((sigmoid(z0+dn)-sigmoid(z0))+(sigmoid(z0+dn+dt)-sigmoid(z0+dt)))
    b = .5*((sigmoid(z0+dt)-sigmoid(z0))+(sigmoid(z0+dn+dt)-sigmoid(z0+dn)))
    total = a+b
    abs_total = abs(a)+abs(b)
    return {'scale_points':a,'non_scale_points':b,'total_model_points':total,
        'signed_scale_share':a/total if abs(total)>.1 else None,'signed_non_scale_share':b/total if abs(total)>.1 else None,
        'absolute_scale_share':abs(a)/abs_total if abs_total else None,
        'absolute_non_scale_share':abs(b)/abs_total if abs_total else None}


def rolling(rows, resources, label='primary'):
    # Reconstruct each past training snapshot before deduplication, never select
    # the final revision of a repeated model using a future submission date.
    rows=rows.copy()
    rows['t']=(rows.date-pd.Timestamp('2024-06-01',tz='UTC')).dt.total_seconds()/(86400*365.25/12)
    rows['month']=rows.date.dt.strftime('%Y-%m')
    rows['logN']=np.log10(rows.N); rows['z']=logit(rows.S)
    rows['developer']=rows.Model.str.split('/').str[0]
    results=[]
    for typ,g in rows.groupby('type'):
        months=sorted(g.month.unique())
        for m in months[4:]:
            train=g[g.month<m].sort_values(['date','source_row']).drop_duplicates('Model',keep='last')
            test=g[g.month==m].sort_values(['date','source_row']).drop_duplicates('Model',keep='last')
            if len(train)<20 or len(test)<10: continue
            b=fit_frontier(train); a=anchor(train)
            h=float(test.t.max()-a['t'])
            annual=[]
            visible=resources[resources.date<=train.date.max()]
            for year,v in visible.groupby(visible.date.dt.year):
                if year<train.date.max().year and year>=2020 and len(v)>=3:
                    annual.append((year,float(np.quantile(np.log10(v.C),.9))))
            gc=max(0,ols(np.array([v[0]-2020 for v in annual])[:,None],np.array([v[1] for v in annual]))[1]) if len(annual)>=3 else 0
            pred=sigmoid(logit(a['S'])+b[1]*.5*gc*h/12+.5*b[2]*h)
            monthly=train.groupby('month').agg(t=('t','max'),S=('S',lambda x:x.quantile(.9)))
            trend=ols(monthly.t.to_numpy()[:,None],logit(monthly.S))
            trend_pred=sigmoid(trend[0]+trend[1]*test.t.max())
            overlap=set(train.developer)&set(test.developer)
            results.append({'type':typ,'test_month':m,'train_n':len(train),'test_n':len(test),
                'actual_q90':test.S.quantile(.9),'constant':a['S'],'monthly_trend':trend_pred,'resource_dynamic':pred,
                'gC_visible':gc,'developer_overlap_test_fraction':test.developer.isin(overlap).mean(),
                'model_overlap_test_fraction':test.Model.isin(set(train.Model)).mean(),
                'individual_score_rmse':metric(test.S,sigmoid(b[0]+b[1]*test.logN+b[2]*test.t))['rmse']})
    table=pd.DataFrame(results)
    table.to_csv(OUT/f'rolling_frontier_backtest_{label}.csv',index=False,lineterminator='\n')
    summary={typ:{k:metric(g.actual_q90,g[k]) for k in ['constant','monthly_trend','resource_dynamic']} for typ,g in table.groupby('type')}
    return {'folds':len(table),'summary':summary,'design':'Expanding months, first four for training; monthly q90 target, >=10 test models. Diagnostic, not blind final test. Developer overlap retained and reported.'}


def dynamics(rows, resources, resource_info):
    coefficients=[]; contributions=[]; forecasts=[]; sensitivities=[]; unavailable=[]
    gc=resource_info['gC_log10_per_year']
    rng=np.random.default_rng(SEED)
    origin=rows.date.max()
    d0=float(resources[resources.date>=origin-pd.Timedelta(days=365)].D.median()/1e9)
    for filter_name, subset in [('base_chat_domain_latest',rows[rows.model_class.isin(['pretrained','chat','domain_finetuned'])]),
        ('expanded_latest',rows),('strict_yes',rows[rows.open_status=='yes']),('permissive_label',rows[rows.license.isin(PERMISSIVE)])]:
      for typ,g in subset.groupby('type'):
        if len(g)<30 or g.month.nunique()<4: continue
        b=fit_frontier(g); end=rows.t.max(); a=anchor(g,end)
        pred=sigmoid(b[0]+b[1]*g.logN+b[2]*g.t)
        coefficients.append({'filter':filter_name,'type':typ,'n':len(g),'intercept':b[0],'b_logN':b[1],'b_month':b[2],
            'fit_rmse':metric(g.S,pred)['rmse'],'frontier_start':a['S'],'N_anchor_B':a['N_B']})
        for window in [1,2,3]:
            early=g[g.t<=g.t.min()+window]; late=g[g.t>=end-window]
            if len(early)<10 or len(late)<10: continue
            f0=float(early.S.quantile(.9)); f1=float(late.S.quantile(.9))
            n0=float(early[early.S>=f0].logN.median()); n1=float(late[late.S>=f1].logN.median())
            t0=float(early.t.median()); t1=float(late.t.median())
            c=shapley(logit(f0),b[1]*(n1-n0),b[2]*(t1-t0))
            contributions.append({'filter':filter_name,'type':typ,'window_months':window,'n_start':len(early),'n_end':len(late),
                'frontier_start':f0,'frontier_end':f1,'observed_change':f1-f0,'unexplained_change':f1-f0-c['total_model_points'],
                'accounting_non_scale_including_unexplained':f1-f0-c['scale_points'],
                'accounting_scale_share':c['scale_points']/(f1-f0) if abs(f1-f0)>.1 else None,
                'accounting_non_scale_share':1-c['scale_points']/(f1-f0) if abs(f1-f0)>.1 else None,
                'logN_start':n0,'logN_end':n1,'t_start':t0,'t_end':t1,**c})
        if a['recent_n']<10:
            unavailable.append({'filter':filter_name,'type':typ,'recent_n':a['recent_n'],'reason':'fewer_than_10_recent_models_no_forecast'})
            continue
        groups=[v for _,v in g.groupby('developer')]
        boots=[]
        for _ in range(200):
            draw=pd.concat([groups[i] for i in rng.integers(0,len(groups),len(groups))],ignore_index=True)
            if len(draw[draw.t>=end-2])<5: continue
            try: boots.append((fit_frontier(draw),anchor(draw,end)))
            except ValueError: continue
        if len(boots)<100: raise ValueError('too few valid block draws')
        monthly=g.groupby('month').agg(t=('t','max'),S=('S',lambda v:v.quantile(.9)))
        trend=ols(monthly.t.to_numpy()[:,None],logit(monthly.S))
        for h in [12,24]:
          for name,slow in [('historical_growth',1),('half_growth',.5),('quarter_growth',.25),('no_growth',0)]:
            dzN=b[1]*.5*gc*slow*h/12; dzt=.5*b[2]*h
            point=float(sigmoid(logit(a['S'])+dzN+dzt))
            conditional=[sigmoid(logit(ab['S'])+bb[1]*.5*gc*slow*h/12+.5*bb[2]*h) for bb,ab in boots]
            envelope=[]
            for eta in [.25,.5,.75]:
              for lam in [0,.5,1]:
                value=sigmoid(logit(a['S'])+b[1]*eta*gc*slow*h/12+lam*b[2]*h)
                sensitivities.append({'filter':filter_name,'type':typ,'horizon_months':h,'scenario':name,'eta':eta,'drift_retention':lam,'frontier_quantile':.9,'anchor_window_months':2,'score':value})
                for resource_multiplier in [.5,1,1.5]:
                    envelope.extend(sigmoid(logit(ab['S'])+bb[1]*eta*gc*slow*resource_multiplier*h/12+lam*bb[2]*h) for bb,ab in boots)
            model_choices=[a['S'],sigmoid(trend[0]+trend[1]*(end+h))]
            for q,window in [(.85,2),(.95,2),(.9,1),(.9,3)]:
                alt=anchor(g,end,q,window)
                value=sigmoid(logit(alt['S'])+dzN+dzt)
                model_choices.append(value)
                sensitivities.append({'filter':filter_name,'type':typ,'horizon_months':h,'scenario':name,'eta':.5,'drift_retention':.5,'frontier_quantile':q,'anchor_window_months':window,'score':value})
            lo=min(point,np.quantile(envelope,.05),*model_choices); hi=max(point,np.quantile(envelope,.95),*model_choices)
            nfuture=a['N_B']*10**(.5*gc*slow*h/12)
            dfuture=d0*10**(.5*gc*slow*h/12)
            forecasts.append({'filter':filter_name,'type':typ,'origin':origin.strftime('%Y-%m-%d'),
                'target_date':(origin+pd.DateOffset(months=h)).strftime('%Y-%m-%d'),'horizon_months':h,'scenario':name,
                'status':'conditional_scenario_not_empirical_forecast','frontier_definition':'recent_2_month_type_score_q90_local_translation',
                'observed_anchor_score':a['S'],'predicted_score':point,'conditional_parameter_p05':np.quantile(conditional,.05),
                'conditional_parameter_p95':np.quantile(conditional,.95),'scenario_lower':lo,'scenario_upper':hi,
                'constant_baseline':a['S'],'monthly_trend_scenario':model_choices[1],
                'gC_log10_per_year':gc*slow,'eta_assumed':.5,'drift_retention_assumed':.5,
                'N_anchor_B':a['N_B'],'N_future_B':nfuture,'D_anchor_B_scenario':d0,'D_future_B_scenario':dfuture,
                'C_anchor_FLOPs_scenario':6e18*a['N_B']*d0,'C_future_FLOPs_scenario':6e18*nfuture*dfuture,
                'N_extrapolation_log10_beyond_C2':max(0,np.log10(nfuture)-g.logN.max()),
                'D_extrapolation_log10_beyond_C4':max(0,np.log10(dfuture*1e9/resource_info['support']['D'][1])),
                'time_extrapolation_observed_spans':h/(g.t.max()-g.t.min()),'bootstrap_draws':len(boots),
                **shapley(logit(a['S']),dzN,dzt)})
    for name,table in [('dynamic_coefficients',coefficients),('historical_contributions',contributions),('frontier_forecast',forecasts),('forecast_sensitivity',sensitivities)]:
        pd.DataFrame(table).to_csv(OUT/f'{name}.csv',index=False,lineterminator='\n')
    return {'coefficients':coefficients,'contributions':contributions,'predictions':forecasts,'unavailable_filter_type_forecasts':unavailable,
        'bootstrap':'200 developer blocks, seed 20260926; conditional parameter ranges, not total prediction intervals',
        'range_scope':'5--95% bootstrap pooled over eta, drift retention and C-growth multipliers; expanded to include constant, monthly-trend, q85/q95 and 1/3-month anchor alternatives. A sensitivity envelope, not a calibrated coverage claim.',
        'resource_transfer':'C4 D anchor is a recent median; pairing with C2 frontier N is assumed. No observed model join.',
        'data_effect':'D determines remaining resource allocation through 6ND. C2 has no D; no independent empirical D-to-score coefficient is claimed.'}


def bridge_analysis():
    r=read('loss_benchmark_bridge_expanded.csv')
    for c in ['Val_Loss','N_params_B',*BTASKS]: r[c]=numeric(r[c])
    r=r[np.isfinite(r.Val_Loss)&(r.Val_Loss>0)&(r.N_params_B>0)&r[BTASKS].notna().all(axis=1)].copy()
    r['S']=r[BTASKS].mean(axis=1); r['z']=logit(r.S); r['logN']=np.log10(r.N_params_B)
    r['grade']=np.where(r.Loss_Comparability.str.lower().str.startswith('high'),'high','medium')
    def report_family(source):
        s=source.lower()
        # Group report-name aliases and adjacent versions conservatively. This
        # is a leakage guard, not a claim of equal validation-loss coordinates.
        for key,patterns in [('pythia',['pythia']),('qwen',['qwen']),('gemma',['gemma']),
            ('llama',['llama']),('phi',['phi-']),('yi',['yi']),('falcon',['falcon']),
            ('mistral_mixtral',['mistral','mixtral']),('deepseek',['deepseek']),
            ('opt',['opt paper']),('bloom',['bloom']),('gpt_neox',['neox'])]:
            if any(p in s for p in patterns): return key
        return source
    r['report_family']=r.Loss_Source.map(report_family)
    r.to_csv(OUT/'bridge_sample.csv',index=False,lineterminator='\n')
    diagnostics=[]; mappings=[]
    for name,g in [('high',r[r.grade=='high']),('medium_heterogeneous',r[r.grade=='medium'])]:
        for model in ['constant','loss_only','loss_and_N','monotone_loss']:
            def fit(v):
                if model=='constant': return np.array([v.z.mean(),0.,0.])
                cols=['Val_Loss'] if model!='loss_and_N' else ['Val_Loss','logN']
                b=ols(v[cols].to_numpy(),v.z)
                if len(b)==2: b=np.append(b,0.)
                if model=='monotone_loss' and b[1]>0: b=np.array([v.z.mean(),0.,0.])
                return b
            b=fit(g); predictions=[]
            for i in range(len(g)):
                tr=g.drop(g.index[i]); te=g.iloc[i]; bb=fit(tr)
                predictions.append(sigmoid(bb[0]+bb[1]*te.Val_Loss+bb[2]*te.logN))
            diagnostics.append({'grade':name,'model':model,**metric(g.S,predictions)})
            mappings.append({'grade':name,'model':model,'a':b[0],'bLoss':b[1],'b_logN':b[2],
                'loss_min':g.Val_Loss.min(),'loss_max':g.Val_Loss.max(),'N_min_B':g.N_params_B.min(),'N_max_B':g.N_params_B.max()})
    # Source-group holdout of the heterogeneous pool is a transfer stress test.
    actual=[]; predicted=[]; constant=[]
    for source,g in r.groupby('report_family'):
        train=r[r.report_family!=source]
        b=ols(train[['Val_Loss','logN']].to_numpy(),train.z)
        actual.extend(g.S); predicted.extend(sigmoid(b[0]+b[1]*g.Val_Loss+b[2]*g.logN)); constant.extend([sigmoid(train.z.mean())]*len(g))
    high=r[r.grade=='high']; b=ols(high[['Val_Loss']].to_numpy(),high.z)
    boots=[]; rng=np.random.default_rng(SEED+1)
    for _ in range(1000):
        draw=high.iloc[rng.integers(0,len(high),len(high))]
        if draw.Val_Loss.nunique()<2: continue
        boots.append(ols(draw[['Val_Loss']].to_numpy(),draw.z)[1])
    pd.DataFrame(diagnostics).to_csv(OUT/'bridge_validation.csv',index=False,lineterminator='\n')
    pd.DataFrame(mappings).to_csv(OUT/'bridge_mappings.csv',index=False,lineterminator='\n')
    source_rows=[]
    for source,g in r.groupby('Loss_Source'):
        record={'source':source,'n':len(g),'grade':g.grade.iloc[0],'loss_min':g.Val_Loss.min(),'loss_max':g.Val_Loss.max(),
            'N_min_B':g.N_params_B.min(),'N_max_B':g.N_params_B.max()}
        if len(g)>=4 and g.Val_Loss.nunique()>=3:
            bsrc=ols(g[['Val_Loss']].to_numpy(),g.z)
            preds=[]; baselines=[]
            for i in range(len(g)):
                tr=g.drop(g.index[i]); te=g.iloc[i]
                if tr.Val_Loss.nunique()<2: continue
                bs=ols(tr[['Val_Loss']].to_numpy(),tr.z)
                preds.append((te.S,sigmoid(bs[0]+bs[1]*te.Val_Loss))); baselines.append((te.S,sigmoid(tr.z.mean())))
            record.update({'a':bsrc[0],'bLoss':bsrc[1], 'loocv_rmse':metric(*zip(*preds))['rmse'],
                'constant_loocv_rmse':metric(*zip(*baselines))['rmse']})
        source_rows.append(record)
    pd.DataFrame(source_rows).to_csv(OUT/'bridge_source_diagnostics.csv',index=False,lineterminator='\n')
    medium=r[r.grade=='medium']; errors=[]
    for source,g in medium.groupby('report_family'):
        train=medium[medium.report_family!=source]
        bb=ols(train[['Val_Loss']].to_numpy(),train.z)
        if bb[1]>0: bb=np.array([train.z.mean(),0.])
        errors.extend(g.S-sigmoid(bb[0]+bb[1]*g.Val_Loss))
    return {'n_high':len(high),'n_medium':int((r.grade=='medium').sum()),'diagnostics':diagnostics,'mappings':mappings,
        'high_loss_logN_correlation':high[['Val_Loss','logN']].corr().iloc[0,1],
        'high_loss_slope_bootstrap_p05_p95':np.quantile(boots,[.05,.95]),
        'source_holdout':metric(actual,predicted),'source_constant':metric(actual,constant),
        'source_diagnostics':source_rows,'medium_monotone_source_error_q10_q90':np.quantile(errors,[.1,.9]),
        'source_holdout_groups':r.report_family.value_counts().to_dict(),
        'source_holdout_policy':'Leave report family out, aliases and adjacent versions grouped. Family grouping is not validation-coordinate equality.',
        'formal_cross_coordinate_status':'unidentified',
        'conditional_mapping_status':'sensitivity_only',
        'formula':'S=100*sigmoid(a+bLoss*L+b_logN*log10(N_B)); only within grade-specific support and explicit same-coordinate assumption',
        'high_role':'7 Pythia final checkpoints overlap Attachment B, not independent Q2 validation. Loss and scale co-vary.',
        'medium_role':'Cross-source mixed validation sets; pooled mapping is an assumption scenario, not a calibrated absolute bridge.'}


def q3_sensitivity(bridge):
    ref=Q3_REF
    source=ROOT/'outputs/Q3'
    snapshot_names=['fixed_policy_grid.csv','observed_joint_grid.csv','native_Q_sensitivity_grid.csv']
    for name in ['manifest.json',*snapshot_names]:
        path=source/('upstream_manifest.json' if name=='manifest.json' else name)
        raw=path.read_bytes()
        (OUT/f'upstream_q3_{name}').write_bytes(raw)
    manifest=json.loads((OUT/'upstream_q3_manifest.json').read_text(encoding='utf-8'))
    for name in snapshot_names:
        if sha(OUT/f'upstream_q3_{name}')!=manifest['output_files_sha256'][name]:
            raise ValueError(f'Q3 snapshot hash mismatch: {name}')
    table=pd.read_csv(OUT/'upstream_q3_fixed_policy_grid.csv')
    outputs=[]
    maps=[x for x in bridge['mappings'] if x['model']=='monotone_loss']
    for _,row in table.iterrows():
      for mapping in maps:
        loss=row.get('conditional_bridge_loss',np.nan); n=row.get('N_params_B',np.nan)
        supported=np.isfinite(loss) and np.isfinite(n) and mapping['loss_min']<=loss<=mapping['loss_max'] and mapping['N_min_B']<=n<=mapping['N_max_B']
        score=sigmoid(mapping['a']+mapping['bLoss']*loss) if supported else None
        outputs.append({'budget_FLOPs':row.budget_FLOPs,'context_tokens':row.context_tokens,'quality_family':row.quality_family,
            'producer_status':row.status,'bridge_grade':mapping['grade'],'upstream_conditional_loss':loss,
            'N_params_B':n,'status':'same_coordinate_assumption_sensitivity_only' if supported else 'out_of_support_or_infeasible',
            'assumption_score':score,'empirically_calibrated_score':None,
            'transfer_error_sensitivity_lower':max(0,score+bridge['medium_monotone_source_error_q10_q90'][0]) if supported and mapping['grade']=='medium_heterogeneous' else None,
            'transfer_error_sensitivity_upper':min(100,score+bridge['medium_monotone_source_error_q10_q90'][1]) if supported and mapping['grade']=='medium_heterogeneous' else None,
            'assumption':'Q3 conditional Loss equals this C6 Loss coordinate; not established by attachments',
            'joint_95_prediction_interval':None})
    pd.DataFrame(outputs).to_csv(OUT/'q3_bridge_sensitivity.csv',index=False,lineterminator='\n')
    return {'branch':'integration/chm-q1-clean-20260923','commit':ref,'manifest_hash':sha(OUT/'upstream_q3_manifest.json'),
        'producer_release_subject':manifest['inputs']['release_subject'],
        'grid_hashes':{name:sha(OUT/f'upstream_q3_{name}') for name in snapshot_names},
        'producer_status':manifest['status'],'joint_95_prediction_interval':manifest['joint_prediction_interval_95'],
        'rows':len(outputs),'supported_assumption_rows':sum(x['assumption_score'] is not None for x in outputs),
        'scope':'Integrated Q3 v8 consumed only as explicit coordinate-equality sensitivity, not an empirical benchmark optimization result.'}


def c8_profiles():
    base=ROOT/'outputs/Q4/c8_bbh_task_aggregation.csv'
    r=pd.read_csv(base)
    summary={c:{'median':r[c].median(),'p10':r[c].quantile(.1),'p90':r[c].quantile(.9)} for c in ['bbhMacroMean','bbhTaskSd','bbhTaskMin']}
    return {'n':len(r),'task_counts':r.bbhTaskCount.value_counts().to_dict(),'profiles':summary,
        'low_min_high_mean_n':int(((r.bbhMacroMean>=r.bbhMacroMean.quantile(.75))&(r.bbhTaskMin<10)).sum()),
        'source':'Existing C8 per-model latest parseable JSON aggregation rerun by q4_analysis.js. No C2 identity join.'}


def c3_roles():
    r=read('leaderboard_extended_timeseries.csv')
    return {'n':len(r),'source_counts':r.Source.value_counts().to_dict(),
        'year_counts':r.Year.value_counts().sort_index().to_dict(),
        'role':'Source-stratified historical coverage and inherited annual descriptive stats only; not fitted as a homogeneous six-task capability trajectory.',
        'reason':'Different benchmarks/score definitions across years. No common-model evaluation calibration is supplied.'}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows,audit=leaderboard()
    resources,res_info=audit_resources(rows.date.max())
    dynamic=dynamics(rows,resources,res_info)
    bridge=bridge_analysis()
    result={'schema':'zhh.q4.conditional.v2','status':'conditional_problem_answer_not_causal_or_calibrated_future_truth',
        'audit':audit,'resources':res_info,'dynamics':dynamic,
        'backtest':rolling(leaderboard.all_versions[leaderboard.all_versions.model_class.isin(['pretrained','chat','domain_finetuned'])],resources),
        'expanded_backtest':rolling(leaderboard.all_versions,resources,'expanded'),
        'bridge':bridge,'q3_consumption':q3_sensitivity(bridge),'c8':c8_profiles(),'c3':c3_roles()}
    dump('results.json',result)
    files=[DATA/name for name in ['leaderboard_enhanced.csv','epoch_all_ai_models.csv','loss_benchmark_bridge_expanded.csv','leaderboard_extended_timeseries.csv']]
    files+=[ROOT/'outputs/Q4/c8_bbh_task_aggregation.csv',ROOT/'problem/readable/DATA_DESCRIPTION_VISIBLE.md',Path(__file__)]
    dump('manifest.json',{'schema':result['schema'],'seed':SEED,'code_base_commit':'main_integrated_tree',
        'code_sha256':sha(Path(__file__)),'input_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},
        'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
        'commands':['node src/zhh/q4_analysis.js','python -B src/zhh/q4_complete.py'],
        'upstream':result['q3_consumption'],
        'output_sha256':{name:sha(OUT/name) for name in (
            'leaderboard_sample.csv','leaderboard_all_versions.csv','c4_resource_audit.csv',
            'bridge_sample.csv','upstream_q3_fixed_policy_grid.csv','upstream_q3_observed_joint_grid.csv',
            'upstream_q3_native_Q_sensitivity_grid.csv','upstream_q3_manifest.json')},
        'uncertainty_scope':'Scenario envelopes and conditional bootstrap. No calibrated prediction interval; Q3 joint interval unavailable.'})
    print(json.dumps(json_safe({'audit':audit,'resources':{k:res_info[k] for k in ['candidate_n','primary_n','loose_ratio_n','gC_log10_per_year']},
        'backtest':result['backtest'],'bridge':bridge['diagnostics'],'q3':result['q3_consumption']}),ensure_ascii=False,indent=2))


if __name__=='__main__': main()
