"""Read-only model metric audit of main c6b36c0; writes only audit evidence."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RAW = ROOT / 'data/raw/real_attachments'
FILES = {}

def read(path):
    path = ROOT / path
    FILES[str(path.relative_to(ROOT)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path)

def doc(path):
    path = ROOT / path
    FILES[str(path.relative_to(ROOT)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text(encoding='utf-8'))

def metrics(y, pred):
    y, pred = np.asarray(y, float), np.asarray(pred, float)
    assert len(y) == len(pred) and np.isfinite(y).all() and np.isfinite(pred).all()
    residual = pred-y
    sst = np.sum((y-y.mean())**2)
    return dict(n=len(y), r2=float(1-np.sum(residual**2)/sst) if sst>1e-20 else None,
                rmse=float(np.sqrt(np.mean(residual**2))), mae=float(np.mean(abs(residual))),
                mape_percent=float(np.mean(abs(residual/y))*100) if np.all(y != 0) else None,
                bias=float(residual.mean()), actual_mean=float(y.mean()),
                spearman=float(pd.Series(y).rank().corr(pd.Series(pred).rank())))

def q1():
    model = doc('outputs/Q1/interaction_coefficients_13_targets.json')['targets']
    features = doc('outputs/Q1/interaction_feature_definition.json')
    domains = features['domain_order']
    result, detail, overlap = {}, [], {}
    observed = {}
    for scope, suffix in [('train_1m','1m'),('test_1m','1m'),('test_60m','60m'),('test_1B','1B'),('est_10b','10b'),('est_70b','70b')]:
        stem = scope.split('_')[0]
        mix = read(f'data/raw/real_attachments/A_data_value/regmix_tables/{stem}_mixture_{suffix}.csv')
        loss = read(f'data/raw/real_attachments/A_data_value/regmix_tables/{stem}_pile_loss_{suffix}.csv')
        assert mix['index'].is_unique and loss['index'].is_unique
        assert list(mix['index']) == list(loss['index'])
        x = mix[['train_the_pile_'+d for d in domains]].to_numpy(float)
        assert np.isfinite(x).all() and (x>=0).all() and (x.sum(axis=1)>0).all()
        x /= x.sum(axis=1, keepdims=True)
        observed[scope] = x
        values=[]
        for target, entry in model.items():
            y=loss['metric/the_pile_'+target+'_val_loss'].to_numpy(float)
            pred=entry['intercept']+x@np.array([entry['main'][d] for d in domains])
            for pair in entry['pairs']:
                a,b=pair['domains']
                pred+=pair['gamma']*x[:,domains.index(a)]*x[:,domains.index(b)]
            val=metrics(y,pred)
            detail.append(dict(scope=scope,target=target,**val))
            values.append(val)
        result[scope] = dict(n_recipes=len(x), median_r2=float(np.median([v['r2'] for v in values])),
            r2_range=[min(v['r2'] for v in values),max(v['r2'] for v in values)],
            median_mape_percent=float(np.median([v['mape_percent'] for v in values])),
            median_rmse=float(np.median([v['rmse'] for v in values])),
            median_spearman=float(np.median([v['spearman'] for v in values])),negative_r2_targets=sum(v['r2']<0 for v in values))
    table=read('outputs/Q1/targetwise_validation.csv')
    d=pd.DataFrame(detail)
    for row in table[table.support_group.eq('all')].itertuples():
        match=d[d.scope.eq(row.scope)&d.target.eq(row.target)].iloc[0]
        assert abs(match.rmse-row.interaction_rmse)<1e-10
        assert abs(match.spearman-row.interaction_spearman)<1e-10
    # Summary OOF RMSE covers all 512 rows, so R2 can be recovered from raw target SST.
    oof=read('outputs/Q1/targetwise_oof.csv')
    train=read('data/raw/real_attachments/A_data_value/regmix_tables/train_pile_loss_1m.csv')
    oof_metrics=[]
    for row in oof.itertuples():
        y=train['metric/the_pile_'+row.target+'_val_loss'].to_numpy(float)
        oof_metrics.append(dict(model=row.model,target=row.target,r2=float(1-row.oof_rmse**2/np.var(y)),rmse=row.oof_rmse,mae=row.oof_mae,spearman=row.oof_spearman))
    for kind in ['interaction','ridge']:
        sub=[v for v in oof_metrics if v['model']==kind]
        result['nested_oof_'+kind]={f'median_{key}':float(np.median([v[key] for v in sub])) for key in ['r2','rmse','mae','spearman']}
    keys=lambda x:set(tuple(np.round(row,12)) for row in x)
    for a,b in [('train_1m','test_1m'),('test_1m','test_60m'),('train_1m','test_1B'),('train_1m','est_10b'),('train_1m','est_70b')]:
        overlap[a+'__'+b]=len(keys(observed[a])&keys(observed[b]))
    pd.DataFrame(detail).to_csv(OUT/'q1_target_metrics.csv',index=False)
    pd.DataFrame(oof_metrics).to_csv(OUT/'q1_oof_r2.csv',index=False)
    return dict(summary=result,recipe_overlap=overlap)

def backbone(p,n,d):
    return p['E']+p['A']*n**(-p['alpha'])+p['B']*d**(-p['beta'])

def q2():
    classic=doc('outputs/Q2/classic_fit.json')
    data=read('data/raw/real_attachments/B_scaling_laws/pythia_training_log_existing.csv')
    p=classic['full_fit']['parameters']
    n,d,y=[data[c].to_numpy(float) for c in ['N_params_B','D_tokens_B','val_loss']]
    full=metrics(y,backbone(p,n,d))
    assert abs(full['r2']-classic['full_fit']['metrics']['r2'])<1e-12
    assert abs(full['mape_percent']/100-classic['full_fit']['metrics']['mape'])<1e-12
    result=dict(B1_full=full,B1_loso_fold_mean_reported=classic['validation']['leave_one_model_size_out']['aggregate'],
                B1_token_tail_reported=classic['validation']['token_tail_70_30']['metrics'])
    ext=doc('outputs/Q2/b7_quality_extension.json')
    b7=read('data/raw/real_attachments/B_scaling_laws/supplementary_NQ_experiment_expanded.csv')
    x=b7[['N_params_B','D_tokens_B','Q_score']].to_numpy(float); yy=b7.val_loss.to_numpy(float)
    z=(1-x[:,2,None])*np.column_stack([np.ones(len(x)),np.log(x[:,0]),np.log(x[:,1]/100)])
    base=backbone(p,x[:,0],x[:,1]); gamma=np.array([ext['quality_parameters'][k] for k in ['G0','GN','GD']])
    result['B7_full']=metrics(yy,base+z@gamma)
    result['B7_no_quality']=metrics(yy,base)
    assert abs(result['B7_full']['rmse']-ext['train_RMSE'])<1e-12
    for axis,name in enumerate(['N_params_B','D_tokens_B','Q_score']):
        pred=np.empty(len(x)); fold_errors=[]
        for fold in ext['outer_folds']:
            if fold['axis']!=name:continue
            keep=x[:,axis]==fold['held_level']; tr=~keep
            penalty=np.diag([0,fold['selected_ridge'],fold['selected_ridge']])
            g=np.linalg.solve(z[tr].T@z[tr]+penalty,z[tr].T@(yy[tr]-base[tr]))
            assert min(np.array([[1,np.log(a),np.log(b/100)] for a in [.07,11.97] for b in [10,600]])@g)>0
            pred[keep]=base[keep]+z[keep]@g
            err=metrics(yy[keep],pred[keep])['rmse']
            assert abs(err-fold['outer_rmse'])<1e-10
            fold_errors.append(err)
        result['B7_nested_'+name]=dict(**metrics(yy,pred),mean_fold_rmse=float(np.mean(fold_errors)))
    result['B7_rows_outside_B1_formal_support']=int(((x[:,0]<.070542)|(x[:,0]>11.965825)|(x[:,1]>299.893)).sum())
    return result

def q3():
    coeff=doc('outputs/Q2/model_coefficients.json')
    p,g=coeff['B1_backbone'],coeff['B7_quality_extension']
    result={}
    for name,qfield in [('fixed_policy_grid.csv','Q_B_proxy'),('observed_joint_grid.csv','Q_B_proxy'),('native_Q_sensitivity_grid.csv','Q_score')]:
        table=read('outputs/Q3/'+name)
        feasible=table[table.N_params_B.notna()].copy()
        errors=[]; cost_errors=[]
        for r in feasible.itertuples():
            n,d,q=r.N_params_B,r.D_tokens_B,getattr(r,qfield)
            assert .070542-1e-12<=n<=11.965825+1e-12 and 10-1e-12<=d<=299.893+1e-12 and r.Q0_scenario-1e-12<=q<=1+1e-12
            gain=g['G0']+g['GN']*np.log(n)+g['GD']*np.log(d/100)
            expected=(backbone(p,n,d)+(1-q)*gain)*r.bridge_factor
            errors.append(abs(expected-r.conditional_bridge_loss))
            if r.quality_family=='exponential':costfun=lambda t:1e7*np.exp(6*t)
            elif r.quality_family=='power':costfun=lambda t:5e9*t**4
            else:costfun=lambda t:2e9*np.log(1+10*t)
            costs=np.array([6e18*n*d,2e14*r.context_tokens*n*d,1e9*d*max(0,costfun(q)-costfun(r.Q0_scenario))])
            reported=np.array([r.C_train_FLOPs,r.C_attention_FLOPs,r.C_quality_FLOPs])
            cost_errors.append(float(max(abs(costs-reported))/r.budget_FLOPs))
            assert costs.sum()<=r.budget_FLOPs*(1+1e-9)
        assert max(errors)<1e-10 and max(cost_errors)<1e-10
        result[name]=dict(cells=len(table),feasible=len(feasible),max_loss_recompute_error=max(errors),max_cost_component_error_over_budget=max(cost_errors),prediction_R2=None,reason='No matched observed full N,D,Q,p outcomes; these errors measure arithmetic only')
    return result

def q4():
    rolling=read('outputs/Q4/rolling_two_month_frontier.csv')
    result=[]
    published=read('outputs/Q4/frontier_model_comparison.csv')
    for (typ,gate,model),g in rolling.groupby(['type','resource_gate','model']):
        vals=metrics(g.actual_q90,g.predicted_q90)
        r=published[published.type.eq(typ)&published.resource_gate.eq(gate)&published.model.eq(model)].iloc[0]
        assert abs(vals['r2']-r.r2)<1e-10 and abs(vals['rmse']-r.rmse)<1e-10
        result.append(dict(type=typ,resource_gate=gate,model=model,**vals))
    pd.DataFrame(result).to_csv(OUT/'q4_rolling_metrics.csv',index=False)
    sample=read('outputs/Q4/prepared/bridge_sample.csv')
    validation=read('outputs/Q4/bridge_source_coordinate_validation.csv')
    bridges=[]
    logit=lambda y:np.log(np.clip(np.asarray(y)/100,1e-5,1-1e-5)/(1-np.clip(np.asarray(y)/100,1e-5,1-1e-5)))
    sigmoid=lambda x:100/(1+np.exp(-np.clip(x,-40,40)))
    for source,g in sample.groupby('Loss_Source'):
        if len(g)<4 or g.Val_Loss.nunique()<3:continue
        predictions=[];const=[]
        for i,r in g.iterrows():
            tr=g.drop(i);zy=logit(tr.S)
            a,b=np.linalg.lstsq(np.column_stack([np.ones(len(tr)),tr.Val_Loss]),zy,rcond=None)[0]
            if b>0:a,b=zy.mean(),0
            predictions.append(sigmoid(a+b*r.Val_Loss)); const.append(sigmoid(zy.mean()))
        vals=metrics(g.S,predictions); cvals=metrics(g.S,const)
        row=validation[validation.coordinate_id.eq(source)].iloc[0]
        assert abs(vals['rmse']-row.monotone_LOO_RMSE)<1e-8 and abs(vals['r2']-row.monotone_LOO_R2)<1e-8
        bridges.append(dict(source=source,**vals,constant_rmse=cvals['rmse']))
    pd.DataFrame(bridges).to_csv(OUT/'q4_bridge_metrics.csv',index=False)
    return dict(rolling=result,bridges=bridges)

result=dict(reviewed_main='c6b36c08b5a85c81a3889d48d50c26ac136a048b',definitions={'R2':'1-SSE/SST within each target/group','MAPE_percent':'100*mean(abs(pred-actual)/abs(actual))','aggregation':'median across 13 Q1 targets; no pooled target R2'},Q1=q1(),Q2=q2(),Q3=q3(),Q4=q4())
result['input_sha256']=FILES
(OUT/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},ensure_ascii=False,indent=2))
