from pathlib import Path
import argparse
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCALE_ORDER = [
    ("test_1m_spearman", "1M"),
    ("test_60m_spearman", "60M"),
    ("test_1B_spearman", "1B"),
]
N_MAP = {"1M": 1e6, "60M": 60e6, "1B": 1e9}


def summarize_domainwise(df):
    rows = []
    for col, label in SCALE_ORDER:
        x = pd.to_numeric(df[col], errors="coerce").dropna()
        rows.append({
            "scale": label,
            "n_targets": int(len(x)),
            "spearman_mean": float(x.mean()),
            "spearman_median": float(x.median()),
            "spearman_min": float(x.min()),
            "spearman_max": float(x.max()),
            "spearman_q25": float(x.quantile(0.25)),
            "spearman_q75": float(x.quantile(0.75)),
        })
    return pd.DataFrame(rows)


def fig_domainwise_box(df, out):
    vals = [pd.to_numeric(df[c], errors="coerce").dropna().to_numpy() for c, _ in SCALE_ORDER]
    labels = [label for _, label in SCALE_ORDER]
    fig, ax = plt.subplots(figsize=(6.2, 4.3))
    ax.boxplot(vals, tick_labels=labels, showmeans=True)
    ax.set_xlabel("Model scale")
    ax.set_ylabel("Spearman rank correlation")
    ax.set_title("Cross-scale transfer of data-mixture ranking")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)


def fig_domainwise_lines(df, out):
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    x = np.arange(len(SCALE_ORDER))
    for _, row in df.sort_values("test_1B_spearman", ascending=False).iterrows():
        y = [row[c] for c, _ in SCALE_ORDER]
        ax.plot(x, y, marker="o", linewidth=1, alpha=0.65)
    ax.set_xticks(x, [label for _, label in SCALE_ORDER])
    ax.set_xlabel("Model scale")
    ax.set_ylabel("Spearman rank correlation")
    ax.set_title("Domain-specific mixture-ranking transfer")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)


def fig_direct_rank_stability(df, out):
    d = df[df["pair"] == "test_1m_vs_test_60m"].copy()
    d = d.sort_values("spearman", ascending=True)
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    ax.barh(d["target"], d["spearman"])
    ax.set_xlabel("Spearman(1M loss, 60M loss)")
    ax.set_ylabel("Validation target")
    ax.set_title("Direct rank stability on identical 256 mixtures")
    ax.set_xlim(max(0.95, float(d["spearman"].min()) - 0.01), 1.0)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)


def fig_interaction_heatmap(coefficients, out, matrix_out=None):
    meta = {
        "target", "alpha", "cv_rmse", "intercept",
        "test_1m_spearman", "test_1m_pearson", "test_1m_rmse",
        "test_60m_spearman", "test_60m_pearson", "test_60m_rmse",
        "test_1B_spearman", "test_1B_pearson", "test_1B_rmse",
        "est_10B_spearman", "est_10B_pearson", "est_10B_rmse",
        "est_70B_spearman", "est_70B_pearson", "est_70B_rmse",
    }
    domains = [c for c in coefficients.columns if c not in meta]
    raw = coefficients.set_index("target")[domains].astype(float)
    denom = raw.abs().max(axis=1).replace(0, 1.0)
    norm = raw.div(denom, axis=0)
    if matrix_out is not None:
        norm.to_csv(matrix_out)

    fig, ax = plt.subplots(figsize=(12.5, 6.8))
    im = ax.imshow(norm.to_numpy(), aspect="auto", vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(np.arange(len(domains)), domains, rotation=60, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(norm.index)), norm.index, fontsize=8)
    ax.set_xlabel("Training domain")
    ax.set_ylabel("Validation target")
    ax.set_title("Row-normalized 13 x 17 Ridge interaction matrix")
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label(r"$\tilde{B}_{k,j}=\beta_{k,j}/\max_r|\beta_{k,r}|$")
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)


def top_targets(df):
    cols = ["target"] + [c for c, _ in SCALE_ORDER]
    out = df[cols].copy()
    out["min_heldout_spearman"] = out[[c for c, _ in SCALE_ORDER]].min(axis=1)
    out["mean_heldout_spearman"] = out[[c for c, _ in SCALE_ORDER]].mean(axis=1)
    return out.sort_values(
        ["min_heldout_spearman", "mean_heldout_spearman"],
        ascending=False,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("data/processed/Q1/regmix"))
    parser.add_argument("--figure-dir", type=Path, default=Path("paper/latex/figures/Q1"))
    args = parser.parse_args()

    metrics = pd.read_csv(args.output_root / "q1_regmix_ridge_domainwise_metrics.csv")
    direct = pd.read_csv(args.output_root / "q1_regmix_direct_scale_rank_stability.csv")

    args.figure_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)

    summarize_domainwise(metrics).to_csv(
        args.output_root / "q1_regmix_scale_summary.csv", index=False
    )
    top_targets(metrics).to_csv(
        args.output_root / "q1_regmix_target_robustness.csv", index=False
    )

    fig_domainwise_box(
        metrics,
        args.figure_dir / "q1_domainwise_spearman_box.png",
    )
    fig_direct_rank_stability(
        direct,
        args.figure_dir / "q1_direct_rank_stability_1m_60m.png",
    )

    inputs = [
        args.output_root / "q1_regmix_ridge_domainwise_metrics.csv",
        args.output_root / "q1_regmix_direct_scale_rank_stability.csv",
    ]
    figure_paths = [
        args.figure_dir / "q1_domainwise_spearman_box.png",
        args.figure_dir / "q1_direct_rank_stability_1m_60m.png",
    ]
    provenance = {
        "output_root": str(args.output_root),
        "input_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs
        },
        "figures": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in figure_paths
        },
        "warning": (
            "Figures are valid only for the recorded local_recheck_v1 input hashes. "
            "The interaction heatmap is row-normalized for visualization only; "
            "it is not an additional fitted model or causal matrix."
        ),
    }
    (args.output_root / "q1_figures_manifest.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
