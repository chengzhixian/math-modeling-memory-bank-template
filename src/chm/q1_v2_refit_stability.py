"""Finite A4 candidate decision sensitivity to 80% train subsamples.

Each replicate reselects five high-variance domains, selects targetwise Ridge
regularization by five-fold CV, and refits all 13 interaction regressions.
This is a stability diagnostic, not a confidence interval for the continuous
convex-hull optimum.
"""
from pathlib import Path
import csv
import hashlib
import json
from itertools import combinations
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from q1_interface import Q1Interface
from q1_mixture_final_audit import read_pairs
from q1_mixture_decision_v2 import quality_constraints

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/Q1/refit_stability"
SEED = 20260925
REPEATS = 30
ALPHAS = (0.001, 0.01, 0.1, 1., 10., 100., 1000.)
POLICIES = ("unconstrained", "quality_direct", "quality_direct_and_near")


def features(x, selected):
    return np.column_stack((x, *[x[:, a]*x[:, b] for a, b in combinations(selected, 2)]))


def fit_predict(x_train, y_train, x_eval, selected):
    a = features(x_train, selected)
    b = features(x_eval, selected)
    folds = list(KFold(5, shuffle=False).split(a))
    preds = np.empty((len(x_eval), y_train.shape[1]))
    chosen = []
    for k in range(y_train.shape[1]):
        y = y_train[:, k]
        scores = []
        for alpha in ALPHAS:
            errors = []
            for tr, va in folds:
                model = Ridge(alpha=alpha).fit(a[tr], y[tr])
                errors.append(float(np.sqrt(np.mean((model.predict(a[va])-y[va])**2))))
            scores.append(float(np.mean(errors)))
        alpha = ALPHAS[int(np.argmin(scores))]
        chosen.append(alpha)
        preds[:, k] = Ridge(alpha=alpha).fit(a, y).predict(b)
    return preds, chosen


def run():
    q1 = Q1Interface(ROOT)
    datasets, _, domains, targets = read_pairs()
    assert domains == q1.domains and targets == q1.targets
    train_mix, train_loss, _, target_cols, train_x = datasets["train_1m"]
    assert list(train_mix.index) == list(train_loss.index)
    train_y = train_loss[target_cols].to_numpy(float)
    rng = np.random.default_rng(SEED)
    eval_x = np.vstack((q1.recipes, q1.ref))
    frozen = q1._predict(q1.recipes)/q1.reference_loss-1
    feasible = {p: quality_constraints(q1, q1.recipes, p)[0] for p in POLICIES}
    baseline = {}
    for policy in POLICIES:
        ids = np.flatnonzero(feasible[policy])
        baseline[policy] = int(ids[np.argmin(frozen[ids].mean(axis=1))])
    baseline["minimax"] = int(np.argmin(frozen.max(axis=1)))
    records = []
    for repeat in range(REPEATS):
        selected_rows = np.sort(rng.choice(len(train_x), size=int(.8*len(train_x)), replace=False))
        x, y = train_x[selected_rows], train_y[selected_rows]
        selected = np.argsort(np.var(x, axis=0))[-5:].tolist()
        pred, alphas = fit_predict(x, y, eval_x, selected)
        ref = pred[-1]
        assert np.isfinite(pred).all() and np.all(ref > 0)
        relative = pred[:-1]/ref-1
        for policy in (*POLICIES, "minimax"):
            if policy == "minimax":
                ids = np.arange(len(q1.recipes))
                score = relative.max(axis=1)
                frozen_score = frozen.max(axis=1)
            else:
                ids = np.flatnonzero(feasible[policy])
                score = relative.mean(axis=1)
                frozen_score = frozen.mean(axis=1)
            selected_idx = int(ids[np.argmin(score[ids])])
            base_idx = baseline[policy]
            records.append({
                "repeat": repeat, "policy": policy,
                "selected_index": q1.recipe_ids[selected_idx],
                "frozen_selected_index": q1.recipe_ids[base_idx],
                "same_as_frozen": selected_idx == base_idx,
                "refit_regret_using_frozen_choice": float(score[base_idx]-score[selected_idx]),
                "frozen_regret_using_refit_choice": float(frozen_score[selected_idx]-frozen_score[base_idx]),
                "selected_feature_domains": "|".join(domains[j] for j in selected),
                "chosen_alpha_13": "|".join(str(a) for a in alphas),
            })
    OUT.mkdir(parents=True, exist_ok=True)
    file = OUT/"replicate_choices.csv"
    with file.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "schema_version": "chm.q1.v2.refit_stability.v1",
        "q1_manifest_sha256": q1.manifest_sha256,
        "seed": SEED, "repeats": REPEATS, "subsample_fraction": 0.8,
        "fit_protocol": "reselect 5 highest-variance domains; 10 pair products; per-target five-fold seven-alpha CV; refit",
        "decision_scope": "512 observed A4 recipes only; no continuous hull recertification",
        "records_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
        "policies": {
            p: {
                "frozen_selected_index": q1.recipe_ids[baseline[p]],
                "same_choice_fraction": float(np.mean([r["same_as_frozen"] for r in records if r["policy"] == p])),
                "distinct_refit_choices": len({r["selected_index"] for r in records if r["policy"] == p}),
                "median_refit_regret_using_frozen_choice": float(np.median([r["refit_regret_using_frozen_choice"] for r in records if r["policy"] == p])),
                "max_refit_regret_using_frozen_choice": float(np.max([r["refit_regret_using_frozen_choice"] for r in records if r["policy"] == p])),
            } for p in (*POLICIES, "minimax")
        },
    }
    (OUT/"manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
