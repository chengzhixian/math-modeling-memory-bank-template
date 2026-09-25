"""Default Q1 decisions: exact enumeration of observed A4 recipes.

The nonlinear model invalidates the legacy LP claim for conv(A4). Each
observed-recipe decision is an exact finite-set optimum for its declared
weights and quality policy; it is not a continuous hull optimum.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np
from q1_interface import Q1Interface

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_v2_decisions"
POLICIES = ("unconstrained", "quality_direct", "quality_direct_and_near")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quality_constraints(q1, x, policy):
    if policy not in POLICIES:
        raise ValueError("unknown quality policy")
    if policy == "unconstrained":
        return np.ones(len(x), bool), np.zeros(len(x)), np.zeros(len(x))
    accepted = {"direct"} if policy == "quality_direct" else {"direct", "near_direct"}
    mask = np.array([q1.qa_rows[d]["mapping_type"] in accepted for d in q1.domains], float)
    values = np.array([0. if q1.qa_rows[d]["Q_A"] is None else float(q1.qa_rows[d]["Q_A"]) for d in q1.domains])
    base_mass = float(q1.ref @ mask)
    assert base_mass > 0
    base_mean = float(q1.ref @ (mask * values) / base_mass)
    coverage = x @ mask
    quality_slack = x @ (mask * (values - base_mean))
    feasible = (coverage >= base_mass - 1e-12) & (quality_slack >= -1e-12)
    return feasible, coverage, quality_slack


def choose(q1, weights, policy="unconstrained", mode="weighted"):
    if not isinstance(weights, dict) or set(weights) != set(q1.targets):
        raise ValueError("explicit weights for all 13 targets required")
    w = np.array([float(weights[t]) for t in q1.targets])
    if not np.isfinite(w).all() or (w < 0).any() or not np.isclose(w.sum(), 1, atol=1e-12):
        raise ValueError("weights must be finite, nonnegative and sum to one")
    if mode not in {"weighted", "minimax"}:
        raise ValueError("mode must be weighted or minimax")
    feasible, coverage, quality_slack = quality_constraints(q1, q1.recipes, policy)
    if not feasible.any():
        raise ValueError("no observed A4 recipe meets quality policy")
    predictions = q1._predict(q1.recipes)
    relative = predictions / q1.reference_loss - 1
    objective = relative @ w if mode == "weighted" else np.max(relative[:, w > 0], axis=1)
    possible = np.flatnonzero(feasible)
    selected = int(possible[np.argmin(objective[possible])])
    x = q1.recipes[selected]
    unknown = float(sum(x[i] for i, d in enumerate(q1.domains) if q1.qa_rows[d]["Q_A"] is None))
    return {
        "schema_version": "chm.q1.decision.v2", "model_version": q1.manifest["schema_version"],
        "model_manifest_sha256": q1.manifest_sha256, "mode": mode, "quality_policy": policy,
        "domain_weights": dict(zip(q1.targets, map(float, w))),
        "normalization": "interaction_fitted_positive_1M_reference_loss_per_target",
        "support": "512_observed_A4_recipes", "global_optimum_within_support": True,
        "n_feasible": int(feasible.sum()), "selected_index": q1.recipe_ids[selected],
        "composition": dict(zip(q1.domains, map(float, x))),
        "objective_relative": float(objective[selected]),
        "target_relative": dict(zip(q1.targets, map(float, relative[selected]))),
        "target_predicted_1M_loss": dict(zip(q1.targets, map(float, predictions[selected]))),
        "quality_covered_mass": None if policy == "unconstrained" else float(coverage[selected]),
        "quality_slack": None if policy == "unconstrained" else float(quality_slack[selected]),
        "unknown_QA_mass": unknown, "full_mixture_Q_A": None if unknown > 1e-10 else float(x @ np.array([
            0. if q1.qa_rows[d]["Q_A"] is None else float(q1.qa_rows[d]["Q_A"]) for d in q1.domains])),
        "B7_Q_score": None, "cross_scale_loss": None, "ready_for_Q3_empirical_absolute_loss": False,
    }


def release(root=ROOT):
    q1 = Q1Interface(root)
    equal = {t: 1 / len(q1.targets) for t in q1.targets}
    scenarios = [("equal_13", equal, "weighted"),
                 ("protect_worst_13", equal, "minimax")]
    scenarios += [(f"only_{t}", {k: float(k == t) for k in q1.targets}, "weighted") for t in q1.targets]
    rows = []
    for scenario, weights, mode in scenarios:
        for policy in POLICIES:
            result = choose(q1, weights, policy, mode)
            result["scenario"] = scenario
            rows.append(result)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "decision_panel.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["scenario", "mode", "quality_policy", "selected_index", "objective_relative",
                  "n_feasible", "quality_covered_mass", "quality_slack", "unknown_QA_mass",
                  *q1.domains]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({**{key: r[key] for key in fields if key not in q1.domains}, **r["composition"]})
    with (OUT / "decision_panel.json").open("w", encoding="utf-8") as stream:
        json.dump(rows, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    result = {"schema_version": "chm.q1.decision_panel.v2", "primary_model": "chm.q1.v2.0",
              "Q1_manifest_sha256": q1.manifest_sha256, "scenario_count": len(scenarios),
              "quality_policies": list(POLICIES), "decision_count": len(rows),
              "optimization_status": "exact_finite_A4_enumeration",
              "continuous_hull_optimum_claimed": False,
              "decision_panel_csv_sha256": _sha(OUT / "decision_panel.csv"),
              "decision_panel_json_sha256": _sha(OUT / "decision_panel.json"),
              "default_equal_unconstrained_index": rows[0]["selected_index"],
              "ready_for_Q3_empirical_absolute_loss": False}
    (OUT / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(release(args.root), ensure_ascii=False, indent=2))
