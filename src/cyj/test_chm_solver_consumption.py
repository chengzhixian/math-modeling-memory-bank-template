"""Exercise CHM's exact generic solver with the frozen CYJ B7 candidate.

This is an integration diagnostic, not CHM owner acceptance or a Q3 result.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from audit_b_scaling_laws import ROOT, sha256
from b7_formal_model import OUTPUT as MODEL_OUTPUT
from chm_adapter_v3 import CHMAdapterV3

CHM_COMMIT = "92e0592000cba58fca355a881dc59caadbd446b2"
CHM_MODULES = ("q3_generic_solver.py", "q3_quality_cost_geometry.py", "q3_nd_baseline.py")
OUTPUT = ROOT / "outputs/cyj/interfaces/chm_solver_consumption_b7_candidate.json"


def run(*, scipy_path: Path | None = None, starts: int = 36) -> dict:
    if scipy_path is not None:
        sys.path.insert(0, str(scipy_path.resolve()))
    import scipy

    frozen = json.loads(MODEL_OUTPUT.read_text(encoding="utf-8"))
    if frozen["ready_for_Q3"] or frozen["family"] != "Q_x_logN_logD":
        raise ValueError("unexpected candidate status or family")
    with tempfile.TemporaryDirectory(prefix="cyj_chm_exact_") as temporary:
        directory = Path(temporary)
        provenance = {}
        for name in CHM_MODULES:
            blob = subprocess.check_output(
                ["git", "show", f"{CHM_COMMIT}:src/chm/{name}"], cwd=ROOT)
            (directory / name).write_bytes(blob)
            provenance[name] = hashlib.sha256(blob).hexdigest()
        sys.path.insert(0, str(directory))
        from q3_generic_solver import Support, cost_and_grad, solve_generic

        class CYJForCHM:
            def __init__(self):
                self.upstream = CHMAdapterV3(mode="conditional_diagnostic")
                self.bounds = self.upstream.bounds
                n, d, q = self.bounds
                self.support = Support(N=tuple(n), D=tuple(d), Q=tuple(q))

            def value_grad(self, N_B: float, D_B: float, Q: float):
                # SLSQP's exp(log(upper bound)) can differ by a few ulps.
                point = (N_B, D_B, Q)
                adjusted = []
                for value, (lo, hi) in zip(point, self.bounds):
                    if value < lo - 1e-12 * hi or value > hi + 1e-12 * hi:
                        raise ValueError("solver requested value outside B7 support")
                    adjusted.append(min(hi, max(lo, value)))
                return self.upstream.value_grad(*adjusted)

        model = CYJForCHM()
        rows = []
        for budget, context, family in itertools.product(
            (1e19, 1e22, 1e24), (2048, 8192, 131072),
            ("exponential", "power", "logarithmic")
        ):
            minimum_cost = cost_and_grad(.07, 10., .5, .5, context, family)[0]
            case = {"budget_FLOPs": budget, "context_tokens": context,
                    "Q0": .5, "quality_family": family,
                    "minimum_supported_cost_FLOPs": minimum_cost}
            if minimum_cost > budget * (1 + 1e-12):
                try:
                    solve_generic(model, budget=budget, context_tokens=context,
                                  Q0=.5, family=family, starts=starts)
                except ValueError as exc:
                    if str(exc) != "budget below minimum supported cost":
                        raise
                    rows.append({**case, "status": "infeasible_by_supported_domain",
                                 "expected_failure": str(exc)})
                    continue
                raise AssertionError("unsupported budget unexpectedly solved")
            solution, trials = solve_generic(
                model, budget=budget, context_tokens=context,
                Q0=.5, family=family, starts=starts)
            diagnostic_keys = ("loss", "cost_FLOPs", "budget_utilization",
                               "kkt_mu_estimate", "kkt_relative_violation",
                               "complementarity_relative_residual")
            if not solution["primal_feasible"] or not all(
                math.isfinite(solution[key]) for key in diagnostic_keys
            ):
                raise AssertionError("solver result violates primal or finite KKT check")
            rows.append({**case, "status": "converged_feasible",
                         "solution": solution,
                         "starts": len(trials),
                         "converged_feasible_starts": sum(
                             r["success"] and r["feasible"] for r in trials)})
    result = {"schema_version": "cyj.chm_solver_consumption_candidate.v1",
              "scientific_status": "software_integration_only_not_formal_Q3",
              "chm_exact_commit": CHM_COMMIT,
              "chm_module_sha256": provenance,
              "cyj_frozen_model_sha256": sha256(MODEL_OUTPUT),
              "scipy_version": scipy.__version__, "starts_per_feasible_case": starts,
              "support": frozen["support"], "results": rows,
              "ready_for_Q3": False,
              "chm_owner_acceptance": False}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scipy-path", type=Path)
    parser.add_argument("--starts", type=int, default=36)
    args = parser.parse_args()
    result = run(scipy_path=args.scipy_path, starts=args.starts)
    print(json.dumps({"output_sha256": sha256(OUTPUT),
                      "cases": len(result["results"]),
                      "statuses": {status: sum(row["status"] == status for row in result["results"])
                                   for status in {r["status"] for r in result["results"]}}}))
