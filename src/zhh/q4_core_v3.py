"""Q4 core remediation; no paper/LaTeX writes. Run from repository root.
Requires NumPy, pandas, SciPy. Old v2 artifacts remain frozen.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import q4_complete as old

LOCAL = old.ROOT / 'data/processed/zhh_runtime'
if LOCAL.exists():
    sys.path.append(str(LOCAL))
import scipy
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, eye, hstack

ROOT, DATA = old.ROOT, old.DATA
V2 = ROOT / 'outputs/Q4/prepared'
OUT = ROOT / 'outputs/Q4'
SEED = 20260927
CLASSES = ['pretrained', 'chat', 'domain_finetuned']
MAIN_RETENTION = {'constant':0., 'frontier_trend':1., 'quantile_resource':.5, 'mean_resource':.5}


def save(name, data):
    pd.DataFrame(data).to_csv(OUT / name, index=False, lineterminator='\n')


def dump(name, data):
    (OUT / name).write_text(json.dumps(old.json_safe(data), ensure_ascii=False,
        indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def prep(rows):
    rows = rows.copy()
    rows['date'] = pd.to_datetime(rows.date, utc=True)
    rows['t'] = (rows.date - pd.Timestamp('2024-06-01', tz='UTC')).dt.total_seconds() / (86400*365.25/12)
    rows['logN'] = np.log10(rows.N)
    rows['z'] = old.logit(rows.S)
    rows['developer'] = rows.Model.str.split('/').str[0]
    return rows


def quantile_fit(x, y, q=.9):
    """Exact check-loss minimization: Xb + positive - negative = y."""
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = x[:, None]
    design = np.column_stack([np.ones(len(x)), x])
    if np.linalg.matrix_rank(design) != design.shape[1]:
        raise ValueError('rank deficient quantile design')
    n, p = design.shape
    result = linprog(np.r_[np.zeros(p), np.full(n, q), np.full(n, 1-q)],
        A_eq=hstack([csr_matrix(design), eye(n), -eye(n)], format='csr'),
        b_eq=np.asarray(y, float), bounds=[(None, None)]*p + [(0, None)]*(2*n), method='highs')
    if not result.success:
        raise ValueError(result.message)
    return result.x[:p]


def decompose(early, late, width=.5, developer_control=False, minimum=2):
    """Two-way standardized mean decomposition, plus full-sample selection gap.
    Conditional temporal term is NOT an identified technology effect.
    """
    data = pd.concat([early.assign(era=0), late.assign(era=1)], ignore_index=True)
    data['N_bin'] = np.floor(data.logN / width).astype(int)
    strata = ['model_class'] + (['developer'] if developer_control else [])
    keys = strata + ['N_bin']
    cells = data.groupby(keys + ['era']).agg(n=('S', 'size'), mean=('S', 'mean'),
        mean_logN=('logN', 'mean')).unstack('era')
    good = (cells['n'].get(0, pd.Series(index=cells.index, dtype=float)) >= minimum) & \
        (cells['n'].get(1, pd.Series(index=cells.index, dtype=float)) >= minimum)
    cells = cells[good].copy()
    full_change = float(late.S.mean() - early.S.mean())
    if cells.empty:
        return {'status': 'insufficient_common_support', 'full_observed_mean_change': full_change}, []
    totals = cells['n'].sum(axis=1).groupby(level=strata).sum()
    pi = totals / totals.sum()
    scale = temporal = standardized_start = standardized_end = 0.
    records = []
    for stratum, part in cells.groupby(level=strata):
        key = stratum if isinstance(stratum, tuple) else (stratum,)
        weight = float(pi.loc[stratum])
        w0, w1 = part['n'][0] / part['n'][0].sum(), part['n'][1] / part['n'][1].sum()
        m0, m1 = part['mean'][0], part['mean'][1]
        scale += weight * float(((w1-w0)*(m1+m0)/2).sum())
        temporal += weight * float(((w1+w0)*(m1-m0)/2).sum())
        standardized_start += weight * float((w0*m0).sum())
        standardized_end += weight * float((w1*m1).sum())
        for idx, row in part.iterrows():
            fields = dict(zip(keys, idx if isinstance(idx, tuple) else (idx,)))
            records.append({**fields, 'stratum_weight':weight,
                'N_low_B':10**(fields['N_bin']*width), 'N_high_B':10**((fields['N_bin']+1)*width),
                'n_early':row[('n',0)], 'n_late':row[('n',1)],
                'S_early':row[('mean',0)], 'S_late':row[('mean',1)],
                'within_bin_logN_shift':row[('mean_logN',1)]-row[('mean_logN',0)]})
    change = standardized_end - standardized_start
    return {'status':'conditional_standardized_decomposition', 'n_early':len(early), 'n_late':len(late),
        'common_cells':len(cells), 'common_strata':len(totals),
        'retained_early':int(cells['n'][0].sum()), 'retained_late':int(cells['n'][1].sum()),
        'coverage_early':cells['n'][0].sum()/len(early), 'coverage_late':cells['n'][1].sum()/len(late),
        'full_observed_mean_change':full_change, 'standardized_start':standardized_start,
        'standardized_end':standardized_end, 'standardized_change':change,
        'scale_distribution_points':scale, 'within_scale_temporal_points':temporal,
        'composition_support_gap_points':full_change-change,
        'conditional_scale_share':scale/change if abs(change)>.1 else None,
        'conditional_temporal_share':temporal/change if abs(change)>.1 else None,
        'closure_error':change-scale-temporal,
        'max_abs_within_bin_logN_shift':max(abs(x['within_bin_logN_shift']) for x in records),
        'technology_interpretation':'only if within-bin scale, data quantity, selection and evaluation confounding are negligible; not empirically identified'}, records


def contributions(rows):
    summaries, cells = [], []
    origin = rows.t.max()
    for gate, subset in [('primary', rows), ('strict_yes', rows[rows.open_status=='yes']),
        ('permissive_label',rows[rows.license.isin(old.PERMISSIVE)])]:
      for typ, group in subset.groupby('type'):
       for window in [1,2,3]:
        early, late = group[group.t<=group.t.min()+window], group[group.t>=origin-window]
        if len(early)<10 or len(late)<10:
            continue
        for width in [.25,.5,.75]:
         for control in [False,True]:
            result, detail = decompose(early,late,width,control)
            tag={'filter':gate,'type':typ,'window_months':window,'bin_width_decades':width,
                 'developer_control':control}
            summaries.append({**tag,**result})
            cells.extend({**tag,**x} for x in detail)
    save('historical_standardized_contributions.csv',summaries)
    save('historical_common_cells.csv',cells)
    return summaries


def contribution_bootstrap(rows):
    rng=np.random.default_rng(SEED+10); output=[]
    for typ,group in rows.groupby('type'):
        early=group[group.t<=group.t.min()+2].assign(era=0)
        late=group[group.t>=rows.t.max()-2].assign(era=1)
        blocks=[g for _,g in pd.concat([early,late]).groupby('developer')]
        for width in [.25,.5,.75]:
            draws=[]
            for _ in range(80):
                sample=pd.concat([blocks[j] for j in rng.integers(0,len(blocks),len(blocks))],ignore_index=True)
                e,l=sample[sample.era==0],sample[sample.era==1]
                if len(e)<10 or len(l)<10:
                    continue
                result,_=decompose(e,l,width)
                if result['status']=='conditional_standardized_decomposition':
                    draws.append(result)
            tag={'type':typ,'bin_width_decades':width,'window_months':2,'valid_draws':len(draws),
                'scope':'joint developer block resampling, recomputed common support; diagnostic variation, not fixed-target confidence coverage'}
            for metric in ['standardized_change','scale_distribution_points','within_scale_temporal_points',
                'conditional_scale_share','conditional_temporal_share','composition_support_gap_points']:
                values=[x[metric] for x in draws if x.get(metric) is not None]
                output.append({**tag,'metric':metric,'defined_draws':len(values),
                    'bootstrap_p05':np.quantile(values,.05) if len(values)>=30 else None,
                    'bootstrap_p95':np.quantile(values,.95) if len(values)>=30 else None})
    save('historical_contribution_bootstrap.csv',output)
    return output


def resource_slope(resources, cutoff):
    visible = resources[resources.date<=cutoff]
    annual=[]
    for year, group in visible.groupby(visible.date.dt.year):
        annual.append({'year':year,'n':len(group),'q90_logC':np.log10(group.C).quantile(.9),
            'q90_logN':np.log10(group.N).quantile(.9),'q90_logD':np.log10(group.D).quantile(.9),
            'complete':year<cutoff.year})
    fitted=[x for x in annual if x['complete'] and x['year']>=2020 and x['n']>=3]
    slope=old.ols(np.array([x['year']-2020 for x in fitted]), np.array([x['q90_logC'] for x in fitted]))[1] if len(fitted)>=3 else 0.
    return max(0,float(slope)), annual


def resources(cutoff):
    audit=pd.read_csv(V2/'c4_resource_audit.csv')
    raw=old.read('epoch_all_ai_models.csv')
    raw['source_row']=np.arange(2,len(raw)+2)
    raw['date']=pd.to_datetime(raw['Publication date'],utc=True,errors='coerce')
    for src,dst in [('Parameters','N'),('Training compute (FLOP)','C'),('Training dataset size (total)','D')]:
        raw[dst]=old.numeric(raw[src])
    sets={}; annual=[]; summaries=[]
    for label,col in [('primary','primary'),('wide_ratio','loose_ratio')]:
        ids=set(audit.loc[audit[col], 'source_row'])
        group=raw[raw.source_row.isin(ids)].sort_values(['date','source_row']).drop_duplicates('Model',keep='last')
        group=group[group.date<=cutoff].copy()
        sets[label]=group
        gc, by_year=resource_slope(group,cutoff)
        annual.extend({'resource_gate':label,**x} for x in by_year)
        summaries.append({'resource_gate':label,'n':len(group),'gC_log10_per_year':gc,
            'annual_compute_factor':10**gc,'recent_D_median_B':group[group.date>=cutoff-pd.Timedelta(days=365)].D.median()/1e9,
            'D_max_B':group.D.max()/1e9,'N_max_B':group.N.max()/1e9})
    save('c4_resource_gate_comparison.csv',summaries)
    save('c4_annual_resource_comparison.csv',annual)
    save('c4_wide_usable_resources.csv',sets['wide_ratio'][['source_row','Model','date','N','C','D']])
    return sets,summaries


def anchor(rows, q=.9, window=2):
    end=rows.date.max()
    recent=rows[rows.date> end-pd.DateOffset(months=window)]
    score=float(recent.S.quantile(q))
    high=recent[recent.S>=score]
    return {'S':score,'N':10**high.logN.median(),'t':rows.t.max(),'n':len(recent),'end':end}


def record_boundary(q90_score, historical_record, tail_gap):
    return float(min(100, max(historical_record, q90_score + max(0, tail_gap))))


def window_series(rows, q=.9):
    records=[]
    for month in sorted(rows.date.dt.strftime('%Y-%m').unique()):
        subset=rows[rows.date.dt.strftime('%Y-%m')<=month]
        a=anchor(subset,q)
        if a['n']>=10:
            records.append({'t':a['t'],'z':old.logit(a['S'])})
    return pd.DataFrame(records)


def fit_candidates(rows, q=.9):
    series=window_series(rows,q)
    trend=old.ols(series.t.to_numpy(),series.z.to_numpy()) if len(series)>=3 else np.array([old.logit(anchor(rows,q)['S']),0.])
    x=rows[['logN','t']].to_numpy()
    return {'constant':np.zeros(3), 'frontier_trend':np.array([trend[0],0.,trend[1]]),
        'quantile_resource':quantile_fit(x,rows.z,q), 'mean_resource':old.ols(x,rows.z)}


def predict(model, coef, a, horizon, gc, slowdown=1, eta=.5, retention=1):
    if model=='frontier_trend':
        # Forecast anchored observed frontier increments, not regression intercept.
        return float(old.sigmoid(old.logit(a['S'])+retention*coef[2]*horizon))
    return float(old.sigmoid(old.logit(a['S'])+coef[1]*eta*gc*slowdown*horizon/12+retention*coef[2]*horizon))


def rolling(versions, resource_sets):
    records=[]
    for typ,group in versions.groupby('type'):
        months=sorted(group.date.dt.strftime('%Y-%m').unique())
        # Test windows are exactly two future calendar months, all unseen at origin.
        for i in range(4,len(months)-1):
            start=pd.Timestamp(months[i]+'-01',tz='UTC'); stop=start+pd.DateOffset(months=2)
            train=group[group.date<start].sort_values(['date','source_row']).drop_duplicates('Model',keep='last')
            test=group[(group.date>=start)&(group.date<stop)].sort_values(['date','source_row']).drop_duplicates('Model',keep='last')
            # Skip truncated final calendar month to preserve full target window.
            if stop-pd.Timedelta(days=1)>group.date.max().normalize() or len(train)<30 or len(test)<10:
                continue
            a=anchor(train); h=((stop-pd.Timedelta(days=1))-a['end']).total_seconds()/(86400*365.25/12)
            models=fit_candidates(train)
            actual=float(test.S.quantile(.9))
            for gate,res in resource_sets.items():
                gc,_=resource_slope(res,train.date.max())
                for model,coef in models.items():
                    prediction=predict(model,coef,a,h,gc,retention=MAIN_RETENTION[model])
                    records.append({'type':typ,'resource_gate':gate,'model':model,'origin':a['end'].strftime('%Y-%m-%d'),
                        'test_start':start.strftime('%Y-%m-%d'),'test_end':(stop-pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
                        'train_n':len(train),'test_n':len(test),'actual_q90':actual,'predicted_q90':prediction,
                        'gC_visible':gc,'horizon_months':h,'forecast_window_months':2,'target_window_months':2,
                        'drift_retention_assumed':MAIN_RETENTION[model],
                        'developer_overlap_fraction':test.developer.isin(set(train.developer)).mean(),
                        'same_model_overlap_fraction':test.Model.isin(set(train.Model)).mean()})
    frame=pd.DataFrame(records); save('rolling_two_month_frontier.csv',frame)
    summary=[]
    for (typ,gate,model),g in frame.groupby(['type','resource_gate','model']):
        summary.append({'type':typ,'resource_gate':gate,'model':model,**old.metric(g.actual_q90,g.predicted_q90)})
    save('frontier_model_comparison.csv',summary)
    return summary


def forecasts(rows, resource_summary, comparison):
    rng=np.random.default_rng(SEED)
    points=[]; envelopes=[]; parameters=[]; scenario_records=[]; error_stress=[]
    residuals=pd.read_csv(OUT/'rolling_two_month_frontier.csv')
    for typ,group in rows.groupby('type'):
        a=anchor(group); models=fit_candidates(group)
        diagnostics=[x for x in comparison if x['type']==typ and x['resource_gate']=='primary']
        selected=min(diagnostics,key=lambda x:x['rmse'])['model'] if diagnostics else 'constant'
        for model,coef in models.items():
            parameters.append({'type':typ,'model':model,'intercept':coef[0],'b_logN':coef[1],'b_month':coef[2],
                'selected_by_diagnostic_rmse':model==selected,'anchor_score':a['S'],'anchor_N_B':a['N']})
        developer_groups=[g for _,g in group.groupby('developer')]
        boot=[]
        for _ in range(80):
            draw=pd.concat([developer_groups[j] for j in rng.integers(0,len(developer_groups),len(developer_groups))],ignore_index=True)
            try:
                boot.append((fit_candidates(draw),anchor(draw)))
            except ValueError:
                continue
        if len(boot)<40:
            raise ValueError('insufficient valid block bootstrap draws')
        alternatives=[]
        for q,win in [(.85,2),(.95,2),(.9,1),(.9,3)]:
            alt=anchor(group,q,win)
            alt_models=fit_candidates(group,q)
            alternatives.append((alt_models,alt))
        for resource in resource_summary:
         gate,gc=resource['resource_gate'],resource['gC_log10_per_year']
         for h in [12,24]:
          for scenario,slow in [('historical',1),('half',.5),('quarter',.25),('stopped',0)]:
            tag={'type':typ,'resource_gate':gate,'horizon_months':h,'compute_scenario':scenario}
            model_values=[]
            for model,coef in models.items():
                retention=MAIN_RETENTION[model]
                value=predict(model,coef,a,h,gc,slow,.5,retention)
                interval=[predict(model,b[model],ab,h,gc,slow,.5,retention) for b,ab in boot]
                points.append({**tag,'model':model,'origin':a['end'].strftime('%Y-%m-%d'),
                    'target_date':(a['end']+pd.DateOffset(months=h)).strftime('%Y-%m-%d'),
                    'score':value,'conditional_p05':np.quantile(interval,.05),'conditional_p95':np.quantile(interval,.95),
                    'selected_by_diagnostic_rmse':model==selected,'eta_assumed':.5,'drift_retention_assumed':retention,
                    'gC_log10_per_year':gc,'scenario_gC_log10_per_year':gc*slow,
                    'N_anchor_B':a['N'],'D_anchor_B_scenario':resource['recent_D_median_B'],
                    'C_anchor_FLOPs_scenario':6e18*a['N']*resource['recent_D_median_B'],
                    'C_future_FLOPs_scenario':6e18*a['N']*resource['recent_D_median_B']*10**(gc*slow*h/12),
                    'N_future_B_scenario':a['N']*10**(.5*gc*slow*h/12),
                    'D_future_B_scenario':resource['recent_D_median_B']*10**(.5*gc*slow*h/12),
                    'time_extrapolation_observed_spans':h/(group.t.max()-group.t.min()),
                    'N_extrapolation_decades_beyond_C2':max(0,np.log10(a['N'])+.5*gc*slow*h/12-group.logN.max()),
                    'D_extrapolation_decades_beyond_C4':max(0,np.log10(resource['recent_D_median_B']/resource['D_max_B'])+.5*gc*slow*h/12),
                    'status':'conditional_scenario_not_calibrated_long_horizon_prediction'})
                model_values.extend([value,np.quantile(interval,.05),np.quantile(interval,.95)])
                if model in ['constant','frontier_trend','quantile_resource','mean_resource']:
                 for eta in [.25,.5,.75]:
                  for retention in [0,.5,1]:
                   for multiplier in [.5,1,1.5]:
                    values=[predict(model,b[model],ab,h,gc*multiplier,slow,eta,retention) for b,ab in boot]
                    low,high=np.quantile(values,[.05,.95])
                    scenario_records.append({**tag,'model':model,'eta':eta,'retention':retention,
                        'resource_multiplier':multiplier,'conditional_p05':low,'conditional_p95':high})
                    model_values.extend([low,high])
            for alt_models,alt in alternatives:
                model_values.extend(predict(m,b,alt,h,gc,slow,retention=MAIN_RETENTION[m]) for m,b in alt_models.items())
            fold_rows=residuals[(residuals.type==typ)&(residuals.resource_gate==gate)]
            bias=float((fold_rows.predicted_q90-fold_rows.actual_q90).abs().max())
            for row in [x for x in points if all(x[k]==v for k,v in tag.items())]:
                error_stress.append({**tag,'model':row['model'],'point':row['score'],
                    'observed_two_month_max_abs_error':bias,
                    'fixed_bias_stress_lower':max(0,row['score']-bias),
                    'fixed_bias_stress_upper':min(100,row['score']+bias),
                    'assumption':'future score bias bounded by historical candidate maximum error; unverified long-horizon assumption, not PI'})
            envelopes.append({**tag,'scenario_union_lower':min(model_values),'scenario_union_upper':max(model_values),
                'with_fixed_bias_stress_lower':max(0,min(model_values)-bias),
                'with_fixed_bias_stress_upper':min(100,max(model_values)+bias),
                'bootstrap_draws':len(boot),'meaning':'union of per-assumption 5--95% conditional ranges and candidate points; no coverage guarantee',
                'model_selected_in_diagnostics':selected,'resource_effect_identified':False})
    save('frontier_parameters.csv',parameters)
    save('frontier_candidate_forecasts.csv',points)
    save('frontier_scenario_conditional_ranges.csv',scenario_records)
    save('frontier_scenario_union.csv',envelopes)
    save('frontier_model_error_stress.csv',error_stress)
    return {'parameters':parameters,'ranges':envelopes}


def maximum_frontier(rows, versions, comparison):
    selected={}
    for typ in rows.type.unique():
        candidates=[x for x in comparison if x['type']==typ and x['resource_gate']=='primary']
        selected[typ]=min(candidates,key=lambda x:x['rmse'])['model'] if candidates else 'constant'
    rolling_rows=pd.read_csv(OUT/'rolling_two_month_frontier.csv')
    backtest=[]
    for _,row in rolling_rows[rolling_rows.resource_gate.eq('primary')].iterrows():
        if row.model!=selected[row.type]:
            continue
        group=versions[versions.type.eq(row.type)]
        start=pd.Timestamp(row.test_start,tz='UTC')
        stop=pd.Timestamp(row.test_end,tz='UTC')+pd.Timedelta(days=1)
        train=group[group.date<start].sort_values(['date','source_row']).drop_duplicates('Model',keep='last')
        test=group[(group.date>=start)&(group.date<stop)].sort_values(['date','source_row']).drop_duplicates('Model',keep='last')
        prior_record=float(train.S.max())
        actual_record=max(prior_record,float(test.S.max()))
        for window in [1,2,3]:
            recent=train[train.date>train.date.max()-pd.DateOffset(months=window)]
            gap=max(0,float(recent.S.max()-recent.S.quantile(.9)))
            backtest.append({'type':row.type,'origin':row.origin,'test_start':row.test_start,'test_end':row.test_end,
                'q90_model':row.model,'tail_window_months':window,'q90_prediction':row.predicted_q90,
                'tail_gap':gap,'prior_historical_record':prior_record,'persistence_prediction':prior_record,
                'tail_gap_prediction':record_boundary(row.predicted_q90,prior_record,gap),
                'actual_cumulative_record':actual_record,'target_definition':'cumulative_best_score_by_target_date'})
    backtest_frame=pd.DataFrame(backtest)
    save('frontier_maximum_backtest.csv',backtest_frame)
    model_comparison=[]
    for typ,group in backtest_frame.groupby('type'):
        baseline=group.drop_duplicates(['origin','test_start','test_end'])
        model_comparison.append({'type':typ,'model':'record_persistence','tail_window_months':None,
            **old.metric(baseline.actual_cumulative_record,baseline.persistence_prediction),
            'selection_status':'diagnostic_on_four_overlapping_two_month_windows'})
        for window,window_rows in group.groupby('tail_window_months'):
            model_comparison.append({'type':typ,'model':'q90_plus_tail_gap','tail_window_months':window,
                **old.metric(window_rows.actual_cumulative_record,window_rows.tail_gap_prediction),
                'selection_status':'conditional_boundary_scenario_not_selected_when_persistence_rmse_is_lower'})
    save('frontier_maximum_model_comparison.csv',model_comparison)
    q90_points=pd.read_csv(OUT/'frontier_candidate_forecasts.csv')
    q90_points=q90_points[(q90_points.resource_gate=='primary') & q90_points.selected_by_diagnostic_rmse]
    scenarios=[]
    for typ,group in rows.groupby('type'):
        historical_record=float(group.S.max())
        gaps={}
        for window in [1,2,3]:
            recent=group[group.date>group.date.max()-pd.DateOffset(months=window)]
            gaps[window]=max(0,float(recent.S.max()-recent.S.quantile(.9)))
        for _,point in q90_points[q90_points.type.eq(typ)].iterrows():
            scenarios.append({'type':typ,'origin':point.origin,'target_date':point.target_date,
                'horizon_months':point.horizon_months,'compute_scenario':point.compute_scenario,
                'q90_model':point.model,'q90_score':point.score,'historical_record_score':historical_record,
                'tail_gap_window_months':2,'tail_gap_center':gaps[2],
                'tail_gap_lower':min(gaps.values()),'tail_gap_upper':max(gaps.values()),
                'record_persistence_baseline':historical_record,
                'conditional_record_lower':record_boundary(point.score,historical_record,min(gaps.values())),
                'conditional_record_center':record_boundary(point.score,historical_record,gaps[2]),
                'conditional_record_upper':record_boundary(point.score,historical_record,max(gaps.values())),
                'target_definition':'cumulative_best_score_by_target_date',
                'status':'conditional_tail_gap_scenario_not_calibrated_prediction_interval'})
    save('frontier_maximum_scenarios.csv',scenarios)
    return {'target_definition':'cumulative_best_score_by_target_date','selected_q90_models':selected,
        'backtest_rows':len(backtest),'scenario_rows':len(scenarios),
        'interpretation':'record persistence is the empirical baseline; q90 plus recent tail gap is a separate conditional boundary scenario'}


def fit_bridge(group):
    b=old.ols(group.Val_Loss.to_numpy(),old.logit(group.S))
    if b[1]>0:
        b=np.array([old.logit(group.S).mean(),0.])
    return b


def bridge():
    rows=pd.read_csv(V2/'bridge_sample.csv')
    mappings=[]; validation=[]
    for source,group in rows.groupby('Loss_Source'):
        text=source.lower()
        kind='validation' if ('validation' in text or group.grade.eq('high').all()) else ('training' if 'training loss' in text else 'unspecified')
        tag={'coordinate_id':source,'grade':group.grade.iloc[0],'loss_kind':kind,'n':len(group),
            'loss_kind_provenance':'attachment source label; not independent paper verification',
            'source_Loss_values_independently_verified':False}
        if len(group)<4 or group.Val_Loss.nunique()<3:
            validation.append({**tag,'status':'insufficient_source_coordinate_support'})
            continue
        b=fit_bridge(group); actual=[]; predicted=[]; constant=[]
        for idx,row in group.iterrows():
            train=group.drop(idx)
            bb=fit_bridge(train)
            actual.append(row.S); predicted.append(old.sigmoid(bb[0]+bb[1]*row.Val_Loss))
            constant.append(old.sigmoid(old.logit(train.S).mean()))
        model_metrics,base_metrics=old.metric(actual,predicted),old.metric(actual,constant)
        accepted=kind=='validation' and b[1]<0 and model_metrics['rmse']<base_metrics['rmse']
        validation.append({**tag,'status':'diagnostic_candidate' if accepted else 'not_validated_primary_bridge',
            'monotone_LOO_RMSE':model_metrics['rmse'],'constant_LOO_RMSE':base_metrics['rmse'],
            'monotone_LOO_R2':model_metrics['r2']})
        mappings.append({**tag,'a':b[0],'bLoss':b[1],'loss_min':group.Val_Loss.min(),
            'loss_max':group.Val_Loss.max(),'N_min_B':group.N_params_B.min(),'N_max_B':group.N_params_B.max(),
            'diagnostic_primary_candidate':accepted,'mapping_LOO_RMSE':model_metrics['rmse'],
            'constant_LOO_RMSE':base_metrics['rmse'],'cross_Q3_coordinate_status':'unidentified'})
    save('bridge_source_coordinate_models.csv',mappings)
    save('bridge_source_coordinate_validation.csv',validation)
    return mappings,validation


def convert(mapping, loss, n, scale=1., offset=0.):
    if not np.isfinite(loss) or not np.isfinite(n):
        return None,'infeasible_or_missing_upstream'
    mapped=scale*loss+offset
    if not (mapping['N_min_B']<=n<=mapping['N_max_B']):
        return None,'N_out_of_support'
    if not (mapping['loss_min']<=mapped<=mapping['loss_max']):
        return None,'Loss_out_of_support'
    return float(old.sigmoid(mapping['a']+mapping['bLoss']*mapped)),'conditional_affine_coordinate_assumption'


def q3_bridge(mappings):
    grids=[]
    for filename,mode,quality_column in [
        ('upstream_q3_fixed_policy_grid.csv','fixed_recipe','Q_B_proxy'),
        ('upstream_q3_observed_joint_grid.csv','observed_joint_recipe','Q_B_proxy'),
        ('upstream_q3_native_Q_sensitivity_grid.csv','independent_native_Q','Q_score')]:
        table=pd.read_csv(V2/filename)
        table['policy_mode']=mode
        table['source_policy_row']=np.arange(len(table))
        table['Q_coordinate_value']=table[quality_column]
        grids.append(table)
    grid=pd.concat(grids,ignore_index=True,sort=False)
    records=[]
    for mapping in mappings:
      for index,row in grid.iterrows():
       for scale in [.9,1.,1.1]:
        for offset in [-.1,0.,.1]:
         for upstream_delta in [-.05,0.,.05]:
            loss=row.conditional_bridge_loss; n=row.N_params_B
            score,status=convert(mapping,loss+upstream_delta,n,scale,offset)
            baseline,base_status=convert(mapping,row.B1_backbone_loss,n,scale,offset)
            records.append({'policy_row':index,'coordinate_id':mapping['coordinate_id'],
                'diagnostic_primary_candidate':mapping['diagnostic_primary_candidate'],
                'mapping_LOO_RMSE':mapping['mapping_LOO_RMSE'],
                'constant_LOO_RMSE':mapping['constant_LOO_RMSE'],
                'budget_FLOPs':row.budget_FLOPs,'context_tokens':row.context_tokens,'quality_family':row.quality_family,
                'policy_mode':row.policy_mode,'source_policy_row':row.source_policy_row,
                'recipe_index':row.recipe_index,'Q_coordinate_value':row.Q_coordinate_value,
                'producer_status':row.status,'coordinate_scale_assumed':scale,'coordinate_offset_assumed':offset,
                'upstream_loss_stress_delta_assumed':upstream_delta,'N_params_B':n,'status':status,
                'conditional_score':score,'conditional_backbone_reference_score':baseline,
                'conditional_gain_vs_backbone':score-baseline if score is not None and baseline is not None else None,
                'reference_status':base_status,'empirically_calibrated_score':None})
    frame=pd.DataFrame(records); save('q3_source_coordinate_stress.csv',frame)
    summaries=[]
    for (coordinate,index),group in frame.groupby(['coordinate_id','policy_row']):
        gains=group.conditional_gain_vs_backbone.dropna(); scores=group.conditional_score.dropna()
        nominal=group[(group.coordinate_scale_assumed==1)&(group.coordinate_offset_assumed==0)&(group.upstream_loss_stress_delta_assumed==0)]
        summaries.append({'coordinate_id':coordinate,'policy_row':index,
            'budget_FLOPs':group.budget_FLOPs.iloc[0],'context_tokens':group.context_tokens.iloc[0],
            'quality_family':group.quality_family.iloc[0],
            'policy_mode':group.policy_mode.iloc[0],'source_policy_row':group.source_policy_row.iloc[0],
            'recipe_index':group.recipe_index.iloc[0],'Q_coordinate_value':group.Q_coordinate_value.iloc[0],
            'diagnostic_primary_candidate':group.diagnostic_primary_candidate.iloc[0],
            'mapping_LOO_RMSE':group.mapping_LOO_RMSE.iloc[0],
            'constant_LOO_RMSE':group.constant_LOO_RMSE.iloc[0],
            'supported_score_scenarios':len(scores),'supported_gain_scenarios':len(gains),'total_scenarios':len(group),
            'score_min':scores.min(),'score_max':scores.max(),'gain_min':gains.min(),'gain_max':gains.max(),
            'gain_sign_robust_within_supported_grid':bool((gains>0).all() or (gains<0).all()) if len(gains) else None,
            'nominal_status':nominal.status.iloc[0],
            'nominal_score':nominal.conditional_score.iloc[0],
            'meaning':'hypothetical coordinate / upstream stress; reference is same N backbone, not an observed benchmark baseline'})
    save('q3_bridge_conclusion_sensitivity.csv',summaries)
    rankings=[]
    # Assess quality-cost policy ranking only where ALL compared candidates map.
    keys=['coordinate_id','policy_mode','budget_FLOPs','context_tokens','coordinate_scale_assumed','coordinate_offset_assumed','upstream_loss_stress_delta_assumed']
    for key,g in frame.groupby(keys):
        feasible=g[g.producer_status.str.contains('feasible') & ~g.producer_status.str.contains('infeasible')]
        supported=feasible.conditional_score.notna().all()
        usable=supported and len(feasible)>=2
        best=feasible.loc[np.isclose(feasible.conditional_score,feasible.conditional_score.max()),'quality_family'].tolist() if usable else []
        rankings.append({**dict(zip(keys,key)),'feasible_policies':len(feasible),
            'all_feasible_policies_supported':bool(supported and len(feasible)>=2),
            'best_quality_families':';'.join(best) if usable else None,
            'unique_winner':len(best)==1 if usable else None,
            'policy_score_spread':feasible.conditional_score.max()-feasible.conditional_score.min() if supported and len(feasible)>=2 else None})
    save('q3_policy_ranking_stress.csv',rankings)
    return {'stress_rows':len(frame),'source_coordinate_models':len(mappings),
        'label_based_diagnostic_candidates':sum(x['diagnostic_primary_candidate'] for x in mappings),
        'policy_mode_rows':grid.policy_mode.value_counts().to_dict(),
        'formal_cross_coordinate_status':'unidentified','stress_is_statistical_interval':False}


def c3_analysis():
    rows=old.read('leaderboard_extended_timeseries.csv')
    tasks=['IFEval','BBH','MATH_Lvl5','GPQA','MUSR','MMLU_PRO']
    for c in ['Year','Params_B','Average',*tasks]:
        rows[c]=old.numeric(rows[c])
    rows['six_task_mean']=rows[tasks].mean(axis=1)
    rows['average_minus_six_task_mean']=rows.Average-rows.six_task_mean
    summary=[]; profiles=[]
    for (source,year),group in rows.groupby(['Source','Year']):
        summary.append({'source':source,'year':year,'n':len(group),'Average_mean':group.Average.mean(),
            'Average_q90':group.Average.quantile(.9),'six_task_mean':group.six_task_mean.mean(),
            'six_task_q90':group.six_task_mean.quantile(.9),'N_median_B':group.Params_B.median(),
            'N_q90_B':group.Params_B.quantile(.9),'zero_task_fraction':(group[tasks]==0).to_numpy().mean(),
            'average_mean_abs_difference_from_six_tasks':group.average_minus_six_task_mean.abs().mean(),
            'Average_comparable_across_sources':False})
        for task in tasks:
            profiles.append({'source':source,'year':year,'task':task,'n':group[task].notna().sum(),
                'mean':group[task].mean(),'q90':group[task].quantile(.9),'zero_fraction':group[task].eq(0).mean()})
    save('c3_source_year_capability.csv',summary); save('c3_source_year_task_profiles.csv',profiles)
    # C3 lacks submission timestamps: last CSV row is a reproducible sensitivity,
    # never claimed to be the latest chronological model revision.
    dedup=rows.drop_duplicates(['Model','Year','Source'],keep='last')
    dedup_summary=[]
    for (source,year),group in dedup.groupby(['Source','Year']):
        dedup_summary.append({'source':source,'year':year,'n':len(group),
            'Average_mean':group.Average.mean(),'Average_q90':group.Average.quantile(.9),
            'six_task_mean':group.six_task_mean.mean(),'six_task_q90':group.six_task_mean.quantile(.9),
            'N_median_B':group.Params_B.median(),
            'dedup_policy':'last CSV row within Model/Year/Source; not chronological latest'})
    save('c3_source_year_dedup_sensitivity.csv',dedup_summary)
    save('c3_row_metric_audit.csv',rows[['Model','Source','Year','Average','six_task_mean','average_minus_six_task_mean']])
    history=rows[rows.Source.str.contains('Historical')]
    return {'rows':len(rows),'duplicate_Model_Year_Source':int(rows.duplicated(['Model','Year','Source']).sum()),
        'historical_rows':len(history),'historical_Average_mean_abs_task_difference':history.average_minus_six_task_mean.abs().mean(),
        'historical_all_six_tasks_zero':int(history[tasks].eq(0).all(axis=1).sum()),
        'conclusion':'Source-specific history and task coverage are analyzed. Sparse historical scores have a different aggregate meaning; no homogeneous 2019--2025 frontier is fitted.'}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=prep(pd.read_csv(V2/'leaderboard_sample.csv'))
    rows=rows[rows.model_class.isin(CLASSES)]
    versions=prep(pd.read_csv(V2/'leaderboard_all_versions.csv'))
    versions=versions[versions.model_class.isin(CLASSES)]
    res_sets,res_summary=resources(rows.date.max())
    historical=contributions(rows)
    contribution_uncertainty=contribution_bootstrap(rows)
    print('Completed resource gates and standardized contributions',flush=True)
    comparison=rolling(versions,res_sets)
    print('Completed consistent two-month frontier backtest',flush=True)
    frontier=forecasts(rows,res_summary,comparison)
    print('Completed tail regressions, block bootstrap and scenario unions',flush=True)
    maximum=maximum_frontier(rows,versions,comparison)
    print('Completed cumulative-record frontier baseline and tail-gap scenarios',flush=True)
    mappings,validation=bridge()
    q3=q3_bridge(mappings)
    c3=c3_analysis()
    dump('interface.json',{'schema':'zhh.q4.core.v3.interface','formal_cross_coordinate_status':'unidentified',
        'ready_for_empirical_Q3_conversion':False,'conditional_mapping_policy':'explicit named C6 source coordinate and declared affine assumptions; source support required',
        'historical_target':'standardized six-task mean, separate from q90 forecast target',
        'technical_effect_identified':False,'frontier_target':'type-specific recent two-calendar-month q90, anchored conditional evolution',
        'maximum_frontier_target':'type-specific cumulative best six-task score by target date; record persistence baseline plus conditional q90-tail-gap scenario',
        'frontier_model_selection':'lowest diagnostic two-month-window RMSE; four overlapping test windows per type, not blind selection',
        'forecast_origin':'latest observed submission per type; supplied per row',
        'paper_status':'Q4 integrated section uses v3 core conditional results'})
    results={'schema':'zhh.q4.core.v3','status':'core_remediation_with_explicit_unidentified_coordinates',
        'resources':res_summary,'frontier_comparison':comparison,'frontier':frontier,'maximum_frontier':maximum,
        'bridge':validation,'q3':q3,'c3':c3,
        'historical_uncertainty':contribution_uncertainty,
        'historical_primary':[x for x in historical if x['filter']=='primary' and x['window_months']==2 and x['bin_width_decades']==.5],
        'bridge_effect_on_direct_frontier':'Direct frontier uses C2 scores and C4 resources, no C6 or Q3 Loss input; bridge uncertainty changes Q3 score/gain/rank statements, not the independent direct-score forecasts.',
        'remaining':'Pure technical effect and Q3-to-C6 empirical Loss coordinate are not identified; long-horizon results are conditional scenarios.'}
    dump('results.json',results)
    inputs=[V2/x for x in ['leaderboard_sample.csv','leaderboard_all_versions.csv','c4_resource_audit.csv','bridge_sample.csv',
        'upstream_q3_fixed_policy_grid.csv','upstream_q3_observed_joint_grid.csv',
        'upstream_q3_native_Q_sensitivity_grid.csv','upstream_q3_manifest.json']]
    inputs += [DATA/x for x in ['epoch_all_ai_models.csv','leaderboard_extended_timeseries.csv']]
    inputs += [V2/'manifest.json', DATA/'leaderboard_enhanced.csv', DATA/'loss_benchmark_bridge_expanded.csv']
    inputs += [Path(__file__),ROOT/'src/zhh/q4_complete.py',ROOT/'src/zhh/test_q4_core_v3.py',
        ROOT/'src/zhh/verify_q4_core_v3.py', ROOT/'src/zhh/requirements-q4-core-v3.txt',
        ROOT/'experiments/Q4/20260926-q4-core-v3-design.md',
        ROOT/'experiments/Q4/20260926-q4-bridge-primary-source-check.md']
    dump('manifest.json',{'schema':'zhh.q4.core.v3.manifest','source_commit':'ee23b200e9de7f78477d945b186233741bd3b8fd','seed':SEED,
        'command':'python -B src/zhh/q4_core_v3.py','versions':{'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__},
        'input_sha256':{str(x.relative_to(ROOT)).replace('\\','/'):old.sha(x) for x in inputs},
        'output_sha256':{x.name:old.sha(x) for x in sorted(OUT.iterdir()) if x.suffix in ['.csv','.json'] and x.name not in {'manifest.json','curated_manifest.json'}},
        'paper_updated':True,'paper_section':'paper/latex/sections/Q4/main.tex',
        'upstream_Q3_commit':old.Q3_REF,'bootstrap_blocks':80,
        'uncertainty':'union of per-assumption 5--95% bootstrap ranges, no calibrated future coverage; coordinate stress assumptions are not confidence intervals'})
    print(json.dumps(old.json_safe({'comparison':comparison,'q3':q3,'c3':c3}),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
