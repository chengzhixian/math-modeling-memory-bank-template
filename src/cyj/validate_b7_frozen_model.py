"""Fixed-family B7 grouped CV; source was already used to propose the family."""
from __future__ import annotations

import hashlib
import json
import platform

import numpy as np

from audit_b_scaling_laws import ROOT, sha256
from b7_formal_model import AXES, BOUNDS, FAMILY, OUTPUT as MODEL_OUTPUT
from compare_b7_quality_interactions import base_exponents, design, gain, predict, score
from quality_scaling import source_data

OUTPUT = ROOT / "outputs/cyj/quality/b7_frozen_validation.json"
FAMILIES = (FAMILY, "constant_G")


def fit_fixed(x: np.ndarray, y: np.ndarray, family: str) -> dict:
    if family not in FAMILIES:
        raise ValueError("unregistered family")
    alpha, beta = base_exponents(x, y)
    matrix = design(x, alpha, beta, family)
    coefficients, _, rank, _ = np.linalg.lstsq(matrix, y, rcond=None)
    if rank != matrix.shape[1] or not np.all(np.isfinite(coefficients)) or np.any(coefficients[:3] <= 0):
        raise ValueError("rank, finiteness or base amplitude failure")
    n = np.array([BOUNDS[0][0], BOUNDS[0][1]] * 2)
    d = np.array([BOUNDS[1][0]] * 2 + [BOUNDS[1][1]] * 2)
    if np.min(gain(n, d, coefficients, family)) <= 0:
        raise ValueError("nonpositive quality gain in declared support")
    return {"family": family, "alpha": float(alpha), "beta": float(beta),
            "coefficients": list(map(float, coefficients)),
            "gain_range_full_rectangle": [float(np.min(gain(n, d, coefficients, family))),
                                          float(np.max(gain(n, d, coefficients, family)))]}


def run() -> dict:
    sources, x, y, rows = source_data()
    if len(y) != 450 or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("B7 data shape or finiteness changed")
    frozen = json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))
    if frozen["family"] != FAMILY or frozen["B7_sha256"] != sources["supplementary_NQ_experiment_expanded.csv"]["sha256"]:
        raise ValueError("frozen candidate identity mismatch")
    folds, oof = [], []
    for axis, name in enumerate(AXES):
        for level in np.unique(x[:, axis]):
            held = x[:, axis] == level
            row = {"axis": name, "held_level": float(level),
                   "train_count": int((~held).sum()), "test_count": int(held.sum()), "families": {}}
            for family in FAMILIES:
                model = fit_fixed(x[~held], y[~held], family)
                predictions = predict(model, x[held], family)
                residual = y[held] - predictions
                metrics = score(predictions, y[held])
                row["families"][family] = {"fit": model, "rmse": metrics["rmse"],
                    "mae": metrics["mae"], "bias_observed_minus_predicted": float(np.mean(residual)),
                    "max_abs_error": float(np.max(np.abs(residual)))}
                if family == FAMILY:
                    oof.extend({"axis": name, "held_level": float(level),
                                "source_line": rows[i]["source_line"],
                                "N_params_B": float(x[i, 0]), "D_tokens_B": float(x[i, 1]),
                                "Q_score": float(x[i, 2]), "observed": float(y[i]),
                                "predicted": float(predictions[j]), "residual_observed_minus_predicted": float(residual[j])}
                               for j, i in enumerate(np.flatnonzero(held)))
            folds.append(row)
    by_axis = {}
    for name in AXES:
        subset = [f for f in folds if f["axis"] == name]
        by_axis[name] = {}
        for family in FAMILIES:
            observations = [f["families"][family] for f in subset]
            residual = np.array([r["residual_observed_minus_predicted"] for r in oof if r["axis"] == name]) if family == FAMILY else None
            by_axis[name][family] = {
                "mean_fold_rmse": float(np.mean([v["rmse"] for v in observations])),
                "mean_fold_mae": float(np.mean([v["mae"] for v in observations])),
                "mean_fold_bias_observed_minus_predicted": float(np.mean([v["bias_observed_minus_predicted"] for v in observations]))}
            if residual is not None:
                by_axis[name][family].update({"pooled_oof_rmse": float(np.sqrt(np.mean(residual ** 2))),
                                              "pooled_oof_mae": float(np.mean(np.abs(residual))),
                                              "max_abs_error": float(np.max(np.abs(residual)))})
    comparison = {name: by_axis[name][FAMILY]["mean_fold_rmse"] < by_axis[name]["constant_G"]["mean_fold_rmse"] for name in AXES}
    if not all(comparison.values()) or len(oof) != 3 * len(y):
        raise ValueError("frozen model validation gate failed")
    result = {"schema_version": "cyj.b7_frozen_validation.v1", "model_family": FAMILY,
              "source_sha256": frozen["B7_sha256"], "frozen_model_sha256": sha256(MODEL_OUTPUT),
              "support": dict(zip(AXES, BOUNDS)),
              "validation_scope": "within_official_attachment_B7_semi_synthetic",
              "role_caveat": "All B7 was inspected before this family was proposed; this repeated fixed-family CV is not an untouched independent final test.",
              "fold_definition": "leave one observed N, D, or Q level out; refit the same frozen family on the other levels",
              "folds": folds, "axis_summary": by_axis, "primary_better_than_constant_G_all_axes": comparison,
              "oof_residuals": oof, "ready_for_Q3_candidate": False,
              "environment": {"python": platform.python_version(), "numpy": np.__version__},
              "code_sha256_utf8_lf": hashlib.sha256((ROOT / "src/cyj/validate_b7_frozen_model.py").read_bytes().replace(b"\r\n", b"\n")).hexdigest()}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps({"sha256": sha256(OUTPUT), "folds": len(result["folds"]),
                      "oof": len(result["oof_residuals"]), "axis_summary": result["axis_summary"]}))
