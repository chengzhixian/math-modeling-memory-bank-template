"""Quantitatively compare frozen B1 curve shapes with B3 interpolation and B2 stress."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

from chm_q1_v2_consumer import ROOT
from fit_b7_quality_extension_from_b1 import b1_parameters, b1_value

BASE = ROOT / "data/raw/real_attachments/B_scaling_laws"
SHAPES = ROOT / "outputs/cyj/diagnostics/b2_b3_shapes.json"
OUT = ROOT / "outputs/cyj/q2_v8"


def read(path: Path, digest: str):
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"B2/B3 input identity mismatch: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def normalized(y):
    y = np.asarray(y, float)
    span = y[0]-y[-1]
    if not np.isfinite(y).all() or span <= 0:
        raise ValueError("trajectory has no positive start-to-end span")
    return (y-y[-1])/span


def score(rows, p, source, curve_id):
    ordered = sorted(rows, key=lambda r: (float(r["D_tokens_B"]), float(r.get("step", r.get("steps", 0)))))
    n = float(ordered[0]["N_params_B"])
    if any(float(row["N_params_B"]) != n for row in ordered):
        raise ValueError("trajectory mixes N")
    d = np.array([float(row["D_tokens_B"]) for row in ordered])
    observed = np.array([float(row["val_loss"]) for row in ordered])
    model = b1_value(p, np.full(len(d), n), d)
    if np.any(d <= 0) or not np.isfinite(model).all():
        raise ValueError("trajectory model evaluation invalid")
    observed_norm, model_norm = normalized(observed), normalized(model)
    adjacent = np.diff(d) > 0
    observed_slopes, model_slopes = np.diff(observed)[adjacent], np.diff(model)[adjacent]
    valid_slopes = observed_slopes != 0
    i, j = np.triu_indices(len(d), k=1)
    comparable = (d[i] < d[j]) & (observed[i] != observed[j]) & (model[i] != model[j])
    concordance = float(np.mean(np.sign(observed[i[comparable]]-observed[j[comparable]]) ==
                                np.sign(model[i[comparable]]-model[j[comparable]])))
    inside = (n >= .070542) & (n <= 11.965825) & (d >= .134) & (d <= 299.893)
    return {"source": source, "curve_id": curve_id, "N_params_B": n, "rows": len(d),
            "D_min_B": float(d.min()), "D_max_B": float(d.max()),
            "B1_support_fraction": float(np.mean(inside)),
            "Spearman_r": float(spearmanr(observed_norm, model_norm).statistic),
            "Pearson_r": float(pearsonr(observed_norm, model_norm).statistic),
            "normalized_RMSE": float(np.sqrt(np.mean((observed_norm-model_norm)**2))),
            "slope_sign_accuracy": float(np.mean(np.sign(observed_slopes[valid_slopes]) ==
                                                   np.sign(model_slopes[valid_slopes]))),
            "slope_pairs_scored": int(valid_slopes.sum()),
            "pairwise_order_concordance": concordance,
            "pairwise_pairs_scored": int(comparable.sum()),
            "role": "interpolation_consistency_not_independent" if source == "B3" else
                    "semi_synthetic_shape_stress_with_B1_extrapolation"}


def main():
    p = b1_parameters()
    prior = json.loads(SHAPES.read_text(encoding="utf-8"))
    if prior["status"] != "shape_diagnostic_only_not_independent_validation":
        raise ValueError("B2/B3 source role changed")
    identity = prior["provenance"]["source_files"]
    results = []
    for curve in prior["b3"]["curves"]:
        name = "training_trajectories/"+curve["file"]
        results.append(score(read(BASE/name, identity[name]["sha256"]), p, "B3", curve["file"]))
    b2_name = "cerebras_training_log.csv"
    b2_rows = read(BASE/b2_name, identity[b2_name]["sha256"])
    for n in sorted({float(row["N_params_B"]) for row in b2_rows}):
        results.append(score([row for row in b2_rows if float(row["N_params_B"]) == n],
                             p, "B2", f"Cerebras_N={n:g}"))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/"b2_b3_model_validation.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(results)
    summary = {source: {"trajectories": sum(row["source"] == source for row in results),
                        "mean_normalized_RMSE": float(np.mean([row["normalized_RMSE"] for row in results
                                                               if row["source"] == source])),
                        "median_Spearman_r": float(np.median([row["Spearman_r"] for row in results
                                                              if row["source"] == source])),
                        "overall_pairwise_concordance": float(sum(row["pairwise_order_concordance"]*
                                                                 row["pairwise_pairs_scored"] for row in results
                                                                 if row["source"] == source) /
                                                             sum(row["pairwise_pairs_scored"] for row in results
                                                                 if row["source"] == source))}
               for source in ("B3", "B2")}
    payload = {"schema_version": "cyj.b2_b3_model_validation.v1", "summary": summary,
               "input_sha256": {k: v["sha256"] for k, v in identity.items()},
               "B1_fit_sha256": hashlib.sha256((ROOT/"outputs/cyj/classic/classic_fit.json").read_bytes()).hexdigest(),
               "interpretation": {"B3": "quantitative interpolation trajectory consistency; derived from B1-style Pythia curves, not independent experiment",
                                  "B2": "semi-synthetic different-family shape stress; many D points outside B1 support and Loss coordinates not independently aligned"},
               "absolute_cross_source_RMSE_claim": None}
    (OUT/"b2_b3_validation_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
