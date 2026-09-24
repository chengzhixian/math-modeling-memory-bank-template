"""JSON batch adapter for the pinned B7 diagnostic release; never refits."""
import argparse
import json
import sys
from pathlib import Path

from quality_scaling import QualityPredictor


def predict_batch(payload):
    if not isinstance(payload, dict) or set(payload) != {"expected_sha256", "requests"}:
        raise ValueError("expected exactly expected_sha256 and requests")
    requests = payload["requests"]
    if not isinstance(requests, list) or not requests:
        raise ValueError("requests must be a nonempty list")
    ids = set()
    for request in requests:
        if not isinstance(request, dict) or set(request) != {"request_id", "N_params_B", "D_tokens_B", "Q_score", "mode"}:
            raise ValueError("each request needs exactly request_id, N_params_B, D_tokens_B, Q_score, mode")
        identifier = request["request_id"]
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise ValueError("request_id must be a unique nonempty string")
        ids.add(identifier)
    model = QualityPredictor(expected_sha256=payload["expected_sha256"])
    results = []
    for request in requests:
        args = {k: v for k, v in request.items() if k != "request_id"}
        if any(isinstance(args[k], bool) or not isinstance(args[k], (int, float))
               for k in ("N_params_B", "D_tokens_B", "Q_score")):
            raise ValueError("N,D,Q must be JSON numbers, not strings or booleans")
        results.append({"request_id": request["request_id"], **model.predict(**args)})
    return {"schema_version": "cyj.b7_batch.v1", "results": results,
            "ready_for_Q3": False, "ready_for_Q4": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(args.request.read_text(encoding="utf-8-sig"))
        result = predict_batch(payload)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
