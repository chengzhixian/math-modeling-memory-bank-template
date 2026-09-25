"""Re-run current CHM numerical bounds without writing to CHM-owned paths."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from chm_q1_v2_consumer import Q1V2Consumer, ROOT, EXPECTED_BOUNDS_SHA, sha256

sys.path.insert(0, str(ROOT / "src/chm"))
from q1_hull_bounds_v2 import certify  # noqa: E402

OUT = ROOT / "outputs/cyj/q2_v7/upstream_bounds_revalidation.json"
SIGNOFF = ROOT / "outputs/chm/q1_v2_signoff/audit.json"


def main():
    consumer = Q1V2Consumer(ROOT)
    signed = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    current_sha = sha256(consumer.bounds_path)
    if current_sha != EXPECTED_BOUNDS_SHA:
        raise ValueError("current bounds differ from CYJ pin")
    rows = []
    for published in consumer.bounds:
        reproduced = certify(consumer.upstream, published["policy"], published["weights"],
                             published["mode"], max_nodes=600, tolerance=0.001)
        comparison = {}
        for field in ("lower_bound_relative", "feasible_upper_bound_relative",
                      "absolute_gap_relative", "best_observed_A4_objective_relative"):
            error = abs(reproduced[field] - published[field])
            comparison[field] = error
            if error > 1e-8:
                raise ValueError(f"current Q1 bound reproduction mismatch: {published['policy']} {field}")
        p = reproduced["feasible_composition"]
        policy = ("convex_hull" if published["policy"] == "unconstrained"
                  else published["policy"])
        support = consumer.support(p, policy)
        if not support["in_A4_hull"]:
            raise ValueError("reproduced Q1 candidate outside A4 hull")
        rows.append({"policy": published["policy"], "mode": published["mode"],
                     "published_and_reproduced_gap": published["absolute_gap_relative"],
                     "numeric_fields_absolute_errors": comparison,
                     "nodes_reproduced": reproduced["nodes_solved"],
                     "candidate_feasible": True})
    result = {"schema_version": "cyj.q1_v2.bounds_revalidation.v1",
              "Q1_manifest_sha256": consumer.manifest_sha256,
              "current_bounds_sha256": current_sha,
              "CHM_signoff_audit_bounds_sha256": signed["bounds_sha256"],
              "CHM_signoff_hash_matches_current_bounds": signed["bounds_sha256"] == current_sha,
              "stale_signoff_note": "CHM audit signs earlier bytes; CYJ regenerated current numerical bounds",
              "method": "rerun_CHM_McCormick_branch_and_bound_plus_CYJ_support_check",
              "scope": "floating_point_numerical_reproduction_not_interval_arithmetic_proof_or_CHM_owner_signoff",
              "all_four_reproduced": len(rows) == 4,
              "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
