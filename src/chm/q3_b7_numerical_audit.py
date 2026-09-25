"""Reproducible B7 conditional optimality, budget and support audit."""
import copy
import csv
import json
import math
from pathlib import Path
import scipy
from q3_b7_diagnostic import (ROOT, CYJ_REF, MODEL_SHA256, CONTEXTS, FAMILIES,
                              BUDGETS, load_model, optimize, loss)
from q3_generic_solver import Support, solve_generic, enrich_kkt


class B7Loss:
    def __init__(self, model):
        self.p=model['models']['linear_quality']['full_fit']['parameters']
        s=model['support']
        self.support=Support(tuple(s['N_params_B'][i] for i in (0,-1)),
                             tuple(s['D_tokens_B'][i] for i in (0,-1)),
                             tuple(s['Q_score'][i] for i in (0,-1)))
    def value_grad(self,n,d,q):
        p=self.p
        return loss(n,d,q,p),(-p['alpha']*p['A']*n**(-p['alpha']-1),
                              -p['beta']*p['B']*d**(-p['beta']-1),-p['G'])


def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader();w.writerows(rows)


def signature(r):
    return r.get('active_support','infeasible')+('' if r.get('budget_utilization',0)<1-1e-7 else ';budget')


def main():
    model=load_model();adapter=B7Loss(model)
    out=ROOT/'outputs/chm/q3_b7_numerical_audit_v2';out.mkdir(parents=True,exist_ok=True)
    nominal=[];scan=[];transitions=[];sensitivity=[]
    for c in CONTEXTS:
        for f in FAMILIES:
            for b in BUDGETS:
                r=optimize(b,c,f,model)
                if r['feasible']:
                    generic,trials=solve_generic(adapter,budget=b,context_tokens=c,Q0=.5,family=f,starts=24)
                    kkt=enrich_kkt({'N_params_B':r['N_params_B'],'D_tokens_B':r['D_tokens_B'],'Q':r['Q_score']},adapter,b,c,.5,f)
                    r.update(kkt_check_pass=kkt['kkt_check_pass'],kkt_relative_violation=kkt['kkt_relative_violation'],
                             multistart_loss_gap=generic['loss']-r['B7_diagnostic_loss'],
                             converged_starts=sum(t['success'] and t['feasible'] for t in trials))
                    assert r['kkt_check_pass'] and abs(r['multistart_loss_gap'])<1e-6
                nominal.append(r)
            # 161 points includes the entire coarser 81-point scan for resolution comparison.
            group=[optimize(10**(19+5*i/160),c,f,model,tolerance=1e-6) for i in range(161)]
            feasible=[r for r in group if r['feasible']]
            assert all(b['B7_diagnostic_loss']<=a['B7_diagnostic_loss']+2e-6 for a,b in zip(feasible,feasible[1:]))
            for a,b in zip(group,group[1:]):
                if signature(a)==signature(b):continue
                left,right=a['budget_FLOPs'],b['budget_FLOPs'];sig=signature(a)
                while right/left-1>1e-5:
                    mid=math.sqrt(left*right);r=optimize(mid,c,f,model)
                    if signature(r)==sig:left=mid
                    else:right=mid
                transitions.append({'context_tokens':c,'quality_family':f,'budget_left':left,'budget_right':right,
                                    'active_left':sig,'active_right':signature(b),'relative_bracket':right/left-1,
                                    'status':'conditional_active_set_change_not_physical_threshold'})
            coarse=group[::2]
            assert [(signature(a),signature(b)) for a,b in zip(coarse,coarse[1:]) if signature(a)!=signature(b)]==[(signature(a),signature(b)) for a,b in zip(group,group[1:]) if signature(a)!=signature(b)]
            scan.extend(group)
            for key in ('N_params_B','D_tokens_B'):
                restricted=copy.deepcopy(model)
                restricted['support'][key]=model['support'][key][:-1]
                for b in BUDGETS:
                    r=optimize(b,c,f,restricted)
                    base=next(x for x in nominal if x['budget_FLOPs']==b and x['context_tokens']==c and x['quality_family']==f)
                    r['restricted_axis']=key;r['restricted_upper']=restricted['support'][key][-1]
                    if r['feasible']:
                        r['loss_penalty']=r['B7_diagnostic_loss']-base['B7_diagnostic_loss']
                        assert r['loss_penalty']>=-2e-7
                    sensitivity.append(r)
    comparisons=[]
    for c in CONTEXTS:
        for b in BUDGETS:
            group=[r for r in nominal if r['context_tokens']==c and r['budget_FLOPs']==b and r['feasible']]
            if group:
                best=min(r['B7_diagnostic_loss'] for r in group)
                comparisons.extend({'context_tokens':c,'budget_FLOPs':b,'quality_family':r['quality_family'],
                                    'loss_gap_to_best_cost_scenario':r['B7_diagnostic_loss']-best,
                                    'training_share':r['C_train_FLOPs']/r['C_total_FLOPs'],
                                    'attention_share':r['C_attention_FLOPs']/r['C_total_FLOPs'],
                                    'quality_share':r['C_quality_FLOPs']/r['C_total_FLOPs']} for r in group)
    write_csv(out/'cost_comparison.csv',comparisons)
    for name,rows in (('nominal',nominal),('budget_scan',scan),('transitions',transitions),('support_sensitivity',sensitivity)):
        write_csv(out/(name+'.csv'),rows)
    feasible=[r for r in nominal if r['feasible']]
    manifest={'status':'VALIDATED_FOR_STATED_NUMERICAL_SCOPE','ready_for_Q3':False,
              'scope':'B7 semi-synthetic conditional model only; rectangular interpolation; Q0=.5; no A/B bridge',
              'cyj_commit':CYJ_REF,'artifact_sha256':MODEL_SHA256,'scipy_version':scipy.__version__,
              'nominal_rows':len(nominal),'feasible_nominal_rows':len(feasible),'budget_scan_rows':len(scan),
              'transition_brackets':len(transitions),'support_sensitivity_rows':len(sensitivity),
              'max_nominal_global_gap':max(r['global_gap'] for r in feasible),
              'max_multistart_loss_gap':max(abs(r['multistart_loss_gap']) for r in feasible),
              'max_kkt_relative_violation':max(r['kkt_relative_violation'] for r in feasible),
              'checks':['all nominal KKT passed','24-start independent SLSQP agreement','budget loss monotonicity',
                        '81/161 point transition signatures agree','nested support cannot improve loss'],
              'limitations':['floating-point bounds are not interval arithmetic proofs','transition brackets use numerical active-set tolerance',
                             'parameter and model uncertainty not included','formal publication remains blocked by upstream validation']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
