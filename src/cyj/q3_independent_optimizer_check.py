"""Derivative-free, dimension-reduced Q3 cross-check of the pinned CHM grid."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import NonlinearConstraint, differential_evolution

from audit_b_scaling_laws import ROOT, sha256
from fit_b7_joint_nonlinear import OUTPUT as MODEL_OUTPUT, metadata, write_json
from q3_costs import quality_cost

OUTPUT = ROOT / "outputs/cyj/q3/q3_independent_optimizer_check.csv"
BUDGETS = (1e19, 1e20, 1e22, 1e23)
CONTEXTS = (2048, 30000, 131072)
FAMILIES = ("exponential", "power", "logarithmic")
Q0 = .5
SEED = 20260925


def native_loss(theta, n, d, q):
    E, A, B, alpha, beta, G0, GN, GD = theta
    return (E + A * n ** (-alpha) + B * d ** (-beta) +
            (1 - q) * (G0 + GN * math.log(n) + GD * math.log(d / 100)))


def run():
    model = json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))
    theta = model["model"]["theta"]
    manifest = json.loads((ROOT / "outputs/cyj/q3/q3_sweep_manifest.json").read_text(encoding="utf-8"))
    if manifest["model_hash"] != sha256(MODEL_OUTPUT):
        raise ValueError("Q3 model identity mismatch")
    baseline_path = ROOT / "outputs/cyj/q3/q3_budget_sweep.csv"
    if manifest["budget_sweep_sha256"] != sha256(baseline_path):
        raise ValueError("Q3 grid identity mismatch")
    with baseline_path.open(encoding="utf-8", newline="") as handle:
        baseline = {(float(row["budget_FLOPs"]), int(row["context_tokens"]), row["quality_family"]): row
                    for row in csv.DictReader(handle)}
    output = []
    for context in CONTEXTS:
        a = 6e18 + 2e14 * context
        for family in FAMILIES:
            g0 = quality_cost(Q0, family)[0]
            for budget in BUDGETS:
                previous = baseline[(budget, context, family)]
                record = {"budget_FLOPs": budget, "context_tokens": context,
                          "quality_family": family, "joint_grid_status": previous["status"],
                          "independent_status": None, "N_params_B": None, "D_tokens_B": None,
                          "Q_score": None, "loss": None, "cost_FLOPs": None,
                          "budget_utilization": None, "support_feasible": None,
                          "solver_success": None, "solver_message": None,
                          "iterations": None, "function_evaluations": None,
                          "CHM_loss": previous["conditional_loss"],
                          "independent_minus_CHM_loss": None}
                minimum = 10 * a * .07
                if budget < minimum * (1 - 1e-12):
                    if previous["status"] != "infeasible_by_supported_domain":
                        raise ValueError("independent support infeasibility disagrees with CHM")
                    record["independent_status"] = "infeasible_by_supported_domain"
                    output.append(record)
                    continue
                if previous["status"] != "converged_feasible":
                    raise ValueError("CHM did not solve independently feasible point")
                upper_n = min(11.97, budget / (10 * a))
                def increment(q):
                    q = float(q)
                    if not math.isfinite(q) or q < Q0 - 1e-6 or q > 1. + 1e-6:
                        raise ValueError("optimizer quality probe outside bounded neighborhood")
                    # trust-constr's finite-difference polish may probe just past a bound.
                    q = min(1., max(Q0, q))
                    return max(0., quality_cost(q, family)[0] - g0)
                def d_from_budget(n, q):
                    return min(600., budget / (a * n + 1e9 * increment(q)))
                def objective(vector):
                    n, q = map(float, vector)
                    d = d_from_budget(n, q)
                    if d < 10.:
                        return 1e6 + 1e6 * (10. - d)
                    return native_loss(theta, n, d, q)
                constraint = NonlinearConstraint(
                    lambda vector: budget - 10 * (a * float(vector[0]) +
                                                   1e9 * increment(vector[1])),
                    0., np.inf)
                result = differential_evolution(objective, ((.07, upper_n), (Q0, 1.)),
                                                constraints=(constraint,), seed=SEED,
                                                popsize=12, maxiter=150, tol=1e-8,
                                                polish=False, updating="immediate")
                n, q = map(float, result.x)
                d = d_from_budget(n, q)
                cost = d * (a * n + 1e9 * increment(q))
                feasible = (.07 - 1e-9 <= n <= 11.97 + 1e-9 and
                            10. - 1e-7 <= d <= 600. + 1e-7 and
                            Q0 - 1e-9 <= q <= 1. + 1e-9 and
                            cost <= budget * (1 + 1e-7))
                loss = native_loss(theta, n, d, q) if feasible else None
                record.update(independent_status="feasible" if feasible else "solver_infeasible",
                              N_params_B=n, D_tokens_B=d, Q_score=q, loss=loss,
                              cost_FLOPs=cost, budget_utilization=cost / budget,
                              support_feasible=feasible, solver_success=bool(result.success),
                              solver_message=str(result.message), iterations=int(result.nit),
                              function_evaluations=int(result.nfev),
                              independent_minus_CHM_loss=(None if loss is None else
                                                          loss - float(previous["conditional_loss"])))
                output.append(record)
                print(f"{context} {family} {budget:.0e}: {record['independent_status']}", flush=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    gaps = [row["independent_minus_CHM_loss"] for row in output if row["independent_status"] == "feasible"]
    report = {**metadata(), "schema_version": "cyj.q3_independent_optimizer_check.v1",
              "model_hash": sha256(MODEL_OUTPUT), "baseline_csv_hash": sha256(baseline_path),
              "result_csv_hash": sha256(OUTPUT), "seed": SEED,
              "method": "independent derivative-free differential_evolution in N,Q; D eliminated analytically",
              "popsize": 12, "maxiter": 150, "tol": 1e-8, "polish": False,
              "protocol_deviation": "SciPy trust-constr polish probed outside Q bounds and raised; disabled local polish before completed run",
              "budgets": BUDGETS, "contexts": CONTEXTS, "quality_families": FAMILIES,
              "rows": len(output), "feasible_rows": len(gaps),
              "min_independent_minus_CHM_loss": min(gaps),
              "max_independent_minus_CHM_loss": max(gaps),
              "num_CHM_beaten_by_more_than_1e_minus_4": sum(g < -1e-4 for g in gaps),
              "limitation": "Independent heuristic cross-check; numerical agreement is not a global-optimality or real-training guarantee"}
    write_json(OUTPUT.with_suffix(".json"), report)
    print(json.dumps({"rows": len(output), "feasible": len(gaps),
                      "min_gap": min(gaps), "max_gap": max(gaps),
                      "large_improvements": report["num_CHM_beaten_by_more_than_1e_minus_4"]}))


if __name__ == "__main__":
    run()
