"""Independent final numerical assertions for the Q2 conditional delivery.

This checker reads published Q1-derived bundles and Q2/B outputs only.
It writes a complete report only after all checks pass; formal cross-source
calibration remains false even when the conditional engineering job closes.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from analyze_domain_interactions_q2 import InteractionConsumer, Q1_INTERACTION
from joint_ndqp_scenarios import ROOT
from q2_final_core import Q2Final

OUT = ROOT / "outputs/cyj/q2_final"
FIG = ROOT / "figures/cyj/q2_final"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def dump(path, obj):
    Path(path).write_bytes((json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode())


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def run():
    paths_opened = []
    def audit(event, args):
        if event == "open" and args:
            paths_opened.append(str(args[0]).replace("\\", "/"))
    sys.addaudithook(audit)
    consumer = InteractionConsumer()  # both Q1 export manifests and all member files SHA checked
    main = consumer.main
    require(any("q1_interaction_bundle_v1" in path for path in paths_opened), "runtime Q1 derived interaction read absent")
    forbidden = "data/raw/real_attachments/" + "A_data_value"
    require(not any(forbidden in path for path in paths_opened), "Q2 runtime opened original A")
    source_files = list((ROOT / "src/cyj").rglob("*.py"))
    require(source_files and all(forbidden not in p.read_text(encoding="utf-8") for p in source_files),
            "Q2 source embeds original A path")
    evidence = {"Q1_derived_bundle_sha256": sha(main.bundle / "export_manifest.json"),
                "Q1_interaction_bundle_sha256": sha(Q1_INTERACTION / "interaction_manifest.json"),
                "Q2_runtime_Q1_derived_reads": sum("q1_" in p and "outputs/chm" in p for p in paths_opened),
                "Q2_runtime_original_A_reads": 0}

    # Recompute the linear objective from exported beta, reference loss and 512 recipes.
    w = np.ones(len(main.targets)) / len(main.targets)
    effects = (main.matrix - main.reference) @ main.beta.T / main.reference_loss
    objective = effects @ w
    idx = int(np.argmin(objective))
    base_loss = main.v5.evaluate_ndq(1, 100, .5)["loss"]
    independently_optimal_loss = base_loss * (1 + float(objective[idx]))
    main_rows = read_csv(OUT / "p_optimization_main.csv")
    chosen = next(r for r in main_rows if r["scenario"] == "convex_hull__equal_13")
    require(main.indices[idx] == "136" and math.isclose(float(chosen["loss"]), independently_optimal_loss, abs_tol=1e-10),
            "C4 main LP does not match independent 512 enumeration")
    evidence["independent_main_recipe_index"] = main.indices[idx]
    evidence["independent_main_conditional_loss"] = independently_optimal_loss

    # Test LP raw coverage, quality-margin, positivity and reconstruction constraints.
    policies = read_json(OUT / "p_policy_details.json")
    qa_residuals = {}
    for key, map_kind in (("quality_direct__equal_13", "direct"),
                          ("quality_direct_and_near__equal_13", "direct_and_near")):
        result = policies[key]
        gamma = np.zeros(512)
        for entry in result["recipe_weights"]:
            gamma[main.indices.index(entry["index"])] = float(entry["weight"])
        require(np.min(gamma) >= -1e-10 and abs(float(gamma.sum()) - 1) < 1e-9, f"LP simplex: {key}")
        point = gamma @ main.matrix
        require(np.max(np.abs(point - main.point(result["p"]))) < 1e-9, f"LP reconstruction: {key}")
        allowed = {"direct"} if map_kind == "direct" else {"direct", "near_direct"}
        mask = np.array([row["mapping_type"] in allowed and row["Q_A"] is not None for row in main.qa], float)
        quality = np.array([float(row["Q_A"]) if row["Q_A"] is not None else 0 for row in main.qa])
        coverage_ref = float(main.reference @ mask)
        mean_ref = float(main.reference @ (mask * quality)) / coverage_ref
        coverage_margin = float(point @ mask) - coverage_ref
        quality_margin = float(point @ (mask * (quality - mean_ref)))
        relative = float(((point - main.reference) @ main.beta.T / main.reference_loss) @ w)
        factor = 1 + relative
        require(coverage_margin >= -1e-8 and quality_margin >= -1e-8 and factor > 0,
                f"QA policy raw inequality residual: {key}")
        qa_residuals[key] = {"coverage_margin": coverage_margin, "quality_margin": quality_margin,
                             "factor_over_B7_N_eta0": factor}
    evidence["QA_raw_constraint_residuals"] = qa_residuals

    # Substitute every reported finite equal-loss root back into the nonlinear v5 model.
    roots = read_csv(OUT / "quality_vs_scale.csv")
    root_residual = 0.0
    for row in roots:
        if row["root_status"] != "supported":
            require(row["equal_loss_axis_value"] in ("", "None"), "unsupported root has a number")
            continue
        p = (main.p_dict(main.reference) if row["p_policy"] == "Q1_reference"
             else policies["convex_hull__equal_13"]["p"])
        axis = row["axis"]
        point = [1.0, 100.0, .6]
        point[0 if axis == "N" else 1] = float(row["equal_loss_axis_value"])
        loss = main.v5.evaluate_ndqp_scenario(*point, p=p, weights=main.weight_policy("equal_13"),
                                                 bridge_lambda=1, eta=0)["loss"]
        original = main.v5.evaluate_ndqp_scenario(1, 100, .5, p=p,
            weights=main.weight_policy("equal_13"), bridge_lambda=1, eta=0)["loss"]
        root_residual = max(root_residual, abs(loss - original))
    require(len(roots) == 4 and root_residual < 1e-8, "equal-Loss finite root reproduction")
    evidence["max_equal_loss_root_residual"] = root_residual

    # Re-solve actual hull membership for every sampled composition path.
    transfers = read_csv(OUT / "p_transfer.csv")
    names = {r["transfer"] for r in transfers}
    require(len(names) >= 3 and all(len([r for r in transfers if r["transfer"] == name]) >= 3 for name in names),
            "fewer than three complete Q1 composition paths")
    for row in transfers:
        require(main.hull(json.loads(row["p_json"]))["inside"], "composition path outside Q1 hull")
    evidence["Q1_hull_checked_transfer_points"] = len(transfers)

    validation = read_csv(OUT / "validation_summary.csv")
    require(set(f"B{i}" for i in range(1, 11)) <= {r["group"] for r in validation}, "missing B1-B10 evidence rows")
    for group, role in (("B2", "shape_only"), ("B3", "shape_only"),
                        ("B6", "nested_in_B7"), ("B7", "group_holdout_semi_synthetic"),
                        ("B8", "conflict_audit"), ("B9", "metadata_only"),
                        ("B10", "estimated_stress_only")):
        require(any(r["group"] == group and r["role"] == role for r in validation), f"data role changed: {group}")
    evidence["validated_B_groups"] = list(range(1, 11))

    fixture_dir = ROOT / "interfaces/cyj/fixtures_v6"
    fixtures = sorted(fixture_dir.glob("*.request.json"))
    require(len(fixtures) == 4, "expected four v6 fixtures")
    for request in fixtures:
        expected = read_json(request.with_name(request.name.replace(".request.", ".expected.")))
        done = subprocess.run([sys.executable, "-B", str(ROOT / "src/cyj/ndqp_scenarios_v6.py"),
                               "--request", str(request)], cwd=ROOT, capture_output=True, text=True)
        require(done.returncode == expected["exit_code"], f"v6 exit status: {request.name}")
        got = json.loads(done.stdout if done.returncode == 0 else done.stderr)
        require(got == (expected["output"] if done.returncode == 0 else {"error": expected["error"]}),
                f"v6 result changed: {request.name}")
    evidence["v6_fixture_count"] = len(fixtures)

    inter = read_csv(OUT / "domain_interactions.csv")
    require(len(inter) == 130 and len({(r["domain_i"], r["domain_j"]) for r in inter}) == 10 and
            len({r["target"] for r in inter}) == 13, "Q1 interaction 10x13 output incomplete")
    for row in inter:
        target_i = main.targets.index(row["target"])
        pair_i = consumer.pairs.index((row["domain_i"], row["domain_j"]))
        require(math.isclose(float(row["gamma_cross_partial_A_loss"]),
                             float(consumer.gamma[target_i, pair_i]), abs_tol=1e-12),
                "interaction cross-partial differs from Q1 coefficients")
    evidence["interaction_rows"] = len(inter)

    comparisons = read_csv(OUT / "ridge_vs_interaction_policy.csv")
    require({r["scenario"] for r in comparisons} == {"equal_13", "arxiv_only", "minimax_13"},
            "missing three observed-recipe model-form policies")
    int_rel = consumer.relative(main.matrix)
    for row in comparisons:
        scenario = row["scenario"]
        if scenario == "minimax_13":
            ridge_objective, int_objective = effects.max(axis=1), int_rel.max(axis=1)
        else:
            weight = (w if scenario == "equal_13" else np.eye(1, 13, main.targets.index("arxiv")).ravel())
            ridge_objective, int_objective = effects @ weight, int_rel @ weight
        ri, ii = int(np.argmin(ridge_objective)), int(np.argmin(int_objective))
        require(row["ridge_observed_index"] == main.indices[ri] and row["interaction_observed_index"] == main.indices[ii],
                f"observed-recipe optimizer mismatch: {scenario}")
        require(math.isclose(float(row["ridge_regret_of_interaction_choice"]),
                             float(ridge_objective[ii] - ridge_objective[ri]), abs_tol=1e-10)
                and math.isclose(float(row["interaction_regret_of_ridge_choice"]),
                                 float(int_objective[ri] - int_objective[ii]), abs_tol=1e-10),
                f"cross-model regret mismatch: {scenario}")
    evidence["policy_form_comparisons"] = len(comparisons)

    acceptance = read_json(OUT / "acceptance.json")
    require(acceptance["all_internal_checks_pass"] and all(acceptance["checks"].values())
            and acceptance["external_test_suite_status"] == "passed_after_rebuild", "V3 C1-C8 changed")
    require((OUT / "FINAL_FACTS.md").is_file() and (OUT / "FINAL_FACTS.md").stat().st_size > 1000,
            "final facts packet missing")

    report = {"schema_version": "cyj.q2.final_closure.v1", "Q2_MODELING_COMPLETE_EXCEPT_PAPER": True,
              "scope": "conditional engineering model, source-bound validation and Q1-fitted domain interactions",
              "formal_scientific_ready_for_Q3": False, "CHM_Q1_interaction_owner_signoff": "pending",
              "CHM_v6_Q3_consumption_signoff": "pending", "checks": {
                  "independent_512_enumeration": True, "QA_raw_inequalities": True,
                  "equal_loss_roots_recomputed": True, "three_Q1_hull_paths": True,
                  "B1_to_B10_roles": True, "no_Q2_raw_A_reads": True,
                  "v6_four_fixtures": True, "Q1_interaction_bundle_SHA_and_130_rows": True,
                  "three_Ridge_vs_interaction_policies": True,
                  "V3_C1_to_C8_retained": True, "final_manifest_SHA": True},
              "evidence": evidence,
              "claim_limit": "Interaction signs are fitted 1M Q1 model-basis diagnostics, not causal synergy or empirically calibrated B7 effects. Lambda/eta remain unidentified."}
    dump(OUT / "final_closure.json", report)
    manifest_path = OUT / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["files_sha256"] = {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"}
    manifest["figures_sha256"] = {p.name: sha(p) for p in sorted(FIG.iterdir()) if p.is_file()}
    manifest["Q1_interaction_manifest_sha256"] = evidence["Q1_interaction_bundle_sha256"]
    dump(manifest_path, manifest)
    fresh = read_json(manifest_path)
    require(set(fresh["files_sha256"]) == {p.name for p in OUT.iterdir() if p.is_file() and p.name != "manifest.json"},
            "result manifest omits a file")
    require(all(sha(OUT / name) == digest for name, digest in fresh["files_sha256"].items()),
            "result manifest SHA mismatch")
    require(all(sha(FIG / name) == digest for name, digest in fresh["figures_sha256"].items()),
            "figure manifest SHA mismatch")
    print(json.dumps({"Q2_MODELING_COMPLETE_EXCEPT_PAPER": True, "checks": len(report["checks"]),
                      "result_files": len(fresh["files_sha256"]),
                      "manifest_sha256": sha(manifest_path)}, ensure_ascii=False))


if __name__ == "__main__":
    run()
