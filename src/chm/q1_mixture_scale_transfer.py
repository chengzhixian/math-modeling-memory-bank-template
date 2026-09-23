from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold

SEED = 20260923
RIDGE_GRID = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 1000.0]
OBSERVED_SCALES = {
    "test_1m": 1e6,
    "test_60m": 60e6,
    "test_1B": 1e9,
}
PAIR_FILES = [
    ("train_mixture_1m.csv", "train_pile_loss_1m.csv", "train_1m"),
    ("test_mixture_1m.csv", "test_pile_loss_1m.csv", "test_1m"),
    ("test_mixture_60m.csv", "test_pile_loss_60m.csv", "test_60m"),
    ("test_mixture_1B.csv", "test_pile_loss_1B.csv", "test_1B"),
    ("est_mixture_10b.csv", "est_pile_loss_10b.csv", "est_10B"),
    ("est_mixture_70b.csv", "est_pile_loss_70b.csv", "est_70B"),
]


def load_pair(root, mf, lf):
    mix = pd.read_csv(root / mf)
    loss = pd.read_csv(root / lf)
    merged = mix.merge(loss, on="index", how="inner", validate="one_to_one")
    mix_cols = [c for c in mix.columns if c != "index"]
    loss_cols = [c for c in loss.columns if c != "index"]
    return mix, loss, merged, mix_cols, loss_cols


def normalize_mix(df, cols):
    x = df[cols].to_numpy(float)
    row_sum = x.sum(axis=1, keepdims=True)
    if np.any(row_sum <= 0):
        raise ValueError("Found non-positive composition row sum.")
    return x / row_sum


def target_name(col):
    return col.replace("metric/the_pile_", "").replace("_val_loss", "")


def select_alpha(x, y):
    kf = KFold(n_splits=5, shuffle=False)
    best = None
    for alpha in RIDGE_GRID:
        rmses = []
        for tr, va in kf.split(x):
            model = Ridge(alpha=alpha).fit(x[tr], y[tr])
            pred = model.predict(x[va])
            rmses.append(mean_squared_error(y[va], pred) ** 0.5)
        score = float(np.mean(rmses))
        if best is None or score < best[1]:
            best = (alpha, score)
    return best


def ols_calibration(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xm = float(x.mean())
    ym = float(y.mean())
    sxx = float(np.sum((x - xm) ** 2))
    if sxx <= 0:
        raise ValueError("Degenerate calibration predictor.")
    slope = float(np.sum((x - xm) * (y - ym)) / sxx)
    intercept = ym - slope * xm
    pred = intercept + slope * x
    rmse = float(mean_squared_error(y, pred) ** 0.5)
    r = float(np.corrcoef(x, y)[0, 1])
    return intercept, slope, r, rmse


def domain_eta(log_n, slopes):
    y = np.log(np.asarray(slopes, dtype=float))
    x = np.asarray(log_n, dtype=float)
    slope = float(np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2))
    return -slope


def pooled_fixed_effect_eta(calibration):
    x = np.log(np.asarray(list(OBSERVED_SCALES.values()), dtype=float) / 1e6)
    x_center = x - x.mean()
    xs = []
    ys = []
    for row in calibration:
        y = np.log(np.array([
            row["b_1M"], row["b_60M"], row["b_1B"]
        ], dtype=float))
        xs.extend(x_center)
        ys.extend(y - y.mean())
    xs = np.asarray(xs)
    ys = np.asarray(ys)
    slope = float(np.dot(xs, ys) / np.dot(xs, xs))
    eta = -slope

    ss_res = 0.0
    ss_tot = 0.0
    for row in calibration:
        y = np.log(np.array([row["b_1M"], row["b_60M"], row["b_1B"]], dtype=float))
        c = float(y.mean() - slope * x.mean())
        pred = c + slope * x
        ss_res += float(np.sum((y - pred) ** 2))
        ss_tot += float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    return eta, r2


