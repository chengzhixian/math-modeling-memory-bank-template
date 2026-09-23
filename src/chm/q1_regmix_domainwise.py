from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold

PAIR_FILES = [
    ("train_mixture_1m.csv", "train_pile_loss_1m.csv", "train_1m"),
    ("test_mixture_1m.csv", "test_pile_loss_1m.csv", "test_1m"),
    ("test_mixture_60m.csv", "test_pile_loss_60m.csv", "test_60m"),
    ("test_mixture_1B.csv", "test_pile_loss_1B.csv", "test_1B"),
    ("est_mixture_10b.csv", "est_pile_loss_10b.csv", "est_10B"),
    ("est_mixture_70b.csv", "est_pile_loss_70b.csv", "est_70B"),
]
RIDGE_GRID = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1000.0]
SEED = 20260923


def load_pair(root, mixture_file, loss_file):
    m = pd.read_csv(root / mixture_file)
    l = pd.read_csv(root / loss_file)
    merged = m.merge(l, on="index", validate="one_to_one")
    mix_cols = [c for c in m.columns if c != "index"]
    loss_cols = [c for c in l.columns if c != "index"]
    return m, l, merged, mix_cols, loss_cols


def metric_name(col):
    return col.replace("metric/the_pile_", "").replace("_val_loss", "")


def normalize_composition(df, mix_cols):
    x = df[mix_cols].to_numpy(float)
    row_sum = x.sum(axis=1, keepdims=True)
    if np.any(row_sum <= 0):
        raise ValueError("Found non-positive mixture row sum.")
    return x / row_sum


def cv_ridge(x, y):
    kf = KFold(n_splits=5, shuffle=False)
    rows = []
    for alpha in RIDGE_GRID:
        rmses = []
        for tr, va in kf.split(x):
            model = Ridge(alpha=alpha)
            model.fit(x[tr], y[tr])
            pred = model.predict(x[va])
            rmses.append(mean_squared_error(y[va], pred) ** 0.5)
        rows.append((alpha, float(np.mean(rmses))))
    rows.sort(key=lambda z: z[1])
    model = Ridge(alpha=rows[0][0]).fit(x, y)
    return model, rows


def eval_regression(y, pred):
    return {
        "spearman": float(spearmanr(y, pred).statistic),
        "pearson": float(pearsonr(y, pred).statistic),
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
    }


def composition_key(df, mix_cols):
    return df[mix_cols].round(6).astype(str).agg("|".join, axis=1)


def paired_scale_corr(a, b, loss_cols):
    rows = []
    b2 = b.set_index("index")
    for c in loss_cols:
        aa = a.set_index("index")[c]
        bb = b2[c]
        idx = aa.index.intersection(bb.index)
        rows.append({
            "target": metric_name(c),
            "spearman": float(spearmanr(aa.loc[idx], bb.loc[idx]).statistic),
            "pearson": float(pearsonr(aa.loc[idx], bb.loc[idx]).statistic),
            "n": int(len(idx)),
        })
    return pd.DataFrame(rows)


