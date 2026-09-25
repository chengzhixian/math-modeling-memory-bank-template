"""Conditionally attach frozen Q1 recipes to B-native Q3 allocations.

The A/B bridge here is a hypothesis. Its amplitude and scale effect have no
paired-data estimate, so its Loss cannot be labeled empirically calibrated.
"""
from __future__ import annotations

import math


def policy_candidates(model) -> list[dict]:
    """Replay signed Q1 equal-13 hull and observed policies without refitting."""
    q1 = model.q1
    candidates = []
    for row in q1.bounds[:3]:
        if row["mode"] != "weighted":
            raise ValueError("expected signed weighted Q1 bound")
        policy = "convex_hull" if row["policy"] == "unconstrained" else row["policy"]
        p = row["feasible_composition"]
        support = q1.support(p, policy)
        effect = q1.weighted_effect(p, row["weights"])
        if abs(effect - row["feasible_upper_bound_relative"]) > 1e-8:
            raise RuntimeError("Q1 feasible composition and objective disagree")
        candidates.append({"candidate_id": "q1_equal13_" + row["policy"] + "_hull",
                           "p_policy": policy, "p": p, "weights": row["weights"],
                           "r_w": effect, "Q1_lower_bound_relative": row["lower_bound_relative"],
                           "Q1_upper_bound_relative": row["feasible_upper_bound_relative"],
                           "Q1_gap_relative": row["absolute_gap_relative"],
                           "p_support_mode": support["mode"], "p_observed_index": None})
        if row["policy"] == "unconstrained":
            index = q1.recipe_ids.index(row["best_observed_A4_index"])
            observed = q1.p_dict(q1.recipes[index])
            support = q1.support(observed, "observed_512")
            candidates.append({"candidate_id": "q1_equal13_observed_512",
                               "p_policy": "observed_512", "p": observed,
                               "weights": row["weights"],
                               "r_w": q1.weighted_effect(observed, row["weights"]),
                               "Q1_lower_bound_relative": row["lower_bound_relative"],
                               "Q1_upper_bound_relative": row["best_observed_A4_objective_relative"],
                               "Q1_gap_relative": row["best_observed_A4_objective_relative"]
                               - row["lower_bound_relative"],
                               "p_support_mode": support["mode"],
                               "p_observed_index": support["observed_index"]})
    return candidates


def evaluate_bridge_sensitivity(model, row: dict, p: dict, weights: dict,
                                policy: str, *, bridge_lambda: float,
                                eta: float, bridge_model: str = "exp_bridge") -> dict:
    if row["status"] != "conditional_B_native_feasible":
        raise ValueError("cannot attach a p scenario to an infeasible B-native row")
    result = model.evaluate(row["N_params_B"], row["D_tokens_B"], row["Q_score"],
                            p, weights, p_policy=policy, bridge_lambda=bridge_lambda,
                            eta=eta, bridge_model=bridge_model)
    if not math.isclose(result["B7_loss"], row["B_native_loss"], rel_tol=1e-9):
        raise RuntimeError("CYJ B7 and CHM B-native Loss disagree")
    return {
        "budget_FLOPs": row["budget_FLOPs"],
        "context_tokens": row["context_tokens"],
        "quality_family": row["quality_family"],
        "status": "conditional_scenario",
        "p_policy": policy,
        "p_support_mode": result["p_support"]["mode"],
        "p_observed_index": result["p_support"].get("observed_index"),
        "p_identifiability": "unidentified" if bridge_lambda == 0 else "conditional_on_bridge",
        "p_composition": p,
        "weights": weights,
        "N_params_B": row["N_params_B"],
        "D_tokens_B": row["D_tokens_B"],
        "Q_score": row["Q_score"],
        "B_native_loss": row["B_native_loss"],
        "conditional_bridge_loss": result["Loss"],
        "r_w": result["Q1_weighted_effect"],
        "bridge_factor": result["bridge_factor"],
        "bridge_lambda": bridge_lambda,
        "eta": eta,
        "bridge_model": bridge_model,
        "Q_A_to_Q_B_mapping": "unidentified",
        "cross_source_empirical_calibration_complete": False,
    }


def evaluate_policy(model, row: dict, p: dict, weights: dict, policy: str) -> dict:
    return evaluate_bridge_sensitivity(model, row, p, weights, policy,
                                       bridge_lambda=1.0, eta=0.0)
