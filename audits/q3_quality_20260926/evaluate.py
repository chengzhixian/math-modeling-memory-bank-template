"""Independent Q3 decision evaluation; never imports production predictors/solvers.

Frozen empirical tables are validation inputs, not fitting inputs.
All optimizations below are conditional on the published mathematical model.
"""
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.optimize import brentq, minimize_scalar

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
HASHES={}
def read(name):
    path=ROOT/name; HASHES[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path)
def doc(name):
    path=ROOT/name; HASHES[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text(encoding='utf-8'))

coeff=doc('outputs/Q2/model_coefficients.json')
B1=coeff['B1_backbone']; G=coeff['B7_quality_extension']
definition=doc('outputs/Q2/model_definition.json')
(NMIN,NMAX),(DMIN,DMAX),_=definition['formal_support']
features=doc('outputs/Q1/interaction_feature_definition.json')
domains=features['domain_order'];targets=features['target_order']
model=doc('outputs/Q1/interaction_coefficients_13_targets.json')['targets']
recipes=read('outputs/Q1/recipes_512.csv');P=recipes[domains].to_numpy(float)
assert recipes['index'].is_unique and np.isfinite(P).all() and (P>=0).all() and np.allclose(P.sum(axis=1),1,atol=1e-12)
ids=recipes['index'].astype(int).to_numpy()
policy=doc('outputs/Q2/main_policy.json')
weights=np.array([policy['weights'][t] for t in targets]);assert np.isclose(weights.sum(),1)
ref=np.array([features['Q1_reference_p'][d] for d in domains])
qarows={r['mixture_domain']:r for r in doc('outputs/Q1/qa_mapping.json')['rows']}
mask=np.array([qarows[d]['mapping_type'] in ['direct','near_direct'] and qarows[d]['Q_A'] is not None for d in domains])
vals=np.array([qarows[d]['Q_A'] if mask[i] else 0 for i,d in enumerate(domains)],float)
coverage=P@mask;qa=P@vals/np.maximum(coverage,1e-30)
refcover=ref@mask;refqa=ref@vals/refcover
eligible=(coverage>1e-8)&(coverage+1e-8>=refcover)&((P@vals-refqa*coverage)>=-1e-8)
low,high=vals[mask].min(),vals[mask].max();slope=.9/(high-low);qref=.1+slope*(refqa-low)
effect=np.zeros(len(P))
for w,target in zip(weights,targets):
    e=model[target];pred=e['intercept']+P@np.array([e['main'][d] for d in domains])
    for pair in e['pairs']:
        a,b=pair['domains'];pred+=pair['gamma']*P[:,domains.index(a)]*P[:,domains.index(b)]
    effect+=w*(pred-e['fitted_reference_loss'])/e['fitted_reference_loss']
index={int(k):i for i,k in enumerate(ids)}

def quality(scale=1):return np.clip(qref+scale*slope*(qa-refqa),.1,1)
def g(q,fam):
    if fam=='exponential':return 1e7*math.exp(6*q)
    if fam=='power':return 5e9*q**4
    if fam=='logarithmic':return 2e9*math.log1p(10*q)
    raise ValueError(fam)
def base(n,d,q):
    return B1['E']+B1['A']*n**(-B1['alpha'])+B1['B']*d**(-B1['beta'])+(1-q)*(G['G0']+G['GN']*math.log(n)+G['GD']*math.log(d/100))
def cost(n,d,q,budget,context,fam,q0):
    c=6e18+2e14*context;h=1e9*max(0,g(q,fam)-g(q0,fam))
    return d*(c*n+h)

def solve_fixed(q,r,budget,context,fam,q0=.5):
    if q<q0-1e-12:return None
    c=6e18+2e14*context;h=1e9*max(0,g(q,fam)-g(q0,fam))
    hi=min(NMAX,(budget/DMIN-h)/c)
    if hi<NMIN*(1-1e-12):return None
    hi=max(NMIN,hi);lo,upper=math.log(NMIN),math.log(hi)
    factor=math.exp(r)
    def value(x):
        n=math.exp(x);d=min(DMAX,budget/(c*n+h));return base(n,d,q)*factor
    points=[lo,upper]
    if upper-lo>1e-12:
        opt=minimize_scalar(value,bounds=(lo,upper),method='bounded',options={'xatol':1e-12,'maxiter':200})
        assert opt.success;points.append(float(opt.x))
    kink=(budget/DMAX-h)/c
    if NMIN<kink<hi:points.append(math.log(kink))
    x=min(points,key=value);n=math.exp(x);d=min(DMAX,budget/(c*n+h))
    return dict(loss=value(x),n=n,d=d,q=q,cost=cost(n,d,q,budget,context,fam,q0))

