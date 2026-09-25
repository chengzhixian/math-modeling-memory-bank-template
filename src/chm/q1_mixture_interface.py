from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold

RIDGE_GRID = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1000.0]
PAIR_FILES = [
    ("train_mixture_1m.csv", "train_pile_loss_1m.csv", "train_1m"),
    ("test_mixture_1m.csv", "test_pile_loss_1m.csv", "test_1m"),
    ("test_mixture_60m.csv", "test_pile_loss_60m.csv", "test_60m"),
    ("test_mixture_1B.csv", "test_pile_loss_1B.csv", "test_1B"),
    ("est_mixture_10b.csv", "est_pile_loss_10b.csv", "est_10B"),
    ("est_mixture_70b.csv", "est_pile_loss_70b.csv", "est_70B"),
]


def target_name(col):
    return col.replace("metric/the_pile_", "").replace("_val_loss", "")


def normalize_composition(df, cols):
    x = df[cols].to_numpy(float)
    s = x.sum(axis=1, keepdims=True)
    if np.any(s <= 0):
        raise ValueError("Found a non-positive mixture row sum.")
    return x / s


def load_pair(root, mf, lf):
    m = pd.read_csv(root / mf)
    l = pd.read_csv(root / lf)
    merged = m.merge(l, on="index", how="inner", validate="one_to_one")
    mix_cols = [c for c in m.columns if c != "index"]
    loss_cols = [c for c in l.columns if c != "index"]
    return m, l, merged, mix_cols, loss_cols


def select_alpha(x, y):
    kf = KFold(n_splits=5, shuffle=False)
    rows = []
    for alpha in RIDGE_GRID:
        scores = []
        for tr, va in kf.split(x):
            model = Ridge(alpha=alpha).fit(x[tr], y[tr])
            pred = model.predict(x[va])
            scores.append(mean_squared_error(y[va], pred) ** 0.5)
        rows.append((alpha, float(np.mean(scores))))
    rows.sort(key=lambda z: z[1])
    return rows[0], rows


def canonicalize_simplex_ridge(model):
    # On the normalized simplex sum(p)=1, adding c to all beta_j and
    # subtracting c from the intercept leaves predictions unchanged.
    # Choose the unique zero-mean contrast representation.
    shift = float(np.mean(model.coef_))
    intercept = float(model.intercept_ + shift)
    coef = np.asarray(model.coef_, dtype=float) - shift
    return intercept, coef


def evaluate(y, pred):
    return {
        "spearman": float(spearmanr(y, pred).statistic),
        "pearson": float(pearsonr(y, pred).statistic),
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data/raw/real_attachments/A_data_value/regmix_tables"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chm/local_recheck_v1"))
    args = parser.parse_args()

    datasets = {}
    for mf, lf, name in PAIR_FILES:
        datasets[name] = load_pair(args.data_root, mf, lf)

    train = datasets["train_1m"]
    mix_cols = train[3]
    loss_cols = train[4]
    x_train = normalize_composition(train[0], mix_cols)

    param_rows = []
    cv_rows = []
    for loss_col in loss_cols:
        y_train = train[2][loss_col].to_numpy(float)
        (alpha, cv_rmse), grid = select_alpha(x_train, y_train)
        model = Ridge(alpha=alpha).fit(x_train, y_train)
        intercept, coef = canonicalize_simplex_ridge(model)

        row = {
            "target": target_name(loss_col),
            "alpha": alpha,
            "cv_rmse": cv_rmse,
            "intercept": intercept,
        }
        for c, beta in zip(mix_cols, coef):
            row[c.replace("train_the_pile_", "")] = float(beta)

        # Evaluate the canonical predictor; do not tune on these held-out sets.
        for name, item in datasets.items():
            if name == "train_1m":
                continue
            x = normalize_composition(item[0], mix_cols)
            y = item[2][loss_col].to_numpy(float)
            pred = intercept + x @ coef
            metrics = evaluate(y, pred)
            for k, v in metrics.items():
                row[f"{name}_{k}"] = v

        if abs(float(np.sum(coef))) > 1e-10:
            raise AssertionError("Canonical coefficients do not sum to zero.")
        param_rows.append(row)
        for a, score in grid:
            cv_rows.append({
                "target": target_name(loss_col),
                "alpha": a,
                "cv_rmse": score,
            })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(param_rows).to_csv(
        args.output_dir / "mixture_effect_ridge_v0.csv", index=False
    )
    pd.DataFrame(cv_rows).to_csv(
        args.output_dir / "mixture_effect_ridge_v0_cv.csv", index=False
    )

    manifest = {
        "interface": "mixture_effect_ridge_v0",
        "status": "draft_verified_ridge",
        "training": "A4+A5 only",
        "validation": ["A6+A7", "A8+A9", "A10+A11"],
        "extrapolation_only": ["A12+A13", "A14+A15"],
        "preprocessing": "renormalize every 17-domain composition to exact sum 1",
        "parameterization": "zero-mean coefficient contrasts on the simplex",
        "prediction": "loss_hat = intercept + p_normalized @ beta",
        "coefficient_interpretation": "relative contrast, not causal effect",
        "primary_metric": "Spearman rank correlation",
        "warning": "Do not aggregate raw 13-domain losses into one training target.",
    }
    (args.output_dir / "mixture_effect_ridge_v0_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
