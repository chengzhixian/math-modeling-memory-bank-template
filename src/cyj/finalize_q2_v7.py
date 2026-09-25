"""Independent, fail-closed acceptance of the conditional CYJ Q2 v7 bundle."""
from __future__ import annotations

import csv
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from audit_q2_v7 import main as rebuild_under_audit
from chm_q1_v2_consumer import ROOT, Q1V2Consumer, sha256
from ndqp_scenarios_v7 import BOUNDS, THETA
from verify_v7_fixtures import main as verify_fixtures

OUT = ROOT / "outputs/cyj/q2_v7"


def read_json(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def read_csv(name):
    with (OUT / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, label, tolerance=1e-8):
    require(math.isfinite(actual) and abs(actual-expected) <= tolerance,
            f"{label}: {actual} != {expected}")


def independent_b7(theta, n, d, q):
    e, a, b, alpha, beta, g0, gn, gd = theta
    return e+a/n**alpha+b/d**beta+(1-q)*(g0+gn*math.log(n)+gd*math.log(d/100))


def independent_relative(q1, p):
    x = [p[d] for d in q1.domains]
    values = []
    for i, target in enumerate(q1.targets):
        value = q1.upstream.intercepts[i]
        value += sum(x[j]*q1.upstream.main[i, j] for j in range(17))
        value += sum(q1.upstream.gamma[i, k]*x[a]*x[b]
                     for k, (a, b) in enumerate(q1.upstream.pairs))
        values.append(value/q1.upstream.reference_loss[i]-1)
    return dict(zip(q1.targets, values))


def check_paper():
    log_path = ROOT / "paper/latex/.build_v7/main.log"
    pdf_path = ROOT / "paper/latex/.build_v7/main.pdf"
    require(log_path.is_file() and pdf_path.is_file(), "Q2 paper needs two-pass XeLaTeX build")
    for relative in ("paper/latex/sections/cyj/q2.tex", "paper/latex/sections/cyj/q2_v7_tail.tex",
                     "paper/latex/figures/cyj/q2_v7_bridge_sensitivity.pdf"):
        require(log_path.stat().st_mtime >= (ROOT / relative).stat().st_mtime,
                f"Q2 paper build is older than {relative}")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    start = log.find("(./sections/cyj/q2.tex")
    end = log.find("(./sections/cyj/q3_theory.tex", start)
    require(start >= 0 and end > start and "Overfull" not in log[start:end],
            "Q2 TeX segment failed layout check")
    require("undefined references" not in log[start:end].lower(), "Q2 unresolved cross-reference")
    match = re.search(r"Output written on .*?\((\d+) pages?\)", log)
    require(match is not None, "compiled PDF page count missing")
    return {"Q2_segment_overfull": 0, "paper_pages": int(match.group(1)),
            "other_section_overfull": log.count("Overfull"),
            "whole_paper_undefined_citations": "There were undefined citations" in log,
            "pdf_sha256": sha256(pdf_path),
            "paper_source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in (
                ROOT / "paper/latex/sections/cyj/q2.tex",
                ROOT / "paper/latex/sections/cyj/q2_v7_tail.tex")}}


