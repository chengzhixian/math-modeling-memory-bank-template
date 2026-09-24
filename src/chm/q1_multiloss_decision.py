"""Multi-dimensional Q1 decision layer over the A4 observed-mixture convex hull.

This module does not introduce a new loss model. It consumes chm.q1.v1.2:
13 target-specific 1M Ridge contrasts m_k(p), and solves transparent linear
decision problems only inside conv(A4).

Modes
-----
weighted:
    minimize sum_k s_k m_k(p)
minimax:
    minimize max_k m_k(p)
protected:
    minimize one target while constraining selected m_k(p) <= epsilon_k

No target weights or protection thresholds are invented here. Equal weights are
available only when explicitly requested by the caller.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from q1_interface import Q1Interface


ROOT = Path(__file__).resolve().parents[2]
A4 = Path("data/raw/real_attachments/A_data_value/regmix_tables/train_mixture_1m.csv")


def load_a4(root=ROOT):
    path = Path(root) / A4
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 512:
        raise ValueError(f"expected 512 A4 rows, got {len(rows)}")

    raw_domains = [c for c in rows[0] if c != "index"]
    domains = [c.replace("train_the_pile_", "") for c in raw_domains]
    ids, x = [], []
    for row in rows:
        vals = np.array([float(row[c]) for c in raw_domains], dtype=float)
        if np.any(vals < 0) or not np.all(np.isfinite(vals)):
            raise ValueError("invalid A4 mixture")
        total = float(vals.sum())
        if total <= 0:
            raise ValueError("non-positive A4 mixture sum")
        vals /= total
        ids.append(row["index"])
        x.append(vals)
    return ids, domains, np.vstack(x)


def build_effect_matrix(q1: Q1Interface, domains, x):
    if set(domains) != set(q1.reference):
        raise ValueError("A4 domains do not match Q1 interface")

    order = [domains.index(d) for d in q1.reference]
    x_ordered = x[:, order]
    targets = list(q1.coefficients)
    beta = np.array(
        [[float(q1.coefficients[k][d]) for d in q1.reference] for k in targets],
        dtype=float,
    )
    pref = np.array([q1.reference[d] for d in q1.reference], dtype=float)
    effects = (x_ordered - pref) @ beta.T
    if not np.all(np.isfinite(effects)):
        raise ValueError("non-finite Q1 effect matrix")
    return targets, list(q1.reference), x_ordered, effects


def mixture_from_omega(omega, x, domains):
    p = omega @ x
    if np.any(p < -1e-10) or not math.isclose(float(p.sum()), 1.0, abs_tol=1e-8):
        raise RuntimeError("solver returned invalid convex-hull mixture")
    return {d: float(v) for d, v in zip(domains, p)}


def summarize_solution(res, ids, x, domains, targets, effects, mode, extra):
    if not res.success:
        raise RuntimeError(f"linear program failed: {res.message}")

    omega = np.asarray(res.x[: len(ids)], dtype=float)
    omega[np.abs(omega) < 1e-10] = 0.0
    p = mixture_from_omega(omega, x, domains)
    target_effects = omega @ effects
    active = [
        {"index": ids[i], "weight": float(w)}
        for i, w in enumerate(omega)
        if w > 1e-7
    ]
    return {
        "schema_version": "chm.q1.multiloss_decision.v1",
        "status": "A_side_1M_decision_only",
        "mode": mode,
        "feasible_set": "conv(A4_512_normalized_mixtures)",
        "loss_coordinate": "A4_A5_1M_target_cross_entropy_contrast",
        "cross_scale_transfer": "not_identified_from_attachment_A",
        "objective_value": float(res.fun),
        "mixture": p,
        "target_effects": {
            k: float(v) for k, v in zip(targets, target_effects)
        },
        "active_A4_vertices": active,
        "solver": "scipy.optimize.linprog(method=highs)",
        **extra,
    }


def solve_weighted(ids, domains, x, targets, effects, weights):
    w = np.asarray(weights, dtype=float)
    if w.shape != (len(targets),):
        raise ValueError("weights must contain all 13 targets")
    if np.any(w < 0) or not np.all(np.isfinite(w)):
        raise ValueError("weights must be finite and nonnegative")
    if not math.isclose(float(w.sum()), 1.0, abs_tol=1e-8):
        raise ValueError("weights must sum to one")

    c = effects @ w
    res = linprog(
        c,
        A_eq=np.ones((1, len(ids))),
        b_eq=np.array([1.0]),
        bounds=[(0, None)] * len(ids),
        method="highs",
    )
    return summarize_solution(
        res,
        ids,
        x,
        domains,
        targets,
        effects,
        "weighted",
        {
            "weights": {k: float(v) for k, v in zip(targets, w)},
            "weight_source": "caller_supplied",
        },
    )


def solve_minimax(ids, domains, x, targets, effects):
    n = len(ids)
    # variables = omega_1 ... omega_n, t
    c = np.zeros(n + 1)
    c[-1] = 1.0

    a_ub = np.zeros((len(targets), n + 1))
    a_ub[:, :n] = effects.T
    a_ub[:, -1] = -1.0

    a_eq = np.zeros((1, n + 1))
    a_eq[0, :n] = 1.0

    res = linprog(
        c,
        A_ub=a_ub,
        b_ub=np.zeros(len(targets)),
        A_eq=a_eq,
        b_eq=np.array([1.0]),
        bounds=[(0, None)] * n + [(None, None)],
        method="highs",
    )
    extra = {
        "criterion": (
            "minimize maximum target-specific excess loss relative to p_ref"
        ),
        "max_target_effect": float(res.x[-1]) if res.success else None,
        "note": (
            "Uses a DoReMi-inspired worst-case excess-loss decision criterion; "
            "it is not DoReMi Group DRO training."
        ),
    }
    return summarize_solution(
        res, ids, x, domains, targets, effects, "minimax", extra
    )


def solve_protected(
    ids, domains, x, targets, effects, primary_target, thresholds
):
    if primary_target not in targets:
        raise ValueError(f"unknown primary target: {primary_target}")

    thresholds = dict(thresholds)
    unknown = sorted(set(thresholds) - set(targets))
    if unknown:
        raise ValueError(f"unknown protected targets: {unknown}")
    if not thresholds:
        raise ValueError("protected mode requires at least one threshold")
    if any(not math.isfinite(float(v)) for v in thresholds.values()):
        raise ValueError("thresholds must be finite")

    c = effects[:, targets.index(primary_target)]
    names = list(thresholds)
    a_ub = np.vstack(
        [effects[:, targets.index(name)] for name in names]
    )
    b_ub = np.array([float(thresholds[name]) for name in names], dtype=float)

    res = linprog(
        c,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=np.ones((1, len(ids))),
        b_eq=np.array([1.0]),
        bounds=[(0, None)] * len(ids),
        method="highs",
    )
    return summarize_solution(
        res,
        ids,
        x,
        domains,
        targets,
        effects,
        "protected",
        {
            "primary_target": primary_target,
            "protection_thresholds": {
                name: float(value) for name, value in thresholds.items()
            },
            "threshold_source": "caller_supplied_not_invented_by_Q1",
        },
    )


def parse_named_values(items):
    out = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"expected name=value, got: {item}")
        name, value = item.split("=", 1)
        name = name.strip()
        if not name or name in out:
            raise ValueError(f"invalid or duplicate name: {name}")
        out[name] = float(value)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("weighted", "minimax", "protected"), required=True
    )
    parser.add_argument("--equal-weights", action="store_true")
    parser.add_argument(
        "--weight",
        action="append",
        default=[],
        help="target=value; provide all 13 unless --equal-weights",
    )
    parser.add_argument("--primary-target")
    parser.add_argument(
        "--protect",
        action="append",
        default=[],
        help="target=epsilon for protected mode",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    q1 = Q1Interface(args.root)
    ids, raw_domains, x = load_a4(args.root)
    targets, domains, x, effects = build_effect_matrix(q1, raw_domains, x)

    if args.mode == "weighted":
        if args.equal_weights and args.weight:
            raise ValueError("choose either --equal-weights or explicit --weight")
        if args.equal_weights:
            weights = np.full(len(targets), 1.0 / len(targets))
            result = solve_weighted(
                ids, domains, x, targets, effects, weights
            )
            result["weight_source"] = "explicit_equal_weights_scenario"
        else:
            named = parse_named_values(args.weight)
            if set(named) != set(targets):
                missing = sorted(set(targets) - set(named))
                extra = sorted(set(named) - set(targets))
                raise ValueError(
                    f"explicit weights must match all targets; "
                    f"missing={missing}, extra={extra}"
                )
            weights = np.array([named[k] for k in targets], dtype=float)
            result = solve_weighted(
                ids, domains, x, targets, effects, weights
            )
    elif args.mode == "minimax":
        result = solve_minimax(ids, domains, x, targets, effects)
    else:
        if not args.primary_target:
            raise ValueError("protected mode requires --primary-target")
        thresholds = parse_named_values(args.protect)
        result = solve_protected(
            ids,
            domains,
            x,
            targets,
            effects,
            args.primary_target,
            thresholds,
        )

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
