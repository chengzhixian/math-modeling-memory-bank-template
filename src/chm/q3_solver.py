"""Q3 solver scaffold for chm.

Formal results are gated by q3_preflight. The currently executable p mode is an
explicit scenario only: Q is fixed at Q0, lambda_loss and eta are mandatory, and
p is selected only from A4 observed training mixtures to avoid unsupported simplex
vertices.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

from q1_interface import Q1Interface
from q3_nd_baseline import DEFAULT_PARAMS, N_RANGE, D_RANGE, base_loss, compute_coeff, bounded_optimum
from q3_preflight import inspect as inspect_upstream

ROOT = Path(__file__).resolve().parents[2]
A4 = Path("data/raw/real_attachments/A_data_value/regmix_tables/train_mixture_1m.csv")
DEFAULT_CYJ_REF = "6c17cb4e387e1ac047f8fe0e9ecb6fe42fc5ef3b"
DEFAULT_ZHH_REF = "d47cd2dc921333caecfcb95f09eb5a2f2714d0db"

def load_observed_mixtures(root=ROOT):
    path = Path(root) / A4
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 512:
        raise ValueError(f"expected 512 A4 rows, got {len(rows)}")
    domains = [c for c in rows[0] if c != "index"]
    out = []
    for row in rows:
        vals = np.array([float(row[d]) for d in domains], dtype=float)
        if np.any(vals < 0) or not np.all(np.isfinite(vals)):
            raise ValueError("invalid A4 mixture")
        total = float(vals.sum())
        if total <= 0:
            raise ValueError("non-positive A4 mixture sum")
        vals /= total
        out.append((row["index"], dict(zip(domains, map(float, vals)))))
    return out

def feasible_n_interval(budget, context):
    product = budget / compute_coeff(context)
    nmin, nmax = N_RANGE
    dmin, _ = D_RANGE
    hi = min(nmax, product / dmin)
    if hi < nmin:
        raise ValueError("budget too small for declared B1 support")
    return nmin, hi, product

def best_d_for_n(n, product):
    dmin, dmax = D_RANGE
    d = min(dmax, product / n)
    if d < dmin:
        raise ValueError("N leaves no feasible D inside support")
    return d

def solve_p_scenario(*, budget, context, target, lambda_loss, eta, root=ROOT):
    budget=float(budget); context=int(context)
    lambda_loss=float(lambda_loss); eta=float(eta)
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be positive")
    if context not in (2048,8192,131072):
        raise ValueError("context must be a declared C7 scenario")
    if not math.isfinite(lambda_loss) or lambda_loss < 0:
        raise ValueError("lambda_loss must be an explicit finite nonnegative scenario")
    if not math.isfinite(eta):
        raise ValueError("eta must be explicit and finite")

    q1 = Q1Interface(root)
    if target not in q1.coefficients:
        raise ValueError("unknown Q1 target")
    lo, hi, product = feasible_n_interval(budget, context)
    candidates = load_observed_mixtures(root)

    best = None
    for mixture_id, p in candidates:
        def objective(log_n):
            n = math.exp(log_n)
            d = best_d_for_n(n, product)
            delta = q1.relative_effect(
                p, target, n_params=n*1e9, eta=eta
            )["delta_target_loss"]
            return base_loss(n,d) + lambda_loss*delta

        res = minimize_scalar(
            objective,
            bounds=(math.log(lo), math.log(hi)),
            method="bounded",
            options={"xatol":1e-10, "maxiter":500},
        )
        for n in (lo, hi, math.exp(res.x)):
            d = best_d_for_n(n, product)
            value = objective(math.log(n))
            item = {
                "objective_loss": float(value),
                "N_params_B": float(n),
                "D_tokens_B": float(d),
                "mixture_id": mixture_id,
                "mixture": p,
                "optimizer_success": bool(res.success),
            }
            if best is None or item["objective_loss"] < best["objective_loss"]:
                best = item

    cost = compute_coeff(context)*best["N_params_B"]*best["D_tokens_B"]
    best.update({
        "schema_version":"chm.q3.p_scenario.v1",
        "status":"scenario_only",
        "ready_for_Q3":False,
        "budget_FLOPs":budget,
        "context_tokens":context,
        "target":target,
        "lambda_loss":lambda_loss,
        "eta":eta,
        "Q_policy":"Q=Q0; Q performance disabled",
        "p_support":"A4 observed training mixtures only (512 normalized rows)",
        "cost_FLOPs":float(cost),
        "budget_utilization":float(cost/budget),
        "cyj_loss_coordinate":"B1.val_loss baseline + explicit cross-Loss scenario correction",
        "warning":"Not a formal Q3 optimum; lambda/anchor/Q bridge are not validated.",
    })
    return best

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight","diagnostic-nd","p-scenario"), required=True)
    parser.add_argument("--budget", type=float)
    parser.add_argument("--context", type=int)
    parser.add_argument("--target")
    parser.add_argument("--lambda-loss", type=float)
    parser.add_argument("--eta", type=float)
    parser.add_argument("--cyj-ref", default=DEFAULT_CYJ_REF)
    parser.add_argument("--zhh-ref", default=DEFAULT_ZHH_REF)
    parser.add_argument("--output", type=Path)
    args=parser.parse_args()

    gate=inspect_upstream(args.cyj_ref,args.zhh_ref)
    if args.mode=="preflight":
        result=gate
    elif args.mode=="diagnostic-nd":
        if args.budget is None or args.context is None:
            raise ValueError("diagnostic-nd requires --budget and --context")
        result=bounded_optimum(args.budget,args.context)
        result.update({"status":"diagnostic_only","ready_for_Q3":False,"upstream":gate})
    else:
        required=(args.budget,args.context,args.target,args.lambda_loss,args.eta)
        if any(v is None for v in required):
            raise ValueError("p-scenario requires budget/context/target/lambda-loss/eta explicitly")
        result=solve_p_scenario(
            budget=args.budget,context=args.context,target=args.target,
            lambda_loss=args.lambda_loss,eta=args.eta,root=ROOT
        )
        result["upstream"]=gate

    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":
    main()
