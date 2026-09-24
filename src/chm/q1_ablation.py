"""Compact Q1 ablations using validated quality scores and paired RegMix tables."""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge

from q1_regmix_domainwise import load_pair, metric_name, normalize_composition


def quality_ablation(root):
    grid = pd.read_csv(root / "quality_review_v1/quality_family_weight_grid_v1.csv")
    primary = pd.read_csv(root / "domain_quality.csv").query("dataset_scope == 'sample'")
    primary = primary.set_index("quality_domain")["Q"].rank(ascending=False)
    rows = []
    for removed in ("rps", "dsir", "model"):
        weights = {f"w_{name}": 0.0 if name == removed else 0.5
                   for name in ("rps", "dsir", "model")}
        chosen = grid.loc[np.logical_and.reduce([
            np.isclose(grid[key], value) for key, value in weights.items()
        ])].set_index("quality_domain")
        if len(chosen) != len(primary):
            raise ValueError(f"Incomplete {removed} ablation in quality grid")
        rank = chosen.loc[primary.index, "rank_high_is_good"]
        rows.append({"removed_family": removed,
                     "rank_spearman_vs_primary": float(spearmanr(primary, rank).statistic),
                     "changed_rank_domains": int((primary != rank).sum()),
                     "top_domain": str(rank.idxmin()), "bottom_domain": str(rank.idxmax())})
    return pd.DataFrame(rows)


def mixture_ablation(data_root, output_root):
    train = load_pair(data_root, "train_mixture_1m.csv", "train_pile_loss_1m.csv")
    mix_cols, loss_cols = train[3], train[4]
    x_train = normalize_composition(train[0], mix_cols)
    fitted = pd.read_csv(output_root / "q1_regmix_ridge_domainwise_metrics.csv").set_index("target")
    rows = []
    for mix_file, loss_file, split in (
        ("test_mixture_1m.csv", "test_pile_loss_1m.csv", "test_1m"),
        ("test_mixture_60m.csv", "test_pile_loss_60m.csv", "test_60m"),
        ("test_mixture_1B.csv", "test_pile_loss_1B.csv", "test_1B"),
    ):
        test = load_pair(data_root, mix_file, loss_file)
        x_test = normalize_composition(test[0], mix_cols)
        for col in loss_cols:
            target = metric_name(col)
            y_train = train[2][col].to_numpy(float)
            y_test = test[2][col].to_numpy(float)
            model = Ridge(alpha=float(fitted.loc[target, "alpha"])).fit(x_train, y_train)
            pred = model.predict(x_test)
            full_rmse = float(np.sqrt(np.mean((pred - y_test) ** 2)))
            saved_rmse = float(fitted.loc[target, f"{split}_rmse"])
            if not np.isclose(full_rmse, saved_rmse, rtol=1e-8, atol=1e-8):
                raise ValueError(f"Full-model reproduction mismatch: {target}, {split}")
            mean_rmse = float(np.sqrt(np.mean((y_train.mean() - y_test) ** 2)))
            rows.append({"target": target, "split": split,
                         "full_rmse": full_rmse, "no_mixture_rmse": mean_rmse,
                         "rmse_gain": mean_rmse - full_rmse,
                         "full_spearman": float(spearmanr(y_test, pred).statistic)})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data/raw/real_attachments/A_data_value/regmix_tables"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/chm"))
    args = parser.parse_args()
    out = args.output_root / "ablation_v1"
    out.mkdir(parents=True, exist_ok=True)
    quality_ablation(args.output_root).to_csv(out / "quality_family_ablation.csv", index=False)
    detail = mixture_ablation(args.data_root, args.output_root / "local_recheck_v1")
    detail.to_csv(out / "mixture_feature_ablation.csv", index=False)
    summary = detail.groupby("split", sort=False).agg(
        targets=("target", "size"), median_full_rmse=("full_rmse", "median"),
        median_no_mixture_rmse=("no_mixture_rmse", "median"),
        improved_targets=("rmse_gain", lambda x: int((x > 0).sum())),
        median_full_spearman=("full_spearman", "median"),
    )
    summary.to_csv(out / "mixture_ablation_summary.csv")
    inputs = [args.output_root / "quality_review_v1/quality_family_weight_grid_v1.csv",
              args.output_root / "domain_quality.csv",
              args.output_root / "local_recheck_v1/q1_regmix_ridge_domainwise_metrics.csv"]
    inputs += [args.data_root / name for name in (
        "train_mixture_1m.csv", "train_pile_loss_1m.csv",
        "test_mixture_1m.csv", "test_pile_loss_1m.csv",
        "test_mixture_60m.csv", "test_pile_loss_60m.csv",
        "test_mixture_1B.csv", "test_pile_loss_1B.csv")]
    manifest = {"input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                "warning": "1B RMSE compares uncalibrated 1M-trained predictions; family removal compares ranks, not Q scales."}
    (out / "ablation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
