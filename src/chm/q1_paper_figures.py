"""Regenerate the two compact Q1 figures from committed summary tables."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper/sections/chm/figures"
BLUE, ORANGE, GREY = "#245A81", "#D47B3D", "#637381"


def style():
    plt.rcParams.update({
        "figure.dpi": 160,
        "savefig.dpi": 240,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#A5AFB8",
        "axes.labelcolor": "#243746",
        "xtick.color": "#243746",
        "ytick.color": "#243746",
    })


def quality_figure():
    data = pd.read_csv(ROOT / "outputs/chm/domain_quality_v0.csv")
    data = data[data.dataset_scope.eq("sample")].sort_values("Q_z_median")
    y = np.arange(len(data))
    med = data.Q_z_median.to_numpy()
    err = np.vstack((med - data.Q_ci_low.to_numpy(), data.Q_ci_high.to_numpy() - med))
    fig, ax = plt.subplots(figsize=(8.0, 4.2), constrained_layout=True)
    ax.axvline(0, color="#B9C4CC", lw=1)
    ax.errorbar(med, y, xerr=err, fmt="o", color=BLUE, ecolor=BLUE,
                capsize=3, markersize=7, lw=1.4)
    ax.set_yticks(y, data.quality_domain)
    ax.set_xlabel("Derived quality score Qz (A1 standardized units)")
    ax.set_title("Seven-domain quality ranking", loc="left", weight="bold")
    ax.grid(axis="x", color="#E7ECF0", zorder=0)
    ax.set_axisbelow(True)
    fig.savefig(OUT / "q1_quality_domain_intervals.png", bbox_inches="tight")
    plt.close(fig)


def ablation_figure():
    data = pd.read_csv(ROOT / "outputs/chm/ablation_v1/mixture_ablation_summary.csv")
    labels = ["1M", "60M", "1B"]
    x = np.arange(3)
    improvement = 100 * (data.median_no_mixture_rmse - data.median_full_rmse) / data.median_no_mixture_rmse
    fig, ax = plt.subplots(figsize=(7.4, 3.8), constrained_layout=True)
    bars = ax.bar(x, improvement, width=.52, color=[BLUE, BLUE, ORANGE], zorder=3)
    for bar, n in zip(bars, data.improved_targets):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + .7,
                f"{int(n)}/13 targets", ha="center", va="bottom", fontsize=9, color=GREY)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Median RMSE reduction vs. no-mixture baseline (%)")
    ax.set_title("Mixture information: stronger at observed small scales", loc="left", weight="bold")
    ax.set_ylim(0, max(36, improvement.max() + 6))
    ax.grid(axis="y", color="#E7ECF0", zorder=0)
    fig.savefig(OUT / "q1_mixture_ablation.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    style()
    quality_figure()
    ablation_figure()
