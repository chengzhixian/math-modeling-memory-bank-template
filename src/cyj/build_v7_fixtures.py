"""Freeze executable request/expected pairs for the conditional v7 contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ndqp_scenarios_v7 import ConditionalV7, VERSION, request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "interfaces/cyj/fixtures_v7"


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def main():
    model = ConditionalV7()
    q1 = model.q1
    OUT.mkdir(parents=True, exist_ok=True)
    w = {k: 1/13 for k in q1.targets}
    base = {"schema_version": VERSION, "mode": "baseline", "N_params_B": 1.0,
            "D_tokens_B": 100.0, "Q_score": 0.5, "p_policy": "observed_512",
            "p": q1.p_dict(q1.recipes[135]), "weights": w}
    policies = json.loads((ROOT / "outputs/cyj/q2_v7/policy_details.json").read_text(encoding="utf-8"))
    scenarios = {
        "baseline_reference": {**base, "p": q1.reference, "p_policy": "algebraic_reference_only"},
        "baseline_main_supported": base,
        "baseline_quality_direct": {**base, "p": policies[1]["continuous_hull"]["p"], "p_policy": "quality_direct"},
        "baseline_quality_direct_and_near": {**base, "p": policies[2]["continuous_hull"]["p"],
                                             "p_policy": "quality_direct_and_near"},
        "baseline_minimax_evaluation": {**base, "p": policies[3]["continuous_hull"]["p"],
                                        "p_policy": "convex_hull"},
        "sensitivity_lambda_eta": {**base, "mode": "bridge_sensitivity", "bridge_lambda": 0.75,
                                   "eta": 0.2, "bridge_model": "exp_bridge"},
        "lambda_zero": {**base, "mode": "bridge_sensitivity", "bridge_lambda": 0,
                        "eta": 0.4, "bridge_model": "exp_bridge"},
        "linear_bridge": {**base, "mode": "bridge_sensitivity", "bridge_lambda": 1,
                          "eta": 0, "bridge_model": "linear_bridge"},
        "invalid_N": {**base, "N_params_B": -1},
        "invalid_D": {**base, "D_tokens_B": 0},
        "invalid_Q": {**base, "Q_score": 1.1},
        "invalid_p": {**base, "p": {}},
        "invalid_weights": {**base, "weights": {}},
        "off_hull": {**base, "p": {d: float(d == q1.domains[0]) for d in q1.domains},
                     "p_policy": "convex_hull"},
        "baseline_override": {**base, "bridge_lambda": 1},
        "nonfinite_replacement": {**base, "N_params_B": "NaN"},
        "zero_coverage_observed": {**base, "p": q1.p_dict(q1.recipes[0])},
    }
    files = {}
    for name, data in scenarios.items():
        req = OUT / f"{name}.request.json"
        exp = OUT / f"{name}.expected.json"
        dump(req, data)
        try:
            result = {"exit_code": 0, "result": request(model, data)}
        except (ValueError, TypeError, KeyError) as exc:
            result = {"exit_code": 2, "error_contains": str(exc)}
        dump(exp, result)
        files[req.name] = hashlib.sha256(req.read_bytes()).hexdigest()
        files[exp.name] = hashlib.sha256(exp.read_bytes()).hexdigest()
    raw_cases = {
        "duplicate_key": ('{"schema_version":"x","schema_version":"y"}', "duplicate JSON key: schema_version"),
        "nonfinite_json": (json.dumps(base, ensure_ascii=False).replace('"N_params_B": 1.0', '"N_params_B": NaN'),
                           "N must be a finite number"),
    }
    for name, (raw, error) in raw_cases.items():
        req = OUT / f"{name}.request.json"
        exp = OUT / f"{name}.expected.json"
        req.write_text(raw + "\n", encoding="utf-8", newline="\n")
        dump(exp, {"exit_code": 2, "error_contains": error})
        files[req.name] = hashlib.sha256(req.read_bytes()).hexdigest()
        files[exp.name] = hashlib.sha256(exp.read_bytes()).hexdigest()
    integrity_cases = {
        "invalid_manifest": ("manifest_identity", "Q1 v2 manifest identity mismatch:"),
        "invalid_file_hash": ("model_file_hash", "Q1 v2 identity mismatch: model"),
    }
    for name, (mutation, error) in integrity_cases.items():
        req = OUT / f"{name}.request.json"
        exp = OUT / f"{name}.expected.json"
        dump(req, {"test_kind": "consumer_integrity", "mutation": mutation})
        dump(exp, {"exit_code": 2, "error_contains": error})
        files[req.name] = hashlib.sha256(req.read_bytes()).hexdigest()
        files[exp.name] = hashlib.sha256(exp.read_bytes()).hexdigest()
    count = len(scenarios) + len(raw_cases) + len(integrity_cases)
    dump(OUT / "manifest.json", {"schema_version": "cyj.v7.fixtures.v1", "count": count,
                                  "Q1_manifest_sha256": q1.manifest_sha256, "files": files,
                                  "raw_parser_cases": list(raw_cases),
                                  "consumer_integrity_cases": list(integrity_cases)})
    return count


if __name__ == "__main__":
    print(f"frozen_v7_fixtures={main()}")
