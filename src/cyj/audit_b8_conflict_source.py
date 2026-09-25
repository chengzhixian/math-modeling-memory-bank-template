"""B7/B8 coordinate, direction, and 0.5 mass audit; mechanism remains unknown."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

import numpy as np

from audit_b_scaling_laws import ROOT, sha256
from diagnose_b_quality import FILES, DEFAULT_DATA_ROOT, AXES, coordinate_map, read_data, trends

OUTPUT=ROOT/"outputs/cyj/diagnostics/b8_conflict_source.json"
EXPECTED={"B7":"880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a",
          "B8":"bda0d449f75c73bbd04141e5cffbf4bea7002073e34b7fa95a638570fa095ffe"}


def main():
    for name,digest in EXPECTED.items():
        if sha256(DEFAULT_DATA_ROOT/FILES[name])!=digest:
            raise ValueError(f"{name} source changed")
    b7=read_data(DEFAULT_DATA_ROOT/FILES["B7"])
    b8=read_data(DEFAULT_DATA_ROOT/FILES["B8"])
    by_type={name:[r for r in b8 if r["data_type"]==name] for name in ("calibrated","extrapolated")}
    if sum(map(len,by_type.values()))!=len(b8):
        raise ValueError("unexpected B8 data_type")
    seven,eight=coordinate_map(b7),coordinate_map(b8)
    common=sorted(seven.keys()&eight.keys())
    difference=np.array([eight[k]["val_loss"]-seven[k]["val_loss"] for k in common])
    overlap_by_type=Counter(eight[k]["data_type"] for k in common)
    summary={}
    for name,rows in by_type.items():
        floors=[r for r in rows if r["val_loss"]==.5]
        summary[name]={"rows":len(rows),"floor_0_5_count":len(floors),
                       "floor_0_5_fraction":len(floors)/len(rows),
                       "floor_by_Q":dict(sorted(Counter(str(r["Q_score"]) for r in floors).items())),
                       "floor_by_N":dict(sorted(Counter(str(r["N_params_B"]) for r in floors).items())),
                       "Q_levels":sorted({r["Q_score"] for r in rows}),
                       "Q_endpoint_directions":trends(rows,"Q_score")["endpoint_directions"],
                       "coordinate_count":len(coordinate_map(rows))}
    output={"schema_version":"cyj.b8_conflict_source.v1","status":"unresolved_keep_isolated",
            "source_sha256":EXPECTED,
            "code_sha256_utf8_lf":hashlib.sha256((ROOT/"src/cyj/audit_b8_conflict_source.py").read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
            "B7":{"rows":len(b7),"Q_endpoint_directions":trends(b7,"Q_score")["endpoint_directions"]},
            "B8":summary,"shared_B7_B8_coordinates":len(common),
            "shared_by_B8_type":dict(overlap_by_type),
            "shared_all_different_loss":bool(np.all(difference!=0)),
            "B8_minus_B7_loss":{"min":float(difference.min()),"max":float(difference.max()),
                                "mean":float(difference.mean()),
                                "positive":int(np.sum(difference>0)),"negative":int(np.sum(difference<0))},
            "origin_gaps":{"Q_score_semantic_identity":None,"B8_generation_formula":None,
                           "floor_0_5_mechanism":None,"calibrated_label_definition":None,
                           "extrapolated_label_definition":None,"same_loss_coordinate":None},
            "decision":"unresolved_keep_isolated; no Q reversal or B7/B8 pooling"}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"output_sha256":sha256(OUTPUT),"shared":len(common),
                      "floor_counts":{k:v["floor_0_5_count"] for k,v in summary.items()},
                      "status":output["status"]}))


if __name__=="__main__":
    main()
