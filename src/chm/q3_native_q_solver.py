"""Current Q3 native-quality sensitivity solver, extracted from the CHM grid.

Only the active solve operation is retained; no historical CYJ v7 checkout is
loaded. This is a conditional, semi-synthetic sensitivity result.
"""
from __future__ import annotations
import math
from q3_generic_solver import cost_and_grad, enrich_kkt
from q3_joint_certificate import certify
from q3_quality_cost_geometry import FAMILIES, delta_g

CONTEXTS = (2048, 8192, 131072)

def solve_scenario(
    model,
    budget: float,
    context: int,
    family: str,
    q0: float = 0.5,
    tolerance: float = 1e-7,
) -> dict:
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be finite and positive")
    if context not in CONTEXTS or family not in FAMILIES:
        raise ValueError("context or quality family outside declared scenarios")
    if not model.support.Q[0] <= q0 < model.support.Q[1]:
        raise ValueError("Q0 outside B7 support")
    minimum = (6e18 + 2e14 * context) * model.support.N[0] * model.support.D[0]
    common = {
        "budget_FLOPs": budget,
        "context_tokens": context,
        "quality_family": family,
        "Q0_scenario": q0,
        "minimum_cost_FLOPs": minimum,
        "model_scope": "B7_semi_synthetic_conditional",
        "cross_source_empirical_calibration_complete": False,
    }
    if budget < minimum * (1 - 1e-12):
        return {**common, "status": "infeasible_within_B7_support", "B_native_loss": None,
                "N_params_B": None, "D_tokens_B": None, "Q_score": None,
                "kkt_check_pass": None, "global_gap": None}
    certificate = certify(model.theta, (model.support.N, model.support.D, model.support.Q),
                          budget, context, family, q0=q0, tolerance=tolerance)
    if not certificate["feasible"]:
        raise RuntimeError("certificate disagrees with minimum-cost check")
    n, d, q = (certificate["N_params_B"], certificate["D_tokens_B"], certificate["Q_score"])
    solution = enrich_kkt({"N_params_B": n, "D_tokens_B": d, "Q": q}, model,
                          budget, context, q0, family)
    if not solution["kkt_check_pass"]:
        raise RuntimeError("B7 numerical solution failed KKT check")
    train = 6e18 * n * d
    attention = 2e14 * context * n * d
    quality = 1e9 * d * delta_g(q, q0, family)
    total = train + attention + quality
    canonical_cost, _ = cost_and_grad(n, d, q, q0, context, family)
    if abs(total - canonical_cost) > 1e-10 * max(total, 1):
        raise RuntimeError("cost breakdown disagrees with CHM cost function")
    if total > budget * (1 + 1e-8):
        raise RuntimeError("budget violated")
    return {
        **common,
        "status": "conditional_B_native_feasible",
        "N_params_B": n,
        "D_tokens_B": d,
        "Q_score": q,
        "B_native_loss": solution["loss"],
        "C_train_FLOPs": train,
        "C_quality_FLOPs": quality,
        "C_attention_FLOPs": attention,
        "C_total_FLOPs": total,
        "budget_residual_FLOPs": total - budget,
        "budget_utilization": total / budget,
        "active_set": ";".join(sorted(solution["active_set"])),
        "kkt_check_pass": True,
        "kkt_relative_violation": solution["kkt_relative_violation"],
        "global_lower_bound": certificate["global_lower_bound"],
        "global_upper_bound": certificate["feasible_upper_bound"],
        "global_gap": certificate["global_gap"],
        "certificate_kind": "floating_point_B7_reduction",
    }
