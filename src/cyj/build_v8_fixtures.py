"""Freeze complete v8 request/expected examples without changing historical v7 fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from chm_q1_v2_consumer import ROOT
from ndqp_scenarios_v8 import ConditionalV8, VERSION, request

OUT = ROOT / "interfaces/cyj/fixtures_v8"


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                    encoding="utf-8", newline="\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model = ConditionalV8()
    q1 = model.q1
    policy = json.loads((ROOT/"outputs/cyj/q2_v8/main_policy.json").read_text(encoding="utf-8"))
    weights = policy["weights"]
    base = {"schema_version": VERSION, "mode": "baseline", "N_params_B": 1.0,
            "D_tokens_B": 100.0, "p": policy["p"], "weights": weights,
            "p_policy": "quality_direct_and_near", "quality_mapping_policy": "direct_and_near"}
    direct = json.loads((ROOT/"outputs/cyj/q2_v7/policy_details.json").read_text(encoding="utf-8"))[1]
    scenarios = {
        "baseline_main": base,
        "baseline_reference": {**base, "p": q1.reference, "p_policy": "algebraic_reference_only"},
        "baseline_direct": {**base, "p": direct["observed_512"]["p"],
                            "p_policy": "quality_direct", "quality_mapping_policy": "direct"},
        "quality_compressed": {**base, "mode": "sensitivity", "quality_mode": "q1_quality_bridge_sensitivity",
                               "quality_bridge_scale": .5},
        "quality_expanded": {**base, "mode": "sensitivity", "quality_mode": "q1_quality_bridge_sensitivity",
                             "quality_bridge_scale": 1.5},
        "native_QB": {**base, "mode": "sensitivity", "quality_mode": "native_QB_sensitivity",
                      "native_QB": .5},
        "lambda_zero": {**base, "mode": "sensitivity", "quality_mode": "q1_quality_bridge_sensitivity",
                        "mixture_bridge_lambda": 0.0, "mixture_bridge_eta": .2},
        "linear_bridge": {**base, "mode": "sensitivity", "quality_mode": "q1_quality_bridge_sensitivity",
                          "bridge_model": "linear_bridge"},
        "baseline_reject_native_QB": {**base, "native_QB": .5},
        "invalid_N": {**base, "N_params_B": .01},
        "invalid_D": {**base, "D_tokens_B": 600},
        "invalid_p": {**base, "p": {}},
        "invalid_weights": {**base, "weights": {}},
        "off_hull": {**base, "p": {d: float(d == q1.domains[0]) for d in q1.domains},
                     "p_policy": "convex_hull"},
        "zero_coverage": {**base, "p": q1.p_dict(q1.recipes[130]), "p_policy": "observed_512"},
        "invalid_quality_scale": {**base, "mode": "sensitivity",
                                  "quality_mode": "q1_quality_bridge_sensitivity",
                                  "quality_bridge_scale": -1},
    }
    hashes = {}
    for name, payload in scenarios.items():
        req, expected = OUT/f"{name}.request.json", OUT/f"{name}.expected.json"
        write(req, payload)
        try:
            value = {"exit_code": 0, "result": request(model, payload)}
        except (ValueError, KeyError, TypeError) as exc:
            value = {"exit_code": 2, "error_contains": str(exc)}
        write(expected, value)
        hashes[req.name] = hashlib.sha256(req.read_bytes()).hexdigest()
        hashes[expected.name] = hashlib.sha256(expected.read_bytes()).hexdigest()
    raw = {"duplicate_key": ('{"schema_version":"one","schema_version":"two"}',
                             "duplicate JSON key: schema_version"),
           "nonfinite_N": (json.dumps(base).replace('"N_params_B": 1.0', '"N_params_B": NaN'),
                           "N_params_B must be a finite number")}
    for name, (body, error) in raw.items():
        req, expected = OUT/f"{name}.request.json", OUT/f"{name}.expected.json"
        req.write_text(body+"\n", encoding="utf-8", newline="\n")
        write(expected, {"exit_code": 2, "error_contains": error})
        hashes[req.name] = hashlib.sha256(req.read_bytes()).hexdigest()
        hashes[expected.name] = hashlib.sha256(expected.read_bytes()).hexdigest()
    write(OUT/"manifest.json", {"schema_version": "cyj.v8.fixtures.v1",
                                "count": len(scenarios)+len(raw),
                                "Q1_manifest_sha256": q1.manifest_sha256,
                                "quality_fit_sha256": model.quality_fit_sha256,
                                "raw_parser_cases": list(raw), "files": hashes})
    return len(scenarios)+len(raw)


if __name__ == "__main__":
    print(f"frozen_v8_fixtures={main()}")
