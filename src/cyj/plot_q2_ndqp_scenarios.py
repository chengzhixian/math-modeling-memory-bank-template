"""Render four labeled sensitivity figures from the frozen scenario grid."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "outputs/cyj/q2_joint_scenarios/scenario_grid.csv"
OUT = ROOT / "figures/cyj/q2_joint_scenarios"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data():
    with GRID.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 540 or {r["status"] for r in rows} != {"conditional_scenario_only"}:
        raise ValueError("unexpected scenario grid")
    return rows


def subset(rows, **filters):
    selected = [r for r in rows if all((float(r[k]) == v if isinstance(v, (int, float)) else r[k] == v)
                                        for k, v in filters.items())]
    return sorted(selected, key=lambda r: float(r["bridge_lambda"]))


def finish(fig, name):
    fig.suptitle("Conditional A-to-B transfer sensitivity; bridge not calibrated", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, .94))
    path = OUT / name
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = data()
    outputs = []
    p = "transfer_freelaw_to_arxiv_one_percent"

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for ax, n in zip(axes, (.1, 1, 10)):
        for eta in (-.5, 0, .5):
            r = subset(rows, N_B=n, p_variant=p, weights="arxiv_only", eta=eta)
            ax.plot([float(x["bridge_lambda"]) for x in r],
                    [float(x["loss"]) - float(x["baseline_loss"]) for x in r],
                    marker="o", label=f"eta={eta:g}")
        ax.axhline(0, color="black", linewidth=.6)
        ax.set(title=f"N={n:g}B", xlabel="assumed lambda", ylabel="conditional minus B7 Loss")
        ax.grid(alpha=.25)
    axes[-1].legend(fontsize=8)
    outputs.append(finish(fig, "lambda_by_scale.png"))

    fig, ax = plt.subplots(figsize=(6, 3.8))
    for weight in ("arxiv_only", "pile_cc_only", "equal_13"):
        r = subset(rows, N_B=1, p_variant=p, weights=weight, eta=0)
        ax.plot([float(x["bridge_lambda"]) for x in r],
                [float(x["loss"]) for x in r], marker="o", label=weight)
    ax.set(xlabel="assumed lambda", ylabel="conditional B-native Loss",
           title="1B, 100B tokens, B-native Q=0.5")
    ax.grid(alpha=.25); ax.legend(fontsize=8)
    outputs.append(finish(fig, "weight_sensitivity.png"))

    fig, ax = plt.subplots(figsize=(6, 3.8))
    for eta in (-.5, 0, .5):
        r = sorted((x for x in rows if x["p_variant"] == p and x["weights"] == "arxiv_only"
                    and float(x["bridge_lambda"]) == .5 and float(x["eta"]) == eta),
                   key=lambda x: float(x["N_B"]))
        ax.plot([float(x["N_B"]) for x in r],
                [100 * (float(x["factor"]) - 1) for x in r], marker="o", label=f"eta={eta:g}")
    ax.set(xscale="log", xlabel="N (billion parameters)", ylabel="conditional change vs B7 (%)",
           title="Assumed lambda=0.5; 1% freelaw to arxiv")
    ax.grid(alpha=.25); ax.legend(fontsize=8)
    outputs.append(finish(fig, "eta_by_scale.png"))

    fig, ax = plt.subplots(figsize=(6, 3.8))
    for weight in ("arxiv_only", "pile_cc_only", "equal_13"):
        treatment = sorted((x for x in rows if x["p_variant"] == p and x["weights"] == weight
                            and float(x["bridge_lambda"]) == .5 and float(x["eta"]) == .5),
                           key=lambda x: float(x["N_B"]))
        baseline = {float(x["N_B"]): float(x["loss"]) for x in rows
                    if x["p_variant"] == "reference" and x["weights"] == weight
                    and float(x["bridge_lambda"]) == .5 and float(x["eta"]) == .5}
        ax.plot([float(x["N_B"]) for x in treatment],
                [float(x["loss"]) - baseline[float(x["N_B"])] for x in treatment],
                marker="o", label=weight)
    ax.axhline(0, color="black", linewidth=.6)
    ax.set(xscale="log", xlabel="N (billion parameters)",
           ylabel="Loss change for 1% mixture transfer",
           title="1% freelaw to arxiv; lambda=0.5, eta=0.5")
    ax.grid(alpha=.25); ax.legend(fontsize=7)
    outputs.append(finish(fig, "mixture_transfer_by_scale.png"))

    manifest = {"schema_version": "cyj.q2.ndqp.figures.v1",
                "source_grid": {"path": GRID.relative_to(ROOT).as_posix(), "sha256": sha(GRID)},
                "plot_code": {"path": "src/cyj/plot_q2_ndqp_scenarios.py", "sha256": sha(Path(__file__))},
                "figures_sha256": {p.name: sha(p) for p in outputs},
                "data_status": "A fitted contrasts plus B7 semi-synthetic fit; lambda/eta/weights are scenarios",
                "bridge_calibrated": False}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(run()["figures_sha256"], indent=2))
