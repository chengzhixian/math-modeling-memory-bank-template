"""Build the competition-role-aligned, explicitly conditional Q2 v8 evidence bundle."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from audit_b4_b5_comparability import read as read_b4_b5
from chm_q1_v2_consumer import ROOT, sha256
from fit_b7_quality_extension_from_b1 import B1_FILE, B7_FILE, b1_value
from ndqp_scenarios_v8 import BOUNDS, ConditionalV8, VERSION
from ndqp_scenarios_v7 import ConditionalV7
from smoke_q3_v8 import main as smoke_q3
from validate_b3_against_b1 import main as validate_trajectories

OUT = ROOT / "outputs/cyj/q2_v8"
N, D = 1.0, 100.0


def write_json(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                          encoding="utf-8", newline="\n")


def write_csv(name, rows):
    if not rows:
        raise ValueError(f"empty v8 table: {name}")
    with (OUT/name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(k for row in rows for k in row)),
                                lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def equal_weights(model):
    return {target: 1/len(model.q1.targets) for target in model.q1.targets}


def observed_policy(model, weights):
    accepted = []
    excluded_zero = 0
    for i, vector in enumerate(model.q1.recipes):
        p = model.q1.p_dict(vector)
        stats = model.q1.qa_stats(p, "quality_direct_and_near")
        if stats["mean_Q_A_on_mapped"] is None:
            excluded_zero += 1
            continue
        if not stats["eligible"]:
            continue
        result = model.predict_baseline_v8(N, D, p, weights, p_policy="observed_512")
        accepted.append((result["Loss"], i, result))
    if not accepted:
        raise ValueError("no observed Q1 recipe satisfies the quality policy")
    accepted.sort(key=lambda row: (row[0], row[1]))
    value, index, prediction = accepted[0]
    model.q1.support(model.q1.p_dict(model.q1.recipes[index]), "quality_direct_and_near")
    return {"policy": "observed_512_plus_quality_direct_and_near",
            "quality_mapping_policy": "direct_and_near", "N_params_B": N, "D_tokens_B": D,
            "weights": weights, "recipe_index": model.q1.recipe_ids[index],
            "p": model.q1.p_dict(model.q1.recipes[index]), "Loss": value,
            "Q_A_mapped": prediction["Q_A_mapped"], "Q_B_proxy": prediction["Q_B_proxy_or_native"],
            "mapped_coverage": prediction["mapped_coverage"],
            "eligible_observed_count": len(accepted), "zero_coverage_excluded": excluded_zero,
            "optimality": "exact_only_among_eligible_512_observed_recipes",
            "next_distinct_Loss_gap": next((v-value for v, _, _ in accepted if v-value > 1e-10), None)}


def epsilon_max(model, center, i, j):
    recipes = model.q1.recipes
    direction = np.zeros(len(model.q1.domains)); direction[i] = 1; direction[j] = -1
    matrix = np.column_stack((recipes.T, -direction))
    c = np.zeros(len(recipes)+1); c[-1] = -1
    result = linprog(c, A_eq=matrix, b_eq=center,
                     bounds=[(0, None)]*len(recipes)+[(0, 1)], method="highs")
    if not result.success:
        raise ValueError(f"Q1 hull pair-direction LP failed: {i},{j}: {result.message}")
    return float(result.x[-1]), float(np.max(np.abs(matrix@result.x-center)))


def domain_pairs(model, weights):
    center = np.mean(model.q1.recipes, axis=0)
    p = model.q1.p_dict(center)
    evaluation = model.predict_baseline_v8(N, D, p, weights, p_policy="convex_hull")
    gradient = np.array([evaluation["gradients"]["p_ambient"][name] for name in model.q1.domains])
    hessian = model.p_hessian_baseline(N, D, p, weights)
    q1_hessian = model.q1.hessian(weights)
    substitution, interaction = [], []
    for i, domain_i in enumerate(model.q1.domains):
        for j in range(i+1, len(model.q1.domains)):
            domain_j = model.q1.domains[j]
            forward, residual_f = epsilon_max(model, center, i, j)
            reverse, residual_r = epsilon_max(model, center, j, i)
            derivative = float(gradient[i]-gradient[j])
            substitution.append({"domain_i": domain_i, "domain_j": domain_j,
                                 "transfer_direction": f"{domain_j}-> {domain_i}",
                                 "dLoss_depsilon": derivative,
                                 "favorable_direction": (f"{domain_j}-> {domain_i}" if derivative < 0 else
                                                         f"{domain_i}-> {domain_j}" if derivative > 0 else "local_tie"),
                                 "feasible_epsilon_max": forward,
                                 "reverse_feasible_epsilon_max": reverse,
                                 "hull_equation_residual_max": max(residual_f, residual_r),
                                 "evaluation_point": "mean_of_512_A4_recipes",
                                 "quality_bridge": "Q1_QA_minmax_proxy",
                                 "claim_scope": "local_model_direction_not_causal"})
            curvature = float(hessian[i,i]+hessian[j,j]-2*hessian[i,j])
            interaction.append({"domain_i": domain_i, "domain_j": domain_j,
                                "Q1_weighted_H_ij": float(q1_hessian[i,j]),
                                "v8_full_Loss_H_ij": float(hessian[i,j]),
                                "v8_transfer_direction_curvature": curvature,
                                "forward_epsilon_max": forward, "reverse_epsilon_max": reverse,
                                "interaction_label": "model_based_not_causal_complementarity",
                                "ambient_cross_partial_warning": "individual ambient coordinates leave simplex; use transfer curvature for feasible direction"})
    write_csv("domain_pair_substitution.csv", substitution)
    write_csv("domain_pair_interaction.csv", interaction)
    write_json("domain_pair_reference.json", {"p": p, "Loss": evaluation["Loss"],
                                                "mapped_coverage": evaluation["mapped_coverage"],
                                                "pair_count": len(substitution),
                                                "all_pairs_hull_feasible_in_both_directions": all(
                                                    x["feasible_epsilon_max"] > 1e-10 and
                                                    x["reverse_feasible_epsilon_max"] > 1e-10
                                                    for x in substitution)})
    return len(substitution)


def finite_scale_root(model, n, d, q, delta, *, compensating):
    if q+delta > BOUNDS[2][1]:
        return {"status": "quality_out_of_support", "root_N_params_B": None}
    target = model.base(n, d, q if compensating else q+delta)[0]
    fixed_q = q+delta if compensating else q
    lo, hi = BOUNDS[0]
    flo, fhi = model.base(lo, d, fixed_q)[0]-target, model.base(hi, d, fixed_q)[0]-target
    if flo*fhi > 0:
        return {"status": "no_root_in_support", "root_N_params_B": None,
                "endpoint_residuals": [flo, fhi]}
    for _ in range(90):
        mid = (lo+hi)/2
        if (model.base(mid, d, fixed_q)[0]-target)*flo > 0:
            lo = mid
        else:
            hi = mid
    root = (lo+hi)/2
    return {"status": "root_in_support", "root_N_params_B": root,
            "Loss_residual": model.base(root, d, fixed_q)[0]-target}


def marginals_tradeoff(model, main, weights):
    p = main["p"]
    rows, tradeoff = [], []
    for n in (.1, 1.0, 10.0):
        evaluation = model.predict_baseline_v8(n, D, p, weights, p_policy="quality_direct_and_near")
        gradients, elasticities = evaluation["gradients"], evaluation["elasticities_signed"]
        rows.append({"policy": main["policy"], "N_params_B": n, "D_tokens_B": D,
                     "Q_A_mapped": evaluation["Q_A_mapped"],
                     "Q_B_proxy": evaluation["Q_B_proxy_or_native"], "Loss": evaluation["Loss"],
                     "N_marginal": gradients["N_B"], "D_marginal": gradients["D_B"],
                     "quality_proxy_marginal": gradients["Q_B_proxy_or_native"],
                     "Q_A_mapped_marginal": gradients["Q_A_mapped"],
                     "N_elasticity": elasticities["N"], "D_elasticity": elasticities["D"],
                     "quality_proxy_elasticity": elasticities["Q_B_proxy_or_native"],
                     "Q_A_mapped_elasticity": elasticities["Q_A_mapped"],
                     "p_marginal_min": min(gradients["p_ambient"].values()),
                     "p_marginal_max": max(gradients["p_ambient"].values())})
        q = evaluation["Q_B_proxy_or_native"]
        roots = {str(delta): finite_scale_root(model, n, D, q, delta, compensating=False)
                 for delta in (.05, .1)}
        compensation = {str(delta): finite_scale_root(model, n, D, q, delta, compensating=True)
                        for delta in (.05, .1)}
        tradeoff.append({"policy": main["policy"], "N_params_B": n, "D_tokens_B": D,
                         "Q_B_proxy": q, "dN_dQproxy": -gradients["Q_B_proxy_or_native"]/gradients["N_B"],
                         "dlnN_dlnQproxy": -elasticities["Q_B_proxy_or_native"]/elasticities["N"],
                         "equivalent_oldQ_N_delta_0_05": roots["0.05"]["root_N_params_B"],
                         "equivalent_oldQ_N_delta_0_05_status": roots["0.05"]["status"],
                         "equivalent_oldQ_N_delta_0_1": roots["0.1"]["root_N_params_B"],
                         "equivalent_oldQ_N_delta_0_1_status": roots["0.1"]["status"],
                         "constant_L_newQ_N_delta_0_05": compensation["0.05"]["root_N_params_B"],
                         "constant_L_newQ_N_delta_0_05_status": compensation["0.05"]["status"],
                         "constant_L_newQ_N_delta_0_1": compensation["0.1"]["root_N_params_B"],
                         "constant_L_newQ_N_delta_0_1_status": compensation["0.1"]["status"],
                         "scope": "fixed_p_hypothetical_proxy_quality_intervention_not_independent_QA_observation"})
    write_csv("marginals_elasticities.csv", rows)
    write_csv("quality_scale_local_tradeoff.csv", tradeoff)
    return rows, tradeoff


def scale_order_validation(model):
    rows = []
    for source in ("B4", "B5"):
        data = read_b4_b5(source)
        grouped = {}
        for index, row in enumerate(data, 2):
            grouped.setdefault((row["family"], row.get("source") if source == "B5" else None), []).append((index, row))
        for (family, stratum), members in grouped.items():
            for a, (line_a, first) in enumerate(members):
                for line_b, second in members[a+1:]:
                    small, large = first, second
                    small_line, large_line = line_a, line_b
                    if not (large["N_params_B"] >= small["N_params_B"] and
                            large["D_tokens_B"] >= small["D_tokens_B"] and
                            (large["N_params_B"] > small["N_params_B"] or
                             large["D_tokens_B"] > small["D_tokens_B"])):
                        if (small["N_params_B"] >= large["N_params_B"] and
                            small["D_tokens_B"] >= large["D_tokens_B"] and
                            (small["N_params_B"] > large["N_params_B"] or
                             small["D_tokens_B"] > large["D_tokens_B"])):
                            small, large = large, small
                            small_line, large_line = large_line, small_line
                        else:
                            continue
                    p1 = float(b1_value(model.b1, small["N_params_B"], small["D_tokens_B"]))
                    p2 = float(b1_value(model.b1, large["N_params_B"], large["D_tokens_B"]))
                    obs = large["val_loss"]-small["val_loss"]
                    model_delta = p2-p1
                    inside = all(BOUNDS[k][0] <= r[key] <= BOUNDS[k][1]
                                 for r in (small, large)
                                 for k, key in ((0, "N_params_B"), (1, "D_tokens_B")))
                    rows.append({"source": source, "family": family, "source_stratum": stratum,
                                 "line_smaller": small_line, "line_larger": large_line,
                                 "observed_direction": math.copysign(1, obs) if obs else 0,
                                 "model_direction": math.copysign(1, model_delta) if model_delta else 0,
                                 "direction_agreement": bool(obs*model_delta > 0),
                                 "both_points_in_v8_ND_support": inside,
                                 "role": "directional_description_not_common_Loss_coordinate_or_external_RMSE"})
    if not rows:
        raise ValueError("no B4/B5 comparable scale-order pairs")
    write_csv("scale_order_validation.csv", rows)
    summary = {source: {scope: {"pairs": sum(r["source"] == source and
                                               r["both_points_in_v8_ND_support"] == inside for r in rows),
                                "agreement": sum(r["source"] == source and
                                                 r["both_points_in_v8_ND_support"] == inside and
                                                 r["direction_agreement"] for r in rows)}
                        for scope, inside in (("inside_common_support", True), ("outside_support_stress", False))}
               for source in ("B4", "B5")}
    write_json("scale_order_validation_summary.json", {"results": summary,
               "same_loss_coordinate_verified": False, "external_absolute_RMSE": None})
    return summary


def b9_b10_stress():
    source = json.loads((ROOT/"outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json").read_text(encoding="utf-8"))
    if source["data_roles"]["B10"] != "estimated_loss_stress_reference_not_independent_test":
        raise ValueError("B10 data role changed")
    checks = source["checks"]
    output = {"B9_role": "metadata_only", "B10_role": "estimated_loss_stress_only",
              "B10_rows": checks["B10_rows"],
              "B10_above_B1_N_support_ratio": checks["B10_above_B1_N_max_count"]/checks["B10_rows"],
              "B10_above_B1_D_support_ratio": checks["B10_above_B1_D_max_count"]/checks["B10_rows"],
              "B10_external_RMSE": None,
              "source_audit_sha256": sha256(ROOT/"outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json")}
    write_json("b9_b10_support_stress.json", output)
    return output


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model = ConditionalV8()
    weights = equal_weights(model)
    validate_trajectories()
    main_policy = observed_policy(model, weights)
    write_json("main_policy.json", main_policy)
    smoke_q3()
    reference = model.predict_baseline_v8(N, D, model.q1.reference, weights,
                                           p_policy="algebraic_reference_only")
    main_prediction = model.predict_baseline_v8(N, D, main_policy["p"], weights,
                                                p_policy="quality_direct_and_near")
    write_json("model_definition.json", {"schema_version": VERSION,
               "formula": "(B1_E+B1_A*N^-alpha+B1_B*D^-beta+(1-Q_B_proxy)*G(N,D))*exp(r_w(p))",
               "quality_proxy": "Q1 mapped Q_A normalized by frozen mapped-domain min/max to B7 [0.1,1]",
               "Q1_quality_mapping": "direct_and_near", "Q_A_to_Q_B_empirically_calibrated": False,
               "mixture_bridge_empirically_calibrated": False,
               "quality_and_mixture_double_counting_identified": False,
               "formal_support": BOUNDS, "p_support": "observed_A4_or_A4_convex_hull",
               "reference_anchor": {"p_ref_r_w": reference["Q1_weighted_effect"],
                                    "Q_A_reference": reference["Q_A_mapped"],
                                    "Q_B_proxy_reference": reference["Q_B_proxy_or_native"],
                                    "Loss_at_reference": reference["Loss"]}})
    fit = json.loads((OUT/"b7_quality_extension.json").read_text(encoding="utf-8"))
    write_json("model_coefficients.json", {"B1_backbone": model.b1,
               "B7_quality_extension": fit["quality_parameters"],
               "B1_fit_sha256": fit["B1_fit_sha256"], "B7_source_sha256": fit["B7_source_sha256"],
               "quality_fit_sha256": model.quality_fit_sha256,
               "Q1_manifest_sha256": model.q1.manifest_sha256})
    quality_rows = []
    for name, scale in (("compressed", .5), ("identity_normalized", 1.0), ("expanded", 1.5)):
        result = model.evaluate(N, D, main_policy["p"], weights, p_policy="quality_direct_and_near",
                                quality_mode="q1_quality_bridge_sensitivity",
                                quality_bridge_scale=scale)
        quality_rows.append({"quality_bridge_scenario": name, "scale": scale,
                             "Q_A_mapped": result["Q_A_mapped"],
                             "Q_B_proxy": result["Q_B_proxy_or_native"],
                             "mapped_coverage": result["mapped_coverage"],
                             "unmapped_mass": result["unmapped_mass"],
                             "Loss": result["Loss"], "empirically_calibrated": False})
    write_csv("quality_bridge_sensitivity.csv", quality_rows)
    marginal_rows, tradeoff_rows = marginals_tradeoff(model, main_policy, weights)
    pair_count = domain_pairs(model, weights)
    b45 = scale_order_validation(model)
    b910 = b9_b10_stress()
    old_main = json.loads((ROOT/"outputs/cyj/q2_v7/main_policy.json").read_text(encoding="utf-8"))
    old_model = ConditionalV7()
    old_prediction = old_model.predict_baseline(N, D, .5, old_main["observed_512"]["p"],
                                                weights, p_policy="observed_512")
    with (ROOT/"outputs/cyj/q2_v7/quality_vs_scale.csv").open(encoding="utf-8", newline="") as stream:
        old_roots = list(csv.DictReader(stream))
    old_root = next(row for row in old_roots if float(row["N_B"]) == N and float(row["D_B"]) == D
                    and float(row["Q_B"]) == .5 and float(row["Delta_Q"]) == .05
                    and float(row["eta"]) == 0 and row["bridge_model"] == "exp_bridge")
    old_smoke = json.loads((ROOT/"outputs/cyj/q3_v7_sample_smoke.json").read_text(encoding="utf-8"))
    new_smoke = json.loads((OUT/"q3_fixed_p_smoke.json").read_text(encoding="utf-8"))
    old_solution = old_smoke["solution"]
    old_recipe_pos = model.q1.recipe_ids.index(old_smoke["recipe_index"])
    old_at_v8 = model.predict_baseline_v8(old_solution["N_params_B"], old_solution["D_tokens_B"],
                                           model.q1.p_dict(model.q1.recipes[old_recipe_pos]), weights,
                                           p_policy="observed_512")
    write_json("migration_audit.json", {"old_version": "cyj.ndqp.scenario.v7",
               "new_version": VERSION,
               "old_backbone": "B7_joint_8_param", "new_backbone": "B1_fixed_plus_B7_quality_extension",
               "old_quality_input": "native_Q_B", "new_quality_input": "Q1_QA_bridge_baseline",
               "old_B2B3_validation": "shape_only", "new_B2B3_validation": "normalized_model_validation_not_independent",
               "old_domain_relation": "recipe_direction", "new_domain_relation": "explicit_domain_pair",
               "old_main_Loss": old_main["observed_512"]["baseline_loss"],
               "new_main_Loss": main_prediction["Loss"],
               "old_main_p": old_main["observed_512"]["p"], "new_main_p": main_policy["p"],
               "new_main_elasticities": main_prediction["elasticities_signed"],
               "old_elasticities_at_old_main": old_prediction["elasticities_signed"],
               "old_quality_scale_equivalent_N_delta_0_05": float(old_root["N_prime_B"]),
               "new_quality_scale_equivalent_N_delta_0_05": tradeoff_rows[1]["equivalent_oldQ_N_delta_0_05"],
               "quality_scale_coordinates_differ": "old_native_QB_0.5_vs_new_Q1_QA_proxy",
               "old_Q3_sample_Loss": old_solution["loss"],
               "v8_at_old_Q3_ND_p_Loss": old_at_v8["Loss"],
               "new_Q3_fixed_p_sample_Loss": new_smoke["solution"]["Loss"],
               "new_Q3_fixed_p_sample_ND": {"N_params_B": new_smoke["solution"]["N_params_B"],
                                           "D_tokens_B": new_smoke["solution"]["D_tokens_B"]},
               "new_Q3_joint_optimum": None,
               "new_Q3_joint_optimum_reason": "final joint Q3 optimization is CHM-owned and excluded by this task",
               "comparison_status": "different_backbone_and_quality_coordinate_not_common_empirical_Loss_measure"})
    write_json("q3_v8_consumer_sample.json", {"input": {"N_params_B": N, "D_tokens_B": D,
               "p": main_policy["p"], "weights": weights,
               "p_policy": "quality_direct_and_near", "quality_mapping_policy": "direct_and_near"},
               "output": main_prediction, "CHM_owner_consumption_verified": False})
    write_csv("requirement_evidence.csv", [
        {"requirement": name, "evidence": evidence, "scope": scope} for name, evidence, scope in (
            ("B1_classic_backbone", "b7_quality_extension.json;model_coefficients.json", "B1_pinned"),
            ("B7_quality_extension", "b7_quality_extension.json;b7_backbone_comparison.csv", "semi_synthetic"),
            ("Q1_quality_in_Loss", "model_definition.json;quality_bridge_sensitivity.csv", "uncalibrated_proxy"),
            ("Q1_p_in_Loss", "model_definition.json;main_policy.json", "conditional_relative_bridge"),
            ("B3_model_validation", "b2_b3_model_validation.csv;b2_b3_validation_summary.json", "interpolated_not_independent"),
            ("B4_B5_direction", "scale_order_validation.csv;scale_order_validation_summary.json", "descriptive_no_common_Loss_coordinate"),
            ("B9_B10_roles", "b9_b10_support_stress.json", "estimated_stress_only"),
            ("N_D_quality_p_marginals", "marginals_elasticities.csv;domain_pair_substitution.csv", "model_internal"),
            ("N_D_quality_elasticities", "marginals_elasticities.csv", "model_internal"),
            ("domain_pair_substitution", "domain_pair_substitution.csv", "136_hull_directions"),
            ("domain_pair_interaction", "domain_pair_interaction.csv", "not_causal"),
            ("quality_scale_finite_and_local", "quality_scale_local_tradeoff.csv", "fixed_p_hypothetical_proxy_quality"),
            ("migration_v7_to_v8", "migration_audit.json", "different_quality_coordinates"),
            ("Q3_v8_interface", "q3_v8_consumer_sample.json;q3_fixed_p_smoke.json", "owner_acceptance_pending"),
            ("cross_source_empirical_calibration", "model_definition.json", "unavailable"),
        )])
    write_json("final_closure.json", {"status": "conditional_v8_engineering_candidate_pending_independent_acceptance",
               "paper_layout_started": False, "CHM_Q3_owner_acceptance": False,
               "A_B_empirical_calibration": False})
    write_json("acceptance.json", {"q2_implementation_complete": False,
               "q2_competition_requirements_complete": False,
               "q3_consumer_interface_ready": False,
               "q3_consumer_verified_by_CHM": False,
               "cross_source_empirical_calibration_complete": False,
               "release_remote_verified": False,
               "status": "generated_pending_independent_acceptance"})
    names = sorted(path.name for path in OUT.iterdir() if path.is_file() and path.name != "manifest.json")
    manifest = {"schema_version": "cyj.q2.v8.outputs.v1", "Q1_manifest_sha256": model.q1.manifest_sha256,
                "B1_fit_sha256": sha256(B1_FILE), "B7_quality_fit_sha256": model.quality_fit_sha256,
                "python": platform.python_version(), "numpy": np.__version__,
                "command": "python -B src/cyj/fit_b7_quality_extension_from_b1.py; python -B src/cyj/build_q2_v8.py",
                "code_sha256": {name: sha256(ROOT/"src/cyj"/name) for name in
                                ("fit_b7_quality_extension_from_b1.py", "validate_b3_against_b1.py",
                                 "ndqp_scenarios_v8.py", "build_q2_v8.py", "smoke_q3_v8.py")},
                "files": {name: sha256(OUT/name) for name in names}}
    write_json("manifest.json", manifest)
    return {"main_Loss": main_prediction["Loss"], "pair_count": pair_count,
            "B4_B5": b45, "B9_B10": b910,
            "manifest_sha256": sha256(OUT/"manifest.json")}


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
