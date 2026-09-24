"""B7-native Q3 diagnostic; never a validated joint N-D-Q-p result.

Reads cyj's pinned model artifact from Git without copying or refitting it.
The selected published formula is evaluated only on its declared B7 support.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

from q3_quality_cost_geometry import FAMILIES, delta_g

ROOT = Path(__file__).resolve().parents[2]
CYJ_REF = "ad1d312c15bcf79c23d715dd199eec7c2e65a0af"
MODEL_PATH = "outputs/cyj/quality/b7_quality_fit.json"
MODEL_SHA256 = "e676bfb06da81c02ad968591aa9ae09da5c7cd6b56def49d59a82c371465b025"
BUDGETS = (1e19, 1e22, 1e24)
CONTEXTS = (2048, 8192, 131072)
Q0 = 0.5  # Explicit diagnostic scenario, not an inferred baseline.


def load_model():
    raw = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{CYJ_REF}:{MODEL_PATH}"])
    if hashlib.sha256(raw).hexdigest() != MODEL_SHA256:
        raise ValueError("cyj B7 model artifact hash mismatch")
    model = json.loads(raw)
    if (model["schema_version"] != "cyj.b7_quality.v1"
            or model["selected_family"] != "linear_quality"
            or model["ready_for_Q3"] is not False):
        raise ValueError("unexpected B7 model status or family")
    return model


def loss(n, d, q, p):
    return p["E"] + p["A"] * n ** -p["alpha"] + p["B"] * d ** -p["beta"] + p["G"] * (1 - q)


def cost_parts(n, d, q, q0, context, family):
    train = 6e18 * n * d
    attention = 2e14 * context * n * d
    quality = 1e9 * d * delta_g(q, q0, family)
    return train, attention, quality


def min_1d(fun, lo, hi, points=51):
    """Grid-bracketed golden search, retaining endpoints and all local minima."""
    if hi <= lo:
        return lo, fun(lo)
    grid = [lo + (hi - lo) * i / (points - 1) for i in range(points)]
    values = [fun(x) for x in grid]
    candidates = [(values[0], grid[0]), (values[-1], grid[-1])]
    golden = (math.sqrt(5) - 1) / 2
    for i in range(1, points - 1):
        if values[i] > values[i - 1] or values[i] > values[i + 1]:
            continue
        a, b = grid[i - 1], grid[i + 1]
        c, d = b - golden * (b - a), a + golden * (b - a)
        fc, fd = fun(c), fun(d)
        for _ in range(68):
            if fc <= fd:
                b, d, fd = d, c, fc
                c = b - golden * (b - a)
                fc = fun(c)
            else:
                a, c, fc = c, d, fd
                d = a + golden * (b - a)
                fd = fun(d)
        x = (a + b) / 2
        candidates.append((fun(x), x))
    value, point = min(candidates)
    return point, value


def optimize(budget, context, family, model, q0=Q0):
    support = model["support"]
    nmin, nmax = support["N_params_B"][0], support["N_params_B"][-1]
    dmin, dmax = support["D_tokens_B"][0], support["D_tokens_B"][-1]
    qmin, qmax = support["Q_score"][0], support["Q_score"][-1]
    if not qmin <= q0 < qmax:
        raise ValueError("Q0 outside B7 support")
    p = model["models"][model["selected_family"]]["full_fit"]["parameters"]
    coeff = 6e18 + 2e14 * context
    minimum_cost = coeff * nmin * dmin
    base = {"budget_FLOPs": budget, "context_tokens": context,
            "quality_family": family, "Q0_scenario": q0,
            "status": "B7_semi_synthetic_diagnostic_only", "ready_for_Q3": False}
    if budget < minimum_cost * (1 - 1e-12):
        return {**base, "feasible": False, "minimum_supported_cost_FLOPs": minimum_cost}

    def at_q(q):
        dg = delta_g(q, q0, family)
        n_hi = min(nmax, (budget / dmin - 1e9 * dg) / coeff)
        if n_hi < nmin:
            return math.inf, None

        def at_n(n):
            d = min(dmax, budget / (coeff * n + 1e9 * dg))
            return loss(n, d, q, p)

        n, value = min_1d(at_n, nmin, n_hi)
        d = min(dmax, budget / (coeff * n + 1e9 * dg))
        return value, (n, d, q)

    q_hi = qmax
    if at_q(q_hi)[1] is None:
        lo, hi = q0, qmax
        for _ in range(70):
            mid = (lo + hi) / 2
            if at_q(mid)[1] is None:
                hi = mid
            else:
                lo = mid
        q_hi = lo
    q, value = min_1d(lambda x: at_q(x)[0], q0, q_hi, points=61)
    n, d, q = at_q(q)[1]
    train, attention, quality = cost_parts(n, d, q, q0, context, family)
    total = train + attention + quality
    if total > budget * (1 + 1e-9) or not (nmin - 1e-9 <= n <= nmax + 1e-9 and dmin - 1e-9 <= d <= dmax + 1e-9):
        raise AssertionError("diagnostic optimizer returned an infeasible configuration")
    flags = [name for name, x, bound in (("N_min", n, nmin), ("N_max", n, nmax),
                                      ("D_min", d, dmin), ("D_max", d, dmax),
                                      ("Q0", q, q0), ("Q_max", q, qmax))
             if abs(x - bound) <= 1e-6 * max(1, bound)]
    return {**base, "feasible": True, "minimum_supported_cost_FLOPs": minimum_cost,
            "N_params_B": n, "D_tokens_B": d, "Q_score": q,
            "B7_diagnostic_loss": value, "loss_coordinate": "attachment_B7_native_val_loss",
            "C_train_FLOPs": train, "C_attention_FLOPs": attention,
            "C_quality_FLOPs": quality, "C_total_FLOPs": total,
            "budget_utilization": total / budget, "active_support": ";".join(flags) or "interior"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/chm/q3_b7_diagnostic_v1")
    args = parser.parse_args()
    model = load_model()
    rows = [optimize(b, c, f, model) for b in BUDGETS for c in CONTEXTS for f in FAMILIES]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (args.output_dir / "scan.csv").open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    p = model["models"][model["selected_family"]]["full_fit"]["parameters"]
    check = loss(.07, 10, .5, p)
    if abs(check - 3.492870995028143) > 1e-8:
        raise AssertionError("published B7 example does not reproduce")
    manifest = {"schema_version": "chm.q3.b7_diagnostic.v1", "status": "diagnostic_only",
                "ready_for_Q3": False, "cyj_commit": CYJ_REF, "cyj_artifact_sha256": MODEL_SHA256,
                "source_data_role": "B7 semi-synthetic, B6 duplicate excluded, B8 excluded",
                "Q0": Q0, "C7_contexts_status": "external scenarios, not optimized",
                "p_policy": "omitted: no A-to-B7 loss bridge; no eta transfer",
                "limitations": ["not an independently validated N-D-Q-p predictor",
                                "B7 rectangular support is an interpolation assumption",
                                "no total predictive or Benchmark interval"],
                "published_example_prediction": check, "rows": len(rows),
                "feasible_rows": sum(r["feasible"] for r in rows)}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "feasible": manifest["feasible_rows"]}))


if __name__ == "__main__":
    main()
