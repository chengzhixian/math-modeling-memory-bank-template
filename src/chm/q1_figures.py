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


def fit_target_intercept(logn, logb, eta):
    # log b = c - eta log(N/1e6)
    x = logn
    return float(np.mean(logb + eta * x))


def fig_scale_decay(cal, eta, out):
    scales = np.array([1e6, 60e6, 1e9], dtype=float)
    labels = ["b_1M", "b_60M", "b_1B"]
    x = np.log10(scales)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for _, row in cal.iterrows():
        y = np.array([row[c] for c in labels], dtype=float)
        ax.plot(scales, y, marker="o", linewidth=1, alpha=0.55)

    # Show a representative pooled-decay curve normalized to the median 1M amplitude.
    b1 = float(pd.to_numeric(cal["b_1M"], errors="coerce").median())
    grid = np.logspace(6, 9, 120)
    pooled = b1 * (grid / 1e6) ** (-eta)
    ax.plot(grid, pooled, linewidth=2.5, label=f"Pooled decay: eta={eta:.3f}")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Parameter scale N")
    ax.set_ylabel("Mixture-effect amplitude b_k(N)")
    ax.set_title("Empirical attenuation of mixture effect with model scale")
    ax.grid(alpha=0.25)
    ax.legend()
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
    parser.add_argument("--output-root", type=Path, default=Path("outputs/chm/local_recheck_v1"))
    parser.add_argument("--figure-dir", type=Path, default=Path("paper/sections/chm/figures"))
    args = parser.parse_args()

    metrics = pd.read_csv(args.output_root / "q1_regmix_ridge_domainwise_metrics.csv")
    direct = pd.read_csv(args.output_root / "q1_regmix_direct_scale_rank_stability.csv")
    cal = pd.read_csv(args.output_root / "mixture_scale_calibration_v0.csv")

    manifest_path = args.output_root / "mixture_scale_transfer_v0_manifest.json"
    import json
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    eta = float(manifest["pooled_eta"])

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
    fig_domainwise_lines(
        metrics,
        args.figure_dir / "q1_domainwise_spearman_lines.png",
    )
    fig_direct_rank_stability(
        direct,
        args.figure_dir / "q1_direct_rank_stability_1m_60m.png",
    )
    fig_scale_decay(
        cal,
        eta,
        args.figure_dir / "q1_mixture_effect_scale_decay.png",
    )

    inputs = [
        args.output_root / "q1_regmix_ridge_domainwise_metrics.csv",
        args.output_root / "q1_regmix_direct_scale_rank_stability.csv",
        args.output_root / "mixture_scale_calibration_v0.csv",
        args.output_root / "mixture_scale_transfer_v0_manifest.json",
    ]
    figure_paths = [
        args.figure_dir / "q1_domainwise_spearman_box.png",
        args.figure_dir / "q1_domainwise_spearman_lines.png",
        args.figure_dir / "q1_direct_rank_stability_1m_60m.png",
        args.figure_dir / "q1_mixture_effect_scale_decay.png",
    ]
    provenance = {
        "output_root": str(args.output_root),
        "input_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs
        },
        "figures": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in figure_paths
        },
        "warning": "Figures are valid only for the recorded local_recheck_v1 input hashes.",
    }
    (args.figure_dir / "q1_figures_manifest.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
