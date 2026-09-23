from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import KFold


PAIR_FILES = [
    ("train_mixture_1m.csv", "train_pile_loss_1m.csv", "train_1m"),
    ("test_mixture_1m.csv", "test_pile_loss_1m.csv", "test_1m"),
    ("test_mixture_60m.csv", "test_pile_loss_60m.csv", "test_60m"),
    ("test_mixture_1B.csv", "test_pile_loss_1B.csv", "test_1B"),
    ("est_mixture_10b.csv", "est_pile_loss_10b.csv", "est_10B"),
    ("est_mixture_70b.csv", "est_pile_loss_70b.csv", "est_70B"),
]


def load_pair(root, mixture_file, loss_file):
    mixture = pd.read_csv(root / mixture_file)
    loss = pd.read_csv(root / loss_file)
    merged = mixture.merge(loss, on="index", how="inner", validate="one_to_one")
    mix_cols = [c for c in mixture.columns if c != "index"]
    loss_cols = [c for c in loss.columns if c != "index"]
    x = merged[mix_cols].to_numpy(dtype=float)
    y = merged[loss_cols].mean(axis=1).to_numpy(dtype=float)
    return mixture, loss, merged, mix_cols, loss_cols, x, y


def audit_pair(mixture, loss, mix_cols, loss_cols):
    sums = mixture[mix_cols].sum(axis=1)
    return {
        "mixture_rows": int(len(mixture)),
        "loss_rows": int(len(loss)),
        "mixture_dims": int(len(mix_cols)),
        "loss_dims": int(len(loss_cols)),
        "paired_indices": int(len(set(mixture["index"]) & set(loss["index"]))),
        "missing_loss_cells": int(loss[loss_cols].isna().sum().sum()),
        "mixture_sum_min": float(sums.min()),
        "mixture_sum_max": float(sums.max()),
        "mixture_sum_max_abs_dev": float((sums - 1.0).abs().max()),
    }


def select_lambda(x, y, lambdas):
    kf = KFold(n_splits=5, shuffle=False)
    rows = []
    for lam in lambdas:
        fold_rmse = []
        for train_idx, val_idx in kf.split(x):
            model = Ridge(alpha=lam, fit_intercept=True)
            model.fit(x[train_idx], y[train_idx])
            pred = model.predict(x[val_idx])
            fold_rmse.append(mean_squared_error(y[val_idx], pred) ** 0.5)
        rows.append((lam, float(np.mean(fold_rmse))))
    return sorted(rows, key=lambda z: z[1])


def top_overlap(y, pred, fraction=0.1):
    k = max(1, int(np.ceil(len(y) * fraction)))
    true_idx = set(np.argsort(y)[:k].tolist())
    pred_idx = set(np.argsort(pred)[:k].tolist())
    overlap = len(true_idx & pred_idx)
    return k, overlap, overlap / k


def evaluate(y, pred):
    k, overlap, rate = top_overlap(y, pred)
    return {
        "n": int(len(y)),
        "mean_loss": float(np.mean(y)),
        "pred_mean": float(np.mean(pred)),
        "rmse_abs": float(mean_squared_error(y, pred) ** 0.5),
        "mae_abs": float(mean_absolute_error(y, pred)),
        "pearson": float(pearsonr(y, pred).statistic),
        "spearman": float(spearmanr(y, pred).statistic),
        "top10_k": int(k),
        "top10_overlap": int(overlap),
        "top10_overlap_rate": float(rate),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/real_attachments/A_data_value/regmix_tables"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chm"))
    args = parser.parse_args()

    datasets = {}
    audit_rows = []
    for mix_file, loss_file, name in PAIR_FILES:
        item = load_pair(args.data_root, mix_file, loss_file)
        datasets[name] = item
        audit = audit_pair(item[0], item[1], item[3], item[4])
        audit["dataset"] = name
        audit_rows.append(audit)

    x_train = datasets["train_1m"][5]
    y_train = datasets["train_1m"][6]
    lambdas = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1, 10]
    cv = select_lambda(x_train, y_train, lambdas)
    best_lambda = cv[0][0]

    model = Ridge(alpha=best_lambda, fit_intercept=True)
    model.fit(x_train, y_train)

    metrics = []
    for name, item in datasets.items():
        pred = model.predict(item[5])
        row = evaluate(item[6], pred)
        row["dataset"] = name
        metrics.append(row)

    mix_cols = datasets["train_1m"][3]
    coef = pd.DataFrame({
        "domain": [c.replace("train_the_pile_", "") for c in mix_cols],
        "coefficient": model.coef_,
    }).sort_values("coefficient")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(audit_rows).to_csv(args.output_dir / "q1_regmix_pair_audit.csv", index=False)
    pd.DataFrame(metrics).to_csv(args.output_dir / "q1_regmix_baseline_metrics.csv", index=False)
    pd.DataFrame(cv, columns=["lambda", "cv_rmse"]).to_csv(args.output_dir / "q1_regmix_ridge_cv.csv", index=False)
    coef.to_csv(args.output_dir / "q1_regmix_ridge_coefficients.csv", index=False)

    manifest = {
        "model": "ridge_on_mean_13_domain_loss",
        "best_lambda": best_lambda,
        "warning": "Preliminary diagnostic baseline. Cross-scale absolute RMSE mixes scale effects; est_10B/70B losses are estimated, not observations.",
    }
    (args.output_dir / "q1_regmix_baseline_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