def main():
    previous_audit = json.loads((ROOT / "outputs/cyj/q2_v7_runtime_audit.json").read_text(encoding="utf-8"))
    rebuilt = rebuild_under_audit()
    require(rebuilt["manifest_sha256"] == previous_audit["manifest_sha256"],
            "two consecutive pre-acceptance builds differ")
    manifest = read_json("manifest.json")
    for name, digest in manifest["files"].items():
        require(sha256(OUT / name) == digest, f"output file changed after build: {name}")
    q1 = Q1V2Consumer()
    require(manifest["Q1_manifest_sha256"] == q1.manifest_sha256, "Q1 pin differs")
    bounds = read_json("upstream_bounds_revalidation.json")
    require(bounds["all_four_reproduced"] and len(bounds["rows"]) == 4, "CHM four-policy bounds not reproduced")
    require(bounds["current_bounds_sha256"] == sha256(q1.bounds_path), "current Q1 bounds differ")
    local_bounds = read_json("single_target_hull_bounds.json")
    require(len(local_bounds["rows"]) == 2 and all(
        r["absolute_gap_relative"] <= .001 for r in local_bounds["rows"]),
        "single-target numerical bound incomplete")
    joint_path = ROOT / "outputs/cyj/quality/b7_joint_fit.json"
    joint = json.loads(joint_path.read_text(encoding="utf-8"))
    theta = tuple(joint["model"]["theta"])
    require(theta == THETA, "B7 joint model differs from frozen coefficients")
    policies = read_json("policy_details.json")
    rows = read_csv("policy_solutions.csv")
    require(len(policies) == 6 and len(rows) == 12, "expected six policies on observed and hull support")
    b7_value = independent_b7(theta, 1, 100, .5)
    checked = 0
    for entry in policies:
        for support_name in ("observed_512", "continuous_hull"):
            item = entry[support_name]
            require("p" in item and item["status"] in ("exact_observed_512", "numerically_bounded_feasible"),
                    "missing Q2 policy candidate")
            p = item["p"]
            policy = ("observed_512" if support_name == "observed_512"
                      else entry["quality_policy"] or "convex_hull")
            q1.support(p, policy)
            effects = independent_relative(q1, p)
            r = sum(entry["weights"].get(k, 0)*effects[k] for k in q1.targets)
            scalar = b7_value*math.exp(r)
            close(item["r_w"], r, "Q1 relative effect")
            close(item["baseline_loss"], scalar, "Q2 conditional Loss")
            if entry["objective_mode"] == "weighted":
                close(item["objective"], r, "weighted optimization objective")
            else:
                close(item["objective"], max(effects[k] for k in q1.targets if entry["weights"].get(k, 0) > 0),
                      "minimax optimization objective")
            if support_name == "continuous_hull":
                require(0 <= item["absolute_gap_relative"] <= .001,
                        "continuous numerical optimality gap exceeds tolerance")
            checked += 1
    grid = read_csv("bridge_sensitivity.csv")
    require(len(grid) == 1728, "bridge grid is incomplete")
    invalid_linear = 0
    for row in grid:
        entry = next(p for p in policies if p["policy"] == row["policy"])
        item = entry[row["support"]]
        n, d, q = map(float, (row["N_params_B"], row["D_tokens_B"], row["Q_score"]))
        lam, eta = float(row["lambda"]), float(row["eta"])
        base = independent_b7(theta, n, d, q)
        effect = independent_relative(q1, item["p"])
        r = sum(entry["weights"].get(k, 0)*effect[k] for k in q1.targets)
        z = lam*n**(-eta)*r
        if row["bridge_model"] == "linear_bridge":
            factor = 1+z
            if factor <= 0:
                require(row["status"] != "valid", "invalid linear factor accepted")
                invalid_linear += 1
                continue
        else:
            factor = math.exp(z)
        require(row["status"] == "valid", "valid bridge case rejected")
        close(float(row["Loss"]), base*factor, "bridge grid independent formula")
    require(invalid_linear == 9, "unexpected count of invalid linear scenarios")
    panel = read_csv("bridge_form_observed_panel.csv")
    require(len(panel) == 5 and all(r["ranking_identical_on_common_valid"] == "True" for r in panel),
            "observed bridge ordering check failed")
    quality = read_csv("quality_vs_scale.csv")
    require(any(r["status"] == "no_root_in_support" for r in quality), "missing no-root case")
    require(any(r["status"] == "target_Q_out_of_support" for r in quality), "missing Q out-of-support case")
    uncertainty = read_json("uncertainty_scope.json")
    require(uncertainty["cross_source_interval"] is None and uncertainty["B7_parameter_bootstrap_draws"] == 200,
            "uncertainty scope exceeds evidence")
    require(len(read_csv("b7_parameter_uncertainty.csv")) == 12, "parameter spread lacks a policy")
    require(len(read_csv("requirement_evidence.csv")) == 11, "official requirement map incomplete")
    require(len(read_csv("claim_ladder.csv")) == 6, "claim ladder incomplete")
    fixture_result = verify_fixtures()
    require(fixture_result["fixtures"] == 21, "v7 fixture set incomplete")
    tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                            "src/cyj/tests", "-p", "test_*.py", "-q"],
                           cwd=ROOT, text=True, capture_output=True, timeout=240, check=False)
    require(tests.returncode == 0, f"CYJ regression failed: {tests.stdout} {tests.stderr}")
    match = re.search(r"Ran (\d+) tests", tests.stderr+tests.stdout)
    require(match is not None and int(match.group(1)) >= 84, "CYJ test count below baseline")
    paper = check_paper()
    smoke = json.loads((ROOT / "outputs/cyj/q3_v7_sample_smoke.json").read_text(encoding="utf-8"))
    require(smoke["status"] == "conditional_integration_smoke_pass" and
            smoke["Q1_manifest_sha256"] == q1.manifest_sha256 and
            smoke["solution"]["primal_feasible"], "Q3 local sample smoke missing")
    audit = json.loads((ROOT / "outputs/cyj/q2_v7_runtime_audit.json").read_text(encoding="utf-8"))
    require(audit["original_A_open_events"] == 0 and audit["derived_Q1_open_events"] > 0
            and audit["approved_legacy_git_show_events"] > 0
            and audit["unapproved_subprocess_launch_events"] == 0, "original A read audit failed")
    acceptance = {"schema_version": "cyj.q2.v7.acceptance.v1",
                  "q2_implementation_complete": True,
                  "q2_answer_complete_under_stated_assumptions": True,
                  "q3_consumer_interface_ready": True,
                  "q3_consumer_verified": False,
                  "release_remote_verified": False,
                  "integrated_in_main": False,
                  "cross_source_empirical_calibration_complete": False,
                  "status": "conditional_Q2_complete_pending_CHM_consumption_and_main_integration",
                  "checks": {"policy_candidates": checked, "grid_rows": len(grid),
                             "invalid_linear_rows": invalid_linear,
                             "fixtures": fixture_result["fixtures"], "CYJ_tests": int(match.group(1)),
                             "raw_A_open_events": 0,
                             "approved_legacy_git_show_events": audit["approved_legacy_git_show_events"],
                             "unapproved_subprocess_launch_events": 0, "paper": paper,
                             "current_Q1_bounds_reproduced": True,
                             "old_CHM_bounds_signoff_hash_matches_current": bounds["CHM_signoff_hash_matches_current_bounds"]},
                  "evidence_paths": ["outputs/cyj/q2_v7/upstream_bounds_revalidation.json",
                                     "outputs/cyj/q2_v7/single_target_hull_bounds.json",
                                     "outputs/cyj/q2_v7/requirement_evidence.csv",
                                     "outputs/cyj/q2_v7/claim_ladder.csv",
                                     "outputs/cyj/q2_v7_runtime_audit.json",
                                     "interfaces/cyj/fixtures_v7/manifest.json",
                                     "paper/latex/sections/cyj/q2_v7_tail.tex"],
                  "review_scope": "CYJ local independent arithmetic and software checks; no A/B empirical calibration or CHM owner signature"}
    closure = {"schema_version": "cyj.q2.v7.closure.v1",
               "status": "Q2_conditional_answer_complete",
               "CHM_owner_Q3_consumer_acceptance": "pending",
               "main_integration": "pending",
               "current_CHM_bounds_signoff_hash": "stale_but_current_bounds_reproduced_by_CYJ",
               "cross_source_empirical_calibration_complete": False,
               "whole_paper_submission_ready": False}
    for name, value in (("acceptance.json", acceptance), ("final_closure.json", closure)):
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                                encoding="utf-8", newline="\n")
    manifest = read_json("manifest.json")
    manifest["code_sha256"]["finalize_q2_v7.py"] = sha256(ROOT / "src/cyj/finalize_q2_v7.py")
    manifest["paper_source_sha256"] = paper["paper_source_sha256"]
    manifest["paper_figure_sha256"] = sha256(ROOT / "paper/latex/figures/cyj/q2_v7_bridge_sensitivity.pdf")
    for name in manifest["files"]:
        manifest["files"][name] = sha256(OUT / name)
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n",
                                         encoding="utf-8", newline="\n")
    return {"status": acceptance["status"], "CYJ_tests": int(match.group(1)),
            "fixtures": fixture_result["fixtures"], "output_manifest_sha256": sha256(OUT / "manifest.json")}


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
