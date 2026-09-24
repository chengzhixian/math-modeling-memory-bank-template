"""Joint constrained least squares for B7; conditional semi-synthetic evidence."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import subprocess

import numpy as np
from scipy.optimize import minimize

from audit_b_scaling_laws import ROOT, sha256
from b7_formal_model import AXES, BOUNDS
from compare_b7_quality_interactions import fit_candidates, predict as staged_predict
from quality_scaling import source_data

NAMES = ("E", "A", "B", "alpha", "beta", "G0", "GN", "GD")
FAMILIES = ("no_Q", "constant_G", "Q_x_logN", "Q_x_logD", "Q_x_logN_logD")
INDICES = {"no_Q": (0,1,2,3,4), "constant_G": (0,1,2,3,4,5),
           "Q_x_logN": (0,1,2,3,4,5,6), "Q_x_logD": (0,1,2,3,4,5,7),
           "Q_x_logN_logD": tuple(range(8))}
SEED = 20260925
SOURCE_HASH = "880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a"
OUTPUT = ROOT / "outputs/cyj/quality/b7_joint_fit.json"
PARAM_BOUNDS = ((0.,10.),(1e-8,100.),(1e-8,100.),(.01,3.),(.01,3.),(-10.,10.),(-10.,10.),(-10.,10.))
CORNERS = np.array([[0.,0.,0.,0.,0.,1.,np.log(n),np.log(d/100)]
                    for n,d in itertools.product(BOUNDS[0], BOUNDS[1])])


def metadata():
    return {"scientific_status": "conditional_B7_semi_synthetic",
            "candidate_result_scope": "B7_NDQ", "formal_result_scope": None,
            "support": dict(zip(AXES, BOUNDS)), "source_dataset": "official_attachment_B7",
            "source_hash": SOURCE_HASH, "ready_for_Q3": False,
            "code_commit": subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")


def value_jac(theta, x):
    n,d,q = np.asarray(x,float).T
    E,A,B,a,b,g0,gn,gd = theta
    u,v,w = n**-a,d**-b,1-q
    ln,ld = np.log(n),np.log(d)
    prediction = E+A*u+B*v+w*(g0+gn*ln+gd*np.log(d/100))
    jac = np.column_stack((np.ones(len(n)),u,v,-A*u*ln,-B*v*ld,w,w*ln,w*np.log(d/100)))
    return prediction,jac


def predict(theta, x):
    x=np.asarray(x,float)
    if x.ndim != 2 or x.shape[1] != 3 or not np.all(np.isfinite(x)):
        raise ValueError("finite Nx3 points required")
    if any(np.any(x[:,i]<lo) or np.any(x[:,i]>hi) for i,(lo,hi) in enumerate(BOUNDS)):
        raise ValueError("outside B7 support")
    return value_jac(theta,x)[0]


def metrics(pred, y):
    r=np.asarray(pred)-y
    return {"rmse":float(np.sqrt(np.mean(r*r))),"mae":float(np.mean(abs(r))),
            "bias_prediction_minus_observed":float(np.mean(r)),"max_abs_error":float(np.max(abs(r)))}


def fit_joint(x,y,family="Q_x_logN_logD",starts=12,seed=SEED,wide=False):
    x,y=np.asarray(x,float),np.asarray(y,float)
    if family not in INDICES or starts<2 or x.shape != (len(y),3) or len(y)<12:
        raise ValueError("invalid fit specification")
    if not np.all(np.isfinite(y)) or np.any(y<=0):
        raise ValueError("invalid training loss")
    predict(np.array([1.,1.,1.,.3,.3,.4,0.,0.]),x)
    ids=np.array(INDICES[family]); matrix=CORNERS[:,ids]
    bounds=np.array(PARAM_BOUNDS,float)
    if wide:
        bounds[:,1]*=2
        bounds[5:,0]*=2
        bounds[3:5,0]/=2
    bounds=bounds[ids]
    initial=np.array([1.5,.5,1.5,.3,.3,.4,0.,0.])[ids]
    rng=np.random.default_rng(seed)
    guesses=[initial]
    for _ in range(starts-1):
        t=np.array([rng.uniform(.5,2.),rng.uniform(.1,1.5),rng.uniform(.5,4.),
                    rng.uniform(.08,.9),rng.uniform(.08,.9),.5,0.,0.])
        guesses.append(t[ids])
    def unpack(v):
        theta=np.zeros(8);theta[ids]=v;return theta
    def objective(v):
        pred,jac=value_jac(unpack(v),x);r=pred-y
        return float(.5*r@r),jac[:,ids].T@r
    constraints=[] if family=="no_Q" else [
        {"type":"ineq","fun":lambda t:matrix@t-1e-8,"jac":lambda t:matrix}]
    trials=[]
    for i,guess in enumerate(guesses):
        res=minimize(objective,guess,jac=True,method="SLSQP",bounds=bounds,
                     constraints=constraints,options={"ftol":1e-11,"maxiter":2000})
        theta=unpack(res.x);pred,_=value_jac(theta,x)
        gains=CORNERS@theta
        feasible=bool(np.all(np.isfinite(theta)) and np.all(np.isfinite(pred))
                      and (family=="no_Q" or min(gains)>=1e-8-1e-10))
        trials.append({"start":i,"initial":list(map(float,guess)),"success":bool(res.success),
                       "feasible":feasible,"message":str(res.message),"iterations":int(res.nit),
                       "sse":float(np.sum((pred-y)**2)),"theta":theta.tolist(),
                       "near_parameter_boundary":bool(np.any(np.minimum(res.x-bounds[:,0],bounds[:,1]-res.x)<1e-6))})
    good=[t for t in trials if t["success"] and t["feasible"]]
    if not good:raise ValueError(f"all joint starts failed: {family}")
    best=min(good,key=lambda t:t["sse"])
    near=[t for t in good if t["sse"]<=best["sse"]+1e-7*max(1,best["sse"])]
    return {"family":family,"theta":best["theta"],"parameter_names":NAMES,
            "fit":metrics(predict(best["theta"],x),y),"sse":best["sse"],
            "free_parameters":len(ids),"best_at_boundary":best["near_parameter_boundary"],
            "corner_quality_gain":(CORNERS@np.array(best["theta"])).tolist(),
            "successful_starts":len(good),"near_best_starts":len(near),
            "near_best_parameter_range":np.ptp([t["theta"] for t in near],axis=0).tolist(),
            "trials":trials}


def run(starts=12,bootstrap=200):
    sources,x,y,rows=source_data()
    if sources["supplementary_NQ_experiment_expanded.csv"]["sha256"]!=SOURCE_HASH:
        raise ValueError("B7 source changed")
    full=fit_joint(x,y,starts=starts)
    staged=fit_candidates(x,y)["Q_x_logN_logD"]
    wide=fit_joint(x,y,starts=starts,wide=True)
    comparison=[];oof=[]
    for axis,name in enumerate(AXES):
        for level in np.unique(x[:,axis]):
            held=x[:,axis]==level
            joint=fit_joint(x[~held],y[~held],starts=starts)
            old=fit_candidates(x[~held],y[~held])["Q_x_logN_logD"]
            jp=predict(joint["theta"],x[held]);sp=staged_predict(old,x[held],"Q_x_logN_logD")
            comparison.append({"axis":name,"held_level":float(level),"joint":metrics(jp,y[held]),
                               "staged":metrics(sp,y[held]),"joint_fit":joint})
            oof.extend({"axis":name,"source_line":rows[i]["source_line"],"observed":float(y[i]),
                        "joint":float(jp[j]),"staged":float(sp[j])} for j,i in enumerate(np.flatnonzero(held)))
        print(name,"joint CV complete",flush=True)
    summary=[]
    for method in ("joint","staged"):
        p=predict(full["theta"],x) if method=="joint" else staged_predict(staged,x,"Q_x_logN_logD")
        sse=float(np.sum((p-y)**2));n=len(y);k=9
        result={"method":method,"train_rmse":metrics(p,y)["rmse"],
                "AIC_descriptive":n*np.log(sse/n)+2*k,"BIC_descriptive":n*np.log(sse/n)+k*np.log(n)}
        for name in AXES:
            result[name+"_mean_fold_RMSE"]=float(np.mean([f[method]["rmse"] for f in comparison if f["axis"]==name]))
        summary.append(result)
    result={**metadata(),"schema_version":"cyj.b7_joint.v1","seed":SEED,
            "source_files":sources,"model":full,"wide_bounds_fit":wide,
            "parameter_bounds":dict(zip(NAMES,PARAM_BOUNDS)),"comparison":summary,"folds":comparison,"oof":oof,
            "information_criterion_caveat":"Gaussian iid working likelihood; staged not MLE; semi-synthetic grouped observations; descriptive only"}
    write_json(OUTPUT,result)
    with (OUTPUT.parent/"b7_joint_vs_staged.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    _,jac=value_jac(full["theta"],x)
    covariance=np.linalg.pinv(jac.T@jac)*(full["sse"]/(len(y)-8))
    sd=np.sqrt(np.diag(covariance));corr=covariance/np.outer(sd,sd)
    groups=[np.flatnonzero(np.all(x[:,:2]==nd,axis=1)) for nd in np.unique(x[:,:2],axis=0)]
    rng=np.random.default_rng(SEED);samples=[];failures=[]
    for b in range(bootstrap):
        ix=np.concatenate([groups[i] for i in rng.integers(0,len(groups),len(groups))])
        try:samples.append(fit_joint(x[ix],y[ix],starts=4,seed=SEED+b)["theta"])
        except ValueError as exc:failures.append({"draw":b,"error":str(exc)})
    identification={**metadata(),"model_hash":sha256(OUTPUT),"parameter_names":NAMES,
                    "jacobian_rank":int(np.linalg.matrix_rank(jac)),"jacobian_condition":float(np.linalg.cond(jac)),
                    "column_scaled_jacobian_condition":float(np.linalg.cond(jac/np.linalg.norm(jac,axis=0))),
                    "gauss_newton":(jac.T@jac).tolist(),"local_working_correlation":corr.tolist(),
                    "bootstrap_requested":bootstrap,"bootstrap_accepted":len(samples),"bootstrap_failures":failures,
                    "bootstrap_parameter_samples":samples,
                    "bootstrap_percentiles":np.quantile(samples,[.025,.5,.975],axis=0).tolist() if samples else None,
                    "interpretation":"Local numerical rank and grouped bootstrap describe conditional estimability, not causal or cross-source identification"}
    write_json(OUTPUT.parent/"b7_identifiability.json",identification)
    print(json.dumps({"comparison":summary,"parameters":full["theta"],"starts":full["successful_starts"],
                      "near_best":full["near_best_starts"],"bootstrap":len(samples),"model_sha256":sha256(OUTPUT)}))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--starts",type=int,default=12)
    parser.add_argument("--bootstrap",type=int,default=200);args=parser.parse_args();run(args.starts,args.bootstrap)
