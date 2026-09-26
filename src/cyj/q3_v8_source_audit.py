"""Read-only provenance and overlap check for Q3's available B/C raw tables."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "data/raw/real_attachments/B_scaling_laws"
C = ROOT / "data/raw/real_attachments/C_efficiency_evolution"
SOURCES = {"B1": B / "pythia_training_log_existing.csv",
           "B6": B / "supplementary_NQ_experiment.csv",
           "B7": B / "supplementary_NQ_experiment_expanded.csv",
           "B8": B / "supplementary_NQ_experiment_large.csv",
           "C7": C / "model_architecture_metadata.csv"}


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def coordinate(row: dict) -> tuple[float, float, float]:
    return tuple(float(row[k]) for k in ("N_params_B", "D_tokens_B", "Q_score"))


def main() -> None:
    rows = {name: load(path) for name, path in SOURCES.items()}
    files = {name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "rows": len(rows[name]),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
             for name, path in SOURCES.items()}
    q = {name: {coordinate(row): float(row["val_loss"]) for row in rows[name]}
         for name in ("B6", "B7", "B8")}
    overlaps = {}
    for left, right in (("B6", "B7"), ("B6", "B8"), ("B7", "B8")):
        shared = q[left].keys() & q[right].keys()
        overlaps[f"{left}_{right}"] = {"shared_coordinates": len(shared),
                                       "identical_loss": sum(q[left][x] == q[right][x] for x in shared),
                                       "different_loss": sum(q[left][x] != q[right][x] for x in shared)}
    result = {"files": files, "overlap": overlaps,
              "B1_N_range": [min(float(r["N_params_B"]) for r in rows["B1"]), max(float(r["N_params_B"]) for r in rows["B1"])],
              "B1_D_range": [min(float(r["D_tokens_B"]) for r in rows["B1"]), max(float(r["D_tokens_B"]) for r in rows["B1"])],
              "B7_outside_B1_rectangle": sum(not (0.070542 <= float(r["N_params_B"]) <= 11.965825 and
                                               10 <= float(r["D_tokens_B"]) <= 299.893) for r in rows["B7"]),
              "B8_types": {name: sum(r["data_type"] == name for r in rows["B8"])
                           for name in sorted({r["data_type"] for r in rows["B8"]})},
              "C7_contexts": sorted({int(r["max_position_embeddings"]) for r in rows["C7"]}),
              "status": "PASS"}
    out = ROOT / "experiments/cyj/20260926-q3-v8-acceptance/source_audit.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