def bootstrap_eta(calibration, reps=10000):
    rng = np.random.default_rng(SEED)
    vals = np.empty(reps, dtype=float)
    for i in range(reps):
        idx = rng.integers(0, len(calibration), size=len(calibration))
        sampled = [calibration[j] for j in idx]
        vals[i] = pooled_fixed_effect_eta(sampled)[0]
    return np.quantile(vals, [0.025, 0.5, 0.975])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data/raw/real_attachments/A_data_value/regmix_tables"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/chm/local_recheck_v1"))
    parser.add_argument("--bootstrap", type=int, default=10000)
    args = parser.parse_args()

    datasets = {}
    for mf, lf, name in PAIR_FILES:
        datasets[name] = load_pair(args.data_root, mf, lf)

    train = datasets["train_1m"]
    mix_cols = train[3]
    loss_cols = train[4]
    x_train = normalize_mix(train[0], mix_cols)
    p_ref = x_train.mean(axis=0)

    calibration = []
    for loss_col in loss_cols:
        y_train = train[2][loss_col].to_numpy(float)
        alpha, cv_rmse = select_alpha(x_train, y_train)
        surrogate = Ridge(alpha=alpha).fit(x_train, y_train)

        row = {
            "target": target_name(loss_col),
            "alpha": alpha,
            "cv_rmse": cv_rmse,
        }
        slopes = []
        for dataset_name, n_params in OBSERVED_SCALES.items():
            item = datasets[dataset_name]
            x = normalize_mix(item[0], mix_cols)
            y = item[2][loss_col].to_numpy(float)
            s = surrogate.predict(x)
            a, b, r, rmse = ols_calibration(s, y)
            label = {"test_1m": "1M", "test_60m": "60M", "test_1B": "1B"}[dataset_name]
            row[f"a_{label}"] = a
            row[f"b_{label}"] = b
            row[f"pearson_{label}"] = r
            row[f"rmse_{label}"] = rmse
            slopes.append(b)

        if any(b <= 0 for b in slopes):
            row["eta_domain"] = np.nan
        else:
            row["eta_domain"] = domain_eta(
                np.log(np.asarray(list(OBSERVED_SCALES.values()), dtype=float) / 1e6),
                slopes,
            )
        calibration.append(row)

    valid = [r for r in calibration if np.isfinite(r["eta_domain"])]
    if len(valid) != len(calibration):
        raise ValueError("At least one target has non-positive scale-calibration slope.")

    pooled_eta, within_r2 = pooled_fixed_effect_eta(valid)
    ci = bootstrap_eta(valid, reps=args.bootstrap)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(calibration).to_csv(
        args.output_dir / "mixture_scale_calibration_v0.csv", index=False
    )
    pd.DataFrame({
        "mixture_domain": [c.replace("train_the_pile_", "") for c in mix_cols],
        "p_ref": p_ref,
    }).to_csv(args.output_dir / "mixture_reference_v0.csv", index=False)

    manifest = {
        "interface": "mixture_scale_transfer_v0",
        "status": "draft_post_validation_calibration",
        "observed_scales_N": list(OBSERVED_SCALES.values()),
        "pooled_decay_model": "log b_k(N) = c_k - eta log(N/1e6)",
        "pooled_eta": pooled_eta,
        "pooled_eta_bootstrap_95": [float(ci[0]), float(ci[2])],
        "pooled_eta_bootstrap_median": float(ci[1]),
        "bootstrap_unit": "target domain",
        "bootstrap_reps": args.bootstrap,
        "seed": SEED,
        "within_domain_log_slope_R2": within_r2,
        "eta_domain_min": float(min(r["eta_domain"] for r in valid)),
        "eta_domain_max": float(max(r["eta_domain"] for r in valid)),
        "reference_composition": "mean normalized A4 training composition",
        "centered_effect": "m_k(p)=beta_k dot (p-p_ref)",
        "extrapolation_policy": "A12-A15 not used to fit eta",
        "warning": "Only three observed model scales; empirical transfer correction, not a universal scaling law.",
    }
    (args.output_dir / "mixture_scale_transfer_v0_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
