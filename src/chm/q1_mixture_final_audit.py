"""Independent audit of the frozen A4+A5 Ridge and A6--A15 roles."""
from pathlib import Path
import hashlib
import json
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

from q1_regmix_domainwise import PAIR_FILES, RIDGE_GRID, SEED, metric_name, normalize_composition

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/raw/real_attachments/A_data_value/regmix_tables"
OUT = ROOT / "outputs/chm/q1_mixture_final"
COEF = ROOT / "outputs/chm/local_recheck_v1/mixture_effect_ridge_v0.csv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pairs():
    result, audits = {}, []
    for mix_file, loss_file, name in PAIR_FILES:
        m, l = pd.read_csv(DATA / mix_file), pd.read_csv(DATA / loss_file)
        for label, df, file in [("mixture", m, mix_file), ("loss", l, loss_file)]:
            if df["index"].isna().any() or df["index"].duplicated().any():
                raise ValueError(f"{name} {label} index missing or duplicated")
            audits.append(dict(scope=name, kind=label, file=file, sha256=sha(DATA / file),
                               n=len(df), n_unique_index=df["index"].nunique()))
        if len(m) != len(l) or set(m["index"]) != set(l["index"]):
            raise ValueError(f"{name} mixture/loss indices do not match one-to-one")
        domains = [c for c in m if c != "index"]
        targets = [c for c in l if c != "index"]
        raw = m[domains].to_numpy(float)
        if not np.isfinite(raw).all() or (raw < 0).any() or (raw.sum(axis=1) <= 0).any():
            raise ValueError(f"{name} invalid raw composition")
        normalized = normalize_composition(m, domains)
        if not np.allclose(normalized.sum(axis=1), 1, atol=1e-12):
            raise ValueError(f"{name} normalized row sum failed")
        audits[-2].update(raw_sum_min=float(raw.sum(axis=1).min()),
                          raw_sum_max=float(raw.sum(axis=1).max()),
                          max_normalization_l1=float(np.max(np.abs(normalized - raw).sum(axis=1))))
        result[name] = (m.set_index("index"), l.set_index("index"), domains, targets, normalized)
    names = [x.replace("train_the_pile_", "") for x in result["train_1m"][2]]
    target_names = [metric_name(x) for x in result["train_1m"][3]]
    for name, (_, _, domains, targets, _) in result.items():
        if [x.replace("train_the_pile_", "") for x in domains] != names:
            raise ValueError(f"{name} domain column order changed")
        if [metric_name(x) for x in targets] != target_names:
            raise ValueError(f"{name} target column order changed")
    return result, pd.DataFrame(audits), names, target_names


def hull_status(train, point, tol=1e-7):
    aeq = np.vstack([train.T, np.ones(len(train))])
    beq = np.r_[point, 1.0]
    result = linprog(np.zeros(len(train)), A_eq=aeq, b_eq=beq,
                     bounds=(0, None), method="highs")
    if result.success and np.max(np.abs(aeq @ result.x - beq)) <= tol:
        return "IN_A4_HULL"
    return "OUT_OF_TRAINING_SUPPORT"


def fit_interaction_candidate(x, y, selected):
    pairs = list(combinations(selected, 2))
    xx = np.column_stack([x] + [(x[:, a] * x[:, b])[:, None] for a, b in pairs])
    kfold = KFold(5, shuffle=False)
    cv = []
    for alpha in RIDGE_GRID:
        errors = []
        for tr, va in kfold.split(xx):
            model = Ridge(alpha=alpha).fit(xx[tr], y[tr])
            errors.append(float(np.sqrt(np.mean((model.predict(xx[va]) - y[va]) ** 2))))
        cv.append((float(np.mean(errors)), alpha))
    best_error, best_alpha = min(cv)
    return Ridge(alpha=best_alpha).fit(xx, y), pairs, best_error


def interaction_features(x, pairs):
    return np.column_stack([x] + [(x[:, a] * x[:, b])[:, None] for a, b in pairs])


