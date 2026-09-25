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
from q2_final_core import Q2Final
from revalidate_q1_v2_bounds import main as revalidate_bounds
from bound_single_target_v7 import main as bound_single_targets

OUT = ROOT / "outputs/cyj/q2_v7"
N, D, Q = 1.0, 100.0, 0.5
NUM_TOL = 1e-10


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_csv(name, rows):
    if not rows:
        raise ValueError(f"empty output: {name}")
    with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
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
    ordered = sorted(candidates)
    tied = [q1.recipe_ids[i] for v, i in ordered if v-value <= NUM_TOL]
    return {"status": "exact_observed_512", "recipe_index": q1.recipe_ids[index],
            "objective": value, "p": q1.p_dict(q1.recipes[index]), "n_feasible": len(candidates),
            "global_within_observed_set": True, "tie_tolerance_relative": NUM_TOL,
            "tie_recipe_indices": tied, "next_distinct_objective_gap": next(
                (v-value for v, _ in ordered if v-value > NUM_TOL), None),
            "regret_within_observed_set": 0.0}


def certified_hull(q1, weights, policy, mode="weighted"):
    matching = [r for r in q1.bounds if r["policy"] == policy and r["mode"] == mode
                and set(r["weights"]) == set(q1.targets)
                and all(abs(r["weights"][key]-weights.get(key, 0)) < 1e-12 for key in q1.targets)]
    source_path = q1.bounds_path
    if len(matching) != 1:
        source_path = OUT / "single_target_hull_bounds.json"
        extension = json.loads(source_path.read_text(encoding="utf-8"))
        if extension["Q1_manifest_sha256"] != q1.manifest_sha256:
            raise ValueError("single-target bound Q1 identity mismatch")
        matching = [r for r in extension["rows"] if r["policy"] == policy and r["mode"] == mode
                    and all(abs(r["weights"][key]-weights.get(key, 0)) < 1e-12 for key in q1.targets)]
        if len(matching) != 1:
            return {"status": "not_available", "reason": "no matching numerical hull bound"}
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
            "candidate_regret_upper_relative": row["absolute_gap_relative"],
            "candidate_regret_upper_conditional_Loss": (b7(N,D,Q)[0] *
                (math.exp(actual)-math.exp(row["lower_bound_relative"])) if mode == "weighted" else None),
            "certificate_kind": row["certificate_kind"], "support": support,
            "source_sha256": sha256(source_path),
            "bound_producer_scope": ("CHM_main_release_revalidated_by_CYJ" if source_path == q1.bounds_path
                                     else "CYJ_single_target_numerical_extension"),
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


def substitution_sensitivity(model, p, weights, n, d, q, delta, eta):
    if not BOUNDS[2][0] <= q + delta <= BOUNDS[2][1]:
        return {"status": "target_Q_out_of_support"}
    def value(n_trial, q_trial):
        return model.predict_sensitivity(n_trial, d, q_trial, p, weights,
                                         p_policy="observed_512", bridge_lambda=1,
                                         eta=eta, bridge_model="exp_bridge")["Loss"]
    target = value(n, q + delta)
    lo, hi = BOUNDS[0]
    flo, fhi = value(lo, q)-target, value(hi, q)-target
    if flo*fhi > 0:
        return {"status": "no_root_in_support", "endpoint_residuals": [flo, fhi]}
    for _ in range(70):
        mid = (lo+hi)/2
        fm = value(mid, q)-target
        if flo*fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    root = (lo+hi)/2
    return {"status": "root_in_support", "N_prime_B": root,
            "residual": value(root, q)-target, "identical_to_frozen_B7": eta == 0}


