"""Independent public-data stress check of the B1 N-D backbone only.

The public testbed has no compatible per-run Q1 recipe or B7 quality score.
It cannot validate the full cross-source Q3 optimum.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import subprocess

from scipy.stats import spearmanr

from q3_conditional_v8 import OUTPUT, write_csv
from q3_v8_inputs import ROOT, digest, load_v8


SOURCE = ROOT / "outputs/Q3/external_nd_runs.csv"
RELEASED_SHA256 = "d7dc42d26734ec8bce48a84d5981016f6e59f689fb1bdf1177163e5cfdee79d1"
DEFAULT_OUTPUT = ROOT / "data/processed/Q3/external_audit"
SOURCE_COMMIT = "a003c4913793ac2ae7ef87b28ecb562955d026d5"
SOURCE_URL = "https://github.com/mlfoundations/scaling"
VALIDATION_TAG = "paloma_c4_en"
BUDGETS = (1e19, 1e20, 1e21, 1e22, 1e24)


def read_runs(source: Path, b1: dict, bounds) -> tuple[list[dict], int]:
    if source.is_file():
        if digest(source) != RELEASED_SHA256:
            raise ValueError("released external-model observation table changed")
        with source.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 42 or {r["training_corpus"] for r in rows} != {"c4_original", "rpj", "rw_original"}:
            raise ValueError("released external common-support subset changed")
        for row in rows:
            n, d = float(row["N_params_B"]), float(row["D_tokens_B"])
            observed = float(row["observed_Paloma_C4_loss_in_OpenLM_coordinates"])
            predicted = (b1["E"] + b1["A"] * n ** (-b1["alpha"])
                         + b1["B"] * d ** (-b1["beta"]))
            if not (bounds[0][0] <= n <= bounds[0][1] and bounds[1][0] <= d <= bounds[1][1]):
                raise ValueError("released external row left Q2 support")
            if not all(math.isfinite(v) and v > 0 for v in (n, d, observed, predicted)):
                raise ValueError("released external row has invalid quantity")
            if not math.isclose(predicted, float(row["B1_predicted_loss_in_Pythia_coordinates"]), rel_tol=0, abs_tol=1e-12):
                raise ValueError("external B1 prediction drift")
            if not math.isclose(6e18*n*d, float(row["C_train_proxy_FLOPs"]), rel_tol=1e-12):
                raise ValueError("external cost proxy drift")
            row.update(N_params_B=n, D_tokens_B=d, C_train_proxy_FLOPs=6e18*n*d,
                       B1_predicted_loss_in_Pythia_coordinates=predicted,
                       observed_Paloma_C4_loss_in_OpenLM_coordinates=observed)
        return rows, 104  # Original source inventory count; source models are not mirrored here.
    actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source,
                            capture_output=True, text=True, check=True).stdout.strip()
    if actual != SOURCE_COMMIT:
        raise ValueError("public scaling testbed commit changed")
    files = sorted((source/"exp_data/models").glob("*.json"))
    if len(files) != 104:
        raise ValueError("public scaling testbed model count changed")
    rows = []
    for file in files:
        item = json.loads(file.read_text(encoding="utf-8"))
        hyper = item["hyperparameters"]
        n = hyper["params"]/1e9
        d = hyper["tokens"]/1e9
        if not (bounds[0][0] <= n <= bounds[0][1] and bounds[1][0] <= d <= bounds[1][1]):
            continue
        observations = [r for r in item["results"] if VALIDATION_TAG in str(r["val_data"])]
        if len(observations) != 1:
            raise ValueError("public testbed lacks a unique common validation loss")
        observed = float(observations[0]["loss"])
        predicted = (b1["E"]+b1["A"]*n**(-b1["alpha"])
                     +b1["B"]*d**(-b1["beta"]))
        if not all(math.isfinite(x) and x > 0 for x in (n, d, observed, predicted)):
            raise ValueError("public testbed contains an invalid comparison")
        rows.append({"source_model": item["name"], "training_corpus": item["dataset_name"],
                     "N_params_B": n, "D_tokens_B": d,
                     "C_train_proxy_FLOPs": 6e18*n*d,
                     "B1_predicted_loss_in_Pythia_coordinates": predicted,
                     "observed_Paloma_C4_loss_in_OpenLM_coordinates": observed,
                     "source_model_sha256": digest(file)})
    if len(rows) != 42 or {r["training_corpus"] for r in rows} != {"c4_original", "rpj", "rw_original"}:
        raise ValueError("public testbed common-support subset changed")
    return rows, len(files)


def compare(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    correlations, budgets = [], []
    predicted_key = "B1_predicted_loss_in_Pythia_coordinates"
    observed_key = "observed_Paloma_C4_loss_in_OpenLM_coordinates"
    for corpus in sorted({row["training_corpus"] for row in rows}):
        group = [row for row in rows if row["training_corpus"] == corpus]
        rho = float(spearmanr([row[predicted_key] for row in group],
                              [row[observed_key] for row in group]).statistic)
        correlations.append({"training_corpus": corpus, "models_in_common_support": len(group),
                             "Spearman_B1_vs_external_loss": rho})
        for budget in BUDGETS:
            eligible = [row for row in group if row["C_train_proxy_FLOPs"] <= budget]
            if not eligible:
                raise ValueError("public testbed budget has no candidate")
            chosen = min(eligible, key=lambda row: (row[predicted_key], row["source_model"]))
            observed_best = min(eligible, key=lambda row: (row[observed_key], row["source_model"]))
            budgets.append({"training_corpus": corpus, "training_cost_budget_FLOPs": budget,
                            "candidate_count": len(eligible),
                            "B1_selected_model": chosen["source_model"],
                            "observed_best_model": observed_best["source_model"],
                            "selection_match": chosen["source_model"] == observed_best["source_model"],
                            "observed_loss_regret_in_OpenLM_coordinates":
                                chosen[observed_key]-observed_best[observed_key],
                            "scope": "discrete_N_D_training_cost_only_no_Q_p_or_attention"})
    return correlations, budgets


def generate(source: Path = SOURCE, out_dir: Path = DEFAULT_OUTPUT) -> dict:
    model, bounds = load_v8()
    rows, source_count = read_runs(source, model.b1, bounds)
    correlations, budgets = compare(rows)
    files = {"external_nd_runs.csv": rows, "external_nd_budget_comparison.csv": budgets}
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, contents in files.items():
        write_csv(out_dir/name, contents)
    summary = {"schema_version": "chm.q3.external_nd_audit.v1",
               "source": SOURCE_URL, "source_commit": SOURCE_COMMIT,
               "source_models": source_count, "common_support_models": len(rows),
               "recheck_scope": ("released_42_row_observations_and_current_B1_predictions"
                                  if source.is_file() else "fresh_pinned_external_source_checkout"),
               "validation_metric": "Paloma_C4_en_loss_same_evaluation_corpus_within_each_training_corpus",
               "correlations": correlations,
               "budget_restricting_selection_match_count": sum(
                   r["selection_match"] for r in budgets if r["training_cost_budget_FLOPs"] in (1e20,1e21)),
               "budget_restricting_selection_total": sum(
                   r["training_cost_budget_FLOPs"] in (1e20,1e21) for r in budgets),
               "all_supported_candidates_selection_match_count": sum(
                   r["selection_match"] for r in budgets if r["training_cost_budget_FLOPs"] == 1e22),
               "full_cross_attachment_optimum_validated": False,
               "limitation": "OpenLM_training_corpora_are_not_A4_17_domain_recipes;_no_compatible_Q_A_or_Q_B;_loss_coordinates_differ;_only_B1_N_D_rank_and_discrete_training_cost_are_checked",
               "output_files_sha256": {name: digest(out_dir/name) for name in files}}
    (out_dir/"external_nd_audit.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
        encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False))
