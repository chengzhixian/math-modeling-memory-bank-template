"""Generate a terse, machine-sourced Q2 facts packet; not a paper section."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from joint_ndqp_scenarios import ROOT

OUT = ROOT / "outputs/cyj/q2_final"


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def table(name):
    with (OUT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def metric(rows, group, name):
    return next(float(r["value"]) for r in rows if r["group"] == group and r["metric"] == name)


def build():
    policy = load("p_policy_details.json")
    coeff = load("model_coefficients.json")
    validation = table("validation_summary.csv")
    quality = table("quality_vs_scale.csv")
    interactions = load("interaction_summary.json")
    comparison = table("ridge_vs_interaction_policy.csv")
    sensitivity = load("sensitivity_summary.json")
    main = policy["convex_hull__equal_13"]
    direct = policy["quality_direct__equal_13"]
    near = policy["quality_direct_and_near__equal_13"]
    minimax = policy["minimax_13__equal_13"]
    theta_names = ("E", "A", "B", "alpha", "beta", "G0", "GN", "GD")
    stable = [p for p in interactions["pairs"] if p["label"] == "consistent_fitted_complement"]
    lines = ["# Q2 FINAL FACTS (paper drafting input, not paper text)", "",
        "Status: conditional engineering Q2 complete after `final_closure.json` passes; scientific A→B calibration and Q3 owner acceptance remain pending.", "",
        "## Frozen model and assumptions", "",
        "- Formula: `L_B(N,D,Q_B) * [1 + lambda*(N/1B)^(-eta)*sum_k w_k*(L_A,k(p)-L_A,k(p_ref))/L_A,k(p_ref)]`.",
        "- B7 base: `E + A*N^(-alpha) + B*D^(-beta) + (1-Q_B)*(G0+GN*ln(N)+GD*ln(D/100))`; N and D are billions.",
        "- B7 parameters: " + ", ".join(f"{name}={value:.12g}" for name, value in zip(theta_names, coeff["theta_B7"])) + ".",
        "- Engineering point: `N=1B, D=100B, Q_B=0.5, lambda=1, eta=0, w_k=1/13`; lambda/eta are not estimated.",
        "- Source: `outputs/cyj/q2_final/model_coefficients.json`, `main_policy.json`; Q1 derived recipe manifest is in `q1_bundle_consumer_audit.json`.",
        "", "## Supported composition policies", "",
        f"- Ridge main convex-hull/observed optimum: Q1 recipe `{main['recipe_weights'][0]['index']}`, conditional Loss `{main['conditional_loss']:.12f}`, factor `{main['factor']:.12f}`.",
        "- All 17 proportions at the main p: " + ", ".join(f"{domain}={value:.9f}" for domain, value in main["p"].items()) + ".",
        f"- Direct Q1 QA policy: Loss `{direct['conditional_loss']:.12f}`, {len(direct['recipe_weights'])} recipe weights; direct+near QA: `{near['conditional_loss']:.12f}`, {len(near['recipe_weights'])} weights.",
        f"- 13-target minimax: conditional equal-weight Loss `{minimax['conditional_loss']:.12f}`, {len(minimax['recipe_weights'])} recipe weights; its optimization objective is max target-relative effect.",
        "- Source: `p_policy_details.json`, `p_optimization_by_scenario.csv`, `quality_mapping_sensitivity.csv`.",
        "", "## Quality versus scale", ""]
    for axis in ("N", "D"):
        row = next(r for r in quality if r["p_policy"] == "ridge_hull_optimum" and r["axis"] == axis)
        lines.append(f"- Raising Q_B from 0.5 to 0.6 at main p keeps old Loss if {axis} becomes `{float(row['equal_loss_axis_value']):.9f}` (base {row['N_base'] if axis == 'N' else row['D_base']}); status `{row['root_status']}`.")
    lines += ["- Source: `quality_vs_scale.csv`, `marginals_elasticities.csv`.", "", "## Source-bound validation", "",
        f"- B1: 1,176 rows; leave-one-N-level mean RMSE `{metric(validation, 'B1', 'leave_one_N_group_mean_rmse'):.9g}`; tail RMSE `{metric(validation, 'B1', 'token_tail_rmse'):.9g}`. B1 is a near-exact reconstruction and requires provenance caution.",
        f"- B4: within-family/source scale-dominance concordance `{int(metric(validation, 'B4', 'concordant_pairs'))}/{int(metric(validation, 'B4', 'dominance_pairs'))}`; B5: `{int(metric(validation, 'B5', 'concordant_pairs'))}/{int(metric(validation, 'B5', 'dominance_pairs'))}`. These are descriptive, not cross-source RMSE.",
        f"- B7: 24 nested held-level folds; pooled N/D/Q RMSE `{metric(validation, 'B7', 'nested_outer_N_params_B_rmse'):.6f}/{metric(validation, 'B7', 'nested_outer_D_tokens_B_rmse'):.6f}/{metric(validation, 'B7', 'nested_outer_Q_score_rmse'):.6f}`. B7 is semi-synthetic; B6 overlaps it and B8 is quarantined.",
        "- B9 is metadata; B10 loss is estimated stress only. Q1 1B Ridge beat a constant-RMSE baseline for 4/13 targets.",
        "- Source: `validation_summary.csv` and its cited frozen source files.",
        "", "## Q1 fitted domain interactions", "",
        "- The following are *screened fitted-basis* 1M Q1 cross partials. Negative means model-conditional complementarity under lower-is-better Loss; the descriptive sign screen is not a significance test, causal result, or B7 transfer claim:",
        f"- A4 design has full feature rank {interactions['A4_design']['full_feature_rank']}/27 and interaction-block rank {interactions['A4_design']['pair_block_rank_after_linear_projection']}/10 after linear projection; this checks numerical design support, not scientific transportability."]
    for row in sorted(stable, key=lambda r: r["equal_weight_normalized_cross_partial"]):
        lines.append(f"  - `{row['domain_i']} × {row['domain_j']}`: equal-weight normalized cross partial `{row['equal_weight_normalized_cross_partial']:.6f}`, negative in {row['negative_targets']}/13 targets, training-fold sign agreement {row['same_sign_training_folds_of_65']}/65, both domains positive in {row['A4_both_domains_positive_rows']}/512 recipes.")
    lines += ["- Remaining pairs have cross-target sign disagreement or weaker training-fold stability; do not call them stable complementarity/substitution.",
        f"- The published interaction candidate beats frozen Ridge RMSE on {interactions['published_candidate_RMSE_better_than_Ridge_target_counts']['test_1B']}/13 Q1 1B targets, yet beats the constant absolute-RMSE baseline on only {interactions['candidate_1B_absolute_RMSE_beats_constant_targets']}/13. The scale shift remains, and no A→B bridge is identified.",
        "- Source: `domain_interactions.csv`, `interaction_summary.json`, Q1 `outputs/chm/q1_exports/q1_interaction_bundle_v1/`.",
        "", "## Model-form and bridge sensitivity", ""]
    for row in comparison:
        lines.append(f"- `{row['scenario']}` on the same 512 observed recipes: Ridge index `{row['ridge_observed_index']}`, interaction index `{row['interaction_observed_index']}`, interaction regret of Ridge choice `{float(row['interaction_regret_of_ridge_choice']):.9f}`, Ridge regret of interaction choice `{float(row['ridge_regret_of_interaction_choice']):.9f}` (objective-relative units).")
    lines += [f"- Added bridge grid: {sensitivity['grid_rows']} rows, valid conditional Loss range `{sensitivity['conditional_loss_range_valid'][0]:.6f}`–`{sensitivity['conditional_loss_range_valid'][1]:.6f}`; this is scenario spread, not a confidence interval.",
        "- Source: `ridge_vs_interaction_policy.csv`, `new_sensitivity_grid.csv`, `sensitivity_summary.json`; four new figure hashes in `manifest.json`.",
        "", "Q1 interaction export and v6 consumption await CHM owner signoff. `ready_for_Q3=false` concerns scientific calibration and stays false.", ""]
    (OUT / "FINAL_FACTS.md").write_bytes("\n".join(lines).encode("utf-8"))
    print(f"wrote FINAL_FACTS.md with {len(stable)} stable fitted-basis pairs")


if __name__ == "__main__":
    build()
