"""Compare conditional Q3 allocations across B7 quality-model ablations."""
from __future__ import annotations

import csv
import json
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from audit_b_scaling_laws import ROOT, sha256
from fit_b7_joint_nonlinear import OUTPUT as JOINT_OUTPUT, fit_joint, metadata, predict, write_json
from quality_scaling import source_data
from quality_substitution import derivatives
from q3_joint_sweeps import CHM_COMMIT, checked_supported_point, load_chm

OUT = ROOT / "outputs/cyj/q3/q3_form_sensitivity.csv"
FAMILIES = ("no_Q", "constant_G", "Q_x_logN", "Q_x_logD")
BUDGETS = (1e19, 1e20, 1e22, 1e23)
CONTEXTS = (2048, 30000, 131072)
COST_FAMILIES = ("exponential", "power", "logarithmic")
Q0 = 0.5


def save_csv(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def run(starts=20):
    if starts < 2:
        raise ValueError("at least two optimizer starts required")
    source, x, y, _ = source_data()
    main = json.loads(JOINT_OUTPUT.read_text(encoding="utf-8"))
    if source["supplementary_NQ_experiment_expanded.csv"]["sha256"] != main["source_hash"]:
        raise ValueError("B7 source changed")
    base_theta = main["model"]["theta"]
    ablations = {family: fit_joint(x, y, family=family, starts=12, seed=20260925)
                 for family in FAMILIES}
    with (ROOT / "outputs/cyj/q3/q3_budget_sweep.csv").open(encoding="utf-8", newline="") as handle:
        joint_rows = list(csv.DictReader(handle))
    joint = {(float(row["budget_FLOPs"]), int(row["context_tokens"]), row["quality_family"]): row
             for row in joint_rows}
    records = []
    with tempfile.TemporaryDirectory(prefix="cyj_q3_form_") as directory:
        solver, module_hashes = load_chm(Path(directory))
        class Model:
            support = solver.Support((.07, 11.97), (10., 600.), (.1, 1.))

            def __init__(self, theta):
                self.theta = theta

            def value_grad(self, n, d, q):
                value, gradient = derivatives(self.theta, *checked_supported_point((n, d, q)))
                return float(value), tuple(map(float, gradient))

        for family in FAMILIES:
            theta = ablations[family]["theta"]
            model = Model(theta)
            for context in CONTEXTS:
                for cost_family in COST_FAMILIES:
                    for budget in BUDGETS:
                        baseline = joint[(budget, context, cost_family)]
                        record = {"model_family": family, "budget_FLOPs": budget,
                                  "context_tokens": context, "quality_family": cost_family,
                                  "model_train_RMSE": ablations[family]["fit"]["rmse"],
                                  "joint_status": baseline["status"], "candidate_status": None,
                                  "joint_N": baseline["N_params_B"], "joint_D": baseline["D_tokens_B"],
                                  "joint_Q": baseline["Q_score"], "candidate_N": None,
                                  "candidate_D": None, "candidate_Q": None,
                                  "candidate_active_set": None, "candidate_budget_utilization": None,
                                  "candidate_KKT_pass": None, "converged_starts": None,
                                  "joint_loss_at_joint": None, "joint_loss_at_candidate": None,
                                  "candidate_loss_at_candidate": None,
                                  "candidate_loss_at_joint": None,
                                  "joint_model_regret": None, "candidate_model_regret": None}
                        if baseline["status"] != "converged_feasible":
                            record["candidate_status"] = "infeasible_by_supported_domain"
                            records.append(record)
                            continue
                        try:
                            solution, trials = solver.solve_generic(
                                model, budget=budget, context_tokens=context, Q0=Q0,
                                family=cost_family, starts=starts)
                        except (RuntimeError, ValueError) as exc:
                            record["candidate_status"] = f"solver_failure:{exc}"
                            records.append(record)
                            continue
                        alt_point = checked_supported_point((solution["N_params_B"],
                                                         solution["D_tokens_B"], solution["Q"]))
                        joint_point = checked_supported_point(tuple(float(baseline[name]) for name in
                                                                  ("N_params_B", "D_tokens_B", "Q_score")))
                        a = float(predict(base_theta, np.array([joint_point]))[0])
                        b = float(predict(base_theta, np.array([alt_point]))[0])
                        c = float(predict(theta, np.array([alt_point]))[0])
                        d = float(predict(theta, np.array([joint_point]))[0])
                        record.update(candidate_status="converged_feasible",
                                      candidate_N=alt_point[0], candidate_D=alt_point[1],
                                      candidate_Q=alt_point[2],
                                      candidate_active_set=";".join(solution["active_set"]),
                                      candidate_budget_utilization=solution["budget_utilization"],
                                      candidate_KKT_pass=solution["kkt_check_pass"],
                                      converged_starts=sum(t["success"] and t["feasible"] for t in trials),
                                      joint_loss_at_joint=a, joint_loss_at_candidate=b,
                                      candidate_loss_at_candidate=c, candidate_loss_at_joint=d,
                                      joint_model_regret=b-a, candidate_model_regret=d-c)
                        records.append(record)
                print(f"{family} context {context}", flush=True)
    save_csv(OUT, records)
    summary = {**metadata(), "schema_version": "cyj.q3_form_sensitivity.v1",
               "model_hash": sha256(JOINT_OUTPUT), "CHM_commit": CHM_COMMIT,
               "CHM_module_sha256": module_hashes, "Q0_scenario": Q0,
               "budgets": BUDGETS, "contexts": CONTEXTS, "cost_families": COST_FAMILIES,
               "optimizer_starts": starts, "seed": 20260925,
               "ablations": {family: {"theta": fit["theta"], "train_RMSE": fit["fit"]["rmse"],
                                       "successful_starts": fit["successful_starts"],
                                       "corner_quality_gain": fit["corner_quality_gain"]}
                             for family, fit in ablations.items()},
               "rows": len(records), "status_counts": dict(Counter(
                   record["candidate_status"] for record in records)),
               "negative_regret_tolerance": 1e-5,
               "csv_sha256": sha256(OUT),
               "limitation": "B7 semi-synthetic model-form ablation; all families explored on source before this test; not an independent external validation"}
    regrets = [record for record in records if record["candidate_status"] == "converged_feasible"]
    summary["max_joint_model_regret"] = max(record["joint_model_regret"] for record in regrets)
    summary["min_joint_model_regret"] = min(record["joint_model_regret"] for record in regrets)
    summary["max_candidate_model_regret"] = max(record["candidate_model_regret"] for record in regrets)
    summary["min_candidate_model_regret"] = min(record["candidate_model_regret"] for record in regrets)
    write_json(OUT.with_suffix(".json"), summary)
    print(json.dumps({"rows": len(records), "statuses": summary["status_counts"],
                      "regret_extrema": {k: summary[k] for k in
                                         ("min_joint_model_regret", "max_joint_model_regret",
                                          "min_candidate_model_regret", "max_candidate_model_regret")}}))


if __name__ == "__main__":
    run()
