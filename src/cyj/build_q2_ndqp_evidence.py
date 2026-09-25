"""Rebuild Q2 coverage and predeclared conditional scenarios without refitting."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from joint_ndqp_scenarios import ConditionalNDQP, ROOT

OUT = ROOT / "outputs/cyj/q2_joint_scenarios"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence(relative):
    path = ROOT / relative
    return {"path": relative, "sha256": digest(path)}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_csv(path, data):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    model = ConditionalNDQP()
    source = {
        "B1": evidence("outputs/cyj/classic/classic_fit.json"),
        "B2_B3": evidence("outputs/cyj/diagnostics/b2_b3_shapes.json"),
        "B4_B5": evidence("outputs/cyj/diagnostics/b4_b5_comparability.json"),
        "B6_B7_B8": evidence("outputs/cyj/quality/b7_b8_conflict_summary.json"),
        "B9_B10": evidence("outputs/cyj/diagnostics/b9_b10_extrapolation_audit.json"),
        "B7_joint": evidence("outputs/cyj/quality/b7_joint_fit.json"),
        "B7_nested": evidence("outputs/cyj/quality/b7_nested_cv_summary.json"),
    }
    b23 = json.loads((ROOT / source["B2_B3"]["path"]).read_text(encoding="utf-8"))
    b45 = json.loads((ROOT / source["B4_B5"]["path"]).read_text(encoding="utf-8"))
    b910 = json.loads((ROOT / source["B9_B10"]["path"]).read_text(encoding="utf-8"))
    coverage = {
        "schema_version": "cyj.q2.requirement_coverage.v1", "source": source,
        "requirements": {
            "B1_main_ND": {"status": "pass_conditional_within_source", "rows": 1176,
                           "role": "fit_and_group_holdout", "source": "B1"},
            "B2_or_B3_trajectory": {"status": "partial_shape_only", "B2_rows": b23["b2"]["rows"],
                                     "B3_rows": b23["b3"]["rows"],
                                     "role": "semi_synthetic_cross_family_and_interpolated_shape; no common absolute RMSE", "source": "B2_B3"},
            "B4_and_B5_external": {"status": "partial_coordinate_unverified",
                                    "B4_rows": b45["datasets"]["B4"]["rows"],
                                    "B5_rows": b45["datasets"]["B5"]["rows"],
                                    "B4_inside_B1_rectangle": b45["datasets"]["B4"]["support_counts"]["inside_rectangle"],
                                    "B5_inside_B1_rectangle": b45["datasets"]["B5"]["support_counts"]["inside_rectangle"],
                                    "role": "descriptive_stratification; tokenizer/corpus/log_base/aggregation unverified", "source": "B4_B5"},
            "B6_B7_B8_quality": {"status": "partial_semi_synthetic_conflict",
                                  "B6_rows": 360, "B7_rows": 450, "B8_rows": 1704,
                                  "B6_nested_in_B7": True, "B8_isolated": True, "source": "B6_B7_B8"},
            "B9_B10_large": {"status": "partial_estimated_stress_only",
                              "B9_rows": b910["checks"]["B9_rows"], "B10_rows": b910["checks"]["B10_rows"],
                              "B10_outside_B1_N": b910["checks"]["B10_above_B1_N_max_count"],
                              "role": "metadata_and_estimated_extrapolation_stress", "source": "B9_B10"},
            "unique_AB_bridge": {"status": "unidentified", "role": "no paired same-Loss N,D,Q,p observations"},
        },
        "interpretation": "Data roles and source checks are recorded; partial does not mean a missing validation was passed.",
    }
    write_json(OUT / "requirement_coverage.json", coverage)

    ref = model.a["reference"]
    variants = {"reference": ref}
    for receiver, donor in (("arxiv", "freelaw"), ("freelaw", "arxiv")):
        p = ref.copy()
        p[receiver] += .01
        p[donor] -= .01
        variants[f"transfer_{donor}_to_{receiver}_one_percent"] = p
    weights = {"arxiv_only": {"arxiv": 1.0}, "pile_cc_only": {"pile_cc": 1.0},
               "equal_13": {k: 1 / 13 for k in model.a["coefficients"]}}
    # The exact equal weights sum to 0.9999999999999998, accepted by tolerance.
    assumptions = {**model.assumptions(), "lambda_grid": [0, .25, .5, 1],
                   "eta_grid": [-.5, 0, .5], "weight_scenarios": weights,
                   "p_variants": variants, "grid_interpretation": "analytic sensitivity ranges, not confidence limits",
                   "N_scenarios_B": [.1, 1, 10], "D_B": 100, "Q_B": .5,
                   "raw_and_prior_evidence": source}
    write_json(OUT / "model_assumptions.json", assumptions)
    grid, failures = [], []
    for n in assumptions["N_scenarios_B"]:
        for p_name, p in variants.items():
            for w_name, w in weights.items():
                for lam in assumptions["lambda_grid"]:
                    for eta in assumptions["eta_grid"]:
                        key = {"N_B": n, "D_B": 100, "Q_B": .5, "p_variant": p_name,
                               "weights": w_name, "bridge_lambda": lam, "eta": eta}
                        try:
                            result = model.evaluate_ndqp_scenario(n, 100, .5, p=p, weights=w,
                                                                   bridge_lambda=lam, eta=eta)
                            grid.append({**key, "loss": result["loss"], "baseline_loss": result["baseline_loss"],
                                         "factor": result["factor"], "relative_A_effect": result["relative_A_effect"],
                                         "gradient_N": result["gradient"]["N"],
                                         "gradient_D": result["gradient"]["D"],
                                         "gradient_Q_B": result["gradient"]["Q_B"],
                                         "status": "conditional_scenario_only"})
                        except ValueError as exc:
                            failures.append({**key, "reason": str(exc)})
    write_csv(OUT / "scenario_grid.csv", grid)
    write_csv(OUT / "support_failures.csv", failures or [{"status": "none_on_predeclared_grid"}])
    validation = [{"source": "CHM_Q1_v1.3", "test": "targetwise_1M_60M_1B_rank",
                   "status": "producer_held_out_metrics_consumed_not_refitted", "target": r["target"],
                   "test_1m_spearman": r["test_1m_spearman"],
                   "test_60m_spearman": r["test_60m_spearman"],
                   "test_1B_spearman": r["test_1B_spearman"]} for r in model.a["validation"]]
    write_csv(OUT / "validation_by_source.csv", validation)
    report = ("# Q2 bridge identifiability\n\n"
              "For every observed B row, p is unrecorded; for every A mixture row, B-native Loss and Q_B are unrecorded. "
              "Both lambda=0 and lambda=1 give the same B predictions when p=p_ref, and the A-native contrasts do not depend on lambda. "
              "They are observationally indistinguishable in the available data, but at any nonzero A relative contrast "
              "their conditional B predictions and potentially Q3 allocations differ. Thus lambda is not identified. "
              "The A scale groups also change training conditions and lack complete D; eta is a predeclared sensitivity axis, not a pure N estimate.\n\n"
              "The A target reference denominators are positive fitted Ridge predictions at p_ref. "
              "They are not a B calibration, and target weights are decision utilities. The Q_A to Q_B map remains unidentified. "
              "B7 bootstrap or OOF intervals cannot cover this bridge uncertainty.\n")
    (OUT / "identifiability_report.md").write_text(report, encoding="utf-8", newline="\n")
    write_json(OUT / "manifest.json", {"schema_version": "cyj.q2.ndqp.evidence.v1",
              "files_sha256": {p.name: digest(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"},
              "CHM_commit": model.assumptions()["producer_commit"], "B7_joint_sha256": source["B7_joint"]["sha256"]})
    return {"scenarios": len(grid), "failures": len(failures), "manifest_sha256": digest(OUT / "manifest.json")}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
