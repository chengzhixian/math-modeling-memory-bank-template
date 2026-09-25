"""Read-only B6/B7/B8 conditional trends and coordinate-overlap audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from audit_b_scaling_laws import (
    ROOT, DEFAULT_DATA_ROOT, DEFAULT_MANIFEST, DEFAULT_SOURCE_MANIFEST,
    sha256, validate_input_version,
)
from scaling_provenance import verify_source_files

FILES = {
    "B6": "supplementary_NQ_experiment.csv",
    "B7": "supplementary_NQ_experiment_expanded.csv",
    "B8": "supplementary_NQ_experiment_large.csv",
}
AXES = ("N_params_B", "D_tokens_B", "Q_score")


def read_data(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("empty input")
    for line, row in enumerate(rows, 2):
        for field in (*AXES, "val_loss"):
            row[field] = float(row[field])
            if not math.isfinite(row[field]) or row[field] <= 0:
                raise ValueError(f"invalid {field} at line {line}")
        if row["Q_score"] > 1:
            raise ValueError(f"invalid Q_score at line {line}")
        row["source_line"] = line
    return rows


def coordinate_map(rows):
    result = {}
    for row in rows:
        key = tuple(row[x] for x in AXES)
        if key in result:
            raise ValueError(f"duplicate N,D,Q coordinate: {key}")
        result[key] = row
    return result


def trends(rows, axis):
    """Adjacent finite differences holding both other inputs exactly fixed."""
    groups = defaultdict(list)
    fixed = [x for x in AXES if x != axis]
    for row in rows:
        groups[tuple(row[x] for x in fixed)].append(row)
    directions = Counter(increasing=0, decreasing=0, tied=0)
    endpoints = Counter(increasing=0, decreasing=0, tied=0)
    group_types = Counter(increasing=0, decreasing=0, tied=0, mixed=0, singleton=0)
    slopes = []
    for group in groups.values():
        group.sort(key=lambda r: r[axis])
        if len(group) > 1:
            delta = group[-1]["val_loss"] - group[0]["val_loss"]
            endpoints["increasing" if delta > 0 else "decreasing" if delta < 0 else "tied"] += 1
        signs = set()
        for left, right in zip(group, group[1:]):
            delta = right["val_loss"] - left["val_loss"]
            sign = "increasing" if delta > 0 else "decreasing" if delta < 0 else "tied"
            directions[sign] += 1
            signs.add(sign)
            slopes.append(delta / (right[axis] - left[axis]))
        group_types[next(iter(signs)) if len(signs) == 1 else "mixed" if signs else "singleton"] += 1
    return {"groups": len(groups), "group_types": dict(group_types),
            "endpoint_directions": dict(endpoints),
            "adjacent_pairs": dict(directions),
            "slope_min": min(slopes) if slopes else None,
            "slope_max": max(slopes) if slopes else None}


def overlap(left, right):
    a, b = coordinate_map(left), coordinate_map(right)
    keys = sorted(a.keys() & b.keys())
    differences = [b[k]["val_loss"] - a[k]["val_loss"] for k in keys]
    examples = []
    for key in keys:
        if a[key]["val_loss"] != b[key]["val_loss"] and len(examples) < 3:
            examples.append({"coordinate": dict(zip(AXES, key)),
                             "left": a[key], "right": b[key]})
    return {"shared_coordinates": len(keys),
            "identical_loss": sum(d == 0 for d in differences),
            "different_loss": sum(d != 0 for d in differences),
            "right_minus_left_min": min(differences) if differences else None,
            "right_minus_left_max": max(differences) if differences else None,
            "examples": examples}


def diagnose():
    identities = verify_source_files(DEFAULT_DATA_ROOT, DEFAULT_MANIFEST, tuple(FILES.values()))
    data = {name: read_data(DEFAULT_DATA_ROOT / filename) for name, filename in FILES.items()}
    labels = Counter(r.get("data_type") for r in data["B8"])
    if set(labels) != {"calibrated", "extrapolated"}:
        raise ValueError(f"unexpected B8 labels: {labels}")
    subsets = data | {f"B8_{label}": [r for r in data["B8"] if r["data_type"] == label]
                      for label in sorted(labels)}
    summary = {}
    for name, rows in subsets.items():
        coordinate_map(rows)
        minimum_loss = min(r["val_loss"] for r in rows)
        summary[name] = {
            "rows": len(rows),
            "minimum_loss": minimum_loss,
            "rows_at_minimum_loss": sum(r["val_loss"] == minimum_loss for r in rows),
            "range": {x: [min(r[x] for r in rows), max(r[x] for r in rows)] for x in AXES},
            "trends": {x: trends(rows, x) for x in AXES},
        }
    return {"schema_version": "cyj.b_quality_audit.v1", "source_files": identities,
            "method": "Exact N,D,Q keys; adjacent differences at fixed other inputs; no tolerance, transformation, fit or causal claim.",
            "datasets": summary,
            "overlap": {f"{a}_vs_{b}": overlap(data[a], data[b])
                        for a, b in itertools.combinations(data, 2)},
            "ready_for_Q3": False,
            "usage_policy": {
                "B6_B7": "deduplicate shared coordinates before exploratory quality fitting; not independent validation",
                "B8_calibrated": "quarantine from common B6/B7 fit pending Q direction and Loss coordinate provenance",
                "B8_extrapolated": "scenario audit only; never fit or independent validation",
                "Q_transform": None,
                "B1_loss_bridge": "not_established",
                "A_Q_to_B_Q_bridge": "not_identified",
            }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-version", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/cyj/diagnostics/b_quality_audit.json")
    args = parser.parse_args()
    version = validate_input_version(args.input_version, DEFAULT_MANIFEST, DEFAULT_SOURCE_MANIFEST)
    result = diagnose()
    result["input_version"] = version
    result["code_hash_encoding"] = "SHA256 of UTF-8 source bytes with CRLF normalized to LF, matching repository eol=lf"
    result["code_sha256"] = {p: hashlib.sha256((ROOT / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in (
        "src/cyj/diagnose_b_quality.py", "src/cyj/scaling_provenance.py", "src/cyj/audit_b_scaling_laws.py")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(args.output.relative_to(ROOT)), "sha256": sha256(args.output),
                      "Q_trends": {k: v["trends"]["Q_score"] for k, v in result["datasets"].items()},
                      "overlap": {k: {f: v[f] for f in ("shared_coordinates", "identical_loss", "different_loss")}
                                  for k, v in result["overlap"].items()}}, indent=2))


if __name__ == "__main__":
    main()
