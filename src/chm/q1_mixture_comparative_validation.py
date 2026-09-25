"""Frozen, matched Ridge/interaction/constant comparison on real A6--A11.

All three predictors use A4+A5 only. Evaluation groups and convex-hull flags
are frozen before computing model comparisons; A12--A15 are excluded.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from q1_mixture_final_audit import read_pairs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_mixture_comparison_v1"
COEF = ROOT / "outputs/chm/local_recheck_v1/mixture_effect_ridge_v0.csv"
INTER = ROOT / "outputs/chm/q1_exports/q1_interaction_bundle_v1/interaction_coefficients_13_targets.json"
SUPPORT = ROOT / "outputs/chm/q1_mixture_final/composition_support.csv"
SOURCE_METRICS = ROOT / "outputs/chm/q1_mixture_final/heldout_target_metrics.csv"
SOURCE_CANDIDATE = ROOT / "outputs/chm/q1_mixture_final/interaction_candidate_comparison.csv"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def metric(y: np.ndarray, pred: np.ndarray) -> dict:
    error = pred - y
    rho = (float(spearmanr(y, pred).statistic)
           if len(y) > 2 and len(np.unique(y)) > 1 and len(np.unique(pred)) > 1 else None)
    return {"rmse": float(np.sqrt(np.mean(error ** 2))),
            "mae": float(np.mean(np.abs(error))),
            "bias": float(np.mean(error)), "spearman": rho}


def run() -> dict:
    data, audit, domains, targets = read_pairs()
    raw_hashes = {r.file: r.sha256 for r in audit.itertuples()}
    assert len(domains) == 17 and len(targets) == 13
    model = json.loads(INTER.read_text(encoding="utf-8"))["targets"]
    ridge = {r["target"]: r for r in csv_rows(COEF)}
    support = {(r["scope"], str(r["index"])): r["hull_status"] for r in csv_rows(SUPPORT)}
    original = {(r["scope"], r["target"]): r for r in csv_rows(SOURCE_METRICS)}
    original_candidate = {(r["scope"], r["target"]): r for r in csv_rows(SOURCE_CANDIDATE)}
    rng = np.random.default_rng(20260925)
    records = []
    for scope in ("test_1m", "test_60m", "test_1B"):
        mix, loss, _, target_cols, x = data[scope]
        assert list(mix.index) == list(loss.index), f"{scope} mixture/loss row order changed"
        ids = [str(i) for i in mix.index]
        flags = np.array([support[(scope, i)] for i in ids])
        groups = {"all": np.ones(len(ids), bool),
                  "in_A4_hull": flags == "IN_A4_HULL",
                  "outside_A4_hull": flags == "OUT_OF_TRAINING_SUPPORT"}
        for target in targets:
            target_col = next(c for c in target_cols if c.replace("metric/the_pile_", "").replace("_val_loss", "") == target)
            train_col = next(c for c in data["train_1m"][3] if c.replace("metric/the_pile_", "").replace("_val_loss", "") == target)
            y = loss[target_col].to_numpy(float)
            rb = np.array([float(ridge[target][d]) for d in domains])
            rpred = x @ rb + float(ridge[target]["intercept"])
            entry = model[target]
            ipred = np.full(len(x), float(entry["intercept"]))
            ipred += x @ np.array([float(entry["main"][d]) for d in domains])
            for pair in entry["pairs"]:
                a, b = pair["domains"]
                ipred += float(pair["gamma"]) * x[:, domains.index(a)] * x[:, domains.index(b)]
            constant = np.full(len(y), float(data["train_1m"][1][train_col].mean()))
            old = original[(scope, target)]
            old_candidate = original_candidate[(scope, target)]
            assert abs(metric(y, rpred)["rmse"] - float(old["rmse"])) < 1e-10
            assert abs(metric(y, ipred)["rmse"] - float(old_candidate["candidate_rmse"])) < 1e-10
            assert abs(metric(y, ipred)["spearman"] - float(old_candidate["candidate_spearman"])) < 1e-10
            for group, keep in groups.items():
                if not keep.any():
                    continue
                yy, rr, ii, cc = y[keep], rpred[keep], ipred[keep], constant[keep]
                rm, im, cm = metric(yy, rr), metric(yy, ii), metric(yy, cc)
                mse_diff = (rr - yy) ** 2 - (ii - yy) ** 2
                boots = np.mean(mse_diff[rng.integers(0, len(yy), size=(1000, len(yy)))], axis=1)
                lo, hi = np.quantile(boots, [0.025, 0.975])
                records.append({"scope": scope, "support_group": group, "target": target, "n": len(yy),
                                "ridge_rmse": rm["rmse"], "interaction_rmse": im["rmse"],
                                "constant_rmse": cm["rmse"], "ridge_spearman": rm["spearman"],
                                "interaction_spearman": im["spearman"],
                                "ridge_mae": rm["mae"], "interaction_mae": im["mae"],
                                "ridge_bias": rm["bias"], "interaction_bias": im["bias"],
                                "ridge_gain_vs_constant": 1 - rm["rmse"] / cm["rmse"],
                                "interaction_gain_vs_constant": 1 - im["rmse"] / cm["rmse"],
                                "paired_mse_improvement": float(mse_diff.mean()),
                                "paired_mse_bootstrap_low": float(lo),
                                "paired_mse_bootstrap_high": float(hi)})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "targetwise_validation.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    counts = {}
    for scope in ("test_1m", "test_60m", "test_1B"):
        for group in ("all", "in_A4_hull", "outside_A4_hull"):
            subset = [r for r in records if r["scope"] == scope and r["support_group"] == group]
            if not subset:
                continue
            counts[f"{scope}/{group}"] = {"n_recipes": subset[0]["n"], "targets": len(subset),
                "interaction_lower_rmse": sum(r["interaction_rmse"] < r["ridge_rmse"] for r in subset),
                "interaction_better_constant": sum(r["interaction_rmse"] < r["constant_rmse"] for r in subset),
                "ridge_better_constant": sum(r["ridge_rmse"] < r["constant_rmse"] for r in subset),
                "spearman_defined_targets": sum(r["interaction_spearman"] is not None and r["ridge_spearman"] is not None for r in subset),
                "interaction_higher_spearman": sum(r["interaction_spearman"] > r["ridge_spearman"] for r in subset
                                                   if r["interaction_spearman"] is not None and r["ridge_spearman"] is not None)}
    summary = {"schema_version": "chm.q1.comparative_validation.v1", "status": "exploratory_same_heldouts_no_new_model_selection",
               "train_only": "A4+A5; 5 high-variance domains selected from A4, then 5-fold unshuffled CV",
               "observed_test_only": "A6--A11; 1M/60M share mixture rows; 1B has a distinct recipe set",
               "bootstrap": "1000 row resamples per target/group, seed 20260925; descriptive, no multiplicity correction",
               "counts": counts, "source_sha256": {"ridge": sha(COEF), "interaction": sha(INTER),
                                              "support": sha(SUPPORT), "published_candidate_metrics": sha(SOURCE_CANDIDATE), **raw_hashes},
               "targetwise_sha256": sha(OUT / "targetwise_validation.csv")}
    (OUT / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