def candidates(budget,context,fam,q0=.5,scale=1,lam=1):
    qs=quality(scale);selected=np.where(eligible&(qs>=q0-1e-12))[0]
    out=[]
    for i in selected:
        sol=solve_fixed(float(qs[i]),float(lam*effect[i]),budget,context,fam,q0)
        if sol is not None:out.append(dict(recipe=int(ids[i]),**sol))
    return selected,out

def native(budget,context,fam,q0=.5):
    c=6e18+2e14*context
    if budget<DMIN*c*NMIN*(1-1e-12):return None
    ceiling=1.
    if cost(NMIN,DMIN,1,budget,context,fam,q0)>budget:
        ceiling=brentq(lambda q:cost(NMIN,DMIN,q,budget,context,fam,q0)-budget,q0,1,xtol=1e-14)
    rw=float(effect[index[172]])
    def objective(q):
        sol=solve_fixed(q,rw,budget,context,fam,q0)
        return sol['loss'] if sol is not None else 1e30
    grid=np.linspace(q0,ceiling,101);values=np.array([objective(q) for q in grid])
    candidates_q=[q0,ceiling]
    for i in range(1,len(grid)-1):
        if values[i]<=values[i-1] and values[i]<=values[i+1]:
            opt=minimize_scalar(objective,bounds=(grid[i-1],grid[i+1]),method='bounded',options={'xatol':1e-12})
            assert opt.success;candidates_q.append(float(opt.x))
    best=min(candidates_q,key=objective)
    return solve_fixed(best,rw,budget,context,fam,q0)

