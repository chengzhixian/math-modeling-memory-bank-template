"""Paper figure for the conditional v8 budget and recipe transition."""
from __future__ import annotations

import csv
import os
from pathlib import Path

_cache = Path(__file__).resolve().parents[2] / "data/processed/Q3/matplotlib"
_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from q3_conditional_v8 import OUTPUT, ROOT


FIGURE = ROOT / "paper/latex/figures/Q3/q3_v8_power_8192.png"


def read(name):
    with (OUTPUT/name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    joint = [r for r in read("observed_budget_scan.csv") if r["context_tokens"] == "8192"
             and r["quality_family"] == "power" and r["status"] == "conditional_v8_fixed_policy_feasible"]
    fixed = [r for r in read("fixed_budget_scan.csv") if r["context_tokens"] == "8192"
             and r["quality_family"] == "power" and r["status"] == "conditional_v8_fixed_policy_feasible"]
    switches = [r for r in read("transitions.csv") if r["scenario"] == "observed_joint"
                and r["context_tokens"] == "8192" and r["quality_family"] == "power"
                and r["state_left"].startswith("recipe=477;")
                and r["state_right"].startswith("recipe=172;")]
    if len(joint) < 3 or len(fixed) < 3 or len(switches) != 1:
        raise ValueError("missing v8 paper figure evidence")
    change = (float(switches[0]["budget_left"])*float(switches[0]["budget_right"]))**0.5
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(7.2, 5.1), sharex=True,
                                       gridspec_kw={"height_ratios": [2.3, 1]})
    top.plot([float(r["budget_FLOPs"]) for r in joint],
             [float(r["conditional_bridge_loss"]) for r in joint], color="#155e75",
             lw=2.0, label="Best of 87 observed recipes")
    top.plot([float(r["budget_FLOPs"]) for r in fixed],
             [float(r["conditional_bridge_loss"]) for r in fixed], color="#a16207",
             lw=1.5, ls="--", label="Fixed Q2 recipe 172")
    top.axvline(change, color="#9f1239", lw=1, ls=":")
    top.annotate("477 to 172", xy=(change, 3.15), xytext=(2.5e19, 3.08),
                 arrowprops={"arrowstyle": "->", "lw": .9}, fontsize=9)
    top.set_ylabel("Conditional Loss")
    top.legend(frameon=False, fontsize=8)
    top.grid(alpha=.2)
    bottom.plot([float(r["budget_FLOPs"]) for r in joint],
                [float(r["Q_B_proxy"]) for r in joint], color="#155e75", lw=1.8)
    bottom.axvline(change, color="#9f1239", lw=1, ls=":")
    bottom.set_ylabel("Q proxy")
    bottom.set_xlabel("Budget (FLOPs)")
    bottom.set_xscale("log")
    bottom.set_ylim(.53, .73)
    bottom.grid(alpha=.2)
    fig.suptitle("Conditional v8: 8192 tokens, power quality cost", fontsize=10)
    fig.tight_layout()
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)
    return FIGURE


if __name__ == "__main__":
    print(main())
