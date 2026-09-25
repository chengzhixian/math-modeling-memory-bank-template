"""Partial A-side quality coverage for named 17-domain mixtures."""
from pathlib import Path
import json
import math

import pandas as pd

from q1_interface import Q1Interface

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/chm/q1_quality_mapping_final"


def validate_mixture(mixture, domains):
    if not isinstance(mixture, dict) or set(mixture) != set(domains):
        raise ValueError("mixture must contain exactly the 17 named domains")
    vals = {name: float(mixture[name]) for name in domains}
    if any(not math.isfinite(v) or v < 0 for v in vals.values()):
        raise ValueError("mixture weights must be finite and nonnegative")
    if not math.isclose(sum(vals.values()), 1.0, abs_tol=1e-6):
        raise ValueError("mixture sum must be one; no silent normalization")
    return vals


def coverage(mixture, mapping_rows):
    names = [r["mixture_domain"] for r in mapping_rows]
    vals = validate_mixture(mixture, names)
    shares = {"direct": 0.0, "near_direct": 0.0, "inferred": 0.0}
    partial_quality_sum = 0.0
    for row in mapping_rows:
        name, kind = row["mixture_domain"], row["mapping_type"]
        if kind not in shares:
            raise ValueError(f"unknown mapping type: {kind}")
        shares[kind] += vals[name]
        if kind != "inferred":
            partial_quality_sum += vals[name] * float(row["Q_A_proxy"])
        elif row.get("Q_A_proxy") is not None:
            raise ValueError("unknown domain must have null quality")
    unknown = shares["inferred"]
    status = "PARTIAL_UNKNOWN" if unknown > 1e-10 else (
        "PROXY_COVERED" if shares["near_direct"] > 1e-10 else "DIRECT_A_SIDE_COVERED")
    return {"mapping_weights": shares, "direct_share": shares["direct"],
            "proxy_share": shares["near_direct"], "unknown_share": unknown,
            "known_plus_proxy_share": shares["direct"] + shares["near_direct"],
            "partial_weighted_quality_sum": partial_quality_sum,
            "global_Q_A": None if unknown > 1e-10 else partial_quality_sum,
            "global_quality_status": status,
            "B7_Q_score": "NOT_IDENTIFIED",
            "note": "near_direct is an A-side semantic proxy; direct means name match, not population identity"}


def main():
    q1 = Q1Interface(ROOT)
    ranks = pd.read_csv(ROOT / "outputs/chm/q1_quality_robustness_final/rule_rank_envelope.csv").set_index("domain")
    rows = []
    for domain, record in q1.mapping_rows.items():
        kind = record["mapping_type"]
        matched = None if kind == "inferred" else q1.quality(record["quality_domain"])
        rank = None if matched is None else ranks.loc[record["quality_domain"]]
        rows.append(dict(mixture_domain=domain, mapped_quality_domain=record["quality_domain"] if matched else None,
            mapping_type=kind, mapping_basis=record["note"],
            Q_A_proxy=None if matched is None else matched["Q_A_median"],
            Q_A_conditional_low=None if matched is None else matched["conditional_95"][0],
            Q_A_conditional_high=None if matched is None else matched["conditional_95"][1],
            Q_A_n=None if matched is None else matched["n_rows"],
            rule_rank_min=None if rank is None else int(rank.rank_min),
            rule_rank_max=None if rank is None else int(rank.rank_max),
            score_version="q1_global_spearman_all22_v1",
            risk="unknown_no_numeric_value" if matched is None else (
                "near_domain_proxy" if kind == "near_direct" else "same_name_not_same_population")))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "mapping_coverage.csv", index=False)
    pref = q1.reference
    scenarios = {"p_ref": pref.copy(), "unknown_heavy": {d: (1.0 if d == "dm_mathematics" else 0.0) for d in pref},
                 "negative_Q_direct": {d: (1.0 if d == "github" else 0.0) for d in pref}}
    cases = []
    for name, mixture in scenarios.items():
        cases.append({"scenario": name, **coverage(mixture, rows)})
    (OUT / "mixture_quality_coverage_cases.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    manifest = {"schema_version": "chm.q1.quality_mapping.v1", "counts": {k: sum(r["mapping_type"] == k for r in rows)
                 for k in ("direct", "near_direct", "inferred")},
                "scientific_limit": "No paired per-mixture Q_A and Loss; full 17-domain quality effect is NOT_IDENTIFIED"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
