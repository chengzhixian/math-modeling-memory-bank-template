"""Validate and seal CHM's conditional Q3 v8 result tables."""
from __future__ import annotations

import csv
import json
import math
import platform
from pathlib import Path

import numpy
import scipy

from q3_conditional_v8 import OUTPUT, OFFICIAL_BUDGETS, main_policy
from q3_v8_inputs import ROOT, digest, load_v8, verify_export


TABLES = (
    "fixed_policy_grid.csv", "observed_joint_grid.csv", "native_Q_sensitivity_grid.csv",
    "fixed_budget_scan.csv", "observed_budget_scan.csv", "transitions.csv",
    "transition_resolution.json",
)
CODE = (
    "src/chm/q3_v8_inputs.py", "src/chm/q3_conditional_v8.py",
    "src/chm/q3_v8_transition_scan.py", "src/chm/q3_v8_publish.py",
    "src/chm/test_q3_conditional_v8.py", "src/chm/plot_q3_v8.py",
)
PAPER = (
    "paper/latex/sections/chm/q3_numerical.tex",
    "paper/latex/figures/chm/q3_v8_power_8192.png",
)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _numeric(value: str, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is missing or invalid") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} is nonfinite")
    return number


def validate_feasible(row: dict, bounds, kind: str) -> None:
    if row.get("cross_source_empirical_calibration_complete") != "False":
        raise ValueError("Q3 row claims cross-source empirical calibration")
    n = _numeric(row.get("N_params_B"), "N")
    d = _numeric(row.get("D_tokens_B"), "D")
    q_field = "Q_score" if kind == "native_Q" else "Q_B_proxy"
    q = _numeric(row.get(q_field), q_field)
    if any(not lo-1e-10 <= value <= hi+1e-10 for value, (lo, hi) in zip((n, d, q), bounds)):
        raise ValueError("Q3 result outside v8 common support")
    if q < _numeric(row.get("Q0_scenario"), "Q0")-1e-10:
        raise ValueError("Q3 result below Q0")
    budget = _numeric(row.get("budget_FLOPs"), "budget")
    parts = [_numeric(row.get(name), name) for name in (
        "C_train_FLOPs", "C_attention_FLOPs", "C_quality_FLOPs")]
    total = _numeric(row.get("C_total_FLOPs"), "total cost")
    if min(parts) < -1e-9 or not math.isclose(sum(parts), total, rel_tol=1e-10):
        raise ValueError("Q3 three-part cost mismatch")
    if total > budget*(1+1e-8):
        raise ValueError("Q3 result exceeds budget")
    if _numeric(row.get("conditional_bridge_loss"), "conditional Loss") <= 0:
        raise ValueError("Q3 Loss is not positive")
    if kind == "fixed" and _numeric(row.get("fixed_p_convex_gap"), "fixed-p gap") > 1e-7:
        raise ValueError("fixed-p numerical gap too wide")
    if kind == "native_Q" and _numeric(row.get("global_gap"), "native-Q gap") > 1.1e-7:
        raise ValueError("native-Q numerical gap too wide")


