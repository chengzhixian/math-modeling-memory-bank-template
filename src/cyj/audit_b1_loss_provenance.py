"""Audit B1 column relationships and provenance gaps without inventing its generator."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from audit_b_scaling_laws import ROOT, sha256

B1 = ROOT / "data/raw/real_attachments/B_scaling_laws/pythia_training_log_existing.csv"
B12 = ROOT / "data/raw/real_attachments/B_scaling_laws/pythia_checkpoint_index.csv"
SOURCE = ROOT / "data/raw/real_attachments/source_manifest.json"
FIT = ROOT / "outputs/cyj/classic/classic_fit.json"
OUTPUT = ROOT / "outputs/cyj/diagnostics/b1_loss_provenance.json"
EXPECTED = {B1: "529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2",
            FIT: "9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead"}


def stats(values):
    array = np.asarray(values,float)
    return {"count":len(array),"min":float(np.min(array)),"max":float(np.max(array)),
            "mean":float(np.mean(array)),"sd":float(np.std(array,ddof=1)) if len(array)>1 else 0.0,
            "rmse":float(np.sqrt(np.mean(array**2)))}


def main():
    for path,digest in EXPECTED.items():
        if sha256(path)!=digest:
            raise ValueError(f"pinned input changed: {path}")
    with B1.open(encoding="utf-8-sig",newline="") as stream:
        raw=list(csv.DictReader(stream))
    if len(raw)!=1176 or len({r["run_id"] for r in raw})!=len(raw):
        raise ValueError("B1 row count or run_id uniqueness changed")
    fit=json.loads(FIT.read_text(encoding="utf-8"))["full_fit"]["parameters"]
    def predicted(n,d):
        return fit["E"]+fit["A"]*n**(-fit["alpha"])+fit["B"]*d**(-fit["beta"])
    groups=defaultdict(list)
    digits=Counter()
    ppl_delta=[]
    ppl_round_match=0
    ppl_rounding_compatible=0
    d_step_delta=[]
    d_exact_batch_delta=[]
    cost_delta=[]
    for row in raw:
        vals={k:float(row[k]) for k in ("N_params_B","D_tokens_B","C_FLOPs_1e21","steps","batch_tokens_M","train_loss","val_loss","ppl")}
        if any(not math.isfinite(v) for v in vals.values()) or min(vals["N_params_B"],vals["D_tokens_B"],vals["val_loss"])<=0:
            raise ValueError("nonfinite or invalid B1 value")
        vals["run_id"]=row["run_id"]
        vals["residual"]=vals["val_loss"]-predicted(vals["N_params_B"],vals["D_tokens_B"])
        groups[vals["N_params_B"]].append(vals)
        decimal=row["val_loss"].partition(".")[2]
        digits[len(decimal)]+=1
        expected_ppl=math.exp(vals["val_loss"])
        ppl_delta.append(vals["ppl"]-expected_ppl)
        if round(expected_ppl,2)==vals["ppl"]:
            ppl_round_match+=1
        if max(math.exp(vals["val_loss"]-.00005),vals["ppl"]-.005) <= min(math.exp(vals["val_loss"]+.00005),vals["ppl"]+.005):
            ppl_rounding_compatible+=1
        d_step_delta.append(vals["D_tokens_B"]-vals["steps"]*vals["batch_tokens_M"]/1000)
        d_exact_batch_delta.append(vals["D_tokens_B"]-vals["steps"]*2.097152/1000)
        cost_delta.append(vals["C_FLOPs_1e21"]-6e-3*vals["N_params_B"]*vals["D_tokens_B"])
    if len(groups)!=8 or any(len(v)!=147 for v in groups.values()):
        raise ValueError("B1 group grid changed")
    with B12.open(encoding="utf-8-sig",newline="") as stream:
        checkpoints=list(csv.DictReader(stream))
    indexed_steps={int(r["step"]) for r in checkpoints}
    b1_steps={int(float(r["steps"])) for r in raw}
    summaries=[]
    all_adjacent=[]
    for n, group in sorted(groups.items()):
        group.sort(key=lambda r:(r["D_tokens_B"],r["steps"]))
        residual=np.array([r["residual"] for r in group])
        loss=np.array([r["val_loss"] for r in group])
        model=np.array([predicted(n,r["D_tokens_B"]) for r in group])
        steps=np.array([r["steps"] for r in group])
        if len(np.unique(steps))!=len(steps):
            raise ValueError("duplicate step within B1 size")
        adjacent=np.diff(loss)-np.diff(model)
        all_adjacent.extend(adjacent.tolist())
        summaries.append({"N_params_B":n,"rows":len(group),"D_range":[group[0]["D_tokens_B"],group[-1]["D_tokens_B"]],
                          "step_range":[int(steps[0]),int(steps[-1])],
                          "loss_monotone_decreasing":bool(np.all(np.diff(loss)<0)),
                          "residual":stats(residual),
                          "residual_lag1_correlation":float(np.corrcoef(residual[:-1],residual[1:])[0,1]),
                          "adjacent_change_minus_model_change":stats(adjacent)})
    source_rows=json.loads(SOURCE.read_text(encoding="utf-8"))
    source_entry=next(r for r in source_rows if r.get("file")=="B_scaling_laws/pythia_training_log_existing.csv")
    output={"schema_version":"cyj.b1_loss_provenance.v1","status":"source_partially_verified_loss_generation_unknown",
            "input_sha256":{p.relative_to(ROOT).as_posix():sha256(p) for p in (B1,B12,SOURCE,FIT)},
            "code_sha256_utf8_lf":hashlib.sha256((ROOT/"src/cyj/audit_b1_loss_provenance.py").read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
            "source_manifest_entry":source_entry,
            "row_count":len(raw),"N_groups":len(groups),"run_id_unique":True,
            "columns":list(raw[0]),"val_loss_decimal_digits":dict(digits),
            "ppl_minus_exp_val_loss":stats(ppl_delta),"ppl_equals_rounded_exp_val_loss_count":ppl_round_match,
            "ppl_compatible_with_four_decimal_loss_and_two_decimal_ppl":ppl_rounding_compatible,
            "D_minus_steps_times_batch_tokens_B":stats(d_step_delta),
            "D_minus_steps_times_2097152_tokens_B":stats(d_exact_batch_delta),
            "D_compatible_with_three_decimal_rounding_of_2097152_batch":sum(abs(v)<=.0005 for v in d_exact_batch_delta),
            "C_reported_minus_6ND_1e21":stats(cost_delta),
            "checkpoint_index_rows":len(checkpoints),
            "B1_unique_steps":len(b1_steps),"B1_steps_in_checkpoint_index":len(b1_steps&indexed_steps),
            "group_summaries":summaries,"all_adjacent_change_minus_model_change":stats(all_adjacent),
            "known_gaps":{"B1_val_loss_generation_formula":None,"interpolation_or_smoothing":None,
                          "evaluation_corpus":None,"tokenizer_for_B1_loss":None,
                          "loss_log_base":None,"aggregation_definition":None,
                          "raw_checkpoint_eval_trace":None},
            "claim":"near-exact within-source reconstruction only; not verified external prediction"}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"output_sha256":sha256(OUTPUT),"B1_rows":len(raw),"groups":len(groups),
                      "ppl_rounded_match":ppl_round_match,"checkpoint_step_overlap":len(b1_steps&indexed_steps),
                      "adjacent_change_rmse":output["all_adjacent_change_minus_model_change"]["rmse"]}))


if __name__=="__main__":
    main()