def validate_tables():
    audit=[];joint_cache={};baseline_rows=[]
    for kind,name,qfield in [('fixed','fixed_policy_grid.csv','Q_B_proxy'),('joint','observed_joint_grid.csv','Q_B_proxy'),('native','native_Q_sensitivity_grid.csv','Q_score')]:
        df=read('outputs/Q3/'+name)
        for r in df.itertuples():
            key=(r.budget_FLOPs,r.context_tokens,r.quality_family)
            if kind=='fixed':
                i=index[172];sol=solve_fixed(float(quality()[i]),float(effect[i]),*key)
            elif kind=='joint':
                sel,allsol=candidates(*key);assert len(sel)==87
                sol=min(allsol,key=lambda x:(x['loss'],x['recipe'])) if allsol else None
                joint_cache[key]=allsol
            else:sol=native(*key)
            published=math.isfinite(r.N_params_B)
            assert published==(sol is not None),(kind,key)
            if sol is None:
                audit.append(dict(mode=kind,budget=key[0],context=key[1],family=key[2],feasible=False));continue
            n,d,q=r.N_params_B,r.D_tokens_B,getattr(r,qfield)
            i=index[int(r.recipe_index)]
            factor=math.exp(float(effect[i]));calc_loss=base(n,d,q)*factor
            cc=cost(n,d,q,*key,.5)
            assert NMIN-1e-10<=n<=NMAX+1e-10 and DMIN-1e-10<=d<=DMAX+1e-10 and .5-1e-10<=q<=1+1e-10
            assert cc<=key[0]*(1+1e-9)
            assert abs(calc_loss-r.conditional_bridge_loss)<1e-10
            if kind!='native':assert abs(q-quality()[i])<1e-10
            diff=r.conditional_bridge_loss-sol['loss']
            assert abs(diff)<2e-7,(kind,key,diff)
            if kind=='joint':assert int(r.recipe_index)==sol['recipe']
            gap=getattr(r,'global_gap',getattr(r,'fixed_p_convex_gap',float('nan')))
            audit.append(dict(mode=kind,budget=key[0],context=key[1],family=key[2],feasible=True,recipe=int(r.recipe_index),
                independent_loss=sol['loss'],published_loss=r.conditional_bridge_loss,independent_loss_abs_difference=abs(diff),
                independently_better_loss=max(0,diff),published_certificate_gap=gap,cost_over_budget=max(0,cc/key[0]-1),
                cost_relative_recompute_error=abs(cc-r.C_total_FLOPs)/key[0],budget_utilization=cc/key[0]))
            if kind=='fixed':
                c=6e18+2e14*key[1];h=1e9*max(0,g(q,key[2])-g(.5,key[2]));rw=float(effect[i]);factor=math.exp(rw)
                simple=[]
                # Both simple baselines retain the same recipe/Q/cost family.
                nn=min(NMAX,(key[0]/DMIN-h)/c)
                if nn>=NMIN:simple.append(('D_at_min',nn,DMIN))
                dd=min(DMAX,key[0]/(c*NMIN+h))
                if dd>=DMIN:simple.append(('N_at_min',NMIN,dd))
                for label,bn,bd in simple:
                    loss=base(bn,bd,q)*factor
                    baseline_rows.append(dict(budget=key[0],context=key[1],family=key[2],baseline=label,
                        baseline_loss=loss,optimal_loss=r.conditional_bridge_loss,model_relative_loss_reduction_percent=100*(loss-r.conditional_bridge_loss)/loss))
    pd.DataFrame(audit).to_csv(OUT/'configuration_audit.csv',index=False)
    pd.DataFrame(baseline_rows).to_csv(OUT/'simple_baselines.csv',index=False)
    df=pd.DataFrame(audit);summary={}
    for mode,gp in df.groupby('mode'):
        good=gp[gp.feasible]
        summary[mode]=dict(cells=len(gp),feasible=len(good),feasibility_agreement=True,
            max_independent_loss_difference=float(good.independent_loss_abs_difference.max()),
            max_published_certificate_gap=float(good.published_certificate_gap.max()),max_budget_overrun=float(good.cost_over_budget.max()),
            max_cost_relative_recompute_error=float(good.cost_relative_recompute_error.max()))
    bl=pd.DataFrame(baseline_rows)
    summary['simple_baselines']={label:dict(n=len(gp),median_model_loss_reduction_percent=float(gp.model_relative_loss_reduction_percent.median()),
        max_model_loss_reduction_percent=float(gp.model_relative_loss_reduction_percent.max())) for label,gp in bl.groupby('baseline')}
    fixed=read('outputs/Q3/fixed_policy_grid.csv');joint=read('outputs/Q3/observed_joint_grid.csv')
    keys=['budget_FLOPs','context_tokens','quality_family']
    pair=fixed.merge(joint,on=keys,suffixes=('_fixed','_joint'))
    both=pair[pair.N_params_B_fixed.notna()&pair.N_params_B_joint.notna()].copy()
    both['conditional_improvement_percent']=100*(both.conditional_bridge_loss_fixed-both.conditional_bridge_loss_joint)/both.conditional_bridge_loss_fixed
    summary['joint_vs_fixed']=dict(comparable_cells=len(both),strictly_better_cells=int((both.conditional_improvement_percent>1e-8).sum()),
        max_improvement_percent=float(both.conditional_improvement_percent.max()),newly_feasible_cells=int((pair.N_params_B_fixed.isna()&pair.N_params_B_joint.notna()).sum()))
    summary['high_budget_utilization']={mode:dict(min_percent=float(gp.budget_utilization.min()*100),max_percent=float(gp.budget_utilization.max()*100))
        for mode,gp in df[df.feasible & df.budget.eq(1e24)].groupby('mode')}
    return summary