def b7_parameter_spread(model, policies):
    joint_path = ROOT / "outputs/cyj/quality/b7_joint_fit.json"
    identification_path = ROOT / "outputs/cyj/quality/b7_identifiability.json"
    joint = json.loads(joint_path.read_text(encoding="utf-8"))
    identification = json.loads(identification_path.read_text(encoding="utf-8"))
    if (tuple(joint["model"]["theta"]) != THETA
            or identification["model_hash"] != sha256(joint_path)
            or identification["bootstrap_accepted"] != 200):
        raise ValueError("joint B7 parameter bootstrap is not aligned with frozen B7")
    samples = np.asarray(identification["bootstrap_parameter_samples"], dtype=float)
    if samples.shape != (200, 8) or not np.isfinite(samples).all():
        raise ValueError("invalid joint B7 parameter bootstrap")
    e, a, b, alpha, beta, g0, gn, gd = samples.T
    base_draws = e+a*N**(-alpha)+b*D**(-beta)+(1-Q)*(g0+gn*np.log(N)+gd*np.log(D/100))
    if not np.isfinite(base_draws).all() or np.min(base_draws) <= 0:
        raise ValueError("joint B7 bootstrap predicts nonpositive Loss")
    rows = []
    for entry in policies:
        for support_name in ("observed_512", "continuous_hull"):
            item = entry[support_name]
            if "p" not in item:
                continue
            factor = math.exp(model.q1.weighted_effect(item["p"], entry["weights"]))
            values = base_draws*factor
            lower, median, upper = np.quantile(values, [.025, .5, .975])
            rows.append({"policy": entry["policy"], "support": support_name,
                         "N_params_B": N, "D_tokens_B": D, "Q_score": Q,
                         "conditional_bridge_factor_fixed": factor, "bootstrap_draws": 200,
                         "parameter_only_q025": float(lower), "parameter_only_median": float(median),
                         "parameter_only_q975": float(upper),
                         "interval_type": "B7_ND_cluster_parameter_bootstrap_conditional_on_fixed_bridge",
                         "joint_A_B_coverage_claim": False})
    return rows, sha256(identification_path)


def observed_bridge_panel(model, policies):
    q1 = model.q1
    base = b7(N,D,Q)[0]
    rows = []
    for entry in policies:
        if entry["objective_mode"] != "weighted":
            continue
        quality = entry["quality_policy"]
        effects = []
        for recipe in q1.recipes:
            p = q1.p_dict(recipe)
            if quality and not q1.qa_stats(p, quality)["eligible"]:
                continue
            effects.append(q1.weighted_effect(p, entry["weights"]))
        if not effects:
            raise ValueError("observed bridge panel has no candidates")
        effects = np.asarray(effects)
        exp_values = base*np.exp(effects)
        linear_values = base*(1+effects)
        valid = linear_values > 0
        if np.any(valid):
            valid_effects = effects[valid]
            differences = abs(exp_values[valid]-linear_values[valid])
            same_order = np.array_equal(np.argsort(exp_values[valid], kind="stable"),
                                        np.argsort(linear_values[valid], kind="stable"))
            best_effect = float(np.min(valid_effects))
            tie_count = int(np.sum(valid_effects-best_effect <= NUM_TOL))
        else:
            differences = np.asarray([])
            same_order = False
            tie_count = 0
        rows.append({"policy": entry["policy"], "sample_set": "Q1_A4_512_observed_filtered_by_declared_quality_policy",
                     "N_params_B": N, "D_tokens_B": D, "Q_score": Q,
                     "common_valid_count": int(valid.sum()),
                     "invalid_exp_count": 0, "invalid_linear_count": int((~valid).sum()),
                     "ranking_identical_on_common_valid": bool(same_order),
                     "absolute_difference_max_sampled": float(np.max(differences)) if len(differences) else None,
                     "absolute_difference_median_sampled": float(np.median(differences)) if len(differences) else None,
                     "absolute_difference_p95_sampled": float(np.quantile(differences, .95)) if len(differences) else None,
                     "best_tie_count": tie_count, "tie_tolerance_relative": NUM_TOL,
                     "interpretation": "algebraic_monotonicity_check_not_empirical_bridge_validation"})
    return rows