def try_lightgbm():
    try:
        from lightgbm import LGBMRegressor
    except ImportError:
        return None
    return LGBMRegressor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/real_attachments/A_data_value/regmix_tables"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chm/local_recheck_v1"))
    parser.add_argument("--run-lightgbm", action="store_true")
    args = parser.parse_args()

    datasets = {}
    for mf, lf, name in PAIR_FILES:
        datasets[name] = load_pair(args.data_root, mf, lf)

    train = datasets["train_1m"]
    mix_cols, loss_cols = train[3], train[4]
    x_train = normalize_composition(train[0], mix_cols)

    ridge_rows = []
    cv_rows = []
    for target in loss_cols:
        y_train = train[2][target].to_numpy(float)
        model, cv = cv_ridge(x_train, y_train)
        for alpha, cv_rmse in cv:
            cv_rows.append({"target": metric_name(target), "alpha": alpha, "cv_rmse": cv_rmse})
        row = {"target": metric_name(target), "alpha": model.alpha}
        for name, item in datasets.items():
            if name == "train_1m":
                continue
            x = normalize_composition(item[0], mix_cols)
            y = item[2][target].to_numpy(float)
            met = eval_regression(y, model.predict(x))
            for k, v in met.items():
                row[f"{name}_{k}"] = v
        ridge_rows.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(ridge_rows).to_csv(args.output_dir / "q1_regmix_ridge_domainwise_metrics.csv", index=False)
    pd.DataFrame(cv_rows).to_csv(args.output_dir / "q1_regmix_ridge_domainwise_cv.csv", index=False)

    # Exact mixture overlap checks.
    overlap_rows = []
    names = ["train_1m", "test_1m", "test_60m", "test_1B", "est_10B", "est_70B"]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ka = set(composition_key(datasets[a][0], mix_cols))
            kb = set(composition_key(datasets[b][0], mix_cols))
            overlap_rows.append({"left": a, "right": b, "exact_composition_overlap": len(ka & kb)})
    pd.DataFrame(overlap_rows).to_csv(args.output_dir / "q1_regmix_composition_overlap.csv", index=False)

    # Direct paired-loss scale correlations for the two identical-mixture pairs.
    p1 = paired_scale_corr(datasets["test_1m"][2], datasets["test_60m"][2], loss_cols)
    p1["pair"] = "test_1m_vs_test_60m"
    p2 = paired_scale_corr(datasets["est_10B"][2], datasets["est_70B"][2], loss_cols)
    p2["pair"] = "est_10B_vs_est_70B"
    pd.concat([p1, p2], ignore_index=True).to_csv(
        args.output_dir / "q1_regmix_direct_scale_rank_stability.csv", index=False
    )

    manifest = {
        "seed": SEED,
        "ridge_grid": RIDGE_GRID,
        "training_split": "A4+A5 only",
        "validation_splits": ["A6+A7", "A8+A9", "A10+A11"],
        "extrapolation_only": ["A12+A13", "A14+A15"],
        "primary_metric": "Spearman rank correlation",
        "note": "Domain-wise modeling. Normalize each mixture row to the simplex; do not aggregate raw losses before fitting.",
        "ridge_grid_source": "RegMix Appendix E: [1e-3,1e-2,1e-1,1e0,1e1,1e2,1e3]",
    }

    if args.run_lightgbm:
        LGBMRegressor = try_lightgbm()
        if LGBMRegressor is None:
            raise RuntimeError("lightgbm is not installed; install it before --run-lightgbm")
        # RegMix Appendix E: 1000 iterations, learning_rate=1e-2, other
        # hyperparameters left at LightGBM defaults. Held-out A6-A11 are not used
        # for tuning.
        lgb_rows = []
        for target in loss_cols:
            y_train = train[2][target].to_numpy(float)
            m = LGBMRegressor(
                n_estimators=1000,
                learning_rate=1e-2,
                random_state=SEED,
                verbosity=-1,
            ).fit(x_train, y_train)
            row = {"target": metric_name(target)}
            for name, item in datasets.items():
                if name == "train_1m":
                    continue
                x = normalize_composition(item[0], mix_cols)
                y = item[2][target].to_numpy(float)
                met = eval_regression(y, m.predict(x))
                for k, v in met.items():
                    row[f"{name}_{k}"] = v
            lgb_rows.append(row)
        pd.DataFrame(lgb_rows).to_csv(
            args.output_dir / "q1_regmix_lightgbm_domainwise_metrics.csv",
            index=False,
        )
        manifest["lightgbm"] = {
            "status": "completed",
            "n_estimators": 1000,
            "learning_rate": 1e-2,
            "other_hyperparameters": "LightGBM defaults, matching RegMix Appendix E",
        }

    (args.output_dir / "q1_regmix_domainwise_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
