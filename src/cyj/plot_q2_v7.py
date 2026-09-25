"""Plot the published conditional bridge grid without reading source attachments."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "outputs/cyj/q2_v7/bridge_sensitivity.csv"
FIGURE = ROOT / "paper/latex/figures/cyj/q2_v7_bridge_sensitivity.pdf"


def main():
    with GRID.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.25), sharey=False)
    for axis, n in zip(axes, (0.1, 1.0, 10.0)):
        for eta, line in ((0.0, "-"), (0.2, "--"), (0.4, ":")):
            matched = sorted((r for r in rows if r["policy"] == "equal_13"
                              and r["support"] == "continuous_hull"
                              and r["bridge_model"] == "exp_bridge"
                              and float(r["N_params_B"]) == n
                              and float(r["eta"]) == eta and r["status"] == "valid"),
                             key=lambda r: float(r["lambda"]))
            if len(matched) != 6:
                raise ValueError(f"missing sensitivity grid at N={n}, eta={eta}")
            axis.plot([float(r["lambda"]) for r in matched],
                      [float(r["Loss"]) for r in matched], line, marker="o", ms=2.5,
                      label=fr"$\eta={eta:g}$")
        axis.set_title(fr"$N={n:g}$ billion")
        axis.set_xlabel(r"bridge $\lambda$ (assumed)")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Conditional Loss")
    axes[-1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, bbox_inches="tight")
    plt.close(fig)
    return FIGURE


if __name__ == "__main__":
    print(main())
