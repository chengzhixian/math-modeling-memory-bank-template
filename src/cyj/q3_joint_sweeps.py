"""Conditional Q3 diagnostics using CHM's pinned optimizer and CYJ joint B7 fit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import itertools
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from audit_b_scaling_laws import ROOT,sha256
from fit_b7_joint_nonlinear import OUTPUT as MODEL_OUTPUT,metadata,predict,write_json
from quality_substitution import derivatives

CHM_COMMIT="92e0592000cba58fca355a881dc59caadbd446b2"
MODULES=("q3_generic_solver.py","q3_quality_cost_geometry.py","q3_nd_baseline.py")
BUDGETS=(1e19,3e19,1e20,3e20,1e21,3e21,1e22,3e22,1e23,3e23,1e24)
CONTEXTS=(2048,4096,8192,16384,24576,30000,32768,49152,65536,131072)
FAMILIES=("exponential","power","logarithmic")
Q0=.5
OUTPUT=ROOT/"outputs/cyj/q3/q3_budget_sweep.csv"


def load_chm(directory):
    hashes={}
    for name in MODULES:
        blob=subprocess.check_output(["git","show",f"{CHM_COMMIT}:src/chm/{name}"],cwd=ROOT)
        (directory/name).write_bytes(blob);hashes[name]=hashlib.sha256(blob).hexdigest()
    sys.path.insert(0,str(directory))
    return importlib.import_module("q3_generic_solver"),hashes


def save_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)


def run(starts=20,transition_points=30):
    modeldata=json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))
    t=modeldata["model"]["theta"]
    identification=json.loads((ROOT/"outputs/cyj/quality/b7_identifiability.json").read_text())
    samples=np.array(identification["bootstrap_parameter_samples"])
    nested=list(csv.DictReader((ROOT/"outputs/cyj/quality/b7_nested_cv_predictions.csv").open(encoding="utf-8",newline="")))
    residuals=np.array([float(r["residual"]) for r in nested if r["axis"]=="N_params_B"])
    rng=np.random.default_rng(20260925)
    selected_residual=residuals[rng.integers(0,len(residuals),len(samples))]
    with tempfile.TemporaryDirectory(prefix="cyj_q3_joint_") as temp:
        solver,hashes=load_chm(Path(temp))
        class JointModel:
            support=solver.Support((.07,11.97),(10.,600.),(.1,1.))
            def value_grad(self,n,d,q):
                values=(n,d,q);bounds=(self.support.N,self.support.D,self.support.Q)
                adjusted=[]
                for v,(lo,hi) in zip(values,bounds):
                    if v<lo-1e-12*hi or v>hi+1e-12*hi:raise ValueError("solver outside B7 support")
                    adjusted.append(min(hi,max(lo,v)))
                L,g=derivatives(t,*adjusted)
                return L,tuple(map(float,g))
        model=JointModel();cache={}
        def solve(budget,context,family):
            key=(float(budget),int(context),family)
            if key in cache:return cache[key]
            minimum=solver.cost_and_grad(.07,10.,Q0,Q0,context,family)[0]
            row={"budget_FLOPs":float(budget),"context_tokens":context,"quality_family":family,"Q0":Q0,
                 "minimum_supported_cost_FLOPs":minimum,"scientific_status":"conditional_B7_semi_synthetic",
                 "ready_for_Q3":False,"N_params_B":None,"D_tokens_B":None,"Q_score":None,
                 "conditional_loss":None,"cost_FLOPs":None,"budget_utilization":None,
                 "interval_95_lower":None,"interval_95_upper":None,"kkt_relative_violation":None,
                 "kkt_check_pass":None,"active_set":None,"budget_active":None,
                 "N_lower_active":None,"N_upper_active":None,"D_lower_active":None,"D_upper_active":None,
                 "Q_lower_active":None,"Q_upper_active":None,"support_saturated":None,"regime":None,
                 "converged_starts":None,"failure":None}
            if minimum>budget*(1+1e-12):
                row.update(status="infeasible_by_supported_domain",regime="infeasible")
                cache[key]=row;return row
            try:
                sol,trials=solver.solve_generic(model,budget=budget,context_tokens=context,Q0=Q0,family=family,starts=starts)
            except (ValueError,RuntimeError) as exc:
                row.update(status="solver_failure",failure=str(exc),regime="unresolved")
                cache[key]=row;return row
            n,d,q=sol["N_params_B"],sol["D_tokens_B"],sol["Q"]
            # CHM transforms log bounds back with exp; clamp only sub-ulp boundary drift.
            x=np.array([[min(11.97,max(.07,n)),min(600.,max(10.,d)),min(1.,max(.1,q))]])
            means=np.array([predict(s,x)[0] for s in samples]);draws=means+selected_residual
            active=set(sol["active_set"])
            near=lambda v,b: abs(v-b)<=1e-6*max(abs(b),1e-12)
            flags={"N_lower_active":near(n,.07),"N_upper_active":near(n,11.97),
                   "D_lower_active":near(d,10.),"D_upper_active":near(d,600.),
                   "Q_lower_active":near(q,Q0),"Q_upper_active":near(q,1.)}
            budget_active=sol["budget_utilization"]>=1-1e-6
            saturated=flags["N_upper_active"] and flags["D_upper_active"] and flags["Q_upper_active"]
            regime=("support_limited" if saturated and not budget_active else
                    "budget_limited_with_bounds" if budget_active and any(flags.values()) else
                    "budget_limited_interior" if budget_active else "unresolved_slack")
            row.update(status="converged_feasible",N_params_B=n,D_tokens_B=d,Q_score=q,
                       conditional_loss=sol["loss"],cost_FLOPs=sol["cost_FLOPs"],
                       budget_utilization=sol["budget_utilization"],
                       interval_95_lower=float(np.quantile(draws,.025)),
                       interval_95_upper=float(np.quantile(draws,.975)),
                       kkt_relative_violation=sol["kkt_relative_violation"],
                       kkt_check_pass=sol["kkt_check_pass"],active_set=";".join(sol["active_set"]),
                       budget_active=budget_active,**flags,support_saturated=saturated,regime=regime,
                       converged_starts=sum(r["success"] and r["feasible"] for r in trials))
            cache[key]=row;return row
        rows=[]
        for context,family in itertools.product(CONTEXTS,FAMILIES):
            for budget in BUDGETS:rows.append(solve(budget,context,family))
            print(f"grid {context} {family}",flush=True)
        save_csv(OUTPUT,rows)
        save_csv(OUTPUT.parent/"q3_context_sweep.csv",[r for r in rows if r["budget_FLOPs"] in (1e20,1e22,1e24)])
        save_csv(OUTPUT.parent/"q3_regime_map.csv",rows)
        transitions=[]
        for context,family in itertools.product(CONTEXTS,FAMILIES):
            minimum=solver.cost_and_grad(.07,10.,Q0,Q0,context,family)[0]
            grid=np.geomspace(minimum*1.001,1e24,transition_points)
            previous=None
            for budget in grid:
                current=solve(float(budget),context,family)
                if previous is not None and previous["status"]==current["status"]=="converged_feasible":
                    for flag in ("Q_lower_active","Q_upper_active","D_lower_active","N_lower_active","N_upper_active","D_upper_active","support_saturated"):
                        if previous[flag]!=current[flag]:
                            lo,hi=previous["budget_FLOPs"],current["budget_FLOPs"]
                            # Six log-bisection steps give a reproducible bracket, not an exact physical threshold.
                            for _ in range(6):
                                mid=math.sqrt(lo*hi);sample=solve(mid,context,family)
                                if sample["status"]!="converged_feasible":break
                                if sample[flag]==previous[flag]:lo=mid
                                else:hi=mid
                            transitions.append({"context_tokens":context,"quality_family":family,"event":flag,
                                                "from":previous[flag],"to":current[flag],
                                                "budget_bracket_low":lo,"budget_bracket_high":hi,
                                                "resolution_ratio":hi/lo,
                                                "interpretation":"numerical active-set bracket conditional on model and solver"})
                previous=current
        write_json(OUTPUT.parent/"q3_transition_points.json",{**metadata(),"model_hash":sha256(MODEL_OUTPUT),
            "CHM_commit":CHM_COMMIT,"CHM_module_sha256":hashes,"Q0_scenario":Q0,"scan_points":transition_points,
            "scan_max_budget":1e24,"transitions":transitions,
            "limitation":"Numerical active flags may change without a structural phase transition; bracket depends on tolerance and SLSQP"})
    return rows,transitions,hashes


def plots(rows,transitions):
    figdir=ROOT/"figures/cyj";figdir.mkdir(parents=True,exist_ok=True)
    for field,suffix,ylabel in (("N_params_B","N","N (billion parameters)"),("D_tokens_B","D","D (billion tokens)"),
                               ("Q_score","Q","B-native Q"),("conditional_loss","loss","Conditional B7 Loss")):
        fig,ax=plt.subplots(figsize=(6,4))
        for fam in FAMILIES:
            subset=[r for r in rows if r["context_tokens"]==30000 and r["quality_family"]==fam and r["status"]=="converged_feasible"]
            ax.plot([r["budget_FLOPs"] for r in subset],[r[field] for r in subset],"o-",label=fam)
        ax.set(xscale="log",xlabel="Budget FLOPs",ylabel=ylabel,title="Joint B7 conditional diagnosis; context=30000")
        ax.legend();fig.tight_layout();fig.savefig(figdir/f"q3_budget_vs_{suffix}.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4))
    for fam in FAMILIES:
        subset=[r for r in rows if r["budget_FLOPs"]==1e22 and r["quality_family"]==fam and r["status"]=="converged_feasible"]
        ax.plot([r["context_tokens"] for r in subset],[r["Q_score"] for r in subset],"o-",label=fam)
    ax.axvline(30000,color="gray",linestyle=":",label="attention=train cost")
    ax.set(xscale="log",xlabel="Context tokens",ylabel="B-native Q",title="Conditional context sensitivity; budget=1e22")
    ax.legend();fig.tight_layout();fig.savefig(figdir/"q3_context_regime_transition.png",dpi=180);plt.close(fig)
    codes={"infeasible":0,"budget_limited_with_bounds":1,"budget_limited_interior":2,"support_limited":3,"unresolved_slack":4,"unresolved":5}
    grid=np.full((len(CONTEXTS),len(BUDGETS)),np.nan)
    for i,ctx in enumerate(CONTEXTS):
        for j,budget in enumerate(BUDGETS):
            matches=[r for r in rows if r["context_tokens"]==ctx and r["budget_FLOPs"]==budget and r["quality_family"]=="exponential"]
            grid[i,j]=codes[matches[0]["regime"]]
    fig,ax=plt.subplots(figsize=(8,4));im=ax.imshow(grid,aspect="auto",vmin=0,vmax=5,cmap="tab10")
    ax.set_xticks(range(len(BUDGETS)),[f"{v:.0e}" for v in BUDGETS],rotation=45)
    ax.set_yticks(range(len(CONTEXTS)),CONTEXTS);ax.set(xlabel="Budget FLOPs",ylabel="Context tokens",title="Exponential cost: conditional regime map")
    fig.colorbar(im,ax=ax,ticks=list(codes.values()),label="0 infeasible, 1 budget+bound, 2 budget interior, 3 support, 4/5 unresolved")
    fig.tight_layout();fig.savefig(figdir/"q3_regime_map.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4))
    for event in ("Q_lower_active","Q_upper_active","support_saturated"):
        tr=[r for r in transitions if r["quality_family"]=="exponential" and r["event"]==event]
        ax.scatter([r["context_tokens"] for r in tr],[math.sqrt(r["budget_bracket_low"]*r["budget_bracket_high"]) for r in tr],label=event)
    ax.set(xscale="log",yscale="log",xlabel="Context tokens",ylabel="Budget FLOPs (bracket midpoint)",title="Exponential cost: numerical active transitions")
    ax.legend();fig.tight_layout();fig.savefig(figdir/"q3_transition_diagram.png",dpi=180);plt.close(fig)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--starts",type=int,default=20)
    parser.add_argument("--transition-points",type=int,default=30)
    args=parser.parse_args();rows,transitions,hashes=run(args.starts,args.transition_points);plots(rows,transitions)
    status={x:sum(r["status"]==x for r in rows) for x in sorted({r["status"] for r in rows})}
    write_json(OUTPUT.parent/"q3_sweep_manifest.json",{**metadata(),"model_hash":sha256(MODEL_OUTPUT),
               "CHM_commit":CHM_COMMIT,"CHM_module_sha256":hashes,"budgets":BUDGETS,"contexts":CONTEXTS,
               "quality_families":FAMILIES,"starts":args.starts,"status_counts":status,
               "budget_sweep_sha256":sha256(OUTPUT),"context_sweep_sha256":sha256(OUTPUT.parent/"q3_context_sweep.csv"),
               "regime_map_sha256":sha256(OUTPUT.parent/"q3_regime_map.csv"),
               "transitions_sha256":sha256(OUTPUT.parent/"q3_transition_points.json"),
               "interval_scope":"B7 conditional bootstrap plus leave-N nested OOF empirical residual; coverage not directly calibrated for this construction",
               "Q0_scenario":Q0,"context_provenance":"2048/8192/131072 are prior C7 scenarios; extra contexts are CYJ external sensitivity grid",
               "ready_for_Q3":False})
    print(json.dumps({"cases":len(rows),"statuses":status,"transition_brackets":len(transitions)}))
