"""Independently recalculate published Q1 v2 scenario feasibility and values."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.optimize import linprog
from q1_interface import Q1Interface
from q1_mixture_decision_v2 import quality_constraints

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/chm/q1_v2_hull_bounds/bounds.json"
OUT = ROOT / "outputs/chm/q1_v2_signoff/audit.json"


def audit():
    q1 = Q1Interface(ROOT)
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert len(rows) == 4
    results = []
    for row in rows:
        assert row["Q1_manifest_sha256"] == q1.manifest_sha256
        p = np.array([row["feasible_composition"][d] for d in q1.domains], float)
        w = np.array([row["weights"][t] for t in q1.targets], float)
        mass_residual = abs(float(p.sum()) - 1)
        nonnegative_residual = max(0., -float(p.min()))
        lp = linprog(np.zeros(len(q1.recipes)),
                     A_eq=np.vstack((q1.recipes.T, np.ones(len(q1.recipes)))),
                     b_eq=np.r_[p, 1.], bounds=(0, None), method="highs")
        hull_residual = float(np.max(abs(lp.eqlin.residual))) if lp.success else None
        feasible, covered, slack = quality_constraints(q1, p[None], row["policy"])
        relative = q1._predict(p[None])[0] / q1.reference_loss - 1
        objective = float(relative @ w if row["mode"] == "weighted" else relative[w > 0].max())
        upper_residual = abs(objective - row["feasible_upper_bound_relative"])
        gap = row["feasible_upper_bound_relative"] - row["lower_bound_relative"]
        passed = bool(
            np.isfinite(p).all() and mass_residual < 1e-10 and nonnegative_residual < 1e-10
            and lp.success and hull_residual < 1e-8 and feasible[0]
            and upper_residual < 1e-8 and 0 <= gap < 0.001
            and abs(gap-row["absolute_gap_relative"]) < 1e-10)
        results.append({
            "policy": row["policy"], "mode": row["mode"], "passed": passed,
            "composition_sum_residual": mass_residual,
            "negative_component_residual": nonnegative_residual,
            "hull_reconstruction_residual": hull_residual,
            "quality_covered_mass": None if row["policy"] == "unconstrained" else float(covered[0]),
            "quality_slack": None if row["policy"] == "unconstrained" else float(slack[0]),
            "recomputed_objective_relative": objective,
            "reported_upper_residual": upper_residual,
            "reported_lower_relative": row["lower_bound_relative"],
            "reported_upper_relative": row["feasible_upper_bound_relative"],
            "numerical_gap_relative": gap,
        })
    output = {
        "schema_version": "chm.q1.signoff_audit.v2",
        "Q1_manifest_sha256": q1.manifest_sha256,
        "bounds_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "all_four_passed": all(r["passed"] for r in results),
        "evidence_role": "A6-A11 compared models and informed selection; not untouched final blind test",
        "certificate_scope": "floating-point LP/McCormick numerical bounds, not interval-arithmetic proof",
        "quality_accuracy_claim": None,
        "scenarios": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not output["all_four_passed"]:
        raise AssertionError("Q1 v2 scenario audit failed")
    return output


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
