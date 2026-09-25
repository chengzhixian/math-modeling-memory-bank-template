"""CYJ numerical hull bounds for two one-target policies absent from CHM release."""
from __future__ import annotations

import json
import sys

from chm_q1_v2_consumer import Q1V2Consumer, ROOT, sha256

sys.path.insert(0, str(ROOT / "src/chm"))
from q1_hull_bounds_v2 import certify  # noqa: E402

OUT = ROOT / "outputs/cyj/q2_v7/single_target_hull_bounds.json"


def main():
    q1 = Q1V2Consumer()
    rows = []
    for target in ("arxiv", "pile_cc"):
        weights = {key: float(key == target) for key in q1.targets}
        row = certify(q1.upstream, "unconstrained", weights, "weighted",
                      max_nodes=600, tolerance=0.001)
        support = q1.support(row["feasible_composition"], "convex_hull")
        actual = q1.relative_effect(row["feasible_composition"], target)
        if (not support["in_A4_hull"] or abs(actual-row["feasible_upper_bound_relative"]) > 1e-8
                or row["absolute_gap_relative"] > 0.001):
            raise ValueError(f"single-target bound audit failed: {target}")
        row["CYJ_policy_name"] = f"{target}_only"
        row["CYJ_independent_upper_recalculation"] = actual
        row["producer_scope"] = "CYJ_single_target_numerical_extension_not_CHM_owner_signed"
        rows.append(row)
    result = {"schema_version": "cyj.q1_v2.single_target_hull_bounds.v1",
              "Q1_manifest_sha256": q1.manifest_sha256,
              "CHM_bound_solver_code_sha256": sha256(ROOT / "src/chm/q1_hull_bounds_v2.py"),
              "method": "McCormick_LP_spatial_branch_and_bound_600_node_limit",
              "seed": None, "tolerance_relative": 0.001,
              "global_optimality": "numerical_gap_not_interval_arithmetic_proof",
              "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"policies": len(rows), "sha256": sha256(OUT)}


if __name__ == "__main__":
    print(json.dumps(main()))
