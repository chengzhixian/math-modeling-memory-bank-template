"""Q1 mixture decision review on the 512 observed A4 recipes.

The frozen v1.3 Ridge remains the primary model. The re-created interaction
model is a sensitivity candidate and is never sent to Q2/Q3 by this script.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from audit_cyj_q1_exports import check as audit_exports
from q1_interface import Q1Interface

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/chm/q1_exports"
OUT = ROOT / "outputs/chm/q1_third_part_review"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def run() -> dict:
    upstream = audit_exports()
    q1 = Q1Interface(ROOT)
    recipe = rows(BASE / "q1_q2_bundle_v1/recipes_512.csv")
    domains = list(q1.reference)
    targets = list(q1.coefficients)
    p = np.array([[float(r[d]) for d in domains] for r in recipe])
    pref = np.array([q1.reference[d] for d in domains])
    assert np.max(np.abs(p.sum(axis=1) - 1)) < 1e-12
    ridge_beta = np.array([[float(q1.coefficients[k][d]) for d in domains] for k in targets])
    ridge = (p - pref) @ ridge_beta.T
    candidate = json.loads((BASE / "q1_interaction_bundle_v1/interaction_coefficients_13_targets.json").read_text(encoding="utf-8"))["targets"]
    interaction = np.zeros_like(ridge)
    for j, target in enumerate(targets):
        m = candidate[target]
        main = np.array([m["main"][d] for d in domains])
        interaction[:, j] = (p - pref) @ main
        for pair in m["pairs"]:
            a, b = pair["domains"]
            ia, ib = domains.index(a), domains.index(b)
            interaction[:, j] += pair["gamma"] * (p[:, ia] * p[:, ib] - pref[ia] * pref[ib])
    frozen_rows = {r["target"]: r for r in rows(BASE / "q1_q2_bundle_v1/coefficients.csv")}
    reference_loss = np.array([float(frozen_rows[k]["intercept"]) + float(pref @ ridge_beta[j])
                               for j, k in enumerate(targets)])
    assert np.all(reference_loss > 0)
    ridge_rel = ridge / reference_loss
    interaction_rel = interaction / reference_loss
    policies = {
        "equal_13_relative": lambda arr: arr.mean(axis=1),
        "minimax_13_relative": lambda arr: arr.max(axis=1),
        "arxiv_only_relative": lambda arr: arr[:, targets.index("arxiv")],
    }
    mapped = q1.mapping_rows
    known = [d for d in domains if mapped[d]["mapping_type"] != "inferred"]
    direct = [d for d in domains if mapped[d]["mapping_type"] == "direct"]
    unknown = [d for d in domains if mapped[d]["mapping_type"] == "inferred"]
    decisions = []
    for name, objective in policies.items():
        for model_name, matrix in (("ridge_v1.3", ridge_rel), ("interaction_candidate", interaction_rel)):
            scores = objective(matrix)
            best = int(np.argmin(scores))
            row = {"policy": name, "model": model_name, "recipe_index": recipe[best]["index"],
                   "objective_relative": float(scores[best]),
                   "known_QA_share": float(sum(p[best, domains.index(d)] for d in known)),
                   "direct_QA_share": float(sum(p[best, domains.index(d)] for d in direct)),
                   "unknown_QA_share": float(sum(p[best, domains.index(d)] for d in unknown)),
                   "max_domain_share": float(p[best].max())}
            decisions.append(row)
    # Re-evaluate the two Q_A policies under the v1.3 primary sample score and
    # the CYJ export's explicitly named extended-sample sensitivity score.
    exported_qa = {r["mixture_domain"]: r for r in json.loads((BASE / "q1_q2_bundle_v1/qa_mapping.json").read_text(encoding="utf-8"))["rows"]}
    primary_qa = []
    for d in domains:
        original = exported_qa[d]
        row = dict(original)
        if d in known:
            row["Q_A"] = float(q1.quality(mapped[d]["quality_domain"])["Q_A_median"])
            row["Q_A_dataset_scope"] = "sample"
            row["Q_A_extended_sensitivity"] = (original["Q_A"]
                                                 if original["Q_A_dataset_scope"] != "sample" else None)
        else:
            row["Q_A"] = None
            row["Q_A_dataset_scope"] = None
            row["Q_A_extended_sensitivity"] = None
        primary_qa.append(row)
    qa_candidate = {"schema_version": "chm.q1.q2_quality_policy.candidate.v2",
                    "status": "USER_REVIEW_REQUIRED_NOT_FORMAL_INTERFACE",
                    "source_q1_version": "chm.q1.v1.3",
                    "source_q1_commit": "cdda1ad62c5c7eb72b413c4228caeff87d2bad30",
                    "quality_primary_scope": "A1_sample",
                    "quality_extended_scope": "arxiv_A2_and_github_A3_sensitivity_only",
                    "B_Q_mapping": "unidentified",
                    "rows": primary_qa}
    (OUT / "qa_mapping_primary_candidate.json").write_text(json.dumps(qa_candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    qa_policy_sensitivity = []
    for score_scope in ("v1.3_primary_sample", "cyj_export_extended_where_available"):
        qvals = np.array([float(q1.quality(mapped[d]["quality_domain"])["Q_A_median"])
                          if score_scope == "v1.3_primary_sample" and d in known else
                          float(exported_qa[d]["Q_A"]) if d in known else 0.0 for d in domains])
        for label, allowed in (("direct", direct), ("direct_and_near", known)):
            mask = np.array([d in allowed for d in domains], float)
            covered_ref = float(pref @ mask)
            mean_ref = float(pref @ (mask * qvals) / covered_ref)
            constraints = np.vstack([-(p @ mask), -(p @ (mask * (qvals - mean_ref)))])
            bounds = np.array([-covered_ref, 0.0])
            sol = linprog(ridge_rel.mean(axis=1), A_ub=constraints, b_ub=bounds,
                          A_eq=np.ones((1, len(recipe))), b_eq=[1.0],
                          bounds=(0, None), method="highs")
            assert sol.success
            composition = sol.x @ p
            qa_policy_sensitivity.append({"score_scope": score_scope, "policy": label,
                                          "objective_relative": float(sol.fun),
                                          "covered_mass": float(composition @ mask),
                                          "mean_Q_A_on_covered": float(composition @ (mask * qvals) / (composition @ mask)),
                                          "active_A4_recipes": [{"index": recipe[i]["index"], "weight": float(w)}
                                                               for i, w in enumerate(sol.x) if w > 1e-8]})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "observed_recipe_policies.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)
    comparisons = rows(ROOT / "outputs/chm/q1_mixture_final/interaction_candidate_comparison.csv")
    metrics = rows(ROOT / "outputs/chm/q1_mixture_final/heldout_target_metrics.csv")
    counts = {}
    for scope in ("test_1m", "test_60m", "test_1B"):
        sub = [r for r in comparisons if r["scope"] == scope]
        base = {r["target"]: float(r["constant_rmse"]) for r in metrics if r["scope"] == scope}
        assert len(sub) == len(base) == 13
        counts[scope] = {"candidate_better_than_ridge_rmse": sum(float(r["candidate_rmse"]) < float(r["ridge_rmse"]) for r in sub),
                         "candidate_better_than_constant_rmse": sum(float(r["candidate_rmse"]) < base[r["target"]] for r in sub),
                         "ridge_better_than_constant_rmse": sum(float(r["ridge_rmse"]) < base[r["target"]] for r in sub)}
    result = {"status": "CANDIDATE_FOR_USER_REVIEW_NOT_FORMAL_RELEASE",
              "primary_q1_model": "chm.q1.v1.3 targetwise Ridge",
              "interaction_role": "A-side 1M sensitivity only; no Q2/Q3 substitution",
              "loss_normalization": "each 1M target contrast divided by the same positive frozen Ridge fitted reference Loss; explicit decision scenario, not a cross-source bridge",
              "policy_support": "512 observed A4 recipes only",
              "quality_coverage": "3 direct + 3 near_direct + 11 unknown; no global Q_A or B7 Q_score assigned to unknown domains",
              "upstream_audit": upstream, "heldout_counts": counts, "policies": decisions,
              "qa_policy_sensitivity": qa_policy_sensitivity,
              "sources_sha256": {"q1_v1.3_manifest": sha(ROOT / "interfaces/chm/q1_interface_v1_3.json"),
                                 "cy_j_q1_bundle": sha(BASE / "q1_q2_bundle_v1/export_manifest.json"),
                                 "cy_j_interaction_bundle": sha(BASE / "q1_interaction_bundle_v1/interaction_manifest.json"),
                                 "qa_mapping_primary_candidate": sha(OUT / "qa_mapping_primary_candidate.json")}}
    (OUT / "review_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
