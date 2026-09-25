"""Independent, fail-closed acceptance of the conditional competition-role Q2 v8 bundle."""
from __future__ import annotations

import csv
import json
import math
import re
import subprocess
import sys

from audit_q2_v8 import main as rebuild_under_audit
from chm_q1_v2_consumer import ROOT, sha256
from fit_b7_quality_extension_from_b1 import B1_FILE, B1_SHA, b1_parameters
from ndqp_scenarios_v8 import ConditionalV8
from verify_v8_fixtures import main as verify_fixtures

OUT = ROOT / "outputs/cyj/q2_v8"


def read_json(name):
    return json.loads((OUT/name).read_text(encoding="utf-8"))


def read_csv(name):
    with (OUT/name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, label, tolerance=1e-8):
    require(math.isfinite(actual) and abs(actual-expected) <= tolerance,
            f"{label}: {actual} != {expected}")


def main():
    prior_audit = json.loads((ROOT/"outputs/cyj/q2_v8_runtime_audit.json").read_text(encoding="utf-8"))
    rebuilt = rebuild_under_audit()
    require(rebuilt["manifest_sha256"] == prior_audit["manifest_sha256"],
            "two v8 pre-acceptance rebuilds are not deterministic")
    require(rebuilt["original_A_open_events"] == 0 and rebuilt["derived_Q1_open_events"] > 0
            and rebuilt["subprocess_launch_events"] == 0, "v8 raw-A audit failed")
    manifest = read_json("manifest.json")
    for name, digest in manifest["files"].items():
        require(sha256(OUT/name) == digest, f"v8 bundle file changed after build: {name}")
    model = ConditionalV8()
    fit = read_json("b7_quality_extension.json")
    require(sha256(B1_FILE) == B1_SHA and fit["B1_parameters"] == b1_parameters(),
            "B1 five-parameter backbone not pinned")
    require(len(fit["outer_folds"]) == 24 and all(math.isfinite(row["outer_rmse"])
                                                   for row in fit["outer_folds"]),
            "new model nested held-level CV incomplete")
    require(fit["selected_ridge"] in (0, .001, .01), "quality fit regularization not frozen")
    comparison = read_csv("b7_backbone_comparison.csv")
    require({row["model"] for row in comparison} == {"B1_fixed_backbone_plus_quality",
                                                     "B7_joint_8_parameter", "B7_nested_family_selection"},
            "joint B7 alternative not preserved")
    main_policy = read_json("main_policy.json")
    p, weights = main_policy["p"], main_policy["weights"]
    result = model.predict_baseline_v8(1, 100, p, weights, p_policy="quality_direct_and_near")
    close(result["Loss"], main_policy["Loss"], "main policy Loss")
    close(result["Q_B_proxy_or_native"], main_policy["Q_B_proxy"], "main proxy quality")
    q1 = model.q1
    mapped = [d for d in q1.domains if q1.qa_rows[d]["Q_A"] is not None and
              q1.qa_rows[d]["mapping_type"] in ("direct", "near_direct")]
    mass = sum(p[d] for d in mapped)
    qa = sum(p[d]*q1.qa_rows[d]["Q_A"] for d in mapped)/mass
    lo, hi = min(q1.qa_rows[d]["Q_A"] for d in mapped), max(q1.qa_rows[d]["Q_A"] for d in mapped)
    proxy = .1+.9*(qa-lo)/(hi-lo)
    close(result["Q_A_mapped"], qa, "independent Q_A average")
    close(result["mapped_coverage"], mass, "mapped coverage")
    close(result["Q_B_proxy_or_native"], proxy, "independent quality proxy")
    n, d = 1.0, 100.0
    backbone = sum((model.b1["E"], model.b1["A"]*n**(-model.b1["alpha"]),
                    model.b1["B"]*d**(-model.b1["beta"])))
    g0, gn, gd = model.gamma
    gain = g0+gn*math.log(n)+gd*math.log(d/100)
    r = model.q1.weighted_effect(p, weights)
    close(result["Loss"], (backbone+(1-proxy)*gain)*math.exp(r), "independent v8 formula")
    require(result["empirically_calibrated_A_to_B"] is False and
            result["quality_and_mixture_double_counting_not_identified"],
            "cross-source bridge claim exceeds evidence")
    quality = read_csv("quality_bridge_sensitivity.csv")
    require([row["quality_bridge_scenario"] for row in quality] ==
            ["compressed", "identity_normalized", "expanded"], "three quality maps missing")
    require(all(row["empirically_calibrated"] == "False" for row in quality),
            "quality sensitivity falsely marked calibrated")
    b3 = read_json("b2_b3_validation_summary.json")
    require(b3["summary"]["B3"]["trajectories"] == 8 and
            b3["summary"]["B3"]["mean_normalized_RMSE"] < .01 and
            b3["absolute_cross_source_RMSE_claim"] is None,
            "B3 quantitative interpolation check missing or overstated")
    require(len(read_csv("b2_b3_model_validation.csv")) == 15,
            "B2/B3 per-trajectory metrics missing")
    pairs = read_csv("domain_pair_substitution.csv")
    interactions = read_csv("domain_pair_interaction.csv")
    require(len(pairs) == 136 and len(interactions) == 136 and all(
        float(row["feasible_epsilon_max"]) > 0 and
        float(row["reverse_feasible_epsilon_max"]) > 0 and
        float(row["hull_equation_residual_max"]) < 1e-8 for row in pairs),
        "full feasible domain-pair analysis incomplete")
    require(all(row["interaction_label"] == "model_based_not_causal_complementarity"
                for row in interactions), "domain interaction causal label invalid")
    tradeoff = read_csv("quality_scale_local_tradeoff.csv")
    at_one = next(row for row in tradeoff if float(row["N_params_B"]) == 1)
    require(float(at_one["dN_dQproxy"]) < 0 and
            float(at_one["equivalent_oldQ_N_delta_0_05"]) > 1 and
            float(at_one["constant_L_newQ_N_delta_0_05"]) < 1,
            "quality-scale local and finite interpretations conflated")
    scale = read_json("scale_order_validation_summary.json")
    require(scale["external_absolute_RMSE"] is None and all(
        scale["results"][name]["inside_common_support"]["pairs"] > 0
        for name in ("B4", "B5")), "B4/B5 directional check missing")
    stress = read_json("b9_b10_support_stress.json")
    require(stress["B10_external_RMSE"] is None and stress["B10_above_B1_N_support_ratio"] == 1,
            "B10 estimated stress misclassified")
    migration = read_json("migration_audit.json")
    require(migration["old_backbone"] == "B7_joint_8_param" and
            migration["new_quality_input"] == "Q1_QA_bridge_baseline" and
            migration["new_Q3_joint_optimum"] is None,
            "v7/v8 migration scope invalid")
    smoke = read_json("q3_fixed_p_smoke.json")
    require(smoke["status"] == "local_fixed_p_quality_proxy_cost_smoke_pass" and
            smoke["solution"]["primal_feasible"] and not smoke["CHM_owner_acceptance"],
            "Q3 v8 fixed-p sample missing or overstated")
    require(len(read_csv("requirement_evidence.csv")) == 15, "requirement evidence map incomplete")
    fixtures = verify_fixtures()
    require(fixtures["fixtures"] == 18, "v8 fixture set incomplete")
    regressions = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                                  "src/cyj/tests", "-p", "test_*.py", "-q"],
                                 cwd=ROOT, capture_output=True, text=True, timeout=240, check=False)
    require(regressions.returncode == 0,
            f"CYJ/v7-v8 regression failed: {regressions.stdout} {regressions.stderr}")
    count = re.search(r"Ran (\d+) tests", regressions.stderr+regressions.stdout)
    require(count is not None and int(count.group(1)) >= 95, "CYJ regression count below v7+v8 floor")
    old_changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD", "--",
                                           "src/cyj/ndqp_scenarios_v7.py", "interfaces/cyj/fixtures_v7",
                                           "outputs/cyj/q2_v7"], cwd=ROOT, text=True).strip()
    require(not old_changed, "published v7 historical code/fixtures/outputs were modified")
    acceptance = {"schema_version": "cyj.q2.v8.acceptance.v1",
                  "q2_implementation_complete": True,
                  "q2_competition_requirements_complete": True,
                  "q3_consumer_interface_ready": True,
                  "q3_consumer_verified_by_CHM": False,
                  "cross_source_empirical_calibration_complete": False,
                  "release_remote_verified": False,
                  "status": "conditional_v8_competition_requirements_complete_pending_remote_and_owner_consumption",
                  "checks": {"B1_fixed_parameter_count": 5, "B7_quality_parameter_count": 3,
                             "nested_CV_folds": 24, "B3_trajectories": 8,
                             "domain_pairs": len(pairs), "v8_fixtures": fixtures["fixtures"],
                             "CYJ_tests_including_v7": int(count.group(1)),
                             "raw_A_open_events": 0, "Q3_fixed_p_smoke": True},
                  "evidence_paths": ["outputs/cyj/q2_v8/b7_quality_extension.json",
                                     "outputs/cyj/q2_v8/b2_b3_model_validation.csv",
                                     "outputs/cyj/q2_v8/domain_pair_substitution.csv",
                                     "outputs/cyj/q2_v8/requirement_evidence.csv",
                                     "outputs/cyj/q2_v8_runtime_audit.json",
                                     "interfaces/cyj/fixtures_v8/manifest.json"],
                  "claim_limit": "uncalibrated_cross_source_quality_and_mixture_bridges; B3 interpolation and B4/B5 directions are not independent absolute validation"}
    closure = {"schema_version": "cyj.q2.v8.closure.v1",
               "status": "conditional_v8_engineering_and_competition_items_complete",
               "CHM_Q3_owner_acceptance": "pending", "main_integration": "pending",
               "A_B_empirical_calibration": False, "paper_layout_started": False,
               "whole_competition_submission_ready": False}
    for name, value in (("acceptance.json", acceptance), ("final_closure.json", closure)):
        (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                              encoding="utf-8", newline="\n")
    manifest = read_json("manifest.json")
    manifest["code_sha256"]["finalize_q2_v8.py"] = sha256(ROOT/"src/cyj/finalize_q2_v8.py")
    manifest["code_sha256"]["audit_q2_v8.py"] = sha256(ROOT/"src/cyj/audit_q2_v8.py")
    for name in manifest["files"]:
        manifest["files"][name] = sha256(OUT/name)
    (OUT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n",
                                     encoding="utf-8", newline="\n")
    return {"status": acceptance["status"], "CYJ_tests": int(count.group(1)),
            "fixtures": fixtures["fixtures"], "manifest_sha256": sha256(OUT/"manifest.json")}


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
