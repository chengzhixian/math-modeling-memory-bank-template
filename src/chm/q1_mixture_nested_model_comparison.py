"""Training-only nested CV of Q1 linear versus interaction model families.

Outer folds never choose the five interaction domains or Ridge alpha. This is
an A4+A5 model-form diagnostic, separate from A6--A11 validation.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

from q1_mixture_final_audit import read_pairs
from q1_regmix_domainwise import RIDGE_GRID

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_nested_model_comparison_v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def features(x: np.ndarray, selected: list[int] | None) -> np.ndarray:
    if selected is None:
        return x
    pairs = list(itertools.combinations(selected, 2))
    return np.column_stack([x] + [(x[:, a] * x[:, b])[:, None] for a, b in pairs])


def choose_alpha(x: np.ndarray, y: np.ndarray, interaction: bool) -> tuple[float, float]:
    cv = KFold(5, shuffle=False)
    candidates = []
    for alpha in RIDGE_GRID:
        errors = []
        for tr, va in cv.split(x):
            selected = np.argsort(np.var(x[tr], axis=0))[-5:].tolist() if interaction else None
            model = Ridge(alpha=alpha).fit(features(x[tr], selected), y[tr])
            errors.append(float(np.sqrt(np.mean((model.predict(features(x[va], selected)) - y[va]) ** 2))))
        candidates.append((float(np.mean(errors)), float(alpha)))
    return min(candidates)


def run() -> dict:
    data, audit, domains, targets = read_pairs()
    mix, losses, _, cols, x = data["train_1m"]
    assert list(mix.index) == list(losses.index) and len(x) == 512
    outer = KFold(5, shuffle=False)
    oof = []
    folds = []
    for target in targets:
        col = next(c for c in cols if c.replace("metric/the_pile_", "").replace("_val_loss", "") == target)
        y = losses[col].to_numpy(float)
        predicted = {"ridge": np.full(len(y), np.nan), "interaction": np.full(len(y), np.nan),
                     "constant": np.full(len(y), np.nan)}
        for fold, (train, valid) in enumerate(outer.split(x), 1):
            selected = np.argsort(np.var(x[train], axis=0))[-5:].tolist()
            for model_name in ("ridge", "interaction"):
                chosen = None if model_name == "ridge" else selected
                xx_train = features(x[train], chosen)
                xx_valid = features(x[valid], chosen)
                cv_rmse, alpha = choose_alpha(x[train], y[train], interaction=chosen is not None)
                fit = Ridge(alpha=alpha).fit(xx_train, y[train])
                predicted[model_name][valid] = fit.predict(xx_valid)
                folds.append({"target": target, "outer_fold": fold, "model": model_name,
                              "alpha": alpha, "inner_cv_rmse": cv_rmse,
                              "selected_domains": "|".join(domains[i] for i in selected) if chosen is not None else "",
                              "outer_rmse": float(np.sqrt(np.mean((predicted[model_name][valid] - y[valid]) ** 2)))})
            predicted["constant"][valid] = y[train].mean()
        assert all(np.isfinite(v).all() for v in predicted.values())
        for model_name, value in predicted.items():
            oof.append({"target": target, "model": model_name, "n_outer_predictions": len(y),
                        "oof_rmse": float(np.sqrt(np.mean((value - y) ** 2))),
                        "oof_mae": float(np.mean(np.abs(value - y))),
                        "oof_spearman": float(spearmanr(y, value).statistic)})
    OUT.mkdir(parents=True, exist_ok=True)
    for file, rows in (("outer_fold_results.csv", folds), ("targetwise_oof.csv", oof)):
        with (OUT / file).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    by = {(r["target"], r["model"]): r for r in oof}
    counts = {"interaction_lower_oof_rmse_than_ridge": sum(by[k, "interaction"]["oof_rmse"] < by[k, "ridge"]["oof_rmse"] for k in targets),
              "interaction_lower_oof_rmse_than_constant": sum(by[k, "interaction"]["oof_rmse"] < by[k, "constant"]["oof_rmse"] for k in targets),
              "ridge_lower_oof_rmse_than_constant": sum(by[k, "ridge"]["oof_rmse"] < by[k, "constant"]["oof_rmse"] for k in targets),
              "interaction_higher_oof_spearman": sum(by[k, "interaction"]["oof_spearman"] > by[k, "ridge"]["oof_spearman"] for k in targets)}
    manifest = {"schema_version": "chm.q1.nested_model_comparison.v1", "status": "A4_A5_training_only_model_form_diagnostic",
                "outer": "KFold(5, shuffle=False)",
                "inner": "KFold(5, shuffle=False), alpha from frozen seven-value grid; selected domains recomputed within every inner train and outer train",
                "targets": 13, "counts": counts,
                "source_sha256": {r.file: r.sha256 for r in audit.itertuples() if r.scope == "train_1m"},
                "outer_fold_results_sha256": sha(OUT / "outer_fold_results.csv"),
                "targetwise_oof_sha256": sha(OUT / "targetwise_oof.csv")}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
