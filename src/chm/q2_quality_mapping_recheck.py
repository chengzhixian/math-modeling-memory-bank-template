"""Owner-side conditional Q2 QA-policy recheck using corrected Q1 sample scores.

Recreates CYJ v6's two quality-constrained Ridge LPs at its declared main
engineering point. This does not edit CYJ's branch or identify an A/B bridge.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q2_mapping_sensitivity_v1"
Q1 = ROOT / "outputs/chm/q1_exports/q1_q2_bundle_v1"
CORRECTED = ROOT / "outputs/chm/q1_third_part_review/qa_mapping_primary_candidate.json"
MODEL = OUT / "cyj_model_coefficients_frozen.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def base_loss(theta: list[float], n: float, d: float, q: float) -> float:
    e, a, b, alpha, beta, g0, gn, gd = theta
    return e + a * n ** (-alpha) + b * d ** (-beta) + (1 - q) * (g0 + gn * math.log(n) + gd * math.log(d / 100))


def run() -> dict:
    frozen = json.loads(MODEL.read_text(encoding="utf-8"))
    qa_old = json.loads((Q1 / "qa_mapping.json").read_text(encoding="utf-8"))
    qa_new = json.loads(CORRECTED.read_text(encoding="utf-8"))
    assert qa_new["status"] == "USER_REVIEW_REQUIRED_NOT_FORMAL_INTERFACE"
    domains = [r["mixture_domain"] for r in read_csv(Q1 / "reference.csv")]
    recipe = read_csv(Q1 / "recipes_512.csv")
    x = np.array([[float(r[d]) for d in domains] for r in recipe])
    ref = np.array([frozen["Q1_reference_p"][d] for d in domains])
    targets = list(frozen["Q1_fitted_positive_reference_loss_by_target"])
    beta = np.array([[frozen["Q1_ridge_beta_by_target"][k][d] for d in domains] for k in targets])
    denom = np.array([frozen["Q1_fitted_positive_reference_loss_by_target"][k] for k in targets])
    assert np.all(denom > 0) and np.max(np.abs(x.sum(axis=1) - 1)) < 1e-12
    exported = {r["target"]: r for r in read_csv(Q1 / "coefficients.csv")}
    for j, target in enumerate(targets):
        fitted_ref = float(exported[target]["intercept"]) + float(ref @ beta[j])
        assert abs(fitted_ref - denom[j]) < 1e-10
    effect = (x - ref) @ (beta / denom[:, None]).T
    weighted = effect.mean(axis=1)
    theta = frozen["theta_B7"]
    baseline = base_loss(theta, 1.0, 100.0, 0.5)
    results = []
    mixtures = []
    for name, mapping in (("CYJ_v1_extended", qa_old), ("CHM_v2_candidate_A1_sample", qa_new)):
        qa = {r["mixture_domain"]: r for r in mapping["rows"]}
        assert set(qa) == set(domains)
        for policy, allowed in (("quality_direct", {"direct"}),
                                ("quality_direct_and_near", {"direct", "near_direct"})):
            mask = np.array([qa[d]["mapping_type"] in allowed and qa[d]["Q_A"] is not None for d in domains], float)
            qvals = np.array([float(qa[d]["Q_A"]) if qa[d]["Q_A"] is not None else 0 for d in domains])
            covered_ref = float(ref @ mask)
            quality_ref = float(ref @ (mask * qvals) / covered_ref)
            quality_a = np.vstack([-(x @ mask), -(x @ (mask * (qvals - quality_ref)))])
            quality_b = np.array([-covered_ref, 0.0])
            # Match CYJ's full-B7-N positivity guard for lambda=1, eta=0.
            positive_a = np.vstack([-weighted, -weighted])
            positive_b = np.array([1 - 1e-9, 1 - 1e-9])
            sol = linprog(weighted, A_ub=np.vstack([positive_a, quality_a]),
                          b_ub=np.r_[positive_b, quality_b],
                          A_eq=np.ones((1, len(x))), b_eq=np.ones(1),
                          bounds=(0, None), method="highs")
            assert sol.success, sol.message
            p = sol.x @ x
            coverage = float(p @ mask)
            mean_quality = float(p @ (mask * qvals) / coverage)
            relative = float(weighted @ sol.x)
            factor = 1 + relative
            assert factor > 0 and coverage >= covered_ref - 1e-9 and mean_quality >= quality_ref - 1e-9
            rows = [{"index": recipe[i]["index"], "weight": float(w)} for i, w in enumerate(sol.x) if w > 1e-8]
            results.append({"quality_mapping_version": name, "policy": policy,
                            "N_params_B": 1.0, "D_tokens_B": 100.0, "Q_B": 0.5,
                            "bridge_lambda": 1.0, "eta": 0.0, "weights": "equal_13",
                            "B7_baseline_loss": baseline, "weighted_relative_A_effect": relative,
                            "factor": factor, "conditional_loss": baseline * factor,
                            "reference_covered_mass": covered_ref, "chosen_covered_mass": coverage,
                            "reference_mean_Q_A_on_covered": quality_ref,
                            "chosen_mean_Q_A_on_covered": mean_quality,
                            "active_A4_vertices_json": json.dumps(rows, separators=(",", ":")),
                            "feasibility_max_violation": float(max(0.0, np.max(np.vstack([positive_a, quality_a]) @ sol.x - np.r_[positive_b, quality_b]))),
                            "ready_for_Q3": False})
            mixtures.append({"quality_mapping_version": name, "policy": policy,
                             **dict(zip(domains, map(float, p)))})
    old = {r["policy"]: r for r in results if r["quality_mapping_version"] == "CYJ_v1_extended"}
    assert abs(old["quality_direct"]["conditional_loss"] - 2.263949598559698) < 1e-9
    assert abs(old["quality_direct_and_near"]["conditional_loss"] - 2.2749885718994807) < 1e-9
    OUT.mkdir(parents=True, exist_ok=True)
    for path, data in ((OUT / "conditional_policy_comparison.csv", results),
                       (OUT / "conditional_policy_mixtures.csv", mixtures)):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(data)
    deltas = {}
    for policy in ("quality_direct", "quality_direct_and_near"):
        a = old[policy]
        b = next(r for r in results if r["quality_mapping_version"] == "CHM_v2_candidate_A1_sample" and r["policy"] == policy)
        pa = next(r for r in mixtures if r["quality_mapping_version"] == "CYJ_v1_extended" and r["policy"] == policy)
        pb = next(r for r in mixtures if r["quality_mapping_version"] == "CHM_v2_candidate_A1_sample" and r["policy"] == policy)
        deltas[policy] = {"conditional_loss_sample_minus_extended": b["conditional_loss"] - a["conditional_loss"],
                          "mixture_l1_distance": sum(abs(pb[d] - pa[d]) for d in domains),
                          "same_active_vertex_set": {v["index"] for v in json.loads(a["active_A4_vertices_json"])} ==
                                                    {v["index"] for v in json.loads(b["active_A4_vertices_json"])}}
    manifest = {"schema_version": "chm.q2.qa_mapping_recheck.v1",
                "status": "conditional_owner_side_recalculation_not_CYJ_release",
                "source_cyj_branch_commit": "86526a17d698e5fcc585f3099248bfa5a4ad28d8",
                "Q1_producer": "chm.q1.v1.3 Ridge unchanged",
                "Q1_quality_mapping_candidate": qa_new["schema_version"],
                "scientific_limit": "lambda/eta and A/B quality coordinate remain unidentified; values are engineering scenarios",
                "old_CYJ_main_policy_reproduction": "both old conditional losses match published v6 within 1e-9",
                "deltas": deltas,
                "source_sha256": {"cyj_frozen_model_coefficients": sha(MODEL),
                                  "Q1_bundle": sha(Q1 / "export_manifest.json"),
                                  "Q1_mapping_candidate": sha(CORRECTED)},
                "comparison_sha256": sha(OUT / "conditional_policy_comparison.csv"),
                "mixtures_sha256": sha(OUT / "conditional_policy_mixtures.csv")}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
