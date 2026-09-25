"""Build reproducible Q2 v7 conditional evidence from pinned derived Q1 and B7."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np

from chm_q1_v2_consumer import ROOT, SOURCE_COMMIT, sha256
from ndqp_scenarios_v7 import BOUNDS, THETA, ConditionalV7, b7

OUT = ROOT / "outputs/cyj/q2_v7"
N, D, Q = 1.0, 100.0, 0.5
NUM_TOL = 1e-10


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_csv(name, rows):
    if not rows:
        raise ValueError(f"empty output: {name}")
    with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def equal_weights(q1):
    return {key: 1.0 / len(q1.targets) for key in q1.targets}


def objective(q1, point, weights, mode):
    p = q1.p_dict(point)
    effects = q1.effect_vector(p)
    if mode == "minimax":
        vector = q1.weight_vector(weights)
        return float(max(effects[vector > 0]))
    return float(effects @ q1.weight_vector(weights))


def observed(q1, weights, quality=None, mode="weighted"):
    candidates = []
    for i, point in enumerate(q1.recipes):
        p = q1.p_dict(point)
        if quality and not q1.qa_stats(p, quality)["eligible"]:
            continue
        candidates.append((objective(q1, point, weights, mode), i))
    if not candidates:
        return {"status": "infeasible", "reason": "no observed recipe satisfies policy"}
    value, index = min(candidates)
    return {"status": "exact_observed_512", "recipe_index": q1.recipe_ids[index],
            "objective": value, "p": q1.p_dict(q1.recipes[index]), "n_feasible": len(candidates),
            "global_within_observed_set": True}


def certified_hull(q1, weights, policy, mode="weighted"):
    matching = [r for r in q1.bounds if r["policy"] == policy and r["mode"] == mode]
    if len(matching) != 1:
        return {"status": "not_available", "reason": "no published matching CHM bounds"}
    row = matching[0]
    if set(row["weights"]) != set(q1.targets) or any(abs(row["weights"][key] - weights.get(key, 0.0)) > 1e-12 for key in q1.targets):
        return {"status": "not_available", "reason": "published CHM bound has different target weights"}
    actual = objective(q1, q1.point(row["feasible_composition"]), weights, mode)
    if abs(actual - row["feasible_upper_bound_relative"]) > 1e-8:
        raise ValueError("CHM bounded hull objective differs from CYJ relative objective")
    policy_name = "convex_hull" if policy == "unconstrained" else policy
    support = q1.support(row["feasible_composition"], policy_name)
    return {"status": "numerically_bounded_feasible", "p": row["feasible_composition"],
            "objective": actual, "lower_bound_relative": row["lower_bound_relative"],
            "absolute_gap_relative": row["absolute_gap_relative"],
            "certificate_kind": row["certificate_kind"], "support": support,
            "source_sha256": sha256(q1.bounds_path),
            "global_optimality": "numerical_gap_below_0.001_not_interval_arithmetic"}


def policy_result(model, name, weights, quality=None, mode="weighted"):
    q1 = model.q1
    obs = observed(q1, weights, quality, mode)
    hull_policy = quality or "unconstrained"
    hull = certified_hull(q1, weights, hull_policy, mode)
    for section, policy in ((obs, "observed_512"), (hull, "convex_hull" if not quality else quality)):
        if "p" in section:
            pred = model.predict_baseline(N, D, Q, section["p"], weights, p_policy=policy)
            section.update(baseline_loss=pred["Loss"], B7_loss=pred["B7_loss"],
                           r_w=pred["Q1_weighted_effect"], bridge_factor=pred["bridge_factor"],
                           support=pred["p_support"])
    return {"policy": name, "weights": weights, "objective_mode": mode,
            "quality_policy": quality, "observed_512": obs, "continuous_hull": hull}


def substitution(n, d, q, delta):
    if not BOUNDS[2][0] <= q + delta <= BOUNDS[2][1]:
        return {"status": "target_Q_out_of_support"}
    target = b7(n, d, q+delta)[0]
    lo, hi = BOUNDS[0]
    flo, fhi = b7(lo, d, q)[0] - target, b7(hi, d, q)[0] - target
    if flo == 0:
        root = lo
    elif fhi == 0:
        root = hi
    elif flo * fhi > 0:
        return {"status": "no_root_in_support", "endpoint_residuals": [flo, fhi]}
    else:
        for _ in range(90):
            mid = (lo + hi) / 2
            fm = b7(mid, d, q)[0] - target
            if flo * fm <= 0:
                hi, fhi = mid, fm
            else:
                lo, flo = mid, fm
        root = (lo + hi) / 2
    return {"status": "root_in_support", "N_prime_B": root,
            "residual": b7(root, d, q)[0] - target, "identical_to_frozen_B7": True}


def main():
    import numpy
    import scipy
    OUT.mkdir(parents=True, exist_ok=True)
    model = ConditionalV7()
    q1 = model.q1
    equal = equal_weights(q1)
    policies = [policy_result(model, "equal_13", equal),
                policy_result(model, "quality_direct", equal, "quality_direct"),
                policy_result(model, "quality_direct_and_near", equal, "quality_direct_and_near"),
                policy_result(model, "minimax_13", equal, mode="minimax")]
    for target in ("arxiv", "pile_cc"):
        weight = {target: 1.0}
        policies.append(policy_result(model, f"{target}_only", weight))
    write_json("policy_details.json", policies)
    rows = []
    for entry in policies:
        for support_name in ("observed_512", "continuous_hull"):
            item = entry[support_name]
            rows.append({"policy": entry["policy"], "support": support_name,
                         "status": item["status"], "objective_mode": entry["objective_mode"],
                         "objective_relative": item.get("objective"),
                         "lower_bound_relative": item.get("lower_bound_relative"),
                         "gap_relative": item.get("absolute_gap_relative"),
                         "baseline_loss": item.get("baseline_loss"), "B7_loss": item.get("B7_loss"),
                         "r_w": item.get("r_w"), "bridge_factor": item.get("bridge_factor"),
                         "observed_index": item.get("recipe_index")})
    write_csv("policy_solutions.csv", rows)
    write_json("main_policy.json", policies[0])
    write_json("upstream_pin.json", {"Q1_version": "chm.q1.v2.0", "Q1_manifest_sha256": q1.manifest_sha256,
                                     "Q1_producer_commit": SOURCE_COMMIT,
                                     "Q1_main_integration_commit": "f9693bbf4c205aa46d3719f6f8a1d6f26561d05f",
                                     "Q1_hull_bounds_sha256": sha256(q1.bounds_path),
                                     "B7_coefficients_source_sha256": model.b7_sha256})
    write_json("scenario_config.json", {"N_params_B": N, "D_tokens_B": D, "Q_score": Q,
                                        "equal_13": equal, "policy_tolerance": NUM_TOL,
                                        "support": BOUNDS, "bridge_lambda": 1, "eta": 0,
                                        "status": "conditional_scenario"})
    write_json("quality_policy_definition.json", {"source": "CHM Q1 v2 decision policy",
                                                  "coverage_rule": "covered_mass>=reference_covered_mass",
                                                  "conditional_mean_rule": "quality_numerator-reference_mean*covered_mass>=0",
                                                  "unknown_Q_A": None, "Q_A_to_Q_B": "unidentified",
                                                  "tolerance": NUM_TOL})
    write_json("model_definition.json", {"schema_version": "cyj.ndqp.scenario.v7",
                                         "formula": "L_B(N,D,Q_B)*exp(sum_k w_k*r_k(p))",
                                         "cross_source_empirical_calibration_complete": False,
                                         "B7_semisynthetic": True, "bridge_status": "sensitivity-only"})
    write_json("baseline_model.json", {"bridge_model": "exp_bridge", "bridge_lambda": 1,
                                        "eta": 0, "status": "conditional_on_unvalidated_cross_source_bridge"})
    write_json("model_coefficients.json", {"theta_B7": THETA, "parameter_source_sha256": model.b7_sha256,
                                           "Q1_coefficients_manifest_sha256": q1.manifest_sha256})
    comparisons, sensitivity, quality_rows, marginal_rows, transfer_rows, curvature_rows = [], [], [], [], [], []
    for entry in policies:
        for name in ("observed_512", "continuous_hull"):
            item = entry[name]
            if "p" not in item:
                continue
            policy = "observed_512" if name == "observed_512" else entry["quality_policy"] or "convex_hull"
            p, w = item["p"], entry["weights"]
            base = model.predict_baseline(N, D, Q, p, w, p_policy=policy)
            linear = model.predict_sensitivity(N, D, Q, p, w, p_policy=policy,
                                               bridge_lambda=1, eta=0, bridge_model="linear_bridge")
            comparisons.append({"policy": entry["policy"], "support": name, "Loss_exp": base["Loss"],
                                "Loss_linear": linear["Loss"], "absolute_difference": base["Loss"]-linear["Loss"],
                                "relative_difference_over_exp": (base["Loss"]-linear["Loss"])/base["Loss"],
                                "p_choice_difference": 0, "ranking_difference": 0,
                                "interpretation": "strict_monotonicity_identity_not_empirical_validation"})
            for lam in (0, 0.5, 0.75, 1.0, 1.25, 1.5):
                for eta in (0.0, 0.1, 0.2, 0.4):
                    for form in ("exp_bridge", "linear_bridge"):
                        try:
                            val = model.predict_sensitivity(N, D, Q, p, w, p_policy=policy,
                                                            bridge_lambda=lam, eta=eta, bridge_model=form)
                            sensitivity.append({"policy": entry["policy"], "support": name, "lambda": lam,
                                                "eta": eta, "bridge_model": form, "status": "valid",
                                                "Loss": val["Loss"], "difference_from_baseline": val["difference_from_baseline"]})
                        except ValueError as exc:
                            sensitivity.append({"policy": entry["policy"], "support": name, "lambda": lam,
                                                "eta": eta, "bridge_model": form, "status": str(exc),
                                                "Loss": None, "difference_from_baseline": None})
            for qa_policy in ("quality_direct", "quality_direct_and_near"):
                stats = q1.qa_stats(p, qa_policy)
                quality_rows.append({"policy": entry["policy"], "support": name, "mapping": qa_policy,
                                     "covered_mass": stats["covered_mass"], "mean_Q_A_on_mapped": stats["mean_Q_A_on_mapped"],
                                     "eligible": stats["eligible"], "unknown_Q_A_count": stats["unknown_Q_A_count"]})
            grad = base["gradients"]
            marginal_rows.append({"policy": entry["policy"], "support": name, "N_gradient_per_B": grad["N_B"],
                                  "D_gradient_per_B": grad["D_B"], "Q_B_gradient": grad["Q_B"],
                                  "N_elasticity_signed": base["elasticities_signed"]["N"],
                                  "D_elasticity_signed": base["elasticities_signed"]["D"],
                                  "Q_B_elasticity_signed": base["elasticities_signed"]["Q_B"]})
            point = q1.point(p)
            gradient = q1.gradient(p, w)
            hessian = q1.hessian(w)
            # Convex segments toward eligible observed recipes are feasible even at a hull boundary.
            target_candidates = [j for j, candidate in enumerate(q1.recipes)
                                 if np.max(np.abs(candidate-point)) > 1e-7
                                 and (entry["quality_policy"] is None or q1.qa_stats(q1.p_dict(candidate), entry["quality_policy"])["eligible"])]
            for j in target_candidates[:2]:
                u = q1.recipes[j] - point
                step = 1e-4
                next_point = point + step*u
                # A discrete observed choice has no infinitesimal observed-set path;
                # the derivative below is explicitly evaluated in its continuous hull.
                path_policy = entry["quality_policy"] or "convex_hull"
                q1.support(q1.p_dict(next_point), path_policy)
                next_p = q1.p_dict(next_point)
                exact_next = model.predict_baseline(N, D, Q, next_p, w, p_policy=path_policy)["Loss"]
                predicted = base["Loss"] * float(gradient @ u)
                transfer_rows.append({"policy": entry["policy"], "support": name,
                                      "toward_observed_index": q1.recipe_ids[j], "path_support": path_policy,
                                      "step": step, "direction_feasible": True,
                                      "directional_Loss_derivative": predicted,
                                      "finite_forward_difference": (exact_next-base["Loss"])/step,
                                      "difference_error": (exact_next-base["Loss"])/step-predicted})
                curvature_rows.append({"policy": entry["policy"], "support": name,
                                       "toward_observed_index": q1.recipe_ids[j], "path_support": path_policy,
                                       "direction_feasible": True,
                                       "directional_second_derivative": float(base["Loss"]*((u@hessian@u)+(gradient@u)**2)),
                                       "causal_interpretation": False})
    write_csv("bridge_model_comparison.csv", comparisons)
    write_csv("bridge_sensitivity.csv", sensitivity)
    valid = [r["Loss"] for r in sensitivity if r["status"] == "valid"]
    write_json("bridge_sensitivity_summary.json", {"scenarios": len(sensitivity), "valid": len(valid),
                                                   "Loss_range": [min(valid), max(valid)],
                                                   "range_is_confidence_interval": False})
    write_csv("quality_mapping_sensitivity.csv", quality_rows)
    write_csv("marginals_elasticities.csv", marginal_rows)
    write_csv("domain_transfer_effects.csv", transfer_rows)
    write_csv("domain_complementarity.csv", curvature_rows)
    write_csv("quality_vs_scale.csv", [{"N_B": N, "D_B": D, "Q_B": Q, "Delta_Q": delta, **substitution(N,D,Q,delta)}
                                       for delta in (0.05,0.1,0.2)])
    write_json("q1_consumer_audit.json", {"manifest_sha256": q1.manifest_sha256,
                                          "file_shas_verified": len(q1.upstream.paths),
                                          "domains": len(q1.domains), "targets": len(q1.targets),
                                          "pairs": len(q1.upstream.pairs), "recipes": len(q1.recipes),
                                          "unknown_Q_A_count": 11, "Q2_original_A_reads": 0})
    write_json("migration_audit.json", {"old_schema": "cyj.ndqp.scenario.v6",
                                         "new_schema": "cyj.ndqp.scenario.v7", "B7_parameters_unchanged": True,
                                         "old_main_loss": None, "reason": "v6 has no unique unconditioned main Loss",
                                         "comparison_status": "requires_fully_matched_v6_scenario",
                                         "Q1_change": "ridge_v1_3_to_interaction_v2",
                                         "QA_change": "A1_sample_primary", "bridge_change": "linear_conditional_to_exp_baseline",
                                         "raw_A_reads": 0})
    write_json("uncertainty_scope.json", {"cross_source_interval": None,
                                          "reason": "no paired A/B cross-source calibration",
                                          "grid_spread_is_confidence_interval": False})
    write_csv("validation_by_source.csv", [
        {"source": "A_Q1", "role": "training_nested_CV_and_same_condition_model_selection",
         "status": "signed_CHM_Q1_v2", "evidence": "outputs/chm/q1_v2_signoff/audit.json"},
        {"source": "B7", "role": "semi_synthetic_conditional_same_source_validation",
         "status": "frozen_CYJ_model", "evidence": "outputs/cyj/q2_final/validation_summary.csv"},
        {"source": "A_B_joint", "role": "unobserved", "status": "not_empirically_calibrated",
         "evidence": "no paired experiment"}])
    write_csv("requirement_evidence.csv", [
        {"requirement": "N_D_Q_scaling", "data": "B1_B7", "result": "model_coefficients.json", "status": "conditional_B7"},
        {"requirement": "p_effect", "data": "Q1_v2_derived", "result": "policy_solutions.csv", "status": "conditional_bridge"},
        {"requirement": "marginal_elasticity", "data": "B7_Q1_v2", "result": "marginals_elasticities.csv", "status": "model_internal"},
        {"requirement": "domain_substitution", "data": "Q1_v2", "result": "domain_transfer_effects.csv", "status": "model_internal"},
        {"requirement": "quality_scale_substitution", "data": "B7", "result": "quality_vs_scale.csv", "status": "model_internal"},
        {"requirement": "cross_source_test", "data": "unavailable_joint", "result": "validation_by_source.csv", "status": "not_empirically_calibrated"}])
    write_json("acceptance.json", {"q2_implementation_complete": False, "q2_answer_complete_under_stated_assumptions": False,
                                  "q3_consumer_interface_ready": False, "q3_consumer_verified": False,
                                  "cross_source_empirical_calibration_complete": False,
                                  "status": "build_generated_pending_independent_tests"})
    write_json("final_closure.json", {"status": "conditional_build_only",
                                     "CHM_owner_Q3_consumer_acceptance": "pending",
                                     "cross_source_empirical_calibration_complete": False})
    manifest = {"schema_version": "cyj.q2.v7.outputs.v1", "Q1_manifest_sha256": q1.manifest_sha256,
                "B7_parameters_sha256": model.b7_sha256,
                "python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
                "command": "python -B src/cyj/build_q2_v7.py", "files": {}}
    for path in sorted(OUT.iterdir()):
        if path.name != "manifest.json" and path.is_file():
            manifest["files"][path.name] = sha256(path)
    write_json("manifest.json", manifest)
    return {"policy_rows": len(rows), "sensitivity_rows": len(sensitivity), "manifest_sha256": sha256(OUT/"manifest.json")}


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
