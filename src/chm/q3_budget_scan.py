"""Analytic budget-transition diagnostics for Q3 B1 N-D baseline.

This module is diagnostic-only. It derives active-set transitions inside the
declared B1 support when Q=Q0 and p=p_ref. It must not be cited as the final Q3
optimum before the upstream cyj interface is ready_for_Q3=true.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

from q3_nd_baseline import DEFAULT_PARAMS, N_RANGE, D_RANGE, compute_coeff, bounded_optimum

CONTEXTS = (2048, 8192, 131072)
SCAN_BUDGETS = (1e16, 1e24)
SCAN_POINTS = 2001


def interior_elasticities(params=DEFAULT_PARAMS):
    alpha, beta = params["alpha"], params["beta"]
    den = alpha + beta
    return beta / den, alpha / den


def product_thresholds(params=DEFAULT_PARAMS):
    A, B = params["A"], params["B"]
    alpha, beta = params["alpha"], params["beta"]
    nmin, nmax = N_RANGE
    dmin, dmax = D_RANGE
    ratio = alpha * A / (beta * B)

    def p_for_n(n):
        return (n ** (alpha + beta) / ratio) ** (1.0 / beta)

    def p_for_d(d):
        return (d * ratio ** (1.0 / (alpha + beta))) ** ((alpha + beta) / alpha)

    return {
        "min_feasible": nmin * dmin,
        "Nmin_to_interior": p_for_n(nmin),
        "Dmin_to_interior": p_for_d(dmin),
        "interior_to_Nmax": p_for_n(nmax),
        "interior_to_Dmax": p_for_d(dmax),
        "support_corner": nmax * dmax,
    }


def transition_rows():
    thresholds = product_thresholds()
    eN, eD = interior_elasticities()
    base_coeff = compute_coeff(2048)
    rows = []
    for context in CONTEXTS:
        c = compute_coeff(context)
        relative_capacity = base_coeff / c
        rows.append({
            "context_tokens": context,
            "cost_coefficient_FLOPs_per_NB_DB": c,
            "attn_train_ratio": context / 30000.0,
            "budget_min_feasible": c * thresholds["min_feasible"],
            "budget_Nmin_to_interior": c * thresholds["Nmin_to_interior"],
            "budget_interior_to_Dmax": c * thresholds["interior_to_Dmax"],
            "budget_support_corner": c * thresholds["support_corner"],
            "elasticity_N_budget": eN,
            "elasticity_D_budget": eD,
            "N_ratio_vs_2048_interior": relative_capacity ** eN,
            "D_ratio_vs_2048_interior": relative_capacity ** eD,
        })
    return rows


def regime(budget, context):
    if budget < compute_coeff(context) * N_RANGE[0] * D_RANGE[0]:
        return "infeasible"
    out = bounded_optimum(budget, context)
    flags = set(out["support_flags"].split(";"))
    if "N_max" in flags and "D_max" in flags:
        return "support_corner"
    if "D_max" in flags:
        return "D_max"
    if "N_min" in flags:
        return "N_min"
    return "interior"


def log_scan(context, low=SCAN_BUDGETS[0], high=SCAN_BUDGETS[1], points=SCAN_POINTS):
    if points < 2 or low <= 0 or high <= low:
        raise ValueError("invalid log-scan specification")
    step = math.log(high / low) / (points - 1)
    transitions = []
    previous = None
    for i in range(points):
        budget = low * math.exp(step * i)
        current = regime(budget, context)
        if current != previous:
            transitions.append({"budget": budget, "regime": current})
            previous = current
    return transitions


def validate_scan():
    rows = {r["context_tokens"]: r for r in transition_rows()}
    expected_keys = {
        "N_min": "budget_min_feasible",
        "interior": "budget_Nmin_to_interior",
        "D_max": "budget_interior_to_Dmax",
        "support_corner": "budget_support_corner",
    }
    grid_factor = (SCAN_BUDGETS[1] / SCAN_BUDGETS[0]) ** (1.0 / (SCAN_POINTS - 1))
    for context in CONTEXTS:
        found = {item["regime"]: item["budget"] for item in log_scan(context)}
        if found.get("infeasible") is None:
            raise AssertionError("scan must start in infeasible regime")
        for name, key in expected_keys.items():
            exact = rows[context][key]
            observed = found[name]
            if not exact <= observed <= exact * grid_factor * (1 + 1e-12):
                raise AssertionError((context, name, exact, observed, grid_factor))
    return grid_factor


def write_csv(path=Path("outputs/chm/q3_budget_transitions.csv")):
    rows = transition_rows()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    write_csv()
    print(f"scan validation passed; multiplicative grid factor={validate_scan():.9f}")
