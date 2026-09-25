"""Small fixed-p, QA-derived-Q Q3 cost coupling smoke; not final joint optimization."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from chm_q1_v2_consumer import ROOT
from ndqp_scenarios_v8 import BOUNDS, ConditionalV8

sys.path.insert(0, str(ROOT/"src/chm"))
from q3_generic_solver import cost_and_grad  # noqa: E402

OUT = ROOT / "outputs/cyj/q2_v8/q3_fixed_p_smoke.json"


def main():
    model = ConditionalV8()
    policy = json.loads((ROOT/"outputs/cyj/q2_v8/main_policy.json").read_text(encoding="utf-8"))
    p, weights = policy["p"], policy["weights"]
    q = model.qa(p, "direct_and_near")["Q_B_proxy"]
    budget, context, q0 = 1e22, 8192, .5
    if q < q0:
        raise ValueError("Q3 smoke baseline quality is below declared Q0")
    bounds = [tuple(map(math.log, BOUNDS[0])), tuple(map(math.log, BOUNDS[1]))]
    seeds = [np.array([math.log(n), math.log(d)]) for n, d in
             ((.2, 50), (1, 100), (5, 200), (10, 250))]

    def evaluate(z):
        n, d = map(math.exp, z)
        result = model.predict_baseline_v8(n, d, p, weights, p_policy="quality_direct_and_near")
        return result["Loss"], np.array([n*result["gradients"]["N_B"],
                                          d*result["gradients"]["D_B"]])

    def constraint(z):
        n, d = map(math.exp, z)
        cost, grad = cost_and_grad(n, d, q, q0, context, "power")
        return 1-cost/budget, -np.array([n*grad[0], d*grad[1]])/budget

    trials = []
    for index, seed in enumerate(seeds):
        result = minimize(evaluate, seed, jac=True, method="SLSQP", bounds=bounds,
                          constraints=[{"type": "ineq", "fun": lambda z: constraint(z)[0],
                                        "jac": lambda z: constraint(z)[1]}],
                          options={"ftol": 1e-12, "maxiter": 1000})
        n, d = map(math.exp, result.x)
        cost = cost_and_grad(n, d, q, q0, context, "power")[0]
        value = model.predict_baseline_v8(n, d, p, weights, p_policy="quality_direct_and_near")["Loss"]
        trials.append({"start": index, "solver_success": bool(result.success),
                       "primal_feasible": bool(cost <= budget*(1+1e-8)),
                       "N_params_B": n, "D_tokens_B": d, "Q_B_proxy": q,
                       "Loss": value, "cost_FLOPs": cost, "budget_utilization": cost/budget,
                       "message": str(result.message)})
    valid = [row for row in trials if row["solver_success"] and row["primal_feasible"]]
    if not valid:
        raise ValueError("no feasible fixed-p Q3 smoke result")
    best = min(valid, key=lambda row: row["Loss"])
    output = {"schema_version": "cyj.q3.v8.fixed_p_smoke.v1",
              "status": "local_fixed_p_quality_proxy_cost_smoke_pass",
              "CHM_owner_acceptance": False, "global_joint_Q3_optimum": False,
              "not_empirically_calibrated": True,
              "budget_FLOPs": budget, "context_tokens": context,
              "quality_cost_family": "power", "Q0": q0,
              "p_policy": policy["policy"], "recipe_index": policy["recipe_index"],
              "quality_from_Q1": True, "starts": len(seeds), "solution": best,
              "trials": trials}
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                   encoding="utf-8", newline="\n")
    return {"status": output["status"], "Loss": best["Loss"],
            "N_params_B": best["N_params_B"], "D_tokens_B": best["D_tokens_B"]}


if __name__ == "__main__":
    print(json.dumps(main()))