def validate(out_dir: Path = OUTPUT) -> dict:
    model, bounds = load_v8()
    policy = main_policy(model)
    data = {name: read_csv(out_dir/name) for name in TABLES if name.endswith(".csv")}
    fixed, joint, native = (data[name] for name in TABLES[:3])
    if any(len(rows) != 36 for rows in (fixed, joint, native)):
        raise ValueError("Q3 official-plus-extra grid must contain 36 rows per mode")
    if len(data["fixed_budget_scan.csv"]) != 1449 or len(data["observed_budget_scan.csv"]) != 1449:
        raise ValueError("Q3 continuous-budget scan is incomplete")
    resolution = json.loads((out_dir/"transition_resolution.json").read_text(encoding="utf-8"))
    if resolution["transition_brackets"] != len(data["transitions.csv"]):
        raise ValueError("Q3 transition count differs from resolution record")
    if resolution["fixed_scan_sha256"] != digest(out_dir/"fixed_budget_scan.csv") or \
       resolution["joint_scan_sha256"] != digest(out_dir/"observed_budget_scan.csv") or \
       resolution["transitions_sha256"] != digest(out_dir/"transitions.csv"):
        raise ValueError("Q3 transition hash changed")
    if max(_numeric(row["relative_width"], "transition width") for row in data["transitions.csv"]) > 1e-4:
        raise ValueError("Q3 transition bracket too wide")
    for rows, status, kind in ((fixed, "conditional_v8_fixed_policy_feasible", "fixed"),
                               (joint, "conditional_v8_fixed_policy_feasible", "joint"),
                               (native, "conditional_v8_native_Q_sensitivity_feasible", "native_Q")):
        cells = set()
        for row in rows:
            key = (row["budget_FLOPs"], row["context_tokens"], row["quality_family"])
            if key in cells:
                raise ValueError("duplicate Q3 scenario key")
            cells.add(key)
            if row["status"] == status:
                validate_feasible(row, bounds, kind)
            elif row.get("conditional_bridge_loss"):
                raise ValueError("infeasible Q3 row contains a Loss")
        if len(cells) != 36:
            raise ValueError("Q3 scenario cells missing")
    if any(row["recipe_index"] != policy["recipe_index"] for row in fixed):
        raise ValueError("fixed Q2 policy changed")
    if any(row["eligible_observed_recipes"] != "87" for row in joint):
        raise ValueError("observed candidate set changed")
    by_key = lambda rows: {(r["budget_FLOPs"], r["context_tokens"], r["quality_family"]): r for r in rows}
    for key, chosen in by_key(joint).items():
        baseline = by_key(fixed)[key]
        if chosen["status"] == "conditional_v8_fixed_policy_feasible" and \
           baseline["status"] == "conditional_v8_fixed_policy_feasible" and \
           _numeric(chosen["conditional_bridge_loss"], "joint Loss") > \
           _numeric(baseline["conditional_bridge_loss"], "fixed Loss")+1e-9:
            raise ValueError("observed joint optimization is worse than its included fixed policy")
    return {"fixed_feasible": sum(r["status"] == "conditional_v8_fixed_policy_feasible" for r in fixed),
            "observed_joint_feasible": sum(r["status"] == "conditional_v8_fixed_policy_feasible" for r in joint),
            "native_Q_sensitivity_feasible": sum(r["status"] == "conditional_v8_native_Q_sensitivity_feasible" for r in native),
            "transition_brackets": len(data["transitions.csv"]),
            "fixed_recipe": policy["recipe_index"],
            "official_budget_count": len(OFFICIAL_BUDGETS)}


def publish(out_dir: Path = OUTPUT) -> dict:
    counts = validate(out_dir)
    inputs = verify_export()
    manifest = {"schema_version": "chm.q3.conditional_v8.release.v1",
                "status": "conditional_problem_answer_not_empirically_calibrated",
                "producer_branch": "integration/chm-q1-clean-20260923",
                "inputs": {key: value for key, value in inputs.items() if key != "verified_files"},
                "input_files_sha256": inputs["verified_files"],
                "output_files_sha256": {name: digest(out_dir/name) for name in TABLES},
                "code_files_sha256": {name: digest(ROOT/name) for name in CODE},
                "paper_files_sha256": {name: digest(ROOT/name) for name in PAPER},
                "counts": counts,
                "data_roles": {"B1": "fixed_backbone_training", "B7": "semi_synthetic_quality_fit_and_nested_CV",
                               "A4_A5": "Q1_frozen_training_only", "A6_A11": "Q1_prior_same_project_check_not_blind_final_test",
                               "C7": "observed_external_context_scenarios", "B10": "estimated_stress_not_validation"},
                "units": {"N": "billion_parameters", "D": "billion_tokens",
                          "context": "tokens", "cost": "FLOPs"},
                "Q0": 0.5, "quality_proxy": "uncalibrated_monotone_A_to_B_assumption",
                "cross_source_empirical_calibration_complete": False,
                "joint_prediction_interval_95": None,
                "optimization_bound_scope": "floating_point_fixed_policy_convex_and_native_Q_certificate_only",
                "python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
                "commands": ["python -B src/chm/q3_conditional_v8.py",
                             "python -B src/chm/q3_v8_transition_scan.py",
                             "python -B src/chm/q3_v8_publish.py"]}
    path = out_dir/"manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                    encoding="utf-8", newline="\n")
    return manifest


def verify_manifest(out_dir: Path = OUTPUT) -> None:
    manifest = json.loads((out_dir/"manifest.json").read_text(encoding="utf-8"))
    for section, base in (("output_files_sha256", out_dir), ("code_files_sha256", ROOT),
                          ("paper_files_sha256", ROOT)):
        for relative, expected in manifest[section].items():
            if digest(base/relative) != expected:
                raise ValueError(f"Q3 manifest hash mismatch: {relative}")


if __name__ == "__main__":
    print(json.dumps(publish()["counts"], ensure_ascii=False))
