from pathlib import Path
import argparse,json,csv,math
parser=argparse.ArgumentParser(description='Read-only independent checks of frozen Q1/Q3/Q4 results')
parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args()
base=args.repo_root.resolve()
out=args.output_dir.resolve()
out.mkdir(parents=True,exist_ok=True)
def js(p): return json.loads((base/p).read_text(encoding='utf-8-sig'))
def rows(p): return list(csv.DictReader((base/p).open(encoding='utf-8-sig')))
co=js('outputs/Q1/interaction_coefficients_13_targets.json')['targets']
def pred(p): return {k:v['intercept']+sum(b*float(p[j]) for j,b in v['main'].items())+sum(t['gamma']*float(p[t['domains'][0]])*float(p[t['domains'][1]]) for t in v['pairs']) for k,v in co.items()}
ev={'q1_hull':[],'q1_discrete':[]}
for row in js('outputs/Q1/hull_bounds.json'):
    ls=pred(row['feasible_composition']); rr=[(ls[k]-co[k]['fitted_reference_loss'])/co[k]['fitted_reference_loss'] for k in ls]
    obj=sum(rr)/len(rr) if row['mode']=='weighted' else max(rr)
    ev['q1_hull'].append({'policy':row['policy'],'mode':row['mode'],'min_loss':min(ls.values()),'negative_targets':{k:v for k,v in ls.items() if v<0},'objective':obj,'published_difference':obj-row['feasible_upper_bound_relative']})
for r in rows('outputs/Q1/decision_panel.csv')[:4]:
    ls=pred(r);ev['q1_discrete'].append({'recipe':r['selected_index'],'min_loss':min(ls.values()),'negative_targets':{k:v for k,v in ls.items() if v<0}})
c=js('outputs/Q2/model_coefficients.json');a=c['B1_backbone'];g=c['B7_quality_extension']
def loss(n,d,q,r): return (a['E']+a['A']*n**(-a['alpha'])+a['B']*d**(-a['beta'])+(1-q)*(g['G0']+g['GN']*math.log(n)+g['GD']*math.log(d/100)))*math.exp(r)
grid=rows('outputs/Q3/observed_joint_grid.csv');checks=[]
for r in grid:
    if not r['N_params_B']:continue
    n,d,q,b,ctx=map(float,[r['N_params_B'],r['D_tokens_B'],r['Q_B_proxy'],r['budget_FLOPs'],r['context_tokens']]);fam=r['quality_family'];q0=float(r['Q0_scenario'])
    fn={'power':lambda x:5e9*x**4,'exponential':lambda x:1e7*math.exp(6*x),'logarithmic':lambda x:2e9*math.log(1+10*x)}[fam]
    cost=6e18*n*d+2e14*n*d*ctx+1e9*d*max(fn(q)-fn(q0),0)
    checks.append({'loss_error':abs(loss(n,d,q,float(r['Q1_weighted_effect']))-float(r['conditional_bridge_loss'])),'cost_relative_error':abs(cost-float(r['C_total_FLOPs']))/b,'budget_excess_relative':max(0,cost/b-1)})
ev['q3_grid']={'feasible_rows':len(checks),'max_errors':{k:max(r[k] for r in checks) for k in checks[0]}}
params=next(r for r in rows('outputs/Q4/frontier_parameters.csv') if r['type']=='non_pretrained' and r['model']=='quantile_resource')
f0=float(params['anchor_score']);bn=float(params['b_logN']);bt=float(params['b_month'])
ev['q4_forecast']={str(h):100/(1+math.exp(-(math.log(f0/(100-f0))+bn*.5*.5*.690315*h/12+.5*bt*h))) for h in [12,24]}
mx=next(r for r in rows('outputs/Q4/frontier_maximum_scenarios.csv') if r['type']=='non_pretrained' and r['horizon_months']=='12' and r['compute_scenario']=='half')
un=next(r for r in rows('outputs/Q4/frontier_scenario_union.csv') if r['type']=='non_pretrained' and r['resource_gate']=='primary' and r['horizon_months']=='12' and r['compute_scenario']=='half')
ev['q4_envelope_diagnostic']={'meaning':'independent illustrative deterministic envelope, not production result nor confidence interval','lower':max(float(mx['historical_record_score']),float(un['scenario_union_lower'])+float(mx['tail_gap_lower'])),'upper':min(100,max(float(mx['historical_record_score']),float(un['scenario_union_upper'])+float(mx['tail_gap_upper'])))}
(out/'independent_checks.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps(ev,ensure_ascii=False,indent=2))
