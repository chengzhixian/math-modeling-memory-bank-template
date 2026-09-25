"""Q1 observed-recipe selection stability and held-out decision stress test.

No A/B bridge or continuous-simplex optimum is inferred. Domain weights and
quality rules are explicit scenarios, not estimated scientific parameters.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from q1_interface import Q1Interface
from q1_mixture_final_audit import read_pairs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_selection_stability_v1"
Q1_BUNDLE = ROOT / "outputs/chm/q1_exports/q1_q2_bundle_v1"
INTER = ROOT / "outputs/chm/q1_exports/q1_interaction_bundle_v1/interaction_coefficients_13_targets.json"
HULL = ROOT / "outputs/chm/q1_mixture_final/composition_support.csv"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def scores(x: np.ndarray, domains: list[str], targets: list[str], p_ref: np.ndarray,
           beta: np.ndarray, interaction: dict, denominator: np.ndarray) -> dict[str, np.ndarray]:
    linear = (x - p_ref) @ beta.T / denominator
    nonlinear = np.zeros_like(linear)
    for j, target in enumerate(targets):
        item = interaction[target]
        main = np.array([float(item["main"][d]) for d in domains])
        nonlinear[:, j] = (x - p_ref) @ main
        for pair in item["pairs"]:
            a, b = pair["domains"]
            ia, ib = domains.index(a), domains.index(b)
            nonlinear[:, j] += float(pair["gamma"]) * (x[:, ia] * x[:, ib] - p_ref[ia] * p_ref[ib])
    nonlinear /= denominator
    return {"ridge_v1.3": linear, "interaction_candidate": nonlinear}


def qa_feasible(x: np.ndarray, p_ref: np.ndarray, domains: list[str], mapping: dict,
                score_scope: str, policy: str, q1: Q1Interface) -> np.ndarray:
    if policy == "unconstrained":
        return np.ones(len(x), bool)
    allowed = {"direct"} if policy == "quality_direct" else {"direct", "near_direct"}
    mask = np.array([mapping[d]["mapping_type"] in allowed for d in domains], float)
    qa = []
    for d in domains:
        row = mapping[d]
        if row["mapping_type"] == "inferred":
            qa.append(0.0)
        elif score_scope == "A1_sample_primary":
            qa.append(float(q1.quality(row["quality_domain"])["Q_A_median"]))
        else:
            qa.append(float(row["Q_A"]))
    qa = np.array(qa)
    covered_ref = float(p_ref @ mask)
    mean_ref = float(p_ref @ (mask * qa) / covered_ref)
    return ((x @ mask >= covered_ref - 1e-12) &
            (x @ (mask * (qa - mean_ref)) >= -1e-12))


def run() -> dict:
    q1 = Q1Interface(ROOT)
    datasets, audit, domains, targets = read_pairs()
    a4 = csv_rows(Q1_BUNDLE / "recipes_512.csv")
    ids = [r["index"] for r in a4]
    xtrain = np.array([[float(r[d]) for d in domains] for r in a4])
    p_ref = np.array([float(q1.reference[d]) for d in domains])
    beta = np.array([[float(q1.coefficients[k][d]) for d in domains] for k in targets])
    ridge_rows = {r["target"]: r for r in csv_rows(Q1_BUNDLE / "coefficients.csv")}
    reference_loss = np.array([float(ridge_rows[k]["intercept"]) + float(p_ref @ beta[j])
                               for j, k in enumerate(targets)])
    assert np.all(reference_loss > 0)
    interaction = json.loads(INTER.read_text(encoding="utf-8"))["targets"]
    train_scores = scores(xtrain, domains, targets, p_ref, beta, interaction, reference_loss)
    mapping = {r["mixture_domain"]: r for r in json.loads((Q1_BUNDLE / "qa_mapping.json").read_text(encoding="utf-8"))["rows"]}
    rng = np.random.default_rng(20260925)
    weights = [("equal_13", np.full(len(targets), 1 / len(targets)))]
    weights += [(f"only_{k}", np.eye(len(targets))[j]) for j, k in enumerate(targets)]
    weights += [(f"dirichlet_sparse_{i:03d}", w) for i, w in enumerate(rng.dirichlet(np.full(len(targets), 0.2), 100))]
    weights += [(f"dirichlet_balanced_{i:03d}", w) for i, w in enumerate(rng.dirichlet(np.full(len(targets), 5.0), 100))]
    decisions = []
    for weight_name, w in weights:
        for score_scope in ("A1_sample_primary", "A2_A3_extended_sensitivity"):
            for policy in ("unconstrained", "quality_direct", "quality_direct_and_near"):
                allowed = qa_feasible(xtrain, p_ref, domains, mapping, score_scope, policy, q1)
                assert allowed.any(), (score_scope, policy)
                for model_name, matrix in train_scores.items():
                    objective = matrix @ w
                    valid = np.flatnonzero(allowed)
                    chosen = int(valid[np.argmin(objective[valid])])
                    decisions.append({"weight_scenario": weight_name, "quality_score_scope": score_scope,
                                      "quality_policy": policy, "model": model_name,
                                      "n_feasible_observed_recipes": len(valid),
                                      "selected_index": ids[chosen], "objective_relative": float(objective[chosen]),
                                      "max_domain_share": float(xtrain[chosen].max()),
                                      "unknown_QA_share": float(sum(xtrain[chosen, domains.index(d)] for d in domains
                                                                     if mapping[d]["mapping_type"] == "inferred"))})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "selection_grid.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(decisions[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(decisions)
    # Evaluate a distinct question: among the actual held-out candidate rows,
    # does each frozen predictor select a low realized weighted target Loss?
    support = {(r["scope"], str(r["index"])): r["hull_status"] for r in csv_rows(HULL)}
    heldout = []
    for scope in ("test_1m", "test_60m", "test_1B"):
        mix, loss, _, cols, x = datasets[scope]
        assert list(mix.index) == list(loss.index)
        y = np.column_stack([loss[next(c for c in cols if c.replace("metric/the_pile_", "").replace("_val_loss", "") == k)].to_numpy(float)
                             for k in targets])
        predicted = scores(x, domains, targets, p_ref, beta, interaction, reference_loss)
        support_inside = np.array([support[(scope, str(i))] == "IN_A4_HULL" for i in mix.index])
        candidate_sets = {"all_heldout": np.arange(len(x))}
        if int(support_inside.sum()) >= 10:
            candidate_sets["in_A4_hull_only"] = np.flatnonzero(support_inside)
        for candidate_set, eligible in candidate_sets.items():
            for weight_name, w in weights:
                actual = (y / reference_loss) @ w
                local_actual = actual[eligible]
                best_true = int(eligible[np.argmin(local_actual)])
                span = float(local_actual.max() - local_actual.min())
                for model_name, matrix in predicted.items():
                    chosen = int(eligible[np.argmin((matrix @ w)[eligible])])
                    rank = int(np.count_nonzero(local_actual < actual[chosen] - 1e-12) + 1)
                    heldout.append({"scope": scope, "candidate_set": candidate_set,
                                    "weight_scenario": weight_name, "model": model_name,
                                    "n_candidates": len(eligible), "selected_index": str(mix.index[chosen]),
                                    "selected_hull_status": support[(scope, str(mix.index[chosen]))],
                                    "actual_best_index": str(mix.index[best_true]),
                                    "realized_rank": rank, "realized_top_decile": rank <= max(1, int(np.ceil(len(eligible) / 10))),
                                    "realized_relative_regret": float((actual[chosen] - actual[best_true]) / span) if span > 0 else 0.0})
    with (OUT / "heldout_selection_stress.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(heldout[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(heldout)
    summary = {}
    for model_name in train_scores:
        main = [r for r in decisions if r["model"] == model_name and r["quality_score_scope"] == "A1_sample_primary" and r["quality_policy"] == "unconstrained"]
        summary[model_name] = {"n_weight_scenarios": len(main), "distinct_selected_A4_recipes": len({r["selected_index"] for r in main}),
                               "share_equal_13_choice": sum(r["selected_index"] == next(z["selected_index"] for z in main if z["weight_scenario"] == "equal_13") for r in main) / len(main)}
    paired = {}
    for key in {(r["weight_scenario"], r["quality_score_scope"], r["quality_policy"]) for r in decisions}:
        subset = [r for r in decisions if (r["weight_scenario"], r["quality_score_scope"], r["quality_policy"]) == key]
        paired[key] = {r["model"]: r["selected_index"] for r in subset}
    model_agreement = sum(v["ridge_v1.3"] == v["interaction_candidate"] for v in paired.values()) / len(paired)
    agreement_by_policy = {policy: sum(v["ridge_v1.3"] == v["interaction_candidate"] for k, v in paired.items()
                                       if k[2] == policy) / sum(k[2] == policy for k in paired)
                           for policy in ("unconstrained", "quality_direct", "quality_direct_and_near")}
    quality_flip = {}
    for model_name in train_scores:
        for policy in ("quality_direct", "quality_direct_and_near"):
            changed = 0
            for weight_name, _ in weights:
                a = next(r for r in decisions if r["model"] == model_name and r["quality_policy"] == policy and r["weight_scenario"] == weight_name and r["quality_score_scope"] == "A1_sample_primary")
                b = next(r for r in decisions if r["model"] == model_name and r["quality_policy"] == policy and r["weight_scenario"] == weight_name and r["quality_score_scope"] == "A2_A3_extended_sensitivity")
                changed += a["selected_index"] != b["selected_index"]
            quality_flip[f"{model_name}/{policy}"] = changed
    for scope in ("test_1m", "test_60m", "test_1B"):
        for candidate_set in ("all_heldout", "in_A4_hull_only"):
          for model_name in train_scores:
            subset = [r for r in heldout if r["scope"] == scope and r["candidate_set"] == candidate_set and r["model"] == model_name]
            if not subset:
                continue
            summary[f"{scope}/{candidate_set}/{model_name}"] = {"n_weight_scenarios": len(subset),
                "median_realized_relative_regret": float(np.median([r["realized_relative_regret"] for r in subset])),
                "top_decile_fraction": float(np.mean([r["realized_top_decile"] for r in subset])),
                "chosen_outside_A4_hull_fraction": float(np.mean([r["selected_hull_status"] != "IN_A4_HULL" for r in subset]))}
    result = {"schema_version": "chm.q1.selection_stability.v1", "status": "A_side_exploratory_not_Q2_Q3_calibrated",
              "weight_scenarios": len(weights), "model_choice_agreement_fraction_all_scenarios": model_agreement,
              "model_agreement_fraction_by_quality_policy": agreement_by_policy,
              "quality_scope_selection_flip_counts": quality_flip, "summary": summary,
              "heldout_selection_limit": "actual Loss of held-out candidate chosen among held-out rows; not actual Loss of selected A4 recipe; model form already inspected held-outs",
              "source_sha256": {"Q1_bundle": sha(Q1_BUNDLE / "export_manifest.json"), "interaction": sha(INTER), "support": sha(HULL)},
              "selection_grid_sha256": sha(OUT / "selection_grid.csv"),
              "heldout_selection_sha256": sha(OUT / "heldout_selection_stress.csv")}
    (OUT / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
