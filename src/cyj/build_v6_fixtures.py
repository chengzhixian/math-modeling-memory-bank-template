"""Publish fixed v6 consumer examples from hash-checked Q1 outputs."""
import json
from pathlib import Path

from ndqp_scenarios_v6 import batch
from q2_final_core import Q2Final, VERSION
from joint_ndqp_scenarios import ROOT


def dump(path, obj):
    path.write_bytes((json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())


def main():
    folder = ROOT / "interfaces/cyj/fixtures_v6"
    folder.mkdir(parents=True, exist_ok=True)
    model = Q2Final()
    weight = model.weight_policy("equal_13")
    reference = model.p_dict(model.reference)
    optimum = model.optimize("convex_hull")["p"]
    invalid_p = {domain: float(domain == "arxiv") for domain in model.domains}
    cases = {
        "reference_lambda_zero": (1, 100, .5, reference, 0, "convex_hull"),
        "main_supported_optimum": (1, 100, .5, optimum, 1, "convex_hull"),
        "invalid_N": (1000, 100, .5, optimum, 1, "convex_hull"),
        "invalid_p": (1, 100, .5, invalid_p, 1, "convex_hull"),
    }
    for name, (n, d, q, p, lam, policy) in cases.items():
        req = {"schema_version": VERSION, "mode": "conditional_diagnostic", "requests": [
            {"request_id": name, "N_params_B": n, "D_tokens_B": d, "Q_score": q,
             "p": p, "weights": weight, "bridge_lambda": lam, "eta": 0,
             "p_policy": policy, "model_variant": "ridge_main"}]}
        dump(folder / f"{name}.request.json", req)
        try:
            expected = {"exit_code": 0, "output": batch(model, req)}
        except ValueError as exc:
            expected = {"exit_code": 2, "error": str(exc)}
        dump(folder / f"{name}.expected.json", expected)
    print(f"wrote {len(cases)} fixed v6 consumer fixtures")


if __name__ == "__main__":
    main()
