"""Observed-support and robust mixture diagnostics for Q3.

Uses the five-target CHM panel only. It never claims equivalence to B1 val_loss.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from q1_interface import Q1Interface

ROOT=Path(__file__).resolve().parents[2]
A4=ROOT/"data/raw/real_attachments/A_data_value/regmix_tables/train_mixture_1m.csv"
TARGETS=("pile_cc","wikipedia_en","arxiv","stackexchange","github")

def load_a4(q1):
    with A4.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    raw=[c for c in rows[0] if c!="index"]
    mapping={c:c.removeprefix("train_the_pile_") for c in raw}
    if set(mapping.values()) != set(q1.reference):
        raise ValueError("A4 domain names do not match Q1 interface domains")
    out=[]
    for row in rows:
        vals=np.array([float(row[c]) for c in raw])
        if np.any(vals<0) or not np.all(np.isfinite(vals)) or vals.sum()<=0:
            raise ValueError("invalid A4 mixture row")
        vals=vals/vals.sum()
        p={mapping[c]:float(vals[i]) for i,c in enumerate(raw)}
        out.append((row["index"],p))
    if len(out)!=512:
        raise ValueError("expected 512 A4 mixtures")
    return out

def effect(q1,p,target):
    row=q1.coefficients[target]
    return sum(float(row[d])*(p[d]-q1.reference[d]) for d in q1.reference)

def effective_domains(p):
    return math.exp(-sum(x*math.log(x) for x in p.values() if x>0))

def dominates(a,b):
    av=a["effects"]; bv=b["effects"]
    return all(av[t] <= bv[t]+1e-14 for t in TARGETS) and any(av[t] < bv[t]-1e-14 for t in TARGETS)

def build(root=ROOT):
    q1=Q1Interface(root)
    rec=[]
    for idx,p in load_a4(q1):
        effects={t:effect(q1,p,t) for t in TARGETS}
        rec.append({"index":idx,"p":p,"effects":effects})
    stats={}
    for t in TARGETS:
        a=np.array([r["effects"][t] for r in rec])
        stats[t]={"mean":float(a.mean()),"sd":float(a.std(ddof=1))}
        for r in rec:
            r.setdefault("z",{})[t]=(r["effects"][t]-stats[t]["mean"])/stats[t]["sd"]
    for t in TARGETS:
        order=sorted(rec,key=lambda r:r["effects"][t])
        rank={r["index"]:i/(len(order)-1) for i,r in enumerate(order)}
        for r in rec:r.setdefault("ranks",{})[t]=rank[r["index"]]
    for r in rec:
        r["mean_z"]=float(np.mean(list(r["z"].values())))
        r["max_z"]=max(r["z"].values())
        r["mean_rank"]=float(np.mean(list(r["ranks"].values())))
        r["all_improve"]=all(r["effects"][t]<0 for t in TARGETS)
        r["nonzero"]=sum(v>1e-12 for v in r["p"].values())
        r["effective_domains"]=effective_domains(r["p"])
        r["max_weight"]=max(r["p"].values())
    pareto=[]
    for r in rec:
        if not any(s is not r and dominates(s,r) for s in rec):
            pareto.append(r["index"])
    best_by_target={t:min(rec,key=lambda r:r["effects"][t])["index"] for t in TARGETS}
    return {
      "schema_version":"chm.q3.p_support.v1",
      "status":"A_side_scenario_only",
      "ready_for_Q3":False,
      "target_panel":TARGETS,
      "linear_convex_hull_equivalence":"min linear effect over conv(A4) equals minimum over observed A4 vertices/rows",
      "single_target_best_indices":best_by_target,
      "robust_best":{
        "standardized_mean":min(rec,key=lambda r:r["mean_z"])["index"],
        "standardized_minimax":min(rec,key=lambda r:r["max_z"])["index"],
        "mean_rank":min(rec,key=lambda r:r["mean_rank"])["index"],
      },
      "all_five_improve_indices":[r["index"] for r in rec if r["all_improve"]],
      "all_five_improve_fraction":sum(r["all_improve"] for r in rec)/len(rec),
      "pareto_front_count":len(pareto),
      "index_139_pareto":"139" in pareto,
      "target_stats":stats,
      "records":rec
    }

def compact_candidates(data):
    ids=set(data["single_target_best_indices"].values())
    ids.update(data["robust_best"].values())
    ids.update(data["all_five_improve_indices"])
    rows=[]
    for r in data["records"]:
        if r["index"] not in ids:continue
        criteria=[]
        for t,i in data["single_target_best_indices"].items():
            if r["index"]==i:criteria.append("best_"+t)
        for c,i in data["robust_best"].items():
            if r["index"]==i:criteria.append(c)
        if r["index"] in data["all_five_improve_indices"]:criteria.append("all_five_improve")
        top=sorted(r["p"].items(),key=lambda x:x[1],reverse=True)[:5]
        rows.append({
          "index":r["index"],"criteria":";".join(criteria),
          "nonzero_domains":r["nonzero"],"effective_domains":r["effective_domains"],
          "max_weight":r["max_weight"],"mean_z":r["mean_z"],"max_z":r["max_z"],"mean_rank":r["mean_rank"],
          **{f"m_{t}":r["effects"][t] for t in TARGETS},
          "top5":";".join(f"{k}:{v:.6g}" for k,v in top)
        })
    return rows

if __name__=="__main__":
    data=build()
    summary={k:v for k,v in data.items() if k!="records"}
    out=ROOT/"outputs/chm/q3_p_support_summary.json"
    out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rows=compact_candidates(data)
    csv_path=ROOT/"outputs/chm/q3_p_robust_candidates.csv"
    with csv_path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    print(json.dumps(summary,ensure_ascii=False))
