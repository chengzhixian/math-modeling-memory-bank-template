"""Descriptive within-(N,D) B7 quality slopes; no causal or external claim."""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

import numpy as np

from audit_b_scaling_laws import ROOT, sha256
from quality_scaling import source_data

FIT = ROOT / "outputs/cyj/quality/b7_quality_fit.json"
FIT_SHA = "e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025"
OUTPUT = ROOT / "outputs/cyj/diagnostics/b7_quality_interaction.json"


def linear_summary(x, y):
    matrix = np.column_stack((np.ones(len(y)), np.asarray(x, float)))
    beta = np.linalg.lstsq(matrix, y, rcond=None)[0]
    residual = np.asarray(y) - matrix @ beta
    tss = float(np.sum((y - np.mean(y)) ** 2))
    return {"intercept": float(beta[0]), "coefficients": list(map(float, beta[1:])),
            "r2": 1 - float(np.sum(residual ** 2)) / tss if tss > 0 else None,
            "residual_mean": float(np.mean(residual)),
            "residual_sd": float(np.std(residual, ddof=1)),
            "residual_max_abs": float(np.max(np.abs(residual)))}


def main():
    if sha256(FIT) != FIT_SHA:
        raise ValueError("pinned B7 fit changed")
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    if fit["selected_family"] != "linear_quality":
        raise ValueError("expected constant-G baseline")
    sources, x, y, rows = source_data()
    groups = defaultdict(list)
    for row in rows:
        groups[(row["N_params_B"], row["D_tokens_B"])].append(row)
    if len(groups) != 45 or len(rows) != 450 or any(len(v) != 10 for v in groups.values()):
        raise ValueError("unexpected B7 grid; review before diagnosis")
    baseline_slope = -fit["models"]["linear_quality"]["full_fit"]["parameters"]["G"]
    result_rows = []
    plot_rows = []
    for (n, d), group in sorted(groups.items()):
        group.sort(key=lambda r: r["Q_score"])
        q = np.array([r["Q_score"] for r in group], float)
        losses = np.array([r["val_loss"] for r in group], float)
        summary = linear_summary(q[:, None], losses)
        slope = summary["coefficients"][0]
        result_rows.append({"N_params_B": n, "D_tokens_B": d, "Q_levels": q.tolist(),
                            "source_lines": [r["source_line"] for r in group],
                            "slope": slope, "intercept": summary["intercept"],
                            "r2": summary["r2"],
                            "residual_mean": summary["residual_mean"],
                            "residual_sd": summary["residual_sd"],
                            "residual_max_abs": summary["residual_max_abs"],
                            "constant_G_slope": baseline_slope,
                            "slope_minus_constant_G": slope - baseline_slope})
        params = fit["models"]["linear_quality"]["full_fit"]["parameters"]
        for value, loss, line in zip(q, losses, [r["source_line"] for r in group]):
            predicted = (params["E"] + params["A"]*n**(-params["alpha"])
                         + params["B"]*d**(-params["beta"]) + params["G"]*(1-value))
            plot_rows.append({"N_params_B": n, "D_tokens_B": d, "Q_score": float(value),
                              "source_line": line, "current_model_residual": float(loss-predicted)})
    def by_axis(name):
        levels = sorted({r[name] for r in result_rows})
        return [{"level": v, "groups": sum(r[name] == v for r in result_rows),
                 "mean_slope": float(np.mean([r["slope"] for r in result_rows if r[name] == v]))}
                for v in levels]
    slopes = np.array([r["slope"] for r in result_rows])
    ln = np.log([r["N_params_B"] for r in result_rows])
    ld = np.log([r["D_tokens_B"] for r in result_rows])
    relationships = {"log_N": linear_summary(ln[:,None], slopes),
                     "log_D": linear_summary(ld[:,None], slopes),
                     "log_N_plus_log_D": linear_summary(np.column_stack((ln,ld)), slopes)}
    output = {"schema_version": "cyj.b7_quality_interaction.v1", "status": "descriptive_only",
              "data_role": "B7 semi-synthetic; B6 nested subset excluded; no independent validation or causal mechanism",
              "source_files": sources, "B7_fit_sha256": FIT_SHA,
              "code_sha256_utf8_lf": hashlib.sha256(__file_bytes()).hexdigest(),
              "method": "OLS of Loss on Q within each exact N,D group; second-stage OLS of 45 slopes on natural logs; no pooling of raw Q across N,D",
              "groups_count": len(result_rows), "rows_count": len(rows), "groups": result_rows,
              "by_N": by_axis("N_params_B"), "by_D": by_axis("D_tokens_B"),
              "slope_range": [float(slopes.min()),float(slopes.max())],
              "slope_relationships": relationships,
              "current_constant_G_slope": baseline_slope,
              "constant_G_slope_bias_mean": float(np.mean(slopes-baseline_slope)),
              "constant_G_slope_rmse": float(np.sqrt(np.mean((slopes-baseline_slope)**2))),
              "plot_data": plot_rows, "ready_for_Q3": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"output_sha256": sha256(OUTPUT), "groups": len(result_rows),
                      "slope_range": output["slope_range"], "slope_R2_logN_logD": relationships["log_N_plus_log_D"]["r2"]}))


def __file_bytes():
    return (ROOT / "src/cyj/diagnose_b7_quality_interaction.py").read_bytes().replace(b"\r\n", b"\n")


if __name__ == "__main__":
    main()
