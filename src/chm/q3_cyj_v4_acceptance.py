"""Owner acceptance of pinned CYJ v4 and CHM joint-model Q3 verification."""
import csv,hashlib,io,json,math
from pathlib import Path
import numpy as np
from cyj_v4_consumer import ROOT,RELEASE,MANIFEST_SHA,blob,consume_release,SolverAdapter
from q3_generic_solver import solve_generic,Support,enrich_kkt,cost_and_grad
from q3_joint_certificate import certify
from q3_quality_cost_geometry import FAMILIES
from q3_b7_numerical_audit import write_csv


def main():
    out=ROOT/'outputs/chm/q3_cyj_v4_acceptance';out.mkdir(parents=True,exist_ok=True)
    with consume_release() as (producer,manifest,smoke):
        model=SolverAdapter(producer)
        # Verify independently supplied gradients, costs, gates and boundary behavior.
        derivative_errors=[]
        for point in ((.1,20.,.6),(.7,150.,.5),(7.,500.,.8)):
            _,g=model.value_grad(*point)
            for i,x in enumerate(point):
                h=1e-5*x;a=list(point);b=list(point);a[i]-=h;b[i]+=h
                fd=(model.value_grad(*b)[0]-model.value_grad(*a)[0])/(2*h)
                derivative_errors.append(abs(fd-g[i])/max(abs(g[i]),1e-12))
        assert max(derivative_errors)<1e-7
        for c in manifest['context_tokens']:
            for f in FAMILIES:
                response=producer.evaluate(N_params_B=.7,D_tokens_B=150.,Q_score=.6,Q0=.5,context_tokens=c,quality_family=f,budget_FLOPs=1e22)
                expected=cost_and_grad(.7,150.,.6,.5,c,f)[0]
                assert abs(response['cost']['total']/expected-1)<1e-12

        for point in ((.07,9.,.5),(.07,10.,float('nan'))):
            try:producer.value_grad(*point)
            except ValueError:pass
            else:raise AssertionError('invalid input accepted')
        from chm_adapter_v4 import CHMAdapterV4
        try:CHMAdapterV4(mode='formal')
        except ValueError:pass
        else:raise AssertionError('formal gate bypassed')
        # Q1 v1.3 changes the A quality proxy, but not the mixture coefficients/reference.
        from chm_adapter_v2 import load_q1
        from q1_interface_v1_3 import Q1Interface
        old,_=load_q1();current=Q1Interface(ROOT)
        assert old.coefficients==current.coefficients and old.reference==current.reference
        compatibility={'old_schema':'chm.q1.v1.2','current_schema':'chm.q1.v1.3',
                       'mixture_coefficients_identical':True,'mixture_reference_identical':True,
                       'A_quality_proxy_changed':True,'B_native_model_uses_A_quality':False,
                       'action':'retain immutable v4; CYJ should repin Q1 metadata in next release'}
        def solve(b,c,f,starts=12,support=None):
            minimum=(6e18+2e14*c)*model.support.N[0]*model.support.D[0]
            base={'budget_FLOPs':b,'context_tokens':c,'quality_family':f,'Q0_scenario':.5,
                  'context_role':'C7_candidate' if c in (2048,8192,131072) else 'CYJ_external_sensitivity',
                  'ready_for_Q3':False,'feasible':b>=minimum}
            if b<minimum:return {**base,'active_support':'infeasible'}
            engine='SLSQP'
            try:
                r,trials=solve_generic(model,budget=b,context_tokens=c,Q0=.5,family=f,starts=starts,support=support)
            except RuntimeError:
                bounds=producer.bounds if support is None else (support.N,support.D,support.Q)
                cert=certify(producer.joint_theta,bounds,b,c,f,tolerance=1e-9)
                point={'N_params_B':cert['N_params_B'],'D_tokens_B':cert['D_tokens_B'],'Q':cert['Q_score']}
                r=enrich_kkt(point,model,b,c,.5,f,support=support)
                engine='certified_reduction_after_SLSQP_failure'
                print('certified fallback',b,c,f,flush=True)
            assert r['kkt_check_pass'],(b,c,f,r)

            return {**base,'N_params_B':r['N_params_B'],'D_tokens_B':r['D_tokens_B'],'Q_score':r['Q'],
                    'B7_diagnostic_loss':r['loss'],'cost_FLOPs':r['cost_FLOPs'],
                    'budget_utilization':r['budget_utilization'],'active_support':';'.join(sorted(r['active_set'])),
                    'kkt_relative_violation':r['kkt_relative_violation'],'kkt_check_pass':True,'solver':engine}
        upstream=list(csv.DictReader(io.StringIO(blob('outputs/cyj/q3/q3_budget_sweep.csv').decode())))
        reproduced=[]
        for u in upstream:
            r=solve(float(u['budget_FLOPs']),int(u['context_tokens']),u['quality_family'])
            if r['feasible']:
                r['producer_loss_difference']=r['B7_diagnostic_loss']-float(u['conditional_loss'])
                assert abs(r['producer_loss_difference'])<1e-6
            reproduced.append(r)
        write_csv(out/'producer_grid_recheck.csv',reproduced)
        print('producer grid checked',len(reproduced),flush=True)
        certificates=[]
        for c in (2048,8192,30000,131072):
            for b in (1e19,1e20,1e22):
                for f in FAMILIES:
                    r=solve(b,c,f,24)
                    certificate=certify(producer.joint_theta,producer.bounds,b,c,f)
                    if r['feasible']:
                        assert certificate['global_lower_bound']-1e-10<=r['B7_diagnostic_loss']<=certificate['feasible_upper_bound']+1e-7
                        r.update({k:v for k,v in certificate.items() if k not in ('N_params_B','D_tokens_B','Q_score')})
                    certificates.append(r)
        write_csv(out/'global_certificates.csv',certificates)
        print('joint global certificates checked',flush=True)
        scan=[];transitions=[];resolution=[]
        for c in (2048,8192,131072):
            for f in FAMILIES:
                group=[solve(10**(19+5*i/160),c,f,5) for i in range(161)]
                valid=[r for r in group if r['feasible']]
                assert all(b['B7_diagnostic_loss']<=a['B7_diagnostic_loss']+1e-7 for a,b in zip(valid,valid[1:]))
                changes=lambda rows:[(a['active_support'],b['active_support']) for a,b in zip(rows,rows[1:]) if a['active_support']!=b['active_support']]
                points=161
                while changes(group)!=changes(group[::2]):
                    if points>=1281:raise RuntimeError(f'unresolved transition resolution: {c}/{f}')
                    points=2*points-1
                    print('refining budget grid',c,f,points,flush=True)
                    previous=group
                    group=[previous[i//2] if i%2==0 else solve(10**(19+5*i/(points-1)),c,f,8) for i in range(points)]
                resolution.append({'context_tokens':c,'quality_family':f,'fine_points':points,'coarse_points':(points+1)//2,'transition_signatures_agree':True})
                for a,b in zip(group,group[1:]):
                    if a['active_support']==b['active_support']:continue
                    left,right=a['budget_FLOPs'],b['budget_FLOPs']
                    while right/left-1>1e-5:
                        mid=math.sqrt(left*right);r=solve(mid,c,f,8)
                        if r['active_support']==a['active_support']:left=mid
                        else:right=mid
                    transitions.append({'context_tokens':c,'quality_family':f,'budget_left':left,'budget_right':right,
                                        'active_left':a['active_support'],'active_right':b['active_support']})
                scan.extend(group)
        write_csv(out/'budget_scan.csv',scan);write_csv(out/'transitions.csv',transitions);write_csv(out/'resolution_check.csv',resolution)
        sensitivity=[]
        # Same nested rectangles as historical linear-Q comparison: observed second-largest bounds.
        from q3_b7_diagnostic import load_model
        historical_support=load_model()['support']
        for axis,key in enumerate(('N_params_B','D_tokens_B')):
            bounds=list(producer.bounds);bounds[axis]=(bounds[axis][0],historical_support[key][-2]);support=Support(*bounds)
            for r in reproduced:
                if r['context_tokens'] not in (2048,8192,131072) or r['budget_FLOPs'] not in (1e19,1e22,1e24):continue
                s=solve(r['budget_FLOPs'],r['context_tokens'],r['quality_family'],support=support)
                s.update(restricted_axis=key,restricted_upper=bounds[axis][1])
                if s['feasible']:
                    s['loss_penalty']=s['B7_diagnostic_loss']-r['B7_diagnostic_loss'];assert s['loss_penalty']>=-1e-7
                sensitivity.append(s)
        write_csv(out/'support_sensitivity.csv',sensitivity)
        feasible=[r for r in reproduced if r['feasible']]
        report={'consumer_status':'ACCEPTED_FOR_CONDITIONAL_NDQ_ONLY','ready_for_Q3':False,
                'release_commit':RELEASE,'manifest_sha256':MANIFEST_SHA,'batch_fixture':smoke,
                'q1_compatibility':compatibility,'max_gradient_relative_error':max(derivative_errors),
                'producer_grid_rows':len(reproduced),'producer_grid_feasible':len(feasible),
                'max_producer_loss_difference':max(abs(r['producer_loss_difference']) for r in feasible),
                'max_kkt_relative_violation':max(r['kkt_relative_violation'] for r in feasible),
                'certificate_rows':len(certificates),'certificate_feasible':sum(r['feasible'] for r in certificates),
                'max_global_gap':max(r['global_gap'] for r in certificates if r['feasible']),
                'budget_scan_rows':len(scan),'transition_brackets':len(transitions),'support_sensitivity_rows':len(sensitivity),
                'remaining_blockers':['real-training external validation','uncalibrated total predictive uncertainty','A/B and Loss/Benchmark bridges'],
                'certificate_scope':'joint model prerequisites checked; floating-point lower bounds, not interval arithmetic',
                'provenance':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ('producer_grid_recheck.csv','global_certificates.csv','budget_scan.csv','transitions.csv','support_sensitivity.csv')}}
        (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2))

def finalize_comparisons():
    out=ROOT/'outputs/chm/q3_cyj_v4_acceptance'
    rows=list(csv.DictReader((out/'producer_grid_recheck.csv').open()))
    key=lambda r:(float(r['budget_FLOPs']),int(r['context_tokens']),r['quality_family'])
    lookup={key(r):r for r in rows}
    audit_ref='2c237b3c6c47133c85e64a50c8129c2a0a829bea'
    independent=list(csv.DictReader(io.StringIO(blob('outputs/cyj/q3/q3_independent_optimizer_check.csv',audit_ref).decode())))
    differences=[]
    for r in independent:
        ours=lookup[key(r)]
        if r['independent_status']=='feasible':
            gap=float(r['loss'])-float(ours['B7_diagnostic_loss'])
            assert abs(gap)<1e-7
            differences.append({'budget_FLOPs':key(r)[0],'context_tokens':key(r)[1],'quality_family':key(r)[2],'DE_minus_owner_loss':gap})
        else:assert ours['feasible']=='False'
    write_csv(out/'independent_DE_comparison.csv',differences)
    comparisons=[]
    from q3_b7_diagnostic import cost_parts
    for r in rows:
        if r['feasible']!='True':continue
        b,c,f=key(r)
        group=[x for x in rows if x['feasible']=='True' and key(x)[:2]==(b,c)]
        costs=cost_parts(float(r['N_params_B']),float(r['D_tokens_B']),float(r['Q_score']),.5,c,f)
        comparisons.append({'budget_FLOPs':b,'context_tokens':c,'quality_family':f,
                            'loss_gap_to_best_cost_scenario':float(r['B7_diagnostic_loss'])-min(float(x['B7_diagnostic_loss']) for x in group),
                            **dict(zip(('training_share','attention_share','quality_share'),(v/sum(costs) for v in costs)))})
    write_csv(out/'cost_comparison.csv',comparisons)
    report=json.loads((out/'manifest.json').read_text())
    report['independent_DE_comparison']={'source_commit':audit_ref,'feasible_rows':len(differences),
                                      'max_absolute_loss_difference':max(abs(r['DE_minus_owner_loss']) for r in differences)}
    import platform,scipy
    report['environment']={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}
    report['solver_policy']={'nominal_starts':12,'certificate_crosscheck_starts':24,'seed':20260924,
                             'transition_relative_width':1e-5,'failed_SLSQP':'independent certified reduction plus KKT'}
    report['hash_mode']='sha256_utf8_lf_normalized_for_csv_and_source_code'
    report['source_code_sha256']={name:hashlib.sha256((ROOT/'src/chm'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                                  for name in ('cyj_v4_consumer.py','q3_cyj_v4_acceptance.py','q3_joint_certificate.py','q3_generic_solver.py','q3_quality_cost_geometry.py')}
    report['provenance']={p.name:hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sorted(out.glob('*.csv'))}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
    finalize_comparisons()