def main():
    datasets, join_audit, domains, targets = read_pairs()
    OUT.mkdir(parents=True, exist_ok=True)
    join_audit.to_csv(OUT / "dataset_join_audit.csv", index=False)
    coefficients = pd.read_csv(COEF).set_index("target")
    if set(coefficients.index) != set(targets) or set(domains) - set(coefficients.columns):
        raise ValueError("frozen coefficient table identity mismatch")
    xtrain = datasets["train_1m"][4]
    ytrain = datasets["train_1m"][1]
    selected = np.argsort(np.var(xtrain, axis=0))[-5:].tolist()  # train-only, target-free rule
    support_rows, metrics, interactions = [], [], []
    for scope in ["test_1m", "test_60m", "test_1B", "est_10B", "est_70B"]:
        x = datasets[scope][4]
        nearest = cdist(x, xtrain).min(axis=1)
        if scope in {"test_1B", "test_1m", "test_60m"}:
            for idx, distance, point in zip(datasets[scope][0].index, nearest, x):
                support_rows.append(dict(scope=scope, index=idx, hull_status=hull_status(xtrain, point),
                                         nearest_A4_l2=float(distance)))
        for target in targets:
            loss_col = next(c for c in datasets[scope][3] if metric_name(c) == target)
            train_col = next(c for c in datasets["train_1m"][3] if metric_name(c) == target)
            actual = datasets[scope][1][loss_col].to_numpy(float)
            row = coefficients.loc[target]
            pred = x @ row[domains].to_numpy(float) + float(row["intercept"])
            constant = np.full(len(actual), ytrain[train_col].mean())
            centered_pred = pred - pred.mean() + actual.mean()  # diagnostic: uses test mean, never deployment
            met = dict(scope=scope, target=target, n=len(actual), alpha=float(row.alpha),
                rmse=float(np.sqrt(np.mean((pred - actual) ** 2))),
                mae=float(np.mean(np.abs(pred - actual))), bias=float(np.mean(pred - actual)),
                spearman=float(spearmanr(actual, pred).statistic),
                constant_rmse=float(np.sqrt(np.mean((constant - actual) ** 2))),
                centered_relative_rmse=float(np.sqrt(np.mean((centered_pred - actual) ** 2))),
                absolute_rmse_beats_constant=bool(np.mean((pred - actual) ** 2) < np.mean((constant - actual) ** 2)),
                role="estimated_stress_only" if scope.startswith("est_") else "observed_heldout")
            metrics.append(met)
    pd.DataFrame(support_rows).to_csv(OUT / "composition_support.csv", index=False)
    pd.DataFrame(metrics).to_csv(OUT / "heldout_target_metrics.csv", index=False)

    # Exactly matched 1M/60M test compositions, checked by index and all 17 fields.
    m1, l1, _, cols, x1 = datasets["test_1m"]
    m60, l60, _, _, x60 = datasets["test_60m"]
    if list(m1.index) != list(m60.index) or not np.allclose(x1, x60, atol=1e-12):
        raise ValueError("A6/A8 same-mixture pairing failed")
    matched = []
    for target in targets:
        col = next(c for c in cols if metric_name(c) == target)
        matched.append(dict(target=target, n=len(m1), spearman_1m_60m=float(spearmanr(l1[col], l60[col]).statistic),
                            mean_delta_60m_minus_1m=float(np.mean(l60[col] - l1[col]))))
    pd.DataFrame(matched).to_csv(OUT / "same_mixture_1m_60m.csv", index=False)

    # Optional diagnostic, never substituted into the released 13x17 main model.
    for target in targets:
        train_col = next(c for c in datasets["train_1m"][3] if metric_name(c) == target)
        y = ytrain[train_col].to_numpy(float)
        model, pairs, cv = fit_interaction_candidate(xtrain, y, selected)
        for scope in ["test_1m", "test_60m", "test_1B"]:
            xx = interaction_features(datasets[scope][4], pairs)
            col = next(c for c in datasets[scope][3] if metric_name(c) == target)
            actual = datasets[scope][1][col].to_numpy(float)
            base = next(r for r in metrics if r["scope"] == scope and r["target"] == target)
            interactions.append(dict(target=target, scope=scope, n_train=512, n_main_features=17,
                n_pairwise_features=len(pairs), selected_domains="|".join(domains[j] for j in selected),
                alpha=float(model.alpha), cv_rmse=float(cv),
                candidate_rmse=float(np.sqrt(np.mean((model.predict(xx) - actual) ** 2))),
                ridge_rmse=base["rmse"],
                candidate_spearman=float(spearmanr(actual, model.predict(xx)).statistic),
                ridge_spearman=base["spearman"]))
    pd.DataFrame(interactions).to_csv(OUT / "interaction_candidate_comparison.csv", index=False)
    manifest = dict(seed=SEED, main_model="frozen A4+A5 targetwise Ridge; unchanged",
        candidate="10 pair products among 5 A4 highest-variance domains; train-only feature selection and 5-fold CV; diagnostic only",
        target_count=13, domain_count=17, composition_effective_rank_max=16,
        support="convex hull of 512 normalized A4 mixtures; geometric interpolation, not observed training",
        estimated="A12--A15 are estimates on 63 A4-seen compositions; never observed heldout",
        input_sha256={r.file: r.sha256 for r in join_audit.itertuples()}, coefficient_sha256=sha(COEF))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    support_counts = pd.DataFrame(support_rows).groupby(["scope", "hull_status"]).size()
    print(json.dumps({"support": {"/".join(k): int(v) for k, v in support_counts.items()},
                      "1B_absolute_beats_constant": int(sum(r["absolute_rmse_beats_constant"] for r in metrics if r["scope"] == "test_1B")),
                      "candidate": manifest["candidate"]}, indent=2))


if __name__ == "__main__":
    main()
