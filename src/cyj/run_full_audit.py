"""One-command evidence audit for CYJ's conditional B7/Q3 release.

Run from the repository root with the local scientific Python environment. The
script validates frozen artifacts; expensive fitting and sweeps are separate
reproduction commands documented in the experiment notes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/cyj/audit"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def document(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def rows(path: str):
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def near(actual, expected, tolerance=1e-10):
    return math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance)


def assess(name, operation, checks):
    try:
        detail = operation()
        checks.append({"name": name, "status": "PASS", "detail": detail})
    except Exception as exc:
        checks.append({"name": name, "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"})


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def data_hashes():
    fit = document("outputs/cyj/quality/b7_joint_fit.json")
    classic = document("outputs/cyj/classic/classic_data_manifest.json")
    all_sources = {**classic["provenance"]["source_files"], **fit["source_files"]}
    conflict = document("outputs/cyj/quality/b7_b8_conflict_summary.json")
    all_sources.update(conflict["source_files"])
    for name, info in all_sources.items():
        path = ROOT / info["path"]
        require(path.stat().st_size == info["bytes"] and sha(path) == info["sha256"], f"source drift: {name}")
    return f"{len(all_sources)} source files match recorded bytes and SHA256"


def model_hashes():
    model = ROOT / "outputs/cyj/quality/b7_joint_fit.json"
    digest = sha(model)
    expected = document("outputs/cyj/quality/b7_identifiability.json")
    require(expected["model_hash"] == digest, "identifiability model hash mismatch")
    manifest = document("outputs/cyj/interfaces/chm_v4_manifest.json")
    require(manifest["model_hash"] == digest, "v4 model hash mismatch")
    require(not manifest["ready_for_Q3"], "formal Q3 gate incorrectly open")
    return digest


def b1_fit():
    fit = document("outputs/cyj/classic/classic_fit.json")
    audit = document("outputs/cyj/classic/b1_structure_audit.json")
    require(fit["status"] == "draft_classic_baseline_not_validated_predictor", "unexpected B1 status")
    require(audit["rows"] == 1176 and audit["N_groups"] == 8 and audit["common_D_grid_across_N"], "B1 structure drift")
    require(audit["explicit_loss_generator_found"] is False, "B1 generator claim changed")
    return f"B1 {audit['rows']} rows, unknown loss generator"


def joint_fit():
    fit = document("outputs/cyj/quality/b7_joint_fit.json")
    model = fit["model"]
    require(len(model["theta"]) == 8 and model["successful_starts"] >= 12, "joint optimization incomplete")
    require(not model["best_at_boundary"] and min(model["corner_quality_gain"]) > 0, "joint constraints failed")
    comparison = fit["comparison"]
    require(len(comparison) == 2, "staged comparison missing")
    return f"8 parameters, {model['successful_starts']} starts, min G={min(model['corner_quality_gain']):.6g}"


def nested_cv():
    summary = document("outputs/cyj/quality/b7_nested_cv_summary.json")
    predictions = ROOT / "outputs/cyj/quality/b7_nested_cv_predictions.csv"
    require(summary["prediction_sha256"] == sha(predictions), "nested OOF hash mismatch")
    data = rows("outputs/cyj/quality/b7_nested_cv_predictions.csv")
    require(len(summary["folds"]) == 24 and len(data) == 1350, "fold or OOF count changed")
    counts = Counter(r["axis"] for r in data)
    require(counts == {"N_params_B": 450, "D_tokens_B": 450, "Q_score": 450}, "axis OOF count changed")
    for row in data:
        require(near(float(row["observed"]) - float(row["prediction"]), row["residual"]), "OOF residual mismatch")
    return f"24 outer folds; {len(data)} held-out predictions"


def monotonicity():
    from quality_substitution import derivatives
    theta = document("outputs/cyj/quality/b7_joint_fit.json")["model"]["theta"]
    worst = -math.inf
    for n in (0.07, 11.97):
        for d in (10.0, 600.0):
            for q in (0.1, 1.0):
                _, gradient = derivatives(theta, n, d, q)
                require(all(math.isfinite(v) and v < 0 for v in gradient), "nondecreasing or nonfinite gradient")
                worst = max(worst, gradient[2])
    return f"all 8 support corners have negative N/D/Q derivatives; max L_Q={worst:.6g}"


def gradient_check():
    from chm_adapter_v4 import CHMAdapterV4
    adapter = CHMAdapterV4(mode="conditional_diagnostic")
    for point in ((0.07, 10.0, 0.1), (0.7, 150.0, 0.5), (11.97, 600.0, 1.0)):
        _, analytic = adapter.value_grad(*point)
        for axis, value in enumerate(point):
            if point != (0.7, 150.0, 0.5):
                continue
            step = value * 1e-5
            lo, hi = list(point), list(point)
            lo[axis] -= step
            hi[axis] += step
            numeric = (adapter.value_grad(*hi)[0] - adapter.value_grad(*lo)[0]) / (2 * step)
            require(abs(numeric - analytic[axis]) <= 1e-5 * max(abs(analytic[axis]), 1e-5), f"gradient axis {axis}")
    return "center-point finite differences agree with analytic N/D/Q derivatives"


def interval_coverage():
    calibration = document("outputs/cyj/quality/b7_interval_calibration.json")
    data = rows("outputs/cyj/quality/b7_nested_cv_predictions.csv")
    checked = 0
    for entry in calibration["coverage"]:
        if entry["held_level"] is not None:
            continue
        axis = entry["axis"]
        selected = [r for r in data if r["axis"] == axis]
        nominal = str(entry["nominal"])
        prefix = f"{entry['method']}_{nominal}"
        cover = sum(float(r[f"{prefix}_lower"]) <= float(r["observed"]) <= float(r[f"{prefix}_upper"]) for r in selected) / len(selected)
        width = sum(float(r[f"{prefix}_upper"]) - float(r[f"{prefix}_lower"]) for r in selected) / len(selected)
        require(near(cover, entry["coverage"]) and near(width, entry["mean_width"]), f"coverage mismatch: {axis}/{prefix}")
        checked += 1
    require(checked == 18, f"only {checked} aggregate coverage cells")
    return "18 nominal/method/axis coverage and interval-width cells independently recomputed"


def q3_sweep():
    manifest = document("outputs/cyj/q3/q3_sweep_manifest.json")
    path = ROOT / "outputs/cyj/q3/q3_budget_sweep.csv"
    require(manifest["budget_sweep_sha256"] == sha(path), "Q3 budget CSV hash mismatch")
    data = rows("outputs/cyj/q3/q3_budget_sweep.csv")
    require(len(data) == 330, f"Q3 grid has {len(data)} rows")
    require({r["quality_family"] for r in data} == {"exponential", "power", "logarithmic"}, "cost family missing")
    require(all(r["ready_for_Q3"] == "False" for r in data), "formal Q3 gate opened")
    return f"{len(data)} grid cells; statuses {dict(Counter(r['status'] for r in data))}"


def q3_context():
    manifest = document("outputs/cyj/q3/q3_sweep_manifest.json")
    path = ROOT / "outputs/cyj/q3/q3_context_sweep.csv"
    require(manifest["context_sweep_sha256"] == sha(path), "context CSV hash mismatch")
    data = rows("outputs/cyj/q3/q3_budget_sweep.csv")
    contexts = {int(r["context_tokens"]) for r in data}
    require({24576, 30000, 32768, 49152} <= contexts, "critical-context neighborhood missing")
    require(len(rows("outputs/cyj/q3/q3_context_sweep.csv")) == 90, "context subset size drift")
    return f"{len(contexts)} contexts including 30000 and 32768"


def q3_support():
    data = rows("outputs/cyj/q3/q3_budget_sweep.csv")
    evaluated = 0
    for row in data:
        if row["status"] != "converged_feasible":
            require(row["regime"] in ("infeasible", "unresolved"), "unclear nonconverged regime")
            continue
        n, d, q = (float(row[k]) for k in ("N_params_B", "D_tokens_B", "Q_score"))
        require(0.07 - 1e-10 <= n <= 11.97 + 1e-10 and 10 - 1e-10 <= d <= 600 + 1e-10 and 0.5 - 1e-10 <= q <= 1 + 1e-10, "Q3 outside supported bounds")
        require(float(row["budget_utilization"]) <= 1 + 1e-6, "budget violation")
        require(row["kkt_check_pass"] == "True", "KKT check failed")
        if row["support_saturated"] == "True":
            require(row["regime"] == "support_limited" and row["budget_active"] == "False", "support saturation misclassified")
        evaluated += 1
    require(evaluated >= 300, "too few evaluated Q3 cells")
    return f"{evaluated} solutions satisfy support, budget and recorded KKT check"


def manifest_reproducibility():
    from build_chm_release_v4 import run
    path = ROOT / "outputs/cyj/interfaces/chm_v4_manifest.json"
    before = path.read_bytes()
    run()
    require(path.read_bytes() == before, "v4 manifest not reproducible")
    manifest = json.loads(before)
    for relative, digest in manifest["files_sha256_utf8_lf"].items():
        require(hashlib.sha256((ROOT / relative).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest, f"manifest file drift: {relative}")
    return f"manifest reproduced; {len(manifest['files_sha256_utf8_lf'])} file hashes agree"


def unit_tests():
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "src/cyj/tests", "-p", "test_*.py", "-q"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=300)
    require(result.returncode == 0, (result.stdout + result.stderr)[-2000:])
    return (result.stdout + result.stderr).strip()[-300:]


def latex_compile():
    program = shutil.which("xelatex")
    if not program:
        return "BLOCKED_BY_EXTERNAL_DEPENDENCY: XeLaTeX unavailable"
    work = ROOT / "paper/latex"
    result = subprocess.run([program, "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=work,
                            capture_output=True, text=True, timeout=120)
    require(result.returncode == 0, result.stdout[-1200:] + result.stderr[-1200:])
    log = (work / "main.log").read_text(encoding="utf-8", errors="replace")
    require("Overfull \\hbox" not in log, "overfull paper box")
    return "XeLaTeX built 8-page team draft; no overfull boxes"


def run():
    checks = []
    tasks = (("data_hashes", data_hashes), ("model_hashes", model_hashes), ("B1_fit", b1_fit),
             ("B7_joint_fit", joint_fit), ("nested_CV", nested_cv), ("monotonicity", monotonicity),
             ("gradient", gradient_check), ("interval_coverage", interval_coverage),
             ("Q3_budget_sweep", q3_sweep), ("Q3_context_sweep", q3_context),
             ("Q3_support_KKT", q3_support), ("manifest_reproducibility", manifest_reproducibility),
             ("unit_tests", unit_tests), ("LaTeX_compile", latex_compile))
    for name, operation in tasks:
        assess(name, operation, checks)
        print(f"{checks[-1]['status']}: {name}: {checks[-1]['detail']}", flush=True)
    for check in checks:
        if check["detail"].startswith("BLOCKED_BY_EXTERNAL_DEPENDENCY:"):
            check["status"] = "BLOCKED_BY_EXTERNAL_DEPENDENCY"
    failed = any(item["status"] == "FAIL" for item in checks)
    blocked = any(item["status"] == "BLOCKED_BY_EXTERNAL_DEPENDENCY" for item in checks)
    status = "FAIL" if failed else "BLOCKED_BY_EXTERNAL_DEPENDENCY" if blocked else "PASS_WITH_LIMITATIONS"
    report = {"status": status, "checks": checks, "scientific_status": "conditional_B7_semi_synthetic",
              "candidate_result_scope": "B7_NDQ_plus_conditional_Q3", "formal_result_scope": None,
              "ready_for_Q3": False,
              "limitations": ["B7 semi-synthetic with no real-training external test",
                              "B7 function family was explored before nested evaluation",
                              "bootstrap-plus-residual v4 interval lacks direct held-out coverage calibration",
                              "A/B loss or quality bridge and team acceptance absent"],
              "model_hash": sha(ROOT / "outputs/cyj/quality/b7_joint_fit.json")}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "full_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# CYJ full audit", "", f"Status: **{status}**", "", "| Check | Status | Detail |", "|---|---|---|"]
    for item in checks:
        lines.append(f"| {item['name']} | {item['status']} | {item['detail'].replace('|', '/').replace(chr(10), ' ')} |")
    lines += ["", "## Scientific limits", ""] + [f"- {item}" for item in report["limitations"]]
    (OUT / "full_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(status)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