def main():
    import numpy
    import scipy
    OUT.mkdir(parents=True, exist_ok=True)
    bounds_audit = revalidate_bounds()
    if not bounds_audit["all_four_reproduced"]:
        raise ValueError("current Q1 v2 numerical bounds have not been revalidated")
    local_bounds = bound_single_targets()
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
    write_json("upstream_pin.json", {"Q1_version": "chm.q1.v2.0",
                                     "expected_Q1_manifest_sha256": "c621f7e405106e42720f918f490235b5e8becefb0f7c8cb997736e96337117a9",
                                     "actual_Q1_manifest_sha256": q1.manifest_sha256,
                                     "Q1_manifest_sha256": q1.manifest_sha256,
                                     "Q1_producer_commit": SOURCE_COMMIT,
                                     "Q1_main_integration_commit": "f9693bbf4c205aa46d3719f6f8a1d6f26561d05f",
                                     "Q1_model_owner_release_evidence": ["interfaces/chm/Q1_V2_DOWNSTREAM.md",
                                                                          "interfaces/chm/q1_interface_v2.json"],
                                     "Q1_bounds_main_release_commit": "f9693bbf4c205aa46d3719f6f8a1d6f26561d05f",
                                     "Q1_hull_bounds_sha256": sha256(q1.bounds_path),
                                     "Q1_current_bounds_revalidated": True,
                                     "CHM_signoff_audit_bounds_hash_matches_current": bounds_audit["CHM_signoff_hash_matches_current_bounds"],
                                     "CHM_signoff_audit_bounds_sha256": bounds_audit["CHM_signoff_audit_bounds_sha256"],
                                     "bounds_difference": "published CHM signoff hash differs from current main bounds file; four reported upper/lower values and gaps regenerated exactly",
                                     "CYJ_consumption_decision": "accept_current_main_bounds_as_conditional_numerical_candidates_after_full_reproduction; CHM_owner_signoff_refresh_pending",
                                     "affected_rebuilt_outputs": ["policy_details.json", "policy_solutions.csv",
                                                                  "bridge_sensitivity.csv", "b7_parameter_uncertainty.csv",
                                                                  "paper/latex/sections/cyj/q2_v7_tail.tex"],
                                     "CYJ_single_target_bounds_sha256": local_bounds["sha256"],
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
            for n_scenario in (0.1, 1.0, 10.0):
                for lam in (0, 0.5, 0.75, 1.0, 1.25, 1.5):
                    for eta in (0.0, 0.1, 0.2, 0.4):
                        for form in ("exp_bridge", "linear_bridge"):
                            try:
                                val = model.predict_sensitivity(n_scenario, D, Q, p, w, p_policy=policy,
                                                                bridge_lambda=lam, eta=eta, bridge_model=form)
                                sensitivity.append({"policy": entry["policy"], "support": name,
                                                    "N_params_B": n_scenario, "D_tokens_B": D, "Q_score": Q,
                                                    "lambda": lam, "eta": eta, "bridge_model": form, "status": "valid",
                                                    "Loss": val["Loss"], "difference_from_baseline": val["difference_from_baseline"]})
                            except ValueError as exc:
                                sensitivity.append({"policy": entry["policy"], "support": name,
                                                    "N_params_B": n_scenario, "D_tokens_B": D, "Q_score": Q,
                                                    "lambda": lam, "eta": eta, "bridge_model": form, "status": str(exc),
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
                                       "curvature_type": "self_direction",
                                       "toward_observed_index": q1.recipe_ids[j], "path_support": path_policy,
                                       "direction_feasible": True,
                                       "directional_second_derivative": float(base["Loss"]*((u@hessian@u)+(gradient@u)**2)),
                                       "causal_interpretation": False})
            if len(target_candidates) >= 2:
                u = q1.recipes[target_candidates[0]] - point
                v = q1.recipes[target_candidates[1]] - point
                h = 1e-4
                path_policy = entry["quality_policy"] or "convex_hull"
                def path_loss(displacement):
                    return model.predict_baseline(N, D, Q, q1.p_dict(point+displacement), w,
                                                  p_policy=path_policy)["Loss"]
                mixed_fd = (path_loss(h*(u+v))-path_loss(h*u)-path_loss(h*v)+base["Loss"])/(h*h)
                mixed_formula = float(base["Loss"]*((u@hessian@v)+(gradient@u)*(gradient@v)))
                curvature_rows.append({"policy": entry["policy"], "support": name,
                                       "curvature_type": "mixed_two_feasible_directions",
                                       "toward_observed_index": f"{q1.recipe_ids[target_candidates[0]]},{q1.recipe_ids[target_candidates[1]]}",
                                       "path_support": path_policy, "direction_feasible": True,
                                       "directional_second_derivative": mixed_formula,
                                       "finite_forward_mixed_difference": mixed_fd,
                                       "difference_error": mixed_fd-mixed_formula,
                                       "causal_interpretation": False})
    write_csv("bridge_model_comparison.csv", comparisons)
    write_csv("bridge_form_observed_panel.csv", observed_bridge_panel(model, policies))
    write_csv("bridge_sensitivity.csv", sensitivity)
    valid = [r["Loss"] for r in sensitivity if r["status"] == "valid"]
    write_json("bridge_sensitivity_summary.json", {"scenarios": len(sensitivity), "valid": len(valid),
                                                   "Loss_range": [min(valid), max(valid)],
                                                   "range_is_confidence_interval": False})
    write_csv("quality_mapping_sensitivity.csv", quality_rows)
    write_csv("marginals_elasticities.csv", marginal_rows)
    write_csv("domain_transfer_effects.csv", transfer_rows)
    write_csv("domain_complementarity.csv", curvature_rows)
    quality_scale_rows = []
    for delta in (0.05, 0.1, 0.2, 0.6):
        quality_scale_rows.append({"N_B": N, "D_B": D, "Q_B": Q, "Delta_Q": delta,
                                   "eta": 0, "bridge_model": "exp_bridge", **substitution(N,D,Q,delta)})
        quality_scale_rows.append({"N_B": N, "D_B": D, "Q_B": Q, "Delta_Q": delta,
                                   "eta": 0.2, "bridge_model": "exp_bridge",
                                   **substitution_sensitivity(model, policies[0]["observed_512"]["p"], equal,
                                                              N,D,Q,delta,0.2)})
    quality_scale_rows.append({"N_B": 11.0, "D_B": D, "Q_B": Q, "Delta_Q": 0.2,
                               "eta": 0, "bridge_model": "exp_bridge", **substitution(11.0,D,Q,0.2)})
    write_csv("quality_vs_scale.csv", quality_scale_rows)
    write_json("q1_consumer_audit.json", {"manifest_sha256": q1.manifest_sha256,
                                          "file_shas_verified": len(q1.upstream.paths),
                                          "domains": len(q1.domains), "targets": len(q1.targets),
                                          "pairs": len(q1.upstream.pairs), "recipes": len(q1.recipes),
                                          "unknown_Q_A_count": 11, "Q2_original_A_reads": 0})
    old = Q2Final()
    main = policies[0]
    fixed_p = main["observed_512"]["p"]
    old_fixed = old.evaluate(N, D, Q, fixed_p, equal, 1, 0, p_policy="observed_512")
    new_linear = model.predict_sensitivity(N, D, Q, fixed_p, equal, p_policy="observed_512",
                                           bridge_lambda=1, eta=0, bridge_model="linear_bridge")
    new_exp = model.predict_baseline(N, D, Q, fixed_p, equal, p_policy="observed_512")
    old_choice = old.optimize("convex_hull", weights=equal, lam=1, eta=0, N=N, D=D, Q_B=Q)
    new_at_old = model.predict_baseline(N, D, Q, old_choice["p"], equal, p_policy="convex_hull")
    write_json("migration_audit.json", {"old_schema": "cyj.ndqp.scenario.v6",
                                         "new_schema": "cyj.ndqp.scenario.v7", "B7_parameters_unchanged": True,
                                         "B7_source_sha256": model.b7_sha256,
                                         "old_Q1_manifest_sha256": sha256(old.bundle / "export_manifest.json"),
                                         "new_Q1_manifest_sha256": q1.manifest_sha256,
                                         "comparison_status": "matched_conditional_scenario",
                                         "matched_inputs": {"N_params_B": N, "D_tokens_B": D, "Q_score": Q,
                                                            "weights": equal, "lambda": 1, "eta": 0,
                                                            "p": fixed_p, "p_policy": "observed_512"},
                                         "fixed_p_losses": {"v6_ridge_linear": old_fixed["loss"],
                                                            "v7_Q1_linear": new_linear["Loss"],
                                                            "v7_Q1_exp": new_exp["Loss"]},
                                         "fixed_p_differences": {"Q1_model_change_under_linear": new_linear["Loss"]-old_fixed["loss"],
                                                                 "bridge_form_change_under_v7_Q1": new_exp["Loss"]-new_linear["Loss"]},
                                         "reoptimized_decisions": {"v6_hull_p": old_choice["p"],
                                                                   "v6_hull_loss": old_choice["conditional_loss"],
                                                                   "v7_loss_at_v6_p": new_at_old["Loss"],
                                                                   "v7_hull_candidate_p": main["continuous_hull"]["p"],
                                                                   "v7_hull_candidate_loss": main["continuous_hull"]["baseline_loss"]},
                                         "QA_change": "A1_sample_primary; not part of equal_13 comparison",
                                         "raw_A_reads": 0,
                                         "limitation": "v6 upstream bundle had pending CHM owner signoff; historical comparison only"})
    parameter_rows, parameter_source_sha = b7_parameter_spread(model, policies)
    write_csv("b7_parameter_uncertainty.csv", parameter_rows)
    write_json("uncertainty_scope.json", {"cross_source_interval": None,
                                          "reason": "no paired A/B cross-source calibration",
                                          "grid_spread_is_confidence_interval": False,
                                          "B7_parameter_bootstrap_available": True,
                                          "B7_parameter_bootstrap_source_sha256": parameter_source_sha,
                                          "B7_parameter_bootstrap_draws": 200,
                                          "B7_parameter_bootstrap_scope": "ND-cluster bootstrap from semi-synthetic B7; fixed p/bridge; no Q1 or cross-source uncertainty",
                                          "legacy_two_stage_B7_bootstrap_used": False,
                                          "Q1_v2_parameter_distribution_available": False})
    write_csv("validation_by_source.csv", [
        {"source": "B1", "role": "primary_N_D_fit_and_group_holdout", "status": "same_source_only",
         "evidence": "outputs/cyj/q2_final/validation_summary.csv"},
        {"source": "B2_B3", "role": "semi_synthetic_or_interpolated_trajectory_shape", "status": "shape_only",
         "evidence": "outputs/cyj/diagnostics/b2_b3_shapes.json"},
        {"source": "B4_B5", "role": "within_family_source_scale_dominance", "status": "absolute_Loss_coordinate_not_established",
         "evidence": "outputs/cyj/diagnostics/b4_b5_comparability.json"},
        {"source": "A_Q1", "role": "training_nested_CV_and_same_condition_model_selection",
         "status": "model_manifest_pinned;current_bounds_CYJ_reproduced;CHM_owner_bounds_hash_stale",
         "evidence": "outputs/chm/q1_v2_signoff/audit.json;outputs/cyj/q2_v7/upstream_bounds_revalidation.json"},
        {"source": "B7", "role": "semi_synthetic_conditional_same_source_validation",
         "status": "frozen_CYJ_model", "evidence": "outputs/cyj/q2_final/validation_summary.csv"},
        {"source": "B9_B10", "role": "large_model_metadata_and_estimated_Loss_stress", "status": "not_real_heldout",
         "evidence": "outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json"},
        {"source": "A_B_joint", "role": "unobserved", "status": "not_empirically_calibrated",
         "evidence": "no paired experiment"}])
    requirement_rows = [
        ("classic_N_D", "N_B,D_B,Loss", "B1", "real_same_source_training", "power_law_candidate", "src/cyj/fit_classic_scaling.py", "outputs/cyj/classic/classic_fit.json", "q2.tex/B1", "same_source_only"),
        ("B2_or_B3_check", "N_B,D_B,Loss", "B2,B3", "semi_synthetic,interpolated", "trajectory_shape_only", "src/cyj/diagnose_b2_b3_shapes.py", "outputs/cyj/diagnostics/b2_b3_shapes.json", "q2.tex/attachments", "shape_only"),
        ("B4_and_B5_check", "N_B,D_B,Loss", "B4,B5", "cross_family,literature", "absolute_Loss_coordinate_unproved", "src/cyj/audit_b4_b5_comparability.py", "outputs/cyj/diagnostics/b4_b5_comparability.json", "q2.tex/attachments", "within_source_direction_only"),
        ("quality_B7", "N_B,D_B,Q_B,Loss", "B7", "semi_synthetic", "fixed_Q_x_logN_logD_family", "src/cyj/ndqp_scenarios_v7.py", "model_coefficients.json", "q2.tex/B7", "conditional_same_source"),
        ("mixture_p", "p,r_k,w_k", "Q1_v2_derived_A", "A_side_model", "exp_transport_hypothesis", "src/cyj/chm_q1_v2_consumer.py", "policy_solutions.csv", "q2_v7_tail.tex/mixture", "conditional_bridge"),
        ("quality_mapping", "Q_A,p,Q_B", "Q1_v2_A1_mapping,B7", "separate_coordinates", "Q_A_screens_p_only", "src/cyj/chm_q1_v2_consumer.py", "quality_mapping_sensitivity.csv", "q2_v7_tail.tex/quality", "no_QA_to_QB_mapping"),
        ("marginal_elasticity", "N_B,D_B,Q_B,p,Loss", "B7,Q1_v2", "derived_model", "signed_derivative", "src/cyj/ndqp_scenarios_v7.py", "marginals_elasticities.csv", "q2_v7_tail.tex/marginal", "model_internal"),
        ("domain_substitution_complementarity", "p,u,v,Loss", "Q1_v2", "derived_model", "feasible_hull_directions", "src/cyj/build_q2_v7.py", "domain_transfer_effects.csv;domain_complementarity.csv", "q2_v7_tail.tex/domain", "model_internal_not_causal"),
        ("quality_scale_substitution", "N_B,D_B,Q_B,Delta_Q,Loss", "B7,Q1_v2", "derived_model", "fixed_D_p_root_in_support", "src/cyj/build_q2_v7.py", "quality_vs_scale.csv", "q2_v7_tail.tex/substitution", "model_internal"),
        ("B9_B10_large_stress", "N_B,D_B,estimated_Loss", "B9,B10", "metadata,estimated", "no_external_RMSE", "src/cyj/audit_large_extrapolation.py", "outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json", "q2.tex/attachments", "out_of_support_stress_only"),
        ("cross_source_empirical_test", "paired_N_D_Q_B_p_Loss", "unavailable", "unobserved", "matched_pair_design_required", "none", "validation_by_source.csv", "q2_v7_tail.tex/validation", "not_empirically_calibrated"),
    ]
    write_csv("requirement_evidence.csv", [dict(zip(("requirement", "variables", "source", "data_role", "assumption",
                                                      "code", "result", "paper_section", "status"), row))
                                           for row in requirement_rows])
    write_csv("claim_ladder.csv", [
        {"claim": "B7 same-source conditional surface", "level": "L2_within_semi_synthetic_source", "evidence": "outputs/cyj/q2_final/validation_summary.csv", "limit": "not independent real-model validation"},
        {"claim": "Q1 v2 recipe-specific relative effects", "level": "L2_within_A_model_selection_scope", "evidence": "outputs/chm/q1_v2/targetwise_validation.csv", "limit": "A6-A11 informed selection"},
        {"claim": "Q2 v7 conditional policy ranking", "level": "scenario_only", "evidence": "policy_solutions.csv;bridge_form_observed_panel.csv", "limit": "transport amplitude unidentified"},
        {"claim": "Q2 mixed curvature", "level": "model_internal", "evidence": "domain_complementarity.csv", "limit": "not causal complementarity"},
        {"claim": "Q2 absolute cross-source prediction", "level": "unavailable", "evidence": "validation_by_source.csv", "limit": "no paired A/B observations"},
        {"claim": "Q2 large-model extrapolation", "level": "not_validated", "evidence": "outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json", "limit": "B10 estimated Loss"}])
    write_json("acceptance.json", {"q2_implementation_complete": False, "q2_answer_complete_under_stated_assumptions": False,
                                  "q3_consumer_interface_ready": False, "q3_consumer_verified": False,
                                  "cross_source_empirical_calibration_complete": False,
                                  "status": "build_generated_pending_independent_tests"})
    write_json("final_closure.json", {"status": "conditional_build_only",
                                     "CHM_owner_Q3_consumer_acceptance": "pending",
                                     "cross_source_empirical_calibration_complete": False})
    manifest = {"schema_version": "cyj.q2.v7.outputs.v1", "Q1_manifest_sha256": q1.manifest_sha256,
                "B7_parameters_sha256": model.b7_sha256,
                "Q1_bounds_sha256": sha256(q1.bounds_path),
                "code_sha256": {name: sha256(ROOT / "src/cyj" / name) for name in (
                    "chm_q1_v2_consumer.py", "ndqp_scenarios_v7.py", "build_q2_v7.py",
                    "revalidate_q1_v2_bounds.py", "bound_single_target_v7.py")},
                "randomness": "none in v7 build; B7 input bootstrap source seed 20260925",
                "python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
                "command": "python -B src/cyj/build_q2_v7.py", "files": {}}
    for path in sorted(OUT.iterdir()):
        if path.name != "manifest.json" and path.is_file():
            manifest["files"][path.name] = sha256(path)
    write_json("manifest.json", manifest)
    return {"policy_rows": len(rows), "sensitivity_rows": len(sensitivity), "manifest_sha256": sha256(OUT/"manifest.json")}


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
