"""Independent CYJ audit of CHM's nine one-factor Q3 v8 scenarios."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ndqp_scenarios_v8 import ConditionalV8
from q3_v8_independent_audit import check_manifest, load_rows, parameters, solve_nd


def audit(subject: Path) -> dict:
    identity = check_manifest(subject)
    model = ConditionalV8()
    theta = parameters(model)
    policy = json.loads((subject / ".upstream/cyj-v8/outputs/cyj/q2_v8/main_policy.json").read_text(encoding="utf-8"))
    weights = policy["weights"]
    recipes = []
    for recipe_id, vector in zip(model.q1.recipe_ids, model.q1.recipes):
        p = model.q1.p_dict(vector)
        if model.q1.qa_stats(p, "quality_direct_and_near")["eligible"]:
            recipes.append((recipe_id, p, model.q1.weighted_effect(p, weights)))
    published = load_rows(subject / "outputs/chm/q3_conditional_v8/assumption_official_grid.csv")
    mismatches = []
    scenario_counts = {}
    max_loss_error = 0.0
    for row in published:
        label = row["scenario"]
        q0 = float(row["Q0"])
        scale = float(row["quality_bridge_scale"])
        bridge = float(row["mixture_bridge_lambda"])
        budget = float(row["budget_FLOPs"])
        context = int(row["context_tokens"])
        family = row["quality_family"]
        eligible = []
        for recipe_id, p, effect in recipes:
            q = model.qa(p, "direct_and_near", scale)["Q_B_proxy"]
            if q >= q0 - 1e-12:
                eligible.append((recipe_id, q, effect))
        solved = []
        for recipe_id, q, effect in eligible:
            result = solve_nd(budget, context, family, q, q0, __import__("math").exp(bridge*effect), theta)
            if result is not None:
                solved.append((result, recipe_id))
        best, selected = min(solved, key=lambda pair: (pair[0]["loss"], pair[1])) if solved else (None, None)
        observed = bool(row["N_params_B"])
        scenario_counts.setdefault(label, {"cells": 0, "eligible": len(eligible), "feasible": 0, "selected_172": 0})
        stats = scenario_counts[label]
        stats["cells"] += 1
        stats["feasible"] += bool(best)
        stats["selected_172"] += selected == "172"
        key = f"{label}/{budget:g}/{context}/{family}"
        if int(row["eligible_observed_recipes"]) != len(eligible) or int(row["feasible_observed_recipes"]) != len(solved):
            mismatches.append(key + ": candidate count")
        if observed != bool(best) or (observed and row["recipe_index"] != selected):
            mismatches.append(key + ": feasibility or selected recipe")
        if best:
            difference = abs(float(row["conditional_bridge_loss"]) - best["loss"])
            max_loss_error = max(max_loss_error, difference)
            if difference > 5e-7:
                mismatches.append(key + ": loss")
            for field, value in (("N_params_B", best["n"]), ("D_tokens_B", best["d"]),
                                 ("Q_B_proxy", best["q"]), ("C_total_FLOPs", best["cost"])):
                if abs(float(row[field])-value) > 1e-5*max(1.0, abs(value)):
                    mismatches.append(key + ": " + field)
    result = {"identity": identity, "scenario_counts": scenario_counts,
              "published_cells": len(published), "max_absolute_loss_error": max_loss_error,
              "mismatches": mismatches,
              "status": "PASS" if len(published) == 243 and len(scenario_counts) == 9 and not mismatches else "FAIL"}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.subject_root.resolve())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "scenarios": result["scenario_counts"], "max_loss_error": result["max_absolute_loss_error"]}))
    if result["status"] != "PASS":
        raise SystemExit(1)
