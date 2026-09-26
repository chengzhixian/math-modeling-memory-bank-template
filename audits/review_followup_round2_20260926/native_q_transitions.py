"""Bracket Q0 release and Qmax activation for one stated Q3 policy.

The fixed recipe is 172; context is 8192 tokens; the quality cost is power.
These are conditional solver state brackets, not physical phase transitions.
Run with PYTHONPATH=src/chm;src/cyj from the repository root.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from q3_conditional_v8 import V8NativeQAdapter
from q3_native_q_solver import solve_scenario
from q3_v8_inputs import load_v8


def quality_state(row: dict) -> str:
    if row["status"] != "conditional_B_native_feasible":
        return "infeasible"
    if "Q0" in row["active_set"].split(";"):
        return "Q0"
    if "Q1" in row["active_set"].split(";"):
        return "Qmax"
    return "interior"


def bracket(adapter, left: dict, right: dict, target_width: float = 1e-4) -> dict:
    left_state, right_state = quality_state(left), quality_state(right)
    if left_state == right_state:
        raise ValueError("same state at both ends")
    for _ in range(40):
        if right["budget_FLOPs"] / left["budget_FLOPs"] - 1 <= target_width:
            break
        budget = math.sqrt(left["budget_FLOPs"] * right["budget_FLOPs"])
        middle = solve_scenario(adapter, budget, 8192, "power")
        middle_state = quality_state(middle)
        if middle_state == left_state:
            left = middle
        elif middle_state == right_state:
            right = middle
        else:
            raise RuntimeError("an unscanned quality state appeared inside the bracket")
    else:
        raise RuntimeError("quality state bracket did not converge")
    return {"budget_left_FLOPs": left["budget_FLOPs"],
            "budget_right_FLOPs": right["budget_FLOPs"],
            "state_left": quality_state(left), "state_right": quality_state(right),
            "Q_left": left["Q_score"], "Q_right": right["Q_score"],
            "relative_width": right["budget_FLOPs"] / left["budget_FLOPs"] - 1}


def main() -> None:
    model, bounds = load_v8()
    adapter = V8NativeQAdapter(model, bounds)
    rows = [solve_scenario(adapter, 10 ** (19 + 3 * i / 48), 8192, "power")
            for i in range(49)]
    transitions = [bracket(adapter, left, right) for left, right in zip(rows, rows[1:])
                   if quality_state(left) != quality_state(right)]
    if [(r["state_left"], r["state_right"]) for r in transitions] != [
        ("Q0", "interior"), ("interior", "Qmax")]:
        raise AssertionError("unexpected native-quality state sequence")
    tolerance_checks = []
    for transition in transitions:
        middle = math.sqrt(transition["budget_left_FLOPs"] *
                           transition["budget_right_FLOPs"])
        for multiplier in (0.995, 1.005):
            outcomes = []
            for tolerance in (1e-7, 1e-8):
                solved = solve_scenario(adapter, middle * multiplier, 8192, "power",
                                        tolerance=tolerance)
                outcomes.append({"certificate_tolerance": tolerance,
                                 "state": quality_state(solved), "Q_score": solved["Q_score"]})
            if outcomes[0]["state"] != outcomes[1]["state"]:
                raise AssertionError("quality state depends on certificate tolerance")
            tolerance_checks.append({"budget_FLOPs": middle * multiplier,
                                     "outcomes": outcomes})
    result = {"scope": "fixed_recipe_172_native_QB_8192_tokens_power_cost",
              "model": "CYJ_v8_B7_semi_synthetic_conditional",
              "Q0": 0.5, "Qmax": 1.0,
              "coarse_budgets": 49, "relative_bracket_tolerance": 1e-4,
              "transitions": transitions, "tolerance_checks": tolerance_checks,
              "claim_limit": "numerical_state_brackets_within_declared_support_not_real_training_thresholds"}
    target = Path(__file__).with_name("native_q_transitions.json")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
