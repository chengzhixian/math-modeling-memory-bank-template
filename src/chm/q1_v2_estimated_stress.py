"""Descriptive A12-A15 stress test of the already frozen Q1 v2 producer.

Estimated 10B/70B losses are never used to fit, tune, or promote either model.
The 63 mixtures are A4-seen recipes, so this probes scale transfer of rankings
on familiar compositions rather than extrapolation in composition space.
"""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
from scipy.stats import spearmanr
from q1_interface import Q1Interface
from q1_mixture_final_audit import read_pairs, DATA

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_v2_estimated_stress"
RIDGE = ROOT / "outputs/chm/local_recheck_v1/mixture_effect_ridge_v0.csv"
FILES = ("est_mixture_10b.csv", "est_pile_loss_10b.csv",
         "est_mixture_70b.csv", "est_pile_loss_70b.csv")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_rho(a, b):
    return float(spearmanr(a, b).statistic)


def run():
    q1 = Q1Interface(ROOT)
    data, _, domains, targets = read_pairs()
    assert domains == q1.domains and targets == q1.targets
    with RIDGE.open(encoding="utf-8-sig", newline="") as stream:
        ridge = {row["target"]: row for row in csv.DictReader(stream)}
    ids_train = [str(i) for i in data["train_1m"][0].index]
    train = dict(zip(ids_train, data["train_1m"][4]))
    rows, decisions, estimated = [], [], {}
    v2_pred = {}
    ridge_pred = {}
    for scope in ("est_10B", "est_70B"):
        mix, loss, _, target_columns, x = data[scope]
        ids = [str(i) for i in mix.index]
        assert len(ids) == len(set(ids)) == 63 and set(ids).issubset(train)
        max_seen_difference = max(float(np.max(abs(p-train[i]))) for i, p in zip(ids, x))
        assert max_seen_difference < 1e-12
        assert all(q1.support(dict(zip(domains, p)))["in_A4_hull"] for p in x)
        y = loss[target_columns].to_numpy(float)
        assert np.isfinite(y).all() and y.shape == (63, 13)
        pred_v2 = q1._predict(x)
        pred_ridge = np.column_stack([
            float(ridge[t]["intercept"]) + x @ np.array([float(ridge[t][d]) for d in domains])
            for t in targets])
        estimated[scope], v2_pred[scope], ridge_pred[scope] = y, pred_v2, pred_ridge
        for k, target in enumerate(targets):
            actual = y[:, k]
            v2 = pred_v2[:, k]
            old = pred_ridge[:, k]
            rows.append({
                "scope": scope, "target": target, "n": len(ids),
                "v2_spearman": rank_rho(actual, v2),
                "ridge_spearman": rank_rho(actual, old),
                "v2_rmse_absolute_cross_scale": float(np.sqrt(np.mean((v2-actual)**2))),
                "ridge_rmse_absolute_cross_scale": float(np.sqrt(np.mean((old-actual)**2))),
                "estimated_10B_70B_spearman": None,
            })
        # Decision stress uses within-group centered, positive mean scaling.
        # It is descriptive and does not re-optimize or revise the Q1 v2 policy.
        equal = np.ones(len(targets)) / len(targets)
        observed_score = ((y-y.mean(axis=0)) / y.mean(axis=0)) @ equal
        for model, pred in (("v2", pred_v2), ("ridge", pred_ridge)):
            score = ((pred-pred.mean(axis=0)) / pred.mean(axis=0)) @ equal
            chosen = int(np.argmin(score))
            best = int(np.argmin(observed_score))
            decisions.append({
                "scope": scope, "model": model, "n_candidate": 63,
                "selected_index": ids[chosen], "estimated_best_index": ids[best],
                "estimated_score_regret": float(observed_score[chosen]-observed_score[best]),
                "estimated_rank_of_selected": int(np.sum(observed_score < observed_score[chosen]) + 1),
                "score_spearman": rank_rho(observed_score, score),
            })
    paired = [rank_rho(estimated["est_10B"][:, k], estimated["est_70B"][:, k])
              for k in range(len(targets))]
    assert abs(float(np.median(paired)) - 0.9906874039938558) < 1e-10
    assert abs(float(np.median([r["ridge_spearman"] for r in rows if r["scope"] == "est_10B"])) - 0.5136328725038403) < 1e-10
    assert abs(float(np.median([r["ridge_spearman"] for r in rows if r["scope"] == "est_70B"])) - 0.4148475284420329) < 1e-10
    for row in rows:
        row["estimated_10B_70B_spearman"] = paired[targets.index(row["target"])]
    OUT.mkdir(parents=True, exist_ok=True)
    for name, records in (("targetwise.csv", rows), ("decision_stress.csv", decisions)):
        with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    summary = {
        "schema_version": "chm.q1.v2.estimated_stress.v1",
        "role": "estimated/extrapolated tables only; no observed large-model validation",
        "model_selection_use": False,
        "composition_support": "63 A4-seen recipes in both groups",
        "max_A4_recipe_difference": max_seen_difference,
        "q1_manifest_sha256": q1.manifest_sha256,
        "input_sha256": {f: sha(DATA/f) for f in FILES},
        "ridge_sha256": sha(RIDGE),
        "targetwise_sha256": sha(OUT/"targetwise.csv"),
        "decision_sha256": sha(OUT/"decision_stress.csv"),
        "groups": {
            scope: {
                "n": 63,
                "v2_spearman_median": float(np.median([r["v2_spearman"] for r in rows if r["scope"] == scope])),
                "ridge_spearman_median": float(np.median([r["ridge_spearman"] for r in rows if r["scope"] == scope])),
                "v2_higher_spearman_targets": sum(r["v2_spearman"] > r["ridge_spearman"] for r in rows if r["scope"] == scope),
            } for scope in ("est_10B", "est_70B")
        },
        "estimated_10B_70B_spearman_median": float(np.median(paired)),
    }
    (OUT/"manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
