"""Hash-checked Q1-output-only NDQP v6 process consumer.

The Q1 export is produced separately by src/chm/export_q1_q2_bundle.py.
This program never opens original attachment-A files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from q2_final_core import Q2Final, VERSION


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def batch(model: Q2Final, request: dict):
    if (not isinstance(request, dict) or set(request) != {"schema_version", "mode", "requests"}
            or request["schema_version"] != VERSION or request["mode"] != "conditional_diagnostic"
            or not isinstance(request["requests"], list) or not request["requests"]):
        raise ValueError("expected explicit cyj.ndqp.scenario.v6 conditional_diagnostic batch")
    required = {"request_id", "N_params_B", "D_tokens_B", "Q_score", "p", "weights", "bridge_lambda", "eta"}
    optional = {"p_policy", "model_variant"}
    seen, rows = set(), []
    for item in request["requests"]:
        if not isinstance(item, dict) or not required <= set(item) or set(item) - required - optional:
            raise ValueError("incorrect v6 scenario fields")
        identity = item["request_id"]
        if not isinstance(identity, str) or not identity.strip() or identity in seen:
            raise ValueError("empty or duplicate request_id")
        seen.add(identity)
        value = model.evaluate(item["N_params_B"], item["D_tokens_B"], item["Q_score"],
            item["p"], item["weights"], item["bridge_lambda"], item["eta"],
            p_policy=item.get("p_policy", "convex_hull"),
            model_variant=item.get("model_variant", "ridge_main"))
        rows.append({"request_id": identity, **value})
    return {"schema_version": VERSION, "mode": "conditional_diagnostic",
            "ready_for_Q3": False, "scenario_solution_ready": True,
            "empirically_calibrated_A_to_B": False, "results": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--describe", action="store_true")
    group.add_argument("--request", type=Path)
    args = parser.parse_args(argv)
    try:
        model = Q2Final()
        if args.describe:
            result = {"schema_version": VERSION, "mode": "conditional_diagnostic",
                "Q1_export_status": model.manifest["status"],
                "Q1_export_manifest_sha256": hashlib.sha256((model.bundle / "export_manifest.json").read_bytes()).hexdigest(),
                "frozen_Q1_commit": model.manifest["frozen_q1_commit"],
                "Q1_audit_commit": model.manifest["audit_commit"],
                "support": model.v5.support(), "p_policies": ["observed_512", "convex_hull",
                    "quality_direct", "quality_direct_and_near", "algebraic_reference_only"],
                "model_variants": {"ridge_main": "available",
                    "interaction_sensitivity": "not_callable_without_full_Q1_coefficients"},
                "ready_for_Q3": False, "empirically_calibrated_A_to_B": False}
        else:
            request = json.loads(args.request.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_pairs)
            result = batch(model, request)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
