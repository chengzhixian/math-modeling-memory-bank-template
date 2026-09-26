"""Detect conditional Q3 budget regime changes under CYJ v8.

Regimes change when feasibility, the best observed A4 recipe, or an active
N/D/budget constraint changes. Brackets are numerical, not physical phase
transitions or extrapolation outside the declared v8 support.
"""
from __future__ import annotations

import json
import math

from q3_conditional_v8 import (
    OUTPUT, CONTEXTS, FAMILIES, main_policy, observed_joint_grid,
    solve_fixed_p, write_csv,
)
from q3_v8_inputs import load_v8, digest


POINTS = 161


def state(row: dict) -> str:
    if row["status"] != "conditional_v8_fixed_policy_feasible":
        return row["status"]
    return f"recipe={row['recipe_index']};active={row['active_set']}"


def changes(group: list[dict]) -> list[tuple[dict, dict]]:
    return [(left, right) for left, right in zip(group, group[1:]) if state(left) != state(right)]


def scan(model, bounds, policy: dict, points: int = POINTS):
    if points < 3 or points % 2 != 1:
        raise ValueError("scan size must be odd and at least 3")
    fixed = []
    for context in CONTEXTS:
        for family in FAMILIES:
            fixed.extend(solve_fixed_p(model, bounds, policy["p"], policy["weights"],
                                      p_policy="observed_512",
                                      mapping_policy=policy["quality_mapping_policy"],
                                      budget=10**(19+5*i/(points-1)), context=context,
                                      family=family, recipe_index=policy["recipe_index"])
                         for i in range(points))
    joint = observed_joint_grid(model, bounds, fixed)
    return fixed, joint


def refine(model, bounds, policy, left: dict, right: dict, kind: str,
           target_width: float = 1e-4) -> list[dict]:
    if state(left) == state(right):
        raise ValueError("transition bracket has the same state on both sides")
    context, family = left["context_tokens"], left["quality_family"]

    def solve(budget):
        fixed = solve_fixed_p(model, bounds, policy["p"], policy["weights"],
                              p_policy="observed_512", mapping_policy=policy["quality_mapping_policy"],
                              budget=budget, context=context, family=family,
                              recipe_index=policy["recipe_index"])
        if kind == "fixed_Q2_policy":
            return fixed
        return observed_joint_grid(model, bounds, [fixed])[0]

    def visit(a: dict, b: dict, depth: int) -> list[dict]:
        width = b["budget_FLOPs"]/a["budget_FLOPs"]-1
        if width <= target_width:
            return [{"scenario": kind, "context_tokens": context, "quality_family": family,
                     "budget_left": a["budget_FLOPs"], "budget_right": b["budget_FLOPs"],
                     "state_left": state(a), "state_right": state(b),
                     "relative_width": width,
                     "transition_type": "feasibility_onset" if "infeasible" in state(a)+state(b)
                     else ("recipe_or_active_set" if kind == "observed_joint" else "active_set") }]
        if depth > 35:
            raise RuntimeError("v8 transition refinement did not converge")
        middle = solve(math.sqrt(a["budget_FLOPs"]*b["budget_FLOPs"]))
        if state(middle) == state(a):
            return visit(middle, b, depth+1)
        if state(middle) == state(b):
            return visit(a, middle, depth+1)
        return visit(a, middle, depth+1)+visit(middle, b, depth+1)

    return visit(left, right, 0)


def generate():
    model, bounds = load_v8()
    policy = main_policy(model)
    fixed, joint = scan(model, bounds, policy)
    write_csv(OUTPUT / "fixed_budget_scan.csv", fixed)
    write_csv(OUTPUT / "observed_budget_scan.csv", joint)
    brackets = []
    coarse_disagreements = []
    for kind, rows in (("fixed_Q2_policy", fixed), ("observed_joint", joint)):
        for i in range(0, len(rows), POINTS):
            group = rows[i:i+POINTS]
            coarse = [(state(a), state(b)) for a, b in changes(group[::2])]
            fine = [(state(a), state(b)) for a, b in changes(group)]
            if coarse != fine:
                coarse_disagreements.append({"scenario": kind,
                                             "context_tokens": group[0]["context_tokens"],
                                             "quality_family": group[0]["quality_family"]})
            for left, right in changes(group):
                brackets.extend(refine(model, bounds, policy, left, right, kind))
    write_csv(OUTPUT / "transitions.csv", brackets)
    resolution = {"schema_version": "chm.q3.v8.transition_resolution.v1",
                  "scan_points_per_context_family": POINTS,
                  "coarse_points_per_context_family": (POINTS+1)//2,
                  "target_bracket_relative_width": 1e-4,
                  "coarse_fine_signature_disagreements": coarse_disagreements,
                  "fixed_scan_rows": len(fixed), "joint_scan_rows": len(joint),
                  "transition_brackets": len(brackets),
                  "fixed_scan_sha256": digest(OUTPUT / "fixed_budget_scan.csv"),
                  "joint_scan_sha256": digest(OUTPUT / "observed_budget_scan.csv"),
                  "transitions_sha256": digest(OUTPUT / "transitions.csv"),
                  "claim_limit": "sampled_and_bisected_numeric_active_sets_not_a_physical_transition_proof"}
    (OUTPUT / "transition_resolution.json").write_text(json.dumps(resolution, indent=2)+"\n",
                                                        encoding="utf-8", newline="\n")
    return resolution


if __name__ == "__main__":
    print(json.dumps(generate()))
