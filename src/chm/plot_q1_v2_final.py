"""Publication figures for the frozen Q1 v2 paper."""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "paper/latex/figures/chm"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    observed = rows(ROOT / "outputs/chm/q1_v2/targetwise_validation.csv")
    estimated = rows(ROOT / "outputs/chm/q1_v2_estimated_stress/targetwise.csv")
    groups = [
        ("1M", [float(r["interaction_spearman"]) for r in observed if r["scope"] == "test_1m" and r["support_group"] == "all"]),
        ("60M", [float(r["interaction_spearman"]) for r in observed if r["scope"] == "test_60m" and r["support_group"] == "all"]),
        ("1B", [float(r["interaction_spearman"]) for r in observed if r["scope"] == "test_1B" and r["support_group"] == "all"]),
        ("10B est.", [float(r["v2_spearman"]) for r in estimated if r["scope"] == "est_10B"]),
        ("70B est.", [float(r["v2_spearman"]) for r in estimated if r["scope"] == "est_70B"]),
    ]
    assert all(len(v) == 13 for _, v in groups)
    fig, ax = plt.subplots(figsize=(7.2, 3.5), constrained_layout=True)
    bp = ax.boxplot([v for _, v in groups], patch_artist=True, widths=.55,
                    medianprops={"color": "#1f2937", "linewidth": 1.5},
                    whiskerprops={"color": "#64748b"}, capprops={"color": "#64748b"},
                    flierprops={"marker": "o", "markersize": 3, "alpha": .55})
    for patch, color in zip(bp["boxes"], ["#3b82a0"]*3 + ["#b9a57a"]*2):
        patch.set_facecolor(color)
        patch.set_alpha(.75)
    ax.axvline(3.5, color="#94a3b8", linestyle="--", linewidth=1)
    ax.set_xticks(np.arange(1, 6), [g[0] for g in groups])
    ax.set_ylabel("Spearman correlation across 13 targets")
    ax.set_ylim(-.1, 1.05)
    ax.grid(axis="y", alpha=.2)
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "q1_v2_rank_stress.png", dpi=300)
    plt.close(fig)

    bounds = json.loads((ROOT / "outputs/chm/q1_v2_hull_bounds/bounds.json").read_text(encoding="utf-8"))
    assert len(bounds) == 4
    labels = ["Equal", "Direct Q", "Direct+near Q", "Minimax"]
    gaps = [1000*row["absolute_gap_relative"] for row in bounds]
    fig, ax = plt.subplots(figsize=(7.2, 2.9), constrained_layout=True)
    bars = ax.barh(labels[::-1], gaps[::-1], color=["#3b82a0", "#3b82a0", "#3b82a0", "#64748b"][::-1])
    ax.axvline(1, color="#9f3a38", linestyle="--", linewidth=1, label="Tolerance = 0.001")
    ax.set_xlim(0, 1.16)
    ax.set_xlabel("Numerical upper-lower gap (× 0.001)")
    for bar, gap in zip(bars, gaps[::-1]):
        ax.text(gap + .02, bar.get_y() + bar.get_height()/2, f"{gap:.3f}",
                va="center", fontsize=8)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.grid(axis="x", alpha=.16)
    fig.savefig(FIG / "q1_v2_bound_gaps.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
