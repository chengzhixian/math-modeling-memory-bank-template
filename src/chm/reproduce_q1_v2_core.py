"""Recompute the released Q1 interaction model from the original A4/A5 tables.

The published release stays immutable. This command writes a verification report
under data/processed/Q1 and fails if its model or held-out metrics drift.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/real_attachments/A_data_value/regmix_tables"
RELEASE = ROOT / "outputs/Q1"
OUT = ROOT / "data/processed/Q1/reproduction"
EXPECTED_RAW_SHA256 = {
    "train_mixture_1m.csv": "04a32ef4ab594376bf90e11404c033668f887c351d6a03ad3744824c7296a2d8",
    "train_pile_loss_1m.csv": "49a959aa07ce5c20831d5abe3a7896ff0cd90a398bd407c8913fd5588be0465a",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ridge(x: np.ndarray, y: np.ndarray, alpha: float) -> tuple[float, np.ndarray]:
    xm, ym = x.mean(axis=0), float(y.mean())
    centered = x - xm
    beta = np.linalg.solve(centered.T @ centered + alpha * np.eye(x.shape[1]), centered.T @ (y - ym))
    return ym - float(xm @ beta), beta


def design(raw_rows: list[dict[str, str]], domains: list[str], pairs: list[list[str]]) -> np.ndarray:
    if list(raw_rows[0]) != ["index", *("train_the_pile_" + d for d in domains)]:
        raise ValueError("A4 mixture domain order changed")
    x = np.array([[float(row["train_the_pile_" + d]) for d in domains] for row in raw_rows])
    if not np.isfinite(x).all() or np.any(x < 0) or np.any(x.sum(axis=1) <= 0):
        raise ValueError("invalid A4 recipe")
    x = x / x.sum(axis=1, keepdims=True)
    return np.column_stack([x, *(x[:, domains.index(a)] * x[:, domains.index(b)] for a, b in pairs)])


def reproduce() -> dict:
    for name, expected in EXPECTED_RAW_SHA256.items():
        if digest(RAW / name) != expected:
            raise ValueError(f"raw Q1 input changed: {name}")
    features = json.loads((RELEASE / "interaction_feature_definition.json").read_text(encoding="utf-8"))
    published = json.loads((RELEASE / "interaction_coefficients_13_targets.json").read_text(encoding="utf-8"))["targets"]
    domains, targets, pairs = features["domain_order"], features["target_order"], features["pairs_order"]
    mix, loss, published_recipes = rows(RAW / "train_mixture_1m.csv"), rows(RAW / "train_pile_loss_1m.csv"), rows(RELEASE / "recipes_512.csv")
    if len(mix) != 512 or len(loss) != 512 or [r["index"] for r in mix] != [r["index"] for r in loss]:
        raise ValueError("A4/A5 index alignment changed")
    x = design(mix, domains, pairs)
    if [domains[i] for i in np.argsort(np.var(x[:, :17], axis=0))[-5:]] != features["selected_domain_order"]:
        raise ValueError("A4 target-free feature selection changed")
    selected = features["selected_domain_order"]
    if pairs != [list(p) for p in itertools.combinations(selected, 2)]:
        raise ValueError("pair feature order changed")
    recipes = np.array([[float(r[d]) for d in domains] for r in published_recipes])
    if [r["index"] for r in published_recipes] != [r["index"] for r in mix] or not np.allclose(x[:, :17], recipes, atol=1e-14, rtol=0):
        raise ValueError("released recipe normalization changed")
    reference = x[:, :17].mean(axis=0)
    if not np.allclose(reference, [features["Q1_reference_p"][d] for d in domains], atol=1e-14, rtol=0):
        raise ValueError("released A4 reference composition changed")
    reference_features = np.r_[reference, [reference[domains.index(a)] * reference[domains.index(b)] for a, b in pairs]]

    folds = np.array_split(np.arange(len(x)), 5)
    max_coefficient_difference = 0.0
    max_cv_difference = 0.0
    reproduced = {}
    reproduced_model = {}
    for target in targets:
        key = f"metric/the_pile_{target}_val_loss"
        y = np.array([float(r[key]) for r in loss])
        if not np.isfinite(y).all() or np.min(y) <= 0:
            raise ValueError(f"invalid training loss: {target}")
        scores = []
        for alpha in features["alpha_grid"]:
            errors = []
            for va in folds:
                train = np.ones(len(x), dtype=bool)
                train[va] = False
                intercept, beta = ridge(x[train], y[train], alpha)
                errors.append(float(np.sqrt(np.mean((intercept + x[va] @ beta - y[va]) ** 2))))
            scores.append((float(np.mean(errors)), float(alpha)))
        cv, alpha = min(scores)
        entry = published[target]
        if alpha != float(entry["alpha"]):
            raise ValueError(f"ridge alpha drift: {target}")
        intercept, beta = ridge(x, y, alpha)
        expected = np.array([*(entry["main"][d] for d in domains), *(r["gamma"] for r in entry["pairs"])])
        difference = float(np.max(np.abs(beta - expected)))
        max_coefficient_difference = max(max_coefficient_difference, difference, abs(intercept - entry["intercept"]))
        max_cv_difference = max(max_cv_difference, abs(cv - entry["cv_rmse"]))
        reference_loss = float(intercept + reference_features @ beta)
        if abs(reference_loss - entry["fitted_reference_loss"]) > 1e-10:
            raise ValueError(f"reference Loss drift: {target}")
        reproduced_model[target] = {
            "intercept": float(intercept),
            "main": dict(zip(domains, map(float, beta[:17]))),
            "pairs": [{"domains": pair, "gamma": float(beta[17+i])} for i, pair in enumerate(pairs)],
            "alpha": alpha, "cv_rmse": cv, "fitted_reference_loss": reference_loss,
        }
        reproduced[target] = {"alpha": alpha, "cv_rmse": cv, "max_coefficient_difference": difference}
    if max_coefficient_difference > 1e-8 or max_cv_difference > 1e-10:
        raise ValueError("released Q1 interaction model did not reproduce")

    validation = {(r["scope"], r["target"]): r for r in rows(RELEASE / "targetwise_validation.csv") if r["support_group"] == "all"}
    heldout_max_rmse_difference = 0.0
    heldout_max_spearman_difference = 0.0
    for scope, mix_name, loss_name in (
        ("test_1m", "test_mixture_1m.csv", "test_pile_loss_1m.csv"),
        ("test_60m", "test_mixture_60m.csv", "test_pile_loss_60m.csv"),
        ("test_1B", "test_mixture_1B.csv", "test_pile_loss_1B.csv"),
    ):
        m, l = rows(RAW / mix_name), rows(RAW / loss_name)
        if [r["index"] for r in m] != [r["index"] for r in l]:
            raise ValueError(f"{scope} mixture/loss index mismatch")
        xx = design(m, domains, pairs)
        for target in targets:
            entry = published[target]
            beta = np.array([*(entry["main"][d] for d in domains), *(r["gamma"] for r in entry["pairs"])])
            prediction = float(entry["intercept"]) + xx @ beta
            observed = np.array([float(r[f"metric/the_pile_{target}_val_loss"]) for r in l])
            published_row = validation[(scope, target)]
            heldout_max_rmse_difference = max(heldout_max_rmse_difference, abs(float(np.sqrt(np.mean((prediction-observed)**2))) - float(published_row["interaction_rmse"])))
            heldout_max_spearman_difference = max(heldout_max_spearman_difference, abs(float(spearmanr(prediction, observed).statistic) - float(published_row["interaction_spearman"])))
    if heldout_max_rmse_difference > 1e-8 or heldout_max_spearman_difference > 1e-10:
        raise ValueError("released Q1 held-out metrics did not reproduce")
    report = {
        "status": "verified_from_raw_A4_A5_A6_A11",
        "source_raw_sha256": {p.name: digest(p) for p in sorted(RAW.glob("*.csv"))},
        "released_model_sha256": digest(RELEASE / "interaction_coefficients_13_targets.json"),
        "seed": None,
        "targets": reproduced,
        "max_coefficient_difference": max_coefficient_difference,
        "max_cv_difference": max_cv_difference,
        "heldout_max_rmse_difference": heldout_max_rmse_difference,
        "heldout_max_spearman_difference": heldout_max_spearman_difference,
        "note": "A6-A11 were used in original form selection; metrics are real held-out group comparisons, not an untouched final blind test.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "interaction_coefficients_13_targets.json").write_text(json.dumps({
        "schema_version": "chm.q1.interaction_13_targets.v2",
        "status": "MAIN_REPRODUCED_FROM_RAW",
        "model": "intercept + 17 linear proportions + ten selected pair products; targetwise Ridge",
        "targets": reproduced_model,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(reproduce(), ensure_ascii=False))