def sensitivity():
    table=read('outputs/Q3/assumption_official_grid.csv')
    nominal=table[table.scenario.eq('baseline')].set_index(['budget_FLOPs','context_tokens','quality_family'])
    records=[];summary=[]
    for scenario,gp in table.groupby('scenario',sort=False):
        changed=0;valid_nominal=0;infeasible_nominal=0;regrets=[];row_errors=[];adaptive_regrets=[];adaptive_invalid=0
        for r in gp.itertuples():
            key=(r.budget_FLOPs,r.context_tokens,r.quality_family);q0=r.Q0;scale=r.quality_bridge_scale;lam=r.mixture_bridge_lambda
            sel,cand=candidates(*key,q0,scale,lam)
            sol=min(cand,key=lambda x:(x['loss'],x['recipe'])) if cand else None
            assert len(sel)==r.eligible_observed_recipes and len(cand)==r.feasible_observed_recipes
            assert (sol is not None)==math.isfinite(r.N_params_B)
            nom=nominal.loc[key]
            if sol is None:
                records.append(dict(scenario=scenario,budget=key[0],context=key[1],family=key[2],scenario_feasible=False));continue
            assert sol['recipe']==int(r.recipe_index),(scenario,key,sol['recipe'],r.recipe_index)
            row_errors.append(abs(sol['loss']-r.conditional_bridge_loss))
            assert row_errors[-1]<1e-8
            changed+=int(sol['recipe']!=int(nom.recipe_index))
            ni=index[int(nom.recipe_index)];nq=float(quality(scale)[ni]);nn,nd=nom.N_params_B,nom.D_tokens_B
            feasible=nq>=q0-1e-12 and cost(nn,nd,nq,*key,q0)<=key[0]*(1+1e-9)
            row=dict(scenario=scenario,budget=key[0],context=key[1],family=key[2],scenario_feasible=True,
                scenario_recipe=sol['recipe'],nominal_recipe=int(nom.recipe_index),nominal_configuration_still_feasible=feasible,
                independent_loss_abs_difference=row_errors[-1])
            same_recipe=[s for s in cand if s['recipe']==int(nom.recipe_index)]
            if same_recipe:
                adaptive=100*max(0,same_recipe[0]['loss']-sol['loss'])/sol['loss'];adaptive_regrets.append(adaptive)
                row.update(nominal_recipe_with_reoptimized_ND_feasible=True,nominal_recipe_reoptimized_relative_regret_percent=adaptive)
            else:
                adaptive_invalid+=1;row.update(nominal_recipe_with_reoptimized_ND_feasible=False)
            if feasible:
                val=base(nn,nd,nq)*math.exp(lam*effect[ni]);assert val-sol['loss']>=-1e-8
                regret=max(0,val-sol['loss']);relative=100*regret/sol['loss']
                valid_nominal+=1;regrets.append(relative);row.update(nominal_decision_regret=regret,nominal_relative_regret_percent=relative)
            else:infeasible_nominal+=1
            records.append(row)
        summary.append(dict(scenario=scenario,scenario_feasible_cells=len(row_errors),changed_recipe_cells=changed,
            matching_recipe_fraction=1-changed/len(row_errors),nominal_configurations_still_feasible=valid_nominal,
            nominal_configurations_infeasible_under_scenario=infeasible_nominal,
            nominal_recipe_with_reoptimized_ND_infeasible=adaptive_invalid,
            max_nominal_recipe_reoptimized_relative_regret_percent=max(adaptive_regrets) if adaptive_regrets else None,
            max_nominal_relative_regret_percent=max(regrets) if regrets else None,max_independent_loss_difference=max(row_errors)))
    pd.DataFrame(records).to_csv(OUT/'sensitivity_decision_regret.csv',index=False)
    return summary

