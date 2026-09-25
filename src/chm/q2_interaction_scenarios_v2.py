"""CHM-side Q2 conditional rerun with Q1 v2; no edit to CYJ-owned release."""
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np
from q1_interface import Q1Interface
from q1_mixture_decision_v2 import choose
from q2_quality_mapping_recheck import base_loss

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q2_interaction_scenarios_v2"
CYJ = ROOT / "outputs/chm/q2_mapping_sensitivity_v1/cyj_model_coefficients_frozen.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def release():
    q1 = Q1Interface(ROOT)
    frozen = json.loads(CYJ.read_text(encoding="utf-8"))
    if frozen["bridge_status"] != "lambda, eta, weights are engineering assumptions; not jointly estimated":
        raise ValueError("unexpected CYJ bridge status")
    base = base_loss(frozen["theta_B7"], 1.0, 100., .5)
    weights = {t: 1 / len(q1.targets) for t in q1.targets}
    rows = []
    for policy in ("unconstrained", "quality_direct", "quality_direct_and_near"):
        selection = choose(q1, weights, policy)
        m = selection["objective_relative"]
        if 1 + m <= 0:
            raise ValueError("nonpositive B7 scenario factor")
        rows.append({
            "Q1_version": q1.manifest["schema_version"],
            "Q1_manifest_sha256": q1.manifest_sha256,
            "Q2_reference": "cyj.team@86526a1 B7 frozen coefficients",
            "quality_policy": policy,
            "support": "512_observed_A4_recipes",
            "selected_index": selection["selected_index"],
            "mixture": selection["composition"],
            "weights": weights,
            "N_params_B": 1., "D_tokens_B": 100., "Q_B": .5,
            "bridge_lambda": 1., "bridge_eta": 0.,
            "B7_baseline_loss": base, "A_side_relative_mixture_effect": m,
            "conditional_B7_loss": base * (1 + m),
            "unknown_QA_mass": selection["unknown_QA_mass"],
            "quality_covered_mass": selection["quality_covered_mass"],
            "full_mixture_Q_A": selection["full_mixture_Q_A"],
            "A_B_bridge_identified": False,
            "ready_for_Q3_empirical_absolute_loss": False,
            "status": "CHM_RECALCULATION_PENDING_CYJ_REPUBLICATION",
        })
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "conditional_scenarios.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "chm.q2.interaction_scenarios.v2",
        "Q1_version": q1.manifest["schema_version"], "Q1_manifest_sha256": q1.manifest_sha256,
        "CYJ_B7_parameters_sha256": sha(CYJ), "Q1_decision_support": "observed_A4_exact",
        "formula": frozen["formula"], "conditional_scenario_count": len(rows),
        "conditional_scenarios_sha256": sha(OUT / "conditional_scenarios.json"),
        "status": "CHM_RECALCULATION_PENDING_CYJ_REPUBLICATION",
        "ready_for_Q3_empirical_absolute_loss": False,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(release(), ensure_ascii=False, indent=2))
