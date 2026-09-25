"""Default Q3 p-selection diagnostic using Q1 v2 interaction predictions."""
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np
from q1_interface import Q1Interface

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q3_p_validation_v2"
PANEL = ("pile_cc", "wikipedia_en", "arxiv", "stackexchange", "github")
DATA = ROOT / "data/raw/real_attachments/A_data_value/regmix_tables"
SETS = (("test_1m", "1m"), ("test_60m", "60m"), ("test_1B", "1B"))


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, records):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def release():
    q1 = Q1Interface(ROOT)
    support = {(r["scope"], r["index"]): r["hull_status"] for r in rows(ROOT / "outputs/chm/q1_mixture_final/composition_support.csv")}
    training = []
    scores = q1._predict(q1.recipes)
    for k, target in enumerate(q1.targets):
        rank = np.argsort(scores[:, k])
        i, runner_up = map(int, rank[:2])
        training.append({"target": target, "in_primary_panel": target in PANEL,
                         "mixture_id": q1.recipe_ids[i], "predicted_delta_1m": float(scores[i,k]-q1.reference_loss[k]),
                         "second_best_gap": float(scores[runner_up,k]-scores[i,k]),
                         "max_share": float(q1.recipes[i].max())})
    held = []
    for scope, suffix in SETS:
        mixes = rows(DATA / f"test_mixture_{suffix}.csv")
        losses = {r["index"]: r for r in rows(DATA / f"test_pile_loss_{suffix}.csv")}
        if set(r["index"] for r in mixes) != set(losses):
            raise ValueError("held-out mixture and loss indices differ")
        x = np.array([[float(r[f"train_the_pile_{d}"]) for d in q1.domains] for r in mixes])
        x /= x.sum(axis=1)[:, None]
        predicted = q1._predict(x)
        for k, target in enumerate(q1.targets):
            actual = np.array([float(losses[r["index"]][f"metric/the_pile_{target}_val_loss"]) for r in mixes])
            chosen = int(np.argmin(predicted[:,k]))
            truth = int(np.argmin(actual))
            rank = int(1 + np.count_nonzero(actual < actual[chosen] - 1e-12))
            held.append({"scope": scope, "target": target, "in_primary_panel": target in PANEL,
                         "n_candidates": len(mixes), "chosen_mixture_id": mixes[chosen]["index"],
                         "chosen_A4_hull_status": support[(scope, mixes[chosen]["index"])],
                         "predicted_1M_loss": float(predicted[chosen,k]), "chosen_actual_loss": float(actual[chosen]),
                         "actual_rank": rank, "regret": float(actual[chosen]-actual[truth]),
                         "relative_regret": float((actual[chosen]-actual[truth])/actual[truth]),
                         "top10pct": rank <= math.ceil(.1 * len(mixes)),
                         "actual_best_id": mixes[truth]["index"], "actual_best_loss": float(actual[truth])})
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "training_supported_candidates.csv", training)
    write_csv(OUT / "heldout_selection_validation.csv", held)
    def summary(items):
        return {"n": len(items), "exact_best": sum(r["actual_rank"]==1 for r in items),
                "top10pct": sum(r["top10pct"] for r in items),
                "max_rank": max(r["actual_rank"] for r in items),
                "median_relative_regret": float(np.median([r["relative_regret"] for r in items]))}
    manifest = {
        "schema_version": "chm.q3.p_selection_validation.v2",
        "Q1_version": q1.manifest["schema_version"], "Q1_manifest_sha256": q1.manifest_sha256,
        "status": "A_side_selection_diagnostic_only", "ready_for_Q3_empirical_absolute_loss": False,
        "primary_panel": list(PANEL),
        "selection_support": "heldout_candidates_within_each_set; off_hull_allowed_only_for_validation",
        "summary": {"all": summary(held), "primary_panel": summary([r for r in held if r["in_primary_panel"]]),
                    "by_scope_primary_panel": {scope: summary([r for r in held if r["scope"] == scope and r["in_primary_panel"]])
                                               for scope,_ in SETS}},
        "limitations": ["heldout candidates are not selected A4 training recipes",
                        "absolute cross-scale 1M Loss is uncalibrated", "A/B bridge unidentified"],
        "files_sha256": {name: sha(OUT/name) for name in ("training_supported_candidates.csv","heldout_selection_validation.csv")},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(release(), ensure_ascii=False, indent=2))