def external():
    table=read('outputs/Q3/external_nd_runs.csv');published=read('outputs/Q3/external_nd_budget_comparison.csv')
    obs='observed_Paloma_C4_loss_in_OpenLM_coordinates';records=[];correlations=[]
    assert len(table)==42 and table.source_model.is_unique
    for corpus,gp in table.groupby('training_corpus'):
        predicted=B1['E']+B1['A']*gp.N_params_B**(-B1['alpha'])+B1['B']*gp.D_tokens_B**(-B1['beta'])
        assert np.allclose(predicted,gp.B1_predicted_loss_in_Pythia_coordinates,rtol=0,atol=1e-12)
        assert np.allclose(6e18*gp.N_params_B*gp.D_tokens_B,gp.C_train_proxy_FLOPs,rtol=1e-12)
        correlations.append(dict(corpus=corpus,n=len(gp),spearman=float(predicted.rank().corr(gp[obs].rank()))))
        for budget in [1e20,1e21]:
            subset=gp[gp.C_train_proxy_FLOPs<=budget*(1+1e-12)]
            assert 1<len(subset)<len(gp)
            chosen=subset.loc[subset.B1_predicted_loss_in_Pythia_coordinates.idxmin()];best=subset.loc[subset[obs].idxmin()]
            regret=float(chosen[obs]-best[obs]);relative=100*regret/best[obs]
            rank=int((subset[obs]<chosen[obs]-1e-12).sum()+1)
            # Empirical decision regret uses observed losses only within each corpus.
            records.append(dict(corpus=corpus,budget=budget,n_candidates=len(subset),selected_model=chosen.source_model,
                observed_best=best.source_model,top1_match=chosen.source_model==best.source_model,observed_rank_of_selection=rank,
                observed_loss_regret=regret,observed_relative_regret_percent=relative,
                regret_over_candidate_loss_range=regret/(subset[obs].max()-best[obs])))
            pub=published[published.training_corpus.eq(corpus)&published.training_cost_budget_FLOPs.eq(budget)].iloc[0]
            assert abs(regret-pub.observed_loss_regret_in_OpenLM_coordinates)<1e-12
    pd.DataFrame(records).to_csv(OUT/'external_decision_metrics.csv',index=False)
    return dict(correlations=correlations,informative_budget_comparisons=len(records),top1_hits=sum(r['top1_match'] for r in records),
        top2_hits=sum(r['observed_rank_of_selection']<=2 for r in records),max_observed_regret=max(r['observed_loss_regret'] for r in records),
        mean_observed_regret=float(np.mean([r['observed_loss_regret'] for r in records])),max_observed_relative_regret_percent=max(r['observed_relative_regret_percent'] for r in records),
        scope='Frozen 42-row public real-training observation table; N,D and training-cost only; no empirical full Q,p or attention validation')

def transition_checks():
    table=read('outputs/Q3/transitions.csv');resolution=doc('outputs/Q3/transition_resolution.json')
    assert len(table)==82 and (table.budget_right>=table.budget_left).all()
    assert np.allclose(table.relative_width,table.budget_right/table.budget_left-1,atol=1e-12)
    assert table.relative_width.max()<1e-4
    relevant=table[table.scenario.eq('observed_joint')&table.context_tokens.eq(8192)&table.quality_family.eq('power')]
    target=relevant[relevant.state_left.str.contains('recipe=477;')&relevant.state_right.str.contains('recipe=172;')]
    assert len(target)==1
    r=target.iloc[0];states=[];margins=[]
    for budget in [r.budget_left,r.budget_right,r.budget_left*.995,r.budget_right*1.005]:
        _,sols=candidates(budget,8192,'power');sols.sort(key=lambda x:x['loss']);states.append(sols[0]['recipe']);margins.append(sols[1]['loss']-sols[0]['loss'])
    assert states==[477,172,477,172]
    return dict(published_brackets=len(table),max_relative_width=float(table.relative_width.max()),
        key_recipe_transition_budget=[float(r.budget_left),float(r.budget_right)],independent_endpoint_and_half_percent_neighbor_recipes=states,
        best_vs_second_loss_margins=margins,coarse_grid_disagreement_groups=resolution['coarse_fine_signature_disagreements'],
        caution='Numerical brackets of conditional model states; no empirical physical phase transition')

if __name__=='__main__':
    result=dict(reviewed_main='c6b36c08b5a85c81a3889d48d50c26ac136a048b',runtime=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__),
        evaluation_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),random_seed=None,
        independent_solver='JSON equations + bounded scalar search on logN; native Q uses 101-point scan with all sampled local minima refined; no production solver imported')
    print('Checking 108 configurations and simple baselines...',flush=True);result['configuration']=validate_tables()
    print('Checking 243 assumption cells and decision regret...',flush=True);result['sensitivity']=sensitivity()
    print('Checking public empirical selection and transition endpoints...',flush=True);result['external']=external();result['transitions']=transition_checks()
    result['input_sha256']=HASHES
    (OUT/'evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},ensure_ascii=False,indent=2),flush=True)
