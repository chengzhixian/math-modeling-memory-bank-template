"""Validate whether the Q1 mixture surrogate is useful for Q3 candidate selection."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path

PRIMARY_PANEL = ("pile_cc", "wikipedia_en", "arxiv", "stackexchange", "github")
COEF = Path("outputs/chm/local_recheck_v1/mixture_effect_ridge_v0.csv")
REF = Path("outputs/chm/local_recheck_v1/mixture_reference_v0.csv")
A4 = Path("data/raw/real_attachments/A_data_value/regmix_tables/train_mixture_1m.csv")
SETS = (
    ("1M", Path("data/raw/real_attachments/A_data_value/regmix_tables/test_mixture_1m.csv"),
     Path("data/raw/real_attachments/A_data_value/regmix_tables/test_pile_loss_1m.csv")),
    ("60M", Path("data/raw/real_attachments/A_data_value/regmix_tables/test_mixture_60m.csv"),
     Path("data/raw/real_attachments/A_data_value/regmix_tables/test_pile_loss_60m.csv")),
    ("1B", Path("data/raw/real_attachments/A_data_value/regmix_tables/test_mixture_1B.csv"),
     Path("data/raw/real_attachments/A_data_value/regmix_tables/test_pile_loss_1B.csv")),
)

def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def normalize_mix(row, domains):
    vals = [float(row[f"train_the_pile_{d}"]) for d in domains]
    total = sum(vals)
    if total <= 0 or any(v < 0 for v in vals):
        raise ValueError("invalid mixture")
    return {d: v/total for d, v in zip(domains, vals)}

def effect(p, coef, ref, domains):
    return sum(float(coef[d]) * (p[d]-ref[d]) for d in domains)

def training_candidates(root):
    rr=rows(root/REF); domains=[r["mixture_domain"] for r in rr]
    pref={r["mixture_domain"]:float(r["p_ref"]) for r in rr}
    out=[]
    for coef in rows(root/COEF):
        scored=[]
        for r in rows(root/A4):
            p=normalize_mix(r,domains)
            scored.append((effect(p,coef,pref,domains),r["index"],p))
        scored.sort(key=lambda x:x[0]); best,second=scored[:2]
        top_domain,top_share=max(best[2].items(),key=lambda kv:kv[1])
        out.append({"target":coef["target"],"in_primary_panel":coef["target"] in PRIMARY_PANEL,
                    "mixture_id":best[1],"predicted_delta_1m":best[0],
                    "max_component":top_domain,"max_share":top_share,
                    "active_domains":sum(v>1e-12 for v in best[2].values()),
                    "second_best_gap":second[0]-best[0]})
    return out

def heldout_validation(root):
    rr=rows(root/REF); domains=[r["mixture_domain"] for r in rr]
    pref={r["mixture_domain"]:float(r["p_ref"]) for r in rr}
    out=[]
    for scale,mix_path,loss_path in SETS:
        mixes=rows(root/mix_path); loss_by_id={r["index"]:r for r in rows(root/loss_path)}
        for coef in rows(root/COEF):
            target=coef["target"]; col=f"metric/the_pile_{target}_val_loss"; scored=[]
            for r in mixes:
                p=normalize_mix(r,domains)
                scored.append({"id":r["index"],"pred":effect(p,coef,pref,domains),
                               "actual":float(loss_by_id[r["index"]][col])})
            chosen=min(scored,key=lambda x:x["pred"]); actual=sorted(scored,key=lambda x:x["actual"])
            rank=next(i for i,x in enumerate(actual,1) if x["id"]==chosen["id"]); best=actual[0]
            regret=chosen["actual"]-best["actual"]
            out.append({"scale":scale,"target":target,"in_primary_panel":target in PRIMARY_PANEL,
                        "n_candidates":len(scored),"chosen_mixture_id":chosen["id"],
                        "predicted_effect":chosen["pred"],"chosen_actual_loss":chosen["actual"],
                        "actual_rank":rank,"regret":regret,"relative_regret":regret/best["actual"],
                        "top10pct":rank<=math.ceil(.1*len(scored)),
                        "actual_best_id":best["id"],"actual_best_loss":best["actual"]})
    return out

def _write_csv(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0])); w.writeheader(); w.writerows(data)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path("."))
    ap.add_argument("--output-dir",type=Path,default=Path("outputs/chm/q3_p_validation_v1"))
    a=ap.parse_args(); train=training_candidates(a.root); held=heldout_validation(a.root)
    _write_csv(a.output_dir/"training_supported_candidates.csv",train)
    _write_csv(a.output_dir/"heldout_selection_validation.csv",held)
    panel=[r for r in held if r["in_primary_panel"]]
    def s(x):
        return {"n":len(x),"exact_best":sum(r["actual_rank"]==1 for r in x),
                "top10pct":sum(r["top10pct"] for r in x),
                "max_rank":max(r["actual_rank"] for r in x),
                "max_relative_regret":max(r["relative_regret"] for r in x)}
    shares=sorted(r["max_share"] for r in train if r["in_primary_panel"])
    manifest={"schema_version":"chm.q3.p_selection_validation.v1",
              "status":"A-side optimization diagnostic only","ready_for_Q3":False,
              "primary_panel":list(PRIMARY_PANEL),
              "summary":{"all_targets":s(held),"primary_panel":s(panel),
                         "by_scale_all":{z:s([r for r in held if r["scale"]==z]) for z,_,_ in SETS},
                         "by_scale_primary_panel":{z:s([r for r in panel if r["scale"]==z]) for z,_,_ in SETS}},
              "training_candidate_extremeness":{"panel_max_share_median":shares[len(shares)//2],
                                                "panel_count_max_share_gt_0_9":sum(x>0.9 for x in shares),
                                                "panel_count_max_share_gt_0_7":sum(x>0.7 for x in shares)},
              "identifiability":"fixed-target linear p ranking is invariant to positive lambda and scale factor",
              "limitations":["A-target loss is not B1 val_loss",
                             "training-supported optimum can be optimistic",
                             "1B selection reliability is target-dependent",
                             "no continuous simplex optimum is released"]}
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
