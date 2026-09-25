"""One conditional Q3 integration smoke; not an owner signoff or global optimum."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from ndqp_scenarios_v7 import ConditionalV7, BOUNDS, b7

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/chm"))
from q3_generic_solver import Support, solve_generic  # noqa: E402

OUT = ROOT / "outputs/cyj/q3_v7_sample_smoke.json"


def main():
    producer = ConditionalV7()
    q1 = producer.q1
    p = q1.p_dict(q1.recipes[135])
    weights = {target: 1 / len(q1.targets) for target in q1.targets}
    factor = math.exp(q1.weighted_effect(p, weights))

    class FixedMixture:
        support = Support(*BOUNDS)

        def value_grad(self, n, d, q):
            values = []
            for x, (lo, hi) in zip((n, d, q), BOUNDS):
                if x < lo - 1e-12 * hi or x > hi + 1e-12 * hi:
                    raise ValueError("Q3 solver escaped B7 support")
                values.append(min(hi, max(lo, x)))
            value, grad = b7(*values)
            return factor * value, tuple(factor * g for g in grad)

    solution, trials = solve_generic(FixedMixture(), budget=1e22, context_tokens=8192,
                                     Q0=0.5, family="power", starts=4, seed=20260925)
    predicted = producer.predict_baseline(solution["N_params_B"], solution["D_tokens_B"],
                                          solution["Q"], p, weights, p_policy="observed_512")
    residual = abs(predicted["Loss"] - solution["loss"])
    if not solution["primal_feasible"] or residual > 1e-9:
        raise ValueError("Q3 smoke primal or predictor comparison failed")
    report = {"status": "conditional_integration_smoke_pass", "CHM_owner_acceptance": False,
              "not_empirically_calibrated": True, "budget_FLOPs": 1e22,
              "context_tokens": 8192, "quality_cost_family": "power", "Q0": 0.5,
              "p_policy": "observed_512", "recipe_index": q1.recipe_ids[135],
              "Q1_manifest_sha256": q1.manifest_sha256,
              "starts": len(trials), "prediction_residual": residual,
              "solution": solution}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return {"status": report["status"], "Loss": solution["loss"],
            "prediction_residual": residual, "kkt_check_pass": solution["kkt_check_pass"]}


if __name__ == "__main__":
    print(json.dumps(main()))
