"""One-factor-at-a-time Q3 robustness around the pinned CYJ v8 scenario.

Values are explicit modeling assumptions, not confidence intervals.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from q3_conditional_v8 import (
    CONTEXTS, FAMILIES, OFFICIAL_BUDGETS, OUTPUT, main_policy,
    observed_joint_grid, solve_fixed_p, write_csv,
)
from q3_v8_inputs import digest, load_v8

SCENARIOS = (
    ("baseline", 0.50, 1.0, 1.0),
    ("Q0_0p45", 0.45, 1.0, 1.0),
    ("Q0_0p55", 0.55, 1.0, 1.0),
    ("Q0_0p60", 0.60, 1.0, 1.0),
    ("Q0_0p65", 0.65, 1.0, 1.0),
    ("quality_scale_0p5", 0.50, 0.5, 1.0),
    ("quality_scale_1p5", 0.50, 1.5, 1.0),
    ("mixture_lambda_0", 0.50, 1.0, 0.0),
    ("mixture_lambda_2", 0.50, 1.0, 2.0),
)
SCAN_POINTS = 161
SCAN_CONTEXT = 8192
SCAN_FAMILY = "power"
SCAN_LOG10_MIN, SCAN_LOG10_MAX = 19, 21


def fixed(model, bounds, policy, scenario, budget, context, family):
    _, q0, quality_scale, mixture_lambda = scenario
    return solve_fixed_p(model, bounds, policy["p"], policy["weights"],
                         p_policy="observed_512",
                         mapping_policy=policy["quality_mapping_policy"],
                         budget=budget, context=context, family=family,
                         q0=q0, recipe_index=policy["recipe_index"],
                         quality_bridge_scale=quality_scale,
                         mixture_bridge_lambda=mixture_lambda)


def joint(model, bounds, fixed_rows, scenario):
    _, q0, quality_scale, mixture_lambda = scenario
    return observed_joint_grid(model, bounds, fixed_rows, q0=q0,
                               quality_bridge_scale=quality_scale,
                               mixture_bridge_lambda=mixture_lambda)


def key(row):
    return (row["budget_FLOPs"], row["context_tokens"], row["quality_family"])


def state(row):
    if row["status"] != "conditional_v8_fixed_policy_feasible":
        return row["status"]
    return f"recipe={row['recipe_index']}"


def row_export(row, scenario):
    label, q0, quality_scale, mixture_lambda = scenario
    return {"scenario": label, "Q0": q0, "quality_bridge_scale": quality_scale,
            "mixture_bridge_lambda": mixture_lambda,
            "budget_FLOPs": row["budget_FLOPs"],
            "context_tokens": row["context_tokens"],
            "quality_family": row["quality_family"],
            "status": row["status"],
            "eligible_observed_recipes": row["eligible_observed_recipes"],
            "feasible_observed_recipes": row["feasible_observed_recipes"],
            "recipe_index": row.get("recipe_index"),
            "N_params_B": row.get("N_params_B"),
            "D_tokens_B": row.get("D_tokens_B"),
            "Q_B_proxy": row.get("Q_B_proxy"),
            "conditional_bridge_loss": row.get("conditional_bridge_loss"),
            "C_total_FLOPs": row.get("C_total_FLOPs")}


def refine(model, bounds, policy, scenario, left, right):
    """Bisect a bracket; recursively retain intervening sampled states."""
    def visit(a, b, depth):
        width = b["budget_FLOPs"]/a["budget_FLOPs"]-1
        if width <= 1e-4:
            return [{"scenario": scenario[0], "budget_left": a["budget_FLOPs"],
                     "budget_right": b["budget_FLOPs"], "state_left": state(a),
                     "state_right": state(b), "relative_width": width}]
        if depth > 35:
            raise RuntimeError("Q3 robustness transition refinement did not converge")
        budget = math.sqrt(a["budget_FLOPs"]*b["budget_FLOPs"])
        middle_fixed = fixed(model, bounds, policy, scenario, budget, SCAN_CONTEXT, SCAN_FAMILY)
        middle = joint(model, bounds, [middle_fixed], scenario)[0]
        if state(middle) == state(a):
            return visit(middle, b, depth+1)
        if state(middle) == state(b):
            return visit(a, middle, depth+1)
        return visit(a, middle, depth+1)+visit(middle, b, depth+1)
    if state(left) == state(right):
        raise ValueError("robustness transition bracket has equal end states")
    return visit(left, right, 0)


def generate(out_dir: Path = OUTPUT):
    model, bounds = load_v8()
    policy = main_policy(model)
    official, scans, transitions = [], [], []
    comparisons = []
    baseline_rows = None
    for scenario in SCENARIOS:
        label = scenario[0]
        fixed_rows = [fixed(model, bounds, policy, scenario, budget, context, family)
                      for budget in OFFICIAL_BUDGETS for context in CONTEXTS for family in FAMILIES]
        rows = joint(model, bounds, fixed_rows, scenario)
        if len(rows) != 27:
            raise RuntimeError("Q3 robustness official grid incomplete")
        official.extend(row_export(row, scenario) for row in rows)
        if label == "baseline":
            baseline_rows = {key(row): row for row in rows}
        changed = [row for row in rows if state(row) != state(baseline_rows[key(row)])]
        comparisons.append({"scenario": label, "Q0": scenario[1],
                            "quality_bridge_scale": scenario[2],
                            "mixture_bridge_lambda": scenario[3],
                            "eligible_observed_recipes": rows[0]["eligible_observed_recipes"],
                            "feasible_official_cells": sum(r["status"] == "conditional_v8_fixed_policy_feasible"
                                                           for r in rows),
                            "changed_feasibility_or_recipe_cells": len(changed),
                            "changed_cells": [list(key(r)) for r in changed],
                            "recipes_at_mid_budget": {
                                f"{r['context_tokens']}:{r['quality_family']}": r.get("recipe_index")
                                for r in rows if r["budget_FLOPs"] == 1e22}})
        scan_fixed = [fixed(model, bounds, policy, scenario,
                            10**(SCAN_LOG10_MIN+(SCAN_LOG10_MAX-SCAN_LOG10_MIN)*i/(SCAN_POINTS-1)),
                            SCAN_CONTEXT, SCAN_FAMILY)
                      for i in range(SCAN_POINTS)]
        scan_rows = joint(model, bounds, scan_fixed, scenario)
        scans.extend(row_export(row, scenario) for row in scan_rows)
        for left, right in zip(scan_rows, scan_rows[1:]):
            if state(left) != state(right):
                transitions.extend(refine(model, bounds, policy, scenario, left, right))
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {"assumption_official_grid.csv": official,
             "assumption_8192_power_scan.csv": scans,
             "assumption_8192_power_transitions.csv": transitions}
    for name, rows in files.items():
        write_csv(out_dir/name, rows)
    summary = {"schema_version": "chm.q3.v8.assumption_sensitivity.v1",
               "status": "one_factor_at_a_time_hypotheses_not_confidence_intervals",
               "baseline": "CYJ_v8_Q0_0p5_quality_scale_1_mixture_lambda_1",
               "candidate_policy": "A4_observed_512_Q1_direct_and_near_and_Qproxy_at_least_Q0",
               "quality_mapping_policy": "direct_and_near", "bridge_eta": 0.0,
               "scenario_selection": "illustrative_symmetric_bridge_scales_and_Q0_values_straddling_recipe_477_Qproxy",
               "comparisons": comparisons,
               "scan": {"context_tokens": SCAN_CONTEXT, "quality_family": SCAN_FAMILY,
                        "log10_budget_min": SCAN_LOG10_MIN,
                        "log10_budget_max": SCAN_LOG10_MAX,
                        "points_per_scenario": SCAN_POINTS,
                        "transition_target_relative_width": 1e-4,
                        "resolution_limit": "sampled_transitions_only_no_proof_of_absent_narrow_states"},
               "outputs_sha256": {name: digest(out_dir/name) for name in files}}
    (out_dir/"assumption_sensitivity.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
        encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    summary = generate()
    print(json.dumps({item["scenario"]: [item["eligible_observed_recipes"],
                                        item["feasible_official_cells"],
                                        item["changed_feasibility_or_recipe_cells"]]
                      for item in summary["comparisons"]}, ensure_ascii=False))
