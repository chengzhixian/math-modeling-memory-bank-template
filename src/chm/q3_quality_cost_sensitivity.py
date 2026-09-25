"""Quality-cost sensitivity diagnostics for Q3.

Cost-side only: no claim about performance benefit of Q and no formal optimum.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from scipy.optimize import brentq

CONTEXTS = (2048, 8192, 131072)
FAMILIES = ("exp", "power", "log")

def g(name, q):
    if name == "exp":
        return 1e7 * math.exp(6*q)
    if name == "power":
        return 5e9 * q**4
    if name == "log":
        return 2e9 * math.log(1+10*q)
    raise ValueError(name)

def gp(name, q):
    if name == "exp":
        return 6e7 * math.exp(6*q)
    if name == "power":
        return 2e10 * q**3
    if name == "log":
        return 2e10 / (1+10*q)
    raise ValueError(name)

def gpp_sign(name):
    return {"exp":"convex","power":"convex","log":"concave"}[name]

def delta_g(name, q, q0):
    if not (0 < q0 <= 1 and 0 < q <= 1):
        raise ValueError("Q and Q0 must be in (0,1]")
    return max(g(name,q)-g(name,q0),0.0)

def ratio_to_train(name,q,q0,N_B):
    return delta_g(name,q,q0)/(6e9*N_B)

def ratio_to_attn(name,q,q0,N_B,L_ctx):
    return delta_g(name,q,q0)/(2e5*N_B*L_ctx)

def equality_thresholds(name,q,q0):
    dg=delta_g(name,q,q0)
    return {
        "N_B_eq_train": dg/6e9,
        **{f"N_B_eq_attn_{L}": dg/(2e5*L) for L in CONTEXTS},
    }

def roots_between(a,b,q0):
    # roots of equal incremental cost above q0
    lo=q0+1e-8
    xs=[lo+(1-lo)*i/2000 for i in range(2001)]
    vals=[(g(a,x)-g(a,q0))-(g(b,x)-g(b,q0)) for x in xs]
    roots=[]
    for x1,x2,y1,y2 in zip(xs[:-1],xs[1:],vals[:-1],vals[1:]):
        if y1*y2 < 0:
            roots.append(brentq(lambda q:(g(a,q)-g(a,q0))-(g(b,q)-g(b,q0)),x1,x2))
    return roots

def build(q0=0.5, q_values=(0.6,0.8,1.0)):
    rows=[]
    for q in q_values:
        for family in FAMILIES:
            dg=delta_g(family,q,q0)
            rows.append({"Q0":q0,"Q":q,"family":family,"delta_g":dg,
                         **equality_thresholds(family,q,q0)})
    crossings={
        f"{a}_vs_{b}": roots_between(a,b,q0)
        for i,a in enumerate(FAMILIES) for b in FAMILIES[i+1:]
    }
    summary={
        "schema_version":"chm.q3.quality_cost.v1",
        "status":"diagnostic_only",
        "ready_for_Q3":False,
        "Q0_example":q0,
        "Q0_status":"explicit example only; not a fixed official baseline",
        "curvature":{f:gpp_sign(f) for f in FAMILIES},
        "incremental_cost_crossings":crossings,
        "identities":{
            "C_Q_over_C_train":"delta_g/(6e9*N_B)",
            "C_Q_over_C_attn":"delta_g/(2e5*N_B*L_ctx)",
            "Q0_left_derivative":"0 because max(delta_g,0)",
            "Q0_right_derivative":"1e9*D_B*g_prime(Q0)"
        }
    }
    return rows,summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--q0",type=float,default=0.5)
    p.add_argument("--csv",type=Path,default=Path("outputs/chm/q3_quality_cost_sensitivity_q0_0p5.csv"))
    p.add_argument("--json",type=Path,default=Path("outputs/chm/q3_quality_cost_crossings_q0_0p5.json"))
    args=p.parse_args()
    rows,summary=build(args.q0)
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    with args.csv.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    args.json.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))

if __name__=="__main__":
    main()
