"""Support and Loss-coordinate gate for B4/B5 versus B1; no pooled RMSE."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict

from audit_b_scaling_laws import ROOT, sha256

BASE = ROOT / "data/raw/real_attachments/B_scaling_laws"
FILES = {"B1":BASE/"pythia_training_log_existing.csv",
         "B4":BASE/"scaling_baseline.csv", "B5":BASE/"published_scaling_data.csv"}
EXPECTED = {"B1":"529a59644b0f57bf3a76037838b614bfedc35e58bb26b93052e34ffc63e454c2",
            "B4":"2272983ded93de35e05f9acbf95ebceedf43f283345e4be72b54fee94080391e",
            "B5":"dd858c5e48610e28589340d5db023d6abfb31df597506789ccdfc6a546731bbd"}
OUTPUT = ROOT / "outputs/cyj/diagnostics/b4_b5_comparability.json"


def read(name):
    path=FILES[name]
    if sha256(path)!=EXPECTED[name]:
        raise ValueError(f"{name} input hash mismatch")
    with path.open(encoding="utf-8-sig",newline="") as stream:
        rows=list(csv.DictReader(stream))
    for row in rows:
        for key in ("N_params_B","D_tokens_B","val_loss"):
            row[key]=float(row[key])
            if not math.isfinite(row[key]) or row[key]<=0:
                raise ValueError(f"invalid {name} {key}")
    return rows


def classify(rows, bounds):
    detail=[]
    counts=Counter()
    for index,row in enumerate(rows,2):
        n,d=row["N_params_B"],row["D_tokens_B"]
        n_out=not bounds["N_params_B"][0]<=n<=bounds["N_params_B"][1]
        d_out=not bounds["D_tokens_B"][0]<=d<=bounds["D_tokens_B"][1]
        label="both_outside" if n_out and d_out else "N_outside_only" if n_out else "D_outside_only" if d_out else "inside_rectangle"
        counts[label]+=1
        detail.append({"source_line":index,"family":row["family"],"source":row.get("source"),
                       "N_params_B":n,"D_tokens_B":d,"val_loss":row["val_loss"],
                       "support_class":label,"same_loss_coordinate_verified":False})
    return detail,dict(counts)


def main():
    b1,b4,b5=(read(k) for k in ("B1","B4","B5"))
    bounds={key:[min(r[key] for r in b1),max(r[key] for r in b1)] for key in ("N_params_B","D_tokens_B")}
    data={}
    for name,rows in (("B4",b4),("B5",b5)):
        detail,counts=classify(rows,bounds)
        by_family=Counter(r["family"] for r in rows)
        data[name]={"rows":len(rows),"support_counts":counts,"families":dict(by_family),
                    "source_strata":dict(Counter(r.get("source") for r in rows)) if name=="B5" else None,
                    "row_audit":detail,"same_loss_coordinate":"not_established","descriptive_only":True}
    terminal={n:max((r for r in b1 if r["N_params_B"]==n),key=lambda r:r["D_tokens_B"]) for n in sorted({r["N_params_B"] for r in b1})}
    pythia=[]
    for row in b4:
        if row["family"]!="Pythia":
            continue
        nearest=min(terminal,key=lambda n:abs(math.log(n/row["N_params_B"])))
        anchor=terminal[nearest]
        pythia.append({"B4_N":row["N_params_B"],"B4_D":row["D_tokens_B"],"B4_Loss":row["val_loss"],
                       "nearest_B1_N":nearest,"B1_terminal_D":anchor["D_tokens_B"],
                       "B1_terminal_Loss":anchor["val_loss"],
                       "B4_minus_B1_terminal_Loss":row["val_loss"]-anchor["val_loss"],
                       "warning":"nominal nearest-size comparison only; no checkpoint/evaluation identity"})
    output={"schema_version":"cyj.b4_b5_comparability.v1","status":"descriptive_only",
            "input_sha256":{name:EXPECTED[name] for name in FILES},
            "code_sha256_utf8_lf":hashlib.sha256((ROOT/"src/cyj/audit_b4_b5_comparability.py").read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
            "B1_support":bounds,"datasets":data,"B4_Pythia_nearest_terminal":pythia,
            "coordinate_gate":{"B1_tokenizer":None,"B4_tokenizer":None,"B5_tokenizer":None,
                               "evaluation_corpus_alignment":None,"loss_definition_alignment":None,
                               "log_base_alignment":None,"aggregation_alignment":None,
                               "same_loss_coordinate":"not_established","formal_external_RMSE_allowed":False},
            "claim":"support overlap is necessary but insufficient; same val_loss name does not establish comparability"}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"output_sha256":sha256(OUTPUT),
                      "support_counts":{k:v["support_counts"] for k,v in data.items()},
                      "B4_Pythia_rows":len(pythia)}))


if __name__=="__main__":
    main()
