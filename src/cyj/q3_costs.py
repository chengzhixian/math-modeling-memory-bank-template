"""Q3 cost/constraint definitions transcribed from the visible F problem DOCX."""
from __future__ import annotations

import math

from q3_interface import finite

ATTENTION_COEFFICIENT = 2e-4  # eta_attn; distinct from CHM's mixture decay eta.
CONTEXT_SCENARIOS = (2048, 8192, 131072)  # zhh C7 published candidates, pending acceptance.
QUALITY_COSTS = {"exponential": (1e7, 6.0), "power": (5e9, 4.0), "logarithmic": (2e9, 10.0)}


def quality_cost(q, family):
    q = finite(q, "Q_score")
    if not 0 < q <= 1 or family not in QUALITY_COSTS:
        raise ValueError("Q must be in (0,1] and quality cost family must be supported")
    gamma, rate = QUALITY_COSTS[family]
    if family == "exponential":
        return gamma * math.exp(rate * q), gamma * rate * math.exp(rate * q)
    if family == "power":
        return gamma * q ** rate, gamma * rate * q ** (rate - 1)
    return gamma * math.log1p(rate * q), gamma * rate / (1 + rate * q)


def costs(*, N_params_B, D_tokens_B, Q_score, Q0, L_ctx, quality_family,
          budget_FLOPs=None, allowed_contexts=CONTEXT_SCENARIOS):
    """All three terms consume the same D; Q0 is caller-defined, never inferred."""
    n, d = finite(N_params_B, "N_params_B"), finite(D_tokens_B, "D_tokens_B")
    context = finite(L_ctx, "L_ctx")
    if n <= 0 or d <= 0 or context not in allowed_contexts:
        raise ValueError("N,D must be positive; L_ctx must be an explicit supported scenario")
    q, q0 = finite(Q_score, "Q_score"), finite(Q0, "Q0")
    g, derivative = quality_cost(q, quality_family)
    g0, _ = quality_cost(q0, quality_family)
    increment = max(0.0, g - g0)
    train = 6e18 * n * d
    quality = 1e9 * d * increment
    attention = ATTENTION_COEFFICIENT * 1e18 * n * d * context
    total = train + quality + attention
    if not math.isfinite(total):
        raise ValueError("nonfinite total cost")
    budget = None if budget_FLOPs is None else finite(budget_FLOPs, "budget_FLOPs")
    if budget is not None and budget <= 0:
        raise ValueError("budget must be positive")
    slope_q = 1e9 * d * derivative
    return {
        "cost_coordinate": "FLOPs", "training": train, "quality": quality,
        "attention": attention, "total": total,
        "budget_residual": None if budget is None else total - budget,
        "relative_budget_residual": None if budget is None else total / budget - 1,
        "budget_feasible": None if budget is None else total <= budget,
        "gradient": {"N_params_B": (6 + ATTENTION_COEFFICIENT * context) * 1e18 * d,
                     "D_tokens_B": (6 + ATTENTION_COEFFICIENT * context) * 1e18 * n + 1e9 * increment,
                     "Q_score_left": slope_q if q > q0 else 0.0,
                     "Q_score_right": slope_q if q >= q0 else 0.0},
        "context_critical_tokens": 6 / ATTENTION_COEFFICIENT,
        "attention_over_training": ATTENTION_COEFFICIENT * context / 6,
        "Q0": q0, "Q0_status": "explicit_scenario", "quality_family": quality_family,
        "context_source_status": ("zhh_C7_candidate_not_joint_accepted" if context in CONTEXT_SCENARIOS
                                  else "CYJ_external_sensitivity_not_C7_observation"),
        "ready_for_Q3": False,
    }


def constraint_residuals(p, expected_domains, cost_result):
    if set(p) != set(expected_domains):
        raise ValueError("p keys must equal the adopted 17 domains")
    values = [finite(p[name], name) for name in expected_domains]
    return {"budget_FLOPs": cost_result["budget_residual"],
            "budget_relative": cost_result["relative_budget_residual"],
            "simplex_equality": math.fsum(values) - 1.0,
            "nonnegative_violation": max(0.0, -min(values))}
