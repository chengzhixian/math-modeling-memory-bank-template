"""Summarize Q1 conflict replication from already-validated output tables.

This script does not re-read LFS raw records and therefore does not perform new
bootstrap or significance testing.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EXT=ROOT/"outputs/chm/quality_conflict_extended_v0.csv"
NON=ROOT/"outputs/chm/quality_conflict_nonoverlap_v0.csv"

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def key(r):
    return r["quality_domain"],r["metric_a"],r["metric_b"]

def main():
    ext=read(EXT); non=read(NON)
    nm={key(r):r for r in non}
    joined=[]
    for r in ext:
        n=nm[key(r)]
        joined.append({
          "quality_domain":r["quality_domain"],
          "metric_a":r["metric_a"],"metric_b":r["metric_b"],
          "sample":float(r["mean_domain_spearman_sample"]),
          "extended":float(r["mean_domain_spearman_extended"]),
          "nonoverlap":float(n["mean_domain_spearman"])
        })
    summary={"schema_version":"chm.q1.conflict_replication.v1","domains":{}}
    triple_by_pair={}
    for domain in ("arxiv","github"):
        d=[r for r in joined if r["quality_domain"]==domain]
        sample_neg=[r for r in d if r["sample"]<0]
        triple=[r for r in d if r["sample"]<0 and r["extended"]<0 and r["nonoverlap"]<0]
        summary["domains"][domain]={
          "pairs":len(d),
          "sample_negative":len(sample_neg),
          "triple_negative":len(triple),
          "triple_negative_share_of_sample_negative":len(triple)/len(sample_neg),
          "sign_concordance_sample_extended":sum((r["sample"]<0)==(r["extended"]<0) for r in d)/len(d),
          "sign_concordance_sample_nonoverlap":sum((r["sample"]<0)==(r["nonoverlap"]<0) for r in d)/len(d)
        }
        for r in triple:
            triple_by_pair.setdefault((r["metric_a"],r["metric_b"]),[]).append(r)
    shared=[]
    for (a,b),rows in triple_by_pair.items():
        if {r["quality_domain"] for r in rows}=={"arxiv","github"}:
            shared.append({
              "metric_a":a,"metric_b":b,
              "min_abs_across_domains_scopes":min(abs(r[x]) for r in rows for x in ("sample","extended","nonoverlap")),
              **{f"{r['quality_domain']}_{x}":r[x] for r in rows for x in ("sample","extended","nonoverlap")}
            })
    shared.sort(key=lambda r:r["min_abs_across_domains_scopes"],reverse=True)
    summary["shared_triple_negative_pairs"]=len(shared)
    summary["interpretation"]="replication/effect-size evidence only; no bootstrap CI or FDR claim"
    (ROOT/"outputs/chm/quality_conflict_replication_summary.json").write_text(
      json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (ROOT/"outputs/chm/quality_conflict_shared_robust.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(shared[0]))
        w.writeheader();w.writerows(shared)
    print(json.dumps(summary,ensure_ascii=False))

if __name__=="__main__":
    main()
