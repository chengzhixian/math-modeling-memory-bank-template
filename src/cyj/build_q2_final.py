"""Rebuild conditional Q2 artifacts from frozen B audits and a Q1 derived export.

This consumer never opens attachment-A inputs. Run the separate Q1 exporter first.
The cross-source bridge remains an engineering scenario, not an estimated effect.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np

from joint_ndqp_scenarios import ROOT
from q2_final_core import BUNDLE, MAIN_NDQ, Q2Final, VERSION

OUT = ROOT / "outputs/cyj/q2_final"
FIG = ROOT / "figures/cyj/q2_final"


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(name, obj):
    path = OUT / name
    path.write_bytes((json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"))


def write_csv(name, rows, fields=None):
    if fields is None:
        fields = list(rows[0])
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validation_rows(model):
    rows = []
    def add(group, metric, value, n, role, source, meaning):
        rows.append(dict(group=group, metric=metric, value=value, sample_or_pair_count=n,
                         role=role, source_file=source, interpretation=meaning))
    classic = read_json("outputs/cyj/classic/classic_fit.json")
    source = "outputs/cyj/classic/classic_fit.json"
    add("B1", "fit_rmse", classic["full_fit"]["metrics"]["rmse"], 1176, "training", source,
        "Near-exact reconstruction warrants provenance caution")
    add("B1", "leave_one_N_group_mean_rmse", classic["validation"]["leave_one_model_size_out"]["aggregate"]["rmse"]["mean"], 8,
        "group_holdout", source, "Eight held-out N levels")
    add("B1", "token_tail_rmse", classic["validation"]["token_tail_70_30"]["metrics"]["rmse"], 360,
        "ordered_tail_holdout", source, "Within-family token tail")
    ablation = read_json("outputs/cyj/ablation/b1_terms.json")
    for term in ("full", "no_E", "no_N", "no_D"):
        add("B1", f"{term}_LOSO_RMSE_mean", ablation["summary"][term]["LOSO_RMSE_mean"], 8,
            "group_holdout_term_ablation", "outputs/cyj/ablation/b1_terms.json",
            "Each reduced model refit within train folds; same B1 data source")
    shapes = read_json("outputs/cyj/diagnostics/b2_b3_shapes.json")
    source = "outputs/cyj/diagnostics/b2_b3_shapes.json"
    for group in ("B2", "B3"):
        data = shapes[group.lower()]
        curves = data["curves"]
        adjacent = sum(r["rows"] - 1 for r in curves)
        add(group, "trajectory_count", len(curves), data["rows"], "shape_only", source,
            data["nature"])
        add(group, "fraction_curves_end_below_start", sum(r["val_loss_last_minus_first"] < 0 for r in curves) / len(curves),
            len(curves), "shape_only", source, "B3 interpolation is not independent external validation")
        add(group, "adjacent_loss_increase_fraction", data["total_adjacent_loss_increases"] / adjacent,
            adjacent, "shape_only", source, "Adjacent observations by source trajectory order")
        add(group, "mean_normalized_end_minus_start", sum(r["val_loss_last_minus_first"] / r["val_loss_first"] for r in curves) / len(curves),
            len(curves), "shape_only", source, "Each curve normalized by its own first loss")
    comp = read_json("outputs/cyj/diagnostics/b4_b5_comparability.json")
    source = "outputs/cyj/diagnostics/b4_b5_comparability.json"
    for group in ("B4", "B5"):
        data = comp["datasets"][group]
        add(group, "rows", data["rows"], data["rows"], "descriptive_within_source", source,
            "Cross-source absolute RMSE is not a validated common coordinate")
        valid = concordance(data["row_audit"])
        for key, value in valid.items():
            add(group, key, value, valid["dominance_pairs"], "within_family_source_descriptive", source,
                "Pairs share family and source; both N,D weakly increase, at least one strictly")
    nested = read_json("outputs/cyj/quality/b7_nested_cv_summary.json")
    source = "outputs/cyj/quality/b7_nested_cv_summary.json"
    for axis, summary in nested["axis_summary"].items():
        add("B7", f"nested_outer_{axis}_rmse", summary["rmse"], 450,
            "group_holdout_semi_synthetic", source, "Axis-wise held-level aggregate")
    add("B7", "nested_fold_count", len(nested["folds"]),
        sum(len(f["outer_source_lines"]) for f in nested["folds"]),
        "group_holdout_semi_synthetic", source, "24 held-level folds and 1350 pooled predictions across three axes")
    audit_b = read_json("outputs/cyj/b_data_audit.json")
    add("B6", "rows_nested_in_B7", audit_b["summary"]["dataset_rows"]["B6"],
        audit_b["summary"]["dataset_rows"]["B6"], "nested_in_B7", "outputs/cyj/b_data_audit.json",
        "B6 is a subset, not an independent validation set")
    conflict = read_json("outputs/cyj/quality/b7_b8_conflict_summary.json")
    source = "outputs/cyj/quality/b7_b8_conflict_summary.json"
    add("B8", "shared_B7_coordinates", conflict["shared_coordinates"], conflict["shared_coordinates"],
        "conflict_audit", source, "Same NDQ coordinate; separate loss source")
    add("B8", "nonzero_loss_difference_count", conflict["nonzero_loss_difference_count"], conflict["shared_coordinates"],
        "conflict_audit", source, "B8 cannot be pooled into B7 target")
    outer = read_json("outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json")
    source = "outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json"
    checks = outer["checks"]
    add("B9", "metadata_rows", checks["B9_rows"], checks["B9_rows"], "metadata_only", source,
        "No observed val_loss in B9")
    for key in ("B10_rows", "B10_above_B1_N_max_count", "B10_above_B1_D_max_count", "B10_minus_B1_curve_rmse_descriptive_only"):
        add("B10", key, checks[key], checks["B10_rows"], "estimated_stress_only", source,
            "Estimated loss is not independent measured holdout")
    add("B10", "N_max_over_B7_N_max", checks["B10_N_params_B_range"][1] / 11.97,
        checks["B10_rows"], "out_of_support_distance", source, "Ratio only; Q2 makes no prediction outside B7 support")
    add("B10", "D_max_over_B7_D_max", checks["B10_D_tokens_B_range"][1] / 600,
        checks["B10_rows"], "out_of_support_distance", source, "Ratio only; Q2 makes no prediction outside B7 support")
    held = read_csv(BUNDLE / "heldout_target_metrics.csv")
    a1b = [r for r in held if r["scope"] == "test_1B"]
    add("Q1_derived", "test_1B_targets_beating_constant_rmse", sum(r["absolute_rmse_beats_constant"] == "True" for r in a1b),
        len(a1b), "Q1_derived_heldout", "outputs/chm/q1_exports/q1_q2_bundle_v1/heldout_target_metrics.csv",
        "Observed Q1 heldout; 4/13 absolute-RMSE wins at 1B")
    paired = read_csv(BUNDLE / "paired_scale_metrics.csv")
    add("Q1_derived", "paired_1m_60m_targets", len(paired), len(paired), "Q1_derived_same_recipe",
        "outputs/chm/q1_exports/q1_q2_bundle_v1/paired_scale_metrics.csv", "Descriptive paired rank relation, not A-to-B calibration")
    return rows


def concordance(rows):
    groups = {}
    for row in rows:
        if row["N_params_B"] is None or row["D_tokens_B"] is None or row["val_loss"] is None:
            continue
        key = (row["family"], row["source"])
        groups.setdefault(key, []).append(row)
    pairs = concordant = discordant = ties = 0
    relative_loss_reductions = []
    for subset in groups.values():
        for x, y in itertools.combinations(subset, 2):
            n1, d1, l1 = (float(x[k]) for k in ("N_params_B", "D_tokens_B", "val_loss"))
            n2, d2, l2 = (float(y[k]) for k in ("N_params_B", "D_tokens_B", "val_loss"))
            if n1 <= n2 and d1 <= d2 and (n1 < n2 or d1 < d2):
                low, high = l1, l2
            elif n2 <= n1 and d2 <= d1 and (n2 < n1 or d2 < d1):
                low, high = l2, l1
            else:
                continue
            pairs += 1
            if low > 0:
                relative_loss_reductions.append((low - high) / low)
            if high < low:
                concordant += 1
            elif high > low:
                discordant += 1
            else:
                ties += 1
    return {"dominance_pairs": pairs, "concordant_pairs": concordant,
            "discordant_pairs": discordant, "tied_pairs": ties,
            "mean_relative_loss_reduction": sum(relative_loss_reductions) / len(relative_loss_reductions) if relative_loss_reductions else None,
            "concordance_fraction_non_tied": concordant / (concordant + discordant) if concordant + discordant else None}


def policy_rows(model):
    cases = [("observed_512", "equal_13", 1, 0), ("convex_hull", "equal_13", 1, 0),
             ("convex_hull", "arxiv_only", 1, 0), ("convex_hull", "pile_cc_only", 1, 0),
             ("minimax_13", "equal_13", 1, 0), ("quality_direct", "equal_13", 1, 0),
             ("quality_direct_and_near", "equal_13", 1, 0)]
    details, flat = {}, []
    for policy, target, lam, eta in cases:
        name = f"{policy}__{target}"
        result = model.optimize(policy, weights=model.weight_policy(target), lam=lam, eta=eta)
        details[name] = result
        row = {"scenario": name, "p_policy": policy, "target_weights": target,
               "bridge_lambda": lam, "eta": eta, "status": result["status"]}
        if result["status"] == "optimal_conditional":
            row.update(loss=result["conditional_loss"], weighted_relative_A_effect=result["weighted_relative_A_effect"],
                       factor=result["factor"], min_factor_B7_N=result["min_factor_over_B7_N"],
                       recipe_count=len(result["recipe_weights"]), recipe_weights=json.dumps(result["recipe_weights"], separators=(",", ":")),
                       simplex_residual=result["simplex_residual"],
                       reconstruction_residual=result["mixture_reconstruction_residual"],
                       QA_direct_coverage=result["qa_direct"]["covered_mass"],
                       QA_direct_mean=result["qa_direct"]["mean_Q_A_on_mapped"],
                       QA_near_coverage=result["qa_direct_and_near"]["covered_mass"],
                       QA_near_mean=result["qa_direct_and_near"]["mean_Q_A_on_mapped"],
                       **{f"p_{d}": result["p"][d] for d in model.domains})
        flat.append(row)
    return details, flat


def numerical(model, choices):
    weights = model.weight_policy("equal_13")
    best = choices["convex_hull__equal_13"]["p"]
    ref = model.p_dict(model.reference)
    marginal_rows = []
    for name, p in (("Q1_reference", ref), ("ridge_hull_optimum", best),
                    ("QA_direct", choices["quality_direct__equal_13"]["p"])):
        for n, d, q in itertools.product((0.1, 1.0, 10.0), (30.0, 100.0, 300.0), (0.3, 0.5, 0.7)):
            result = model.evaluate(n, d, q, p, weights, 1, 0)
            marginal_rows.append({"p_policy": name, "N_params_B": n, "D_tokens_B": d,
                "Q_score": q, "loss": result["loss"], "factor": result["factor"],
                "dL_dN": result["gradient"]["N"], "dL_dD": result["gradient"]["D"],
                "dL_dQ_B": result["gradient"]["Q_B"],
                "improvement_elasticity_N": result["improvement_elasticity"]["N"],
                "improvement_elasticity_D": result["improvement_elasticity"]["D"],
                "improvement_elasticity_Q_B": result["improvement_elasticity"]["Q_B"]})
    write_csv("marginals_elasticities.csv", marginal_rows)
    substitution_rows = []
    for name, p in (("Q1_reference", ref), ("ridge_hull_optimum", best)):
        base = {"N": 1.0, "D": 100.0, "Q_B": 0.5}
        start = model.v5.evaluate_ndqp_scenario(1, 100, .5, p=p, weights=weights, bridge_lambda=1, eta=0)
        better = model.v5.evaluate_ndqp_scenario(1, 100, .6, p=p, weights=weights, bridge_lambda=1, eta=0)
        for axis in ("N", "D"):
            root = model.v5.equal_loss_root(baseline=base, axis=axis, changed_axis="Q_B",
                changed_value=.6, p=p, weights=weights, bridge_lambda=1, eta=0)
            substitution_rows.append({"p_policy": name, "axis": axis, "N_base": 1,
                "D_base": 100, "Q_B_base": .5, "Q_B_changed": .6,
                "baseline_loss": start["loss"], "quality_improved_loss": better["loss"],
                "root_status": root["status"], "equal_loss_axis_value": root["value"],
                "axis_change": root["value"] - base[axis] if root["value"] is not None else None,
                "support_checked": True})
    write_csv("quality_vs_scale.csv", substitution_rows)
    transfer_rows = []
    destinations = [("equal_weight_optimum", best),
        ("arxiv_only_optimum", choices["convex_hull__arxiv_only"]["p"]),
        ("QA_direct_optimum", choices["quality_direct__equal_13"]["p"])]
    origin = model.v5.evaluate_ndqp_scenario(1, 100, .5, p=ref, weights=weights, bridge_lambda=1, eta=0)
    for name, dest in destinations:
        for fraction in (0, .5, 1):
            p = {key: ref[key] + fraction * (dest[key] - ref[key]) for key in model.domains}
            info = model.hull(p)
            assert info["inside"]
            result = model.v5.evaluate_ndqp_scenario(1, 100, .5, p=p, weights=weights, bridge_lambda=1, eta=0)
            transfer_rows.append({"transfer": f"Q1_reference_to_{name}", "fraction": fraction,
                "loss": result["loss"], "delta_loss_vs_start": result["loss"] - origin["loss"],
                "relative_A_effect": result["relative_A_effect"], "in_Q1_convex_hull": True,
                "p_json": json.dumps(p, separators=(",", ":"), sort_keys=True)})
    write_csv("p_transfer.csv", transfer_rows)
    domain_rows = []
    for name, result in choices.items():
        p = result["p"]
        for domain in model.domains:
            domain_rows.append({"scenario": name, "domain": domain, "p": p[domain],
                "reference_p": ref[domain], "delta_p": p[domain] - ref[domain],
                "qa_mapping_type": next(r["mapping_type"] for r in model.qa if r["mixture_domain"] == domain),
                "quality_Q_A": next(r["Q_A"] for r in model.qa if r["mixture_domain"] == domain),
                "target_absolute_changes_json": json.dumps(result["target_absolute_A_loss_change"], separators=(",", ":"), sort_keys=True)})
    write_csv("domain_combinations.csv", domain_rows)
    sensitivity_rows = []
    for lam, eta, weight_name, name in itertools.product((0, .25, .5, 1), (-.5, 0, .5),
                                                         ("equal_13", "arxiv_only", "pile_cc_only"),
                                                         ("Q1_reference", "ridge_hull_optimum", "QA_direct")):
        p = {"Q1_reference": ref, "ridge_hull_optimum": best,
             "QA_direct": choices["quality_direct__equal_13"]["p"]}[name]
        for n in (.1, 1, 10):
            try:
                v = model.v5.evaluate_ndqp_scenario(n, 100, .5, p=p,
                    weights=model.weight_policy(weight_name), bridge_lambda=lam, eta=eta)
                sensitivity_rows.append({"bridge_lambda": lam, "eta": eta, "weights": weight_name,
                    "p_policy": name, "N_params_B": n, "D_tokens_B": 100, "Q_score": .5,
                    "status": "valid", "loss": v["loss"], "factor": v["factor"]})
            except ValueError as exc:
                sensitivity_rows.append({"bridge_lambda": lam, "eta": eta, "weights": weight_name,
                    "p_policy": name, "N_params_B": n, "D_tokens_B": 100, "Q_score": .5,
                    "status": str(exc), "loss": None, "factor": None})
    write_csv("new_sensitivity_grid.csv", sensitivity_rows)
    valid = [r for r in sensitivity_rows if r["status"] == "valid"]
    write_json("sensitivity_summary.json", {"grid_rows": len(sensitivity_rows),
        "valid_rows": len(valid), "invalid_rows": len(sensitivity_rows) - len(valid),
        "conditional_loss_range_valid": [min(r["loss"] for r in valid), max(r["loss"] for r in valid)],
        "lambda_zero_all_p_tied_at_fixed_NDQ": True,
        "old_v5_grid": "outputs/cyj/q2_joint_scenarios/scenario_grid.csv (retained, not rerun)",
        "Q1_interaction_model": "diagnostic metrics only, full 13-target coefficients unavailable",
        "uncertainty": {"B7_parameter_residual": "See frozen outputs/cyj/quality/b7_interval_calibration.json and b7_nested_cv_summary.json",
                        "B7_example_80pct_training_residual_interval_coverage": next(r["coverage"] for r in read_json("outputs/cyj/quality/b7_interval_calibration.json")["coverage"] if r["axis"] == "N_params_B" and r["held_level"] is None and r["nominal"] == .8 and r["method"] == "training_residual"),
                        "bridge_lambda_eta_weights": "Engineering scenario grid; not a confidence interval"}})
    write_json("conditional_example.json", {"inputs": {"N_params_B": 1, "D_tokens_B": 100,
        "Q_score": .5, "p": best, "weights": weights, "bridge_lambda": 1, "eta": 0,
        "p_policy": "convex_hull", "model_variant": "ridge_main"},
        "result": model.evaluate(1, 100, .5, best, weights, 1, 0),
        "Q1_export_manifest_sha256": sha(BUNDLE / "export_manifest.json"),
        "B7_fit_sha256": sha(ROOT / "outputs/cyj/quality/b7_joint_fit.json")})


def figures(model, choices):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "font.size": 10})
    specs = []
    def save(name, source, explanation):
        plt.tight_layout()
        path = FIG / name
        plt.savefig(path, metadata={"Software": "Matplotlib"})
        plt.close()
        specs.append({"figure": name, "source_csv": source, "source_sha256": sha(OUT / source),
                      "figure_sha256": sha(path), "generator": "src/cyj/build_q2_final.py::figures", "meaning": explanation})
    policies = read_csv(OUT / "p_optimization_main.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    names = [r["p_policy"].replace("quality_", "QA ") for r in policies]
    ax.bar(names, [float(r["loss"]) for r in policies], color=["#8ea9c0", "#295a88", "#76a899", "#b6a36e"])
    for i, row in enumerate(policies):
        ax.text(i, float(row["loss"]) + .015, f'{float(row["loss"]):.3f}', ha="center", fontsize=9)
    ax.set_ylim(0, 2.55)
    ax.set_ylabel("Conditional B7 native Loss")
    ax.set_title("Q1-supported composition policies; lambda=1")
    ax.tick_params(axis="x", rotation=17)
    save("p_policy_loss.png", "p_optimization_main.csv", "Conditional policy comparison")
    quality = read_csv(OUT / "quality_mapping_sensitivity.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for mapping, marker in (("direct", "o"), ("direct_and_near", "s")):
        subset = [r for r in quality if r["mapping"] == mapping]
        ax.scatter([float(r["covered_mass"]) for r in subset], [float(r["mean_Q_A_on_mapped"]) for r in subset],
                   label=mapping, marker=marker, s=65)
        for r in subset:
            short = {"convex_hull": "hull", "quality_direct": "QA-D",
                     "quality_direct_and_near": "QA-DN"}[r["policy"].split("__")[0]]
            ax.annotate(short, (float(r["covered_mass"]), float(r["mean_Q_A_on_mapped"])),
                        xytext=(5, 5 if mapping == "direct" else -12), textcoords="offset points", fontsize=8)
    ax.set(xlabel="Mapped recipe mass", ylabel="Mean Q1 Q_A on mapped mass", title="Q1 quality-policy coordinates")
    ax.set_xlim(.1, .69)
    ax.set_ylim(-.65, 1.2)
    ax.legend()
    save("qa_mapping.png", "quality_mapping_sensitivity.csv", "Q_A is distinct from B7 Q_B")
    margin = read_csv(OUT / "marginals_elasticities.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for name, color in (("Q1_reference", "#777777"), ("ridge_hull_optimum", "#295a88"), ("QA_direct", "#76a899")):
        subset = [r for r in margin if r["p_policy"] == name and float(r["N_params_B"]) == 1 and float(r["D_tokens_B"]) == 100]
        ax.plot([float(r["Q_score"]) for r in subset], [float(r["loss"]) for r in subset], marker="o", label=name, color=color)
    ax.set(xlabel="B7 quality Q_B", ylabel="Conditional Loss", title="Quality response at N=1B, D=100B")
    ax.legend(fontsize=8)
    save("quality_marginal.png", "marginals_elasticities.csv", "Q_B response at supported p")
    transfer = read_csv(OUT / "p_transfer.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for name in dict.fromkeys(r["transfer"] for r in transfer):
        subset = [r for r in transfer if r["transfer"] == name]
        ax.plot([float(r["fraction"]) for r in subset], [float(r["loss"]) for r in subset], marker="o", label=name.replace("Q1_reference_to_", ""))
    ax.set(xlabel="Fraction along Q1 convex-hull segment", ylabel="Conditional Loss", title="Three feasible composition transfers")
    ax.legend(fontsize=8)
    save("composition_transfers.png", "p_transfer.csv", "Supported Q1 recipe-segment transfers")
    (FIG / "manifest.json").write_bytes((json.dumps({"figures": specs}, indent=2, sort_keys=True) + "\n").encode())


def acceptance(model, choices):
    source = (ROOT / "src/cyj/q2_final_core.py").read_text(encoding="utf-8") + (ROOT / "src/cyj/build_q2_final.py").read_text(encoding="utf-8")
    forbidden = "data/raw/real_attachments/" + "A_data_value"
    static_raw_a_read_absent = forbidden not in source
    main = choices["convex_hull__equal_13"]
    observed = choices["observed_512__equal_13"]
    checks = {
        "C1": main["min_factor_over_B7_N"] > 0 and model.v5.evaluate_ndqp_scenario(*MAIN_NDQ,
            p=main["p"], weights=model.weight_policy("equal_13"), bridge_lambda=0, eta=0)["factor"] == 1,
        "C2": all(g in {r["group"] for r in read_csv(OUT / "validation_summary.csv")} for g in
                  ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10")),
        "C3": len([r for r in model.qa if r["Q_A"] is None]) == 11 and
              choices["quality_direct__equal_13"]["quality_constraint"] is not None,
        "C4": len(model.matrix) == 512 and abs(main["conditional_loss"] - observed["conditional_loss"]) < 1e-9,
        "C5": len(read_csv(OUT / "marginals_elasticities.csv")) > 0 and len(read_csv(OUT / "p_transfer.csv")) == 9,
        "C6": len(read_csv(OUT / "new_sensitivity_grid.csv")) > 100 and (OUT / "model_selection.csv").is_file(),
        "C7": len([p for p in FIG.glob("*.png")]) == 4 and (OUT / "conditional_example.json").is_file(),
        "C8": static_raw_a_read_absent and (ROOT / "src/cyj/ndqp_scenarios_v6.py").is_file(),
    }
    write_json("acceptance.json", {"checks": checks, "all_internal_checks_pass": all(checks.values()),
        "external_test_suite_status": "separate test command required",
        "CHM_Q1_export_owner_signoff": "pending", "CHM_v6_Q3_consumption_signoff": "pending",
        "formal_scientific_ready_for_Q3": False,
        "conditional_engineering_delivery": all(checks.values()),
        "C8_runtime_file_trace": "separate test command required"})


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    model = Q2Final()
    weights = model.weight_policy("equal_13")
    ref = model.p_dict(model.reference)
    certificate = model.hull(ref)
    if not certificate["inside"]:
        raise AssertionError("Q1 reference unexpectedly outside 512-recipe hull")
    write_json("q1_bundle_consumer_audit.json", {"schema_version": model.manifest["schema_version"],
        "manifest_sha256": sha(BUNDLE / "export_manifest.json"), "verified_file_count": len(model.manifest["files_sha256"]),
        "recipe_rows": len(model.matrix), "domain_order": model.domains, "p_ref_hull": certificate,
        "Q2_raw_A_reads": 0, "Q1_export_status": model.manifest["status"]})
    write_json("model_coefficients.json", {"formula": model.v5.assumptions()["formula"],
        "units": {"N": "billion parameters", "D": "billion tokens", "Q_B": "B7 native score", "p": "17-domain unit simplex"},
        "theta_B7": model.v5.theta, "B7_fit_sha256": sha(ROOT / "outputs/cyj/quality/b7_joint_fit.json"),
        "Q1_ridge_beta_by_target": {target: dict(zip(model.domains, map(float, model.beta[i])))
                                    for i, target in enumerate(model.targets)},
        "Q1_reference_p": model.p_dict(model.reference),
        "Q1_fitted_positive_reference_loss_by_target": dict(zip(model.targets, map(float, model.reference_loss))),
        "Q1_producer_manifest_sha256": model.v5.a["manifest_sha256"],
        "Q1_bundle_manifest_sha256": sha(BUNDLE / "export_manifest.json"),
        "bridge_status": "lambda, eta, weights are engineering assumptions; not jointly estimated"})
    write_json("main_policy.json", {"schema_version": VERSION, "N_params_B": MAIN_NDQ[0],
        "D_tokens_B": MAIN_NDQ[1], "Q_score": MAIN_NDQ[2], "bridge_lambda": 1,
        "eta": 0, "weights": weights, "p_policy": "convex_hull", "model_variant": "ridge_main",
        "scientific_status": "conditional_uncalibrated_A_to_B", "ready_for_Q3": False})
    write_csv("validation_summary.csv", validation_rows(model))
    choices, flat = policy_rows(model)
    main = choices["convex_hull__equal_13"]
    observed = choices["observed_512__equal_13"]
    assert abs(main["conditional_loss"] - observed["conditional_loss"]) < 1e-9
    write_json("p_policy_details.json", choices)
    write_csv("p_optimization_main.csv", [r for r in flat if r["scenario"] in
        ("observed_512__equal_13", "convex_hull__equal_13", "quality_direct__equal_13", "quality_direct_and_near__equal_13")])
    write_csv("p_optimization_by_scenario.csv", flat)
    write_csv("mixture_support_results.csv", [{"name": name, "inside": True,
        "certificate_size": len(result["recipe_weights"]), "min_factor_B7_N": result["min_factor_over_B7_N"],
        "max_simplex_residual": result["simplex_residual"]} for name, result in choices.items()])
    qa_rows = []
    for name in ("convex_hull__equal_13", "quality_direct__equal_13", "quality_direct_and_near__equal_13"):
        result = choices[name]
        for mapping in ("direct", "direct_and_near"):
            qa = result["qa_direct" if mapping == "direct" else "qa_direct_and_near"]
            qa_rows.append({"policy": name, "mapping": mapping, "loss": result["conditional_loss"],
                "covered_mass": qa["covered_mass"], "unmapped_mass": qa["unmapped_mass"],
                "mean_Q_A_on_mapped": qa["mean_Q_A_on_mapped"]})
    write_csv("quality_mapping_sensitivity.csv", qa_rows)
    mixture_selection = read_csv(BUNDLE / "mixture_model_selection.csv")
    model_select = [{"dataset": "Q1", "model": "ridge_vs_second_order_candidate", "scope": r["scope"],
                     "target": r["target"], "ridge_rmse": r["ridge_rmse"],
                     "candidate_rmse": r["candidate_rmse"], "candidate_cv_rmse": r["cv_rmse"],
                     "role": "Q1_derived_diagnostic_metrics_only"} for r in mixture_selection]
    for r in read_csv(ROOT / "outputs/cyj/quality/b7_joint_vs_staged.csv"):
        model_select.append({"dataset": "B7", "model": r["method"], "scope": "B7_semi_synthetic",
                             "target": "val_loss", "ridge_rmse": "", "candidate_rmse": r["train_rmse"],
                             "role": "B7_form_comparison_not_A_to_B_validation"})
    write_csv("model_selection.csv", model_select)
    numerical(model, choices)
    figures(model, choices)
    acceptance(model, choices)
    manifest = {"schema_version": "cyj.q2_final.manifest.v1", "generator": "python -B src/cyj/build_q2_final.py",
        "Q1_export_manifest_sha256": sha(BUNDLE / "export_manifest.json"),
        "files_sha256": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"},
        "figures_sha256": {p.name: sha(p) for p in sorted(FIG.iterdir()) if p.is_file()}}
    write_json("manifest.json", manifest)
    print(json.dumps({"files": len(manifest["files_sha256"]), "figures": len(manifest["figures_sha256"]),
        "main_loss": main["conditional_loss"], "reference_inside_hull": True}, ensure_ascii=False))


if __name__ == "__main__":
    build()
