"""Fit B7's quality increment while keeping the independently fitted B1 N-D law fixed."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from chm_q1_v2_consumer import ROOT
from quality_scaling import source_data

OUT = ROOT / "outputs/Q2"
B1_FILE = ROOT / "outputs/Q2/classic_fit.json"
B7_FILE = ROOT / "outputs/Q2/evidence/b7_joint_fit.json"
B7_NESTED = ROOT / "outputs/Q2/evidence/b7_nested_cv_summary.json"
B1_SHA = "9b0e381fbc0ea84bb37d63ccb273733f3a03a0c2a834e8ef52cdb75c45bc6ead"
B7_SOURCE_SHA = "880fd265ca3e1d9bc93b4559af7ed7c18f89040634266c50bae03d88486e0f3a"
RIDGES = (0.0, 0.001, 0.01)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def b1_parameters() -> dict[str, float]:
    if sha(B1_FILE) != B1_SHA:
        raise ValueError("B1 classic fit identity changed")
    item = json.loads(B1_FILE.read_text(encoding="utf-8"))
    if item["data_scope"]["rows"] != 1176 or not item["full_fit"]["converged"]:
        raise ValueError("B1 classic fit scope changed")
    return {key: float(item["full_fit"]["parameters"][key])
            for key in ("E", "A", "B", "alpha", "beta")}


def b1_value(p: dict[str, float], n, d):
    n, d = np.asarray(n, float), np.asarray(d, float)
    return p["E"] + p["A"] * n ** (-p["alpha"]) + p["B"] * d ** (-p["beta"])


def design(x: np.ndarray) -> np.ndarray:
    n, d, q = np.asarray(x, float).T
    return (1-q)[:, None] * np.column_stack((np.ones(len(n)), np.log(n), np.log(d/100)))


def predict(p: dict[str, float], gamma, x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, float)
    return b1_value(p, x[:, 0], x[:, 1]) + design(x) @ np.asarray(gamma, float)


def fit_gamma(p: dict[str, float], x: np.ndarray, y: np.ndarray, ridge: float = 0.0) -> np.ndarray:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 30 or x.shape != (len(y), 3) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("invalid B7 quality fit input")
    z = design(x)
    if np.linalg.matrix_rank(z) < 3:
        raise ValueError("quality design not identified on this training fold")
    penalty = np.diag([0.0, ridge, ridge])
    gamma = np.linalg.solve(z.T @ z + penalty, z.T @ (y - b1_value(p, x[:, 0], x[:, 1])))
    corners = np.array([[1, math.log(n), math.log(d/100)]
                        for n in (0.07, 11.97) for d in (10.0, 600.0)])
    if float(np.min(corners @ gamma)) < 1e-8:
        target = y - b1_value(p, x[:, 0], x[:, 1])
        def objective(v):
            residual = z @ v - target
            return float(residual @ residual + ridge * (v[1:] @ v[1:]))
        result = minimize(objective, gamma, method="SLSQP",
                          constraints=[{"type": "ineq", "fun": lambda v: corners @ v - 1e-8}],
                          options={"ftol": 1e-12, "maxiter": 1000})
        if not result.success or np.min(corners @ result.x) < -1e-9:
            raise ValueError("positive quality gain constraint failed")
        gamma = result.x
    return gamma


def rmse(p, gamma, x, y):
    return float(np.sqrt(np.mean((predict(p, gamma, x) - y)**2)))


def nested_cv(p, x, y):
    folds = []
    fixed_folds = []
    all_inner = {ridge: [] for ridge in RIDGES}
    for axis, name in enumerate(("N_params_B", "D_tokens_B", "Q_score")):
        levels = np.unique(x[:, axis])
        for outer in levels:
            scores = {ridge: [] for ridge in RIDGES}
            for inner in levels[levels != outer]:
                train = (x[:, axis] != outer) & (x[:, axis] != inner)
                held = x[:, axis] == inner
                for ridge in RIDGES:
                    scores[ridge].append(rmse(p, fit_gamma(p, x[train], y[train], ridge), x[held], y[held]))
            selected = min(RIDGES, key=lambda ridge: (np.mean(scores[ridge]), ridge))
            train, held = x[:, axis] != outer, x[:, axis] == outer
            value = rmse(p, fit_gamma(p, x[train], y[train], selected), x[held], y[held])
            fixed = rmse(p, fit_gamma(p, x[train], y[train]), x[held], y[held])
            folds.append({"axis": name, "held_level": float(outer), "selected_ridge": selected,
                          "inner_mean_rmse": {str(k): float(np.mean(v)) for k, v in scores.items()},
                          "outer_rmse": value, "held_rows": int(held.sum())})
            fixed_folds.append({"axis": name, "held_level": float(outer), "outer_rmse": fixed})
        for ridge in RIDGES:
            all_inner[ridge].extend(rmse(p, fit_gamma(p, x[x[:, axis] != level],
                                                      y[x[:, axis] != level], ridge),
                                         x[x[:, axis] == level], y[x[:, axis] == level])
                                    for level in levels)
    selected_full = min(RIDGES, key=lambda ridge: (np.mean(all_inner[ridge]), ridge))
    return selected_full, folds, fixed_folds, {str(k): float(np.mean(v)) for k, v in all_inner.items()}


def summarize(folds, field):
    return {axis: float(np.mean([row[field] for row in folds if row["axis"] == axis]))
            for axis in ("N_params_B", "D_tokens_B", "Q_score")}


def main():
    p = b1_parameters()
    sources, x, y, _ = source_data()
    if sources["supplementary_NQ_experiment_expanded.csv"]["sha256"] != B7_SOURCE_SHA:
        raise ValueError("B7 input identity changed")
    selected, folds, fixed_folds, all_inner = nested_cv(p, x, y)
    gamma = fit_gamma(p, x, y, selected)
    pred = predict(p, gamma, x)
    sse = float(np.sum((pred-y)**2))
    joint = json.loads(B7_FILE.read_text(encoding="utf-8"))
    if joint["source_hash"] != B7_SOURCE_SHA or joint["model"]["free_parameters"] != 8:
        raise ValueError("B7 joint comparison identity changed")
    nested_joint = json.loads(B7_NESTED.read_text(encoding="utf-8"))
    if nested_joint["source_hash"] != B7_SOURCE_SHA:
        raise ValueError("B7 nested comparison identity changed")
    joint_summary = next(row for row in joint["comparison"] if row["method"] == "joint")
    joint_nested = {axis: float(np.mean([row["outer_metrics"]["rmse"] for row in nested_joint["folds"]
                                         if row["axis"] == axis]))
                    for axis in ("N_params_B", "D_tokens_B", "Q_score")}
    new_fixed, new_nested = summarize(fixed_folds, "outer_rmse"), summarize(folds, "outer_rmse")
    n = len(y)
    new = {"model": "B1_fixed_backbone_plus_quality", "train_RMSE": float(np.sqrt(sse/n)),
           "parameter_count": 3, "AIC_descriptive": n*math.log(sse/n)+2*3,
           "BIC_descriptive": n*math.log(sse/n)+3*math.log(n), "selected_ridge": selected,
           "CV_scope": "nested_ridge_selection_with_fixed_B1_backbone"}
    old = {"model": "B7_joint_8_parameter", "train_RMSE": joint["model"]["fit"]["rmse"],
           "parameter_count": 8, "AIC_descriptive": joint_summary["AIC_descriptive"],
           "BIC_descriptive": joint_summary["BIC_descriptive"], "selected_ridge": None,
           "CV_scope": "fixed_full_family_held_level; nested_B7_selection_reported_separately"}
    nested_row = {"model": "B7_nested_family_selection", "train_RMSE": None,
                  "parameter_count": None, "AIC_descriptive": None, "BIC_descriptive": None,
                  "selected_ridge": None, "CV_scope": "published_train_only_family_selection_per_outer_fold"}
    for row, fixed, nested in ((new, new_fixed, new_nested),
                               (old, {a: joint_summary[a+"_mean_fold_RMSE"] for a in new_fixed}, {}),
                               (nested_row, {}, joint_nested)):
        for axis, label in (("N_params_B", "N"), ("D_tokens_B", "D"), ("Q_score", "Q")):
            row[label+"_held_level_RMSE"] = fixed.get(axis)
            row[label+"_nested_RMSE"] = nested.get(axis)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "b7_backbone_comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(new), lineterminator="\n")
        writer.writeheader(); writer.writerows((new, old, nested_row))
    result = {"schema_version": "cyj.b1_fixed_b7_quality.v1",
              "status": "conditional_semi_synthetic_quality_extension",
              "B1_parameters": p, "B1_fit_sha256": sha(B1_FILE),
              "B7_source_sha256": B7_SOURCE_SHA, "B7_joint_comparator_sha256": sha(B7_FILE),
              "B7_nested_comparator_sha256": sha(B7_NESTED),
              "quality_parameters": dict(zip(("G0", "GN", "GD"), map(float, gamma))),
              "selected_ridge": selected, "full_inner_CV_mean_RMSE": all_inner,
              "train_RMSE": new["train_RMSE"], "train_SSE": sse,
              "outer_nested_mean_RMSE": new_nested, "outer_fixed_form_mean_RMSE": new_fixed,
              "outer_folds": folds, "positive_gain_corners": [float(v) for v in
                  np.array([[1, math.log(nn), math.log(dd/100)] for nn in (.07, 11.97)
                            for dd in (10, 600)]) @ gamma],
              "training_rows": n, "B7_rows_outside_B1_ND_rectangle": int(np.sum(
                  (x[:,0] < .070542) | (x[:,0] > 11.965825) |
                  (x[:,1] < .134) | (x[:,1] > 299.893))),
              "formal_prediction_support": {"N_params_B": [.070542, 11.965825],
                                            "D_tokens_B": [10, 299.893], "Q_proxy": [.1, 1]},
              "validation_limit": "B7 is semi-synthetic; fixed B1 backbone is extrapolated for some training rows; A/B quality bridge is uncalibrated",
              "python": platform.python_version(), "numpy": np.__version__}
    (OUT / "b7_quality_extension.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    return {"train_RMSE": new["train_RMSE"], "selected_ridge": selected,
            "nested_CV": new_nested, "B7_rows": n}


if __name__ == "__main__":
    print(json.dumps(main()))
