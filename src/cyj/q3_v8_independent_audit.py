"""Independent CYJ numerical consumer audit of CHM's pinned Q3 v8 release.

This reads CHM's grids but never imports its optimizer. It rebuilds each
fixed-recipe N/D problem from the frozen CYJ predictor and solves a separate
log-N grid plus bounded scalar refinement. Native-Q sensitivity is handled by
an outer Q grid and refinement. These are numerical crosschecks, not interval
arithmetic or empirical cross-source validation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

from ndqp_scenarios_v8 import BOUNDS, ConditionalV8


EXPECTED_CHM = "c052b6918c3f77a2285622521d8abb1b429513be"
EXPECTED_CYJ_TREE = "fd2dbb3b2002983430329cdb2ec6a275c2eed4f6"
BUDGETS = (1e19, 1e20, 1e22, 1e24)
CONTEXTS = (2048, 8192, 131072)
FAMILIES = ("exponential", "power", "logarithmic")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def quality_price(q: float, family: str) -> float:
    if family == "exponential":
        return 1e7 * math.exp(6 * q)
    if family == "power":
        return 5e9 * q**4
    if family == "logarithmic":
        return 2e9 * math.log1p(10 * q)
    raise ValueError(family)


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def check_manifest(subject: Path) -> dict:
    commit = subprocess.check_output(["git", "-C", str(subject), "rev-parse", "HEAD"], text=True).strip()
    if commit != EXPECTED_CHM:
        raise ValueError(f"CHM commit mismatch: {commit}")
    manifest = json.loads((subject / "outputs/chm/q3_conditional_v8/manifest.json").read_text(encoding="utf-8"))
    if manifest["inputs"]["CYJ_v8_commit"] != EXPECTED_CYJ_TREE:
        raise ValueError("CHM consumed a different CYJ tree")
    actual = {}
    for field in ("input_files_sha256", "output_files_sha256", "code_files_sha256", "paper_files_sha256"):
        for relative, expected in manifest[field].items():
            if field == "output_files_sha256":
                base = subject / "outputs/chm/q3_conditional_v8"
            elif relative.startswith(("src/cyj/", "outputs/cyj/")):
                base = subject / ".upstream/cyj-v8"
            else:
                base = subject
            path = base / relative
            if not path.is_file():
                raise ValueError(f"missing pinned file: {relative}")
            digest = sha(path)
            if digest != expected:
                raise ValueError(f"manifest mismatch: {relative}: {digest}")
            actual[relative] = digest
    return {"commit": commit, "manifest_sha256": sha(subject / "outputs/chm/q3_conditional_v8/manifest.json"),
            "checked_files": len(actual)}


def parameters(model: ConditionalV8) -> tuple[float, ...]:
    return tuple(model.b1[key] for key in ("E", "A", "B", "alpha", "beta")) + tuple(model.gamma)


def base_loss(n: float, d: float, q: float, theta: tuple[float, ...]) -> float:
    e, a, b, alpha, beta, g0, gn, gd = theta
    return e + a*n**(-alpha) + b*d**(-beta) + (1-q)*(g0+gn*math.log(n)+gd*math.log(d/100))


def solve_nd(budget: float, context: int, family: str, q: float, q0: float,
             factor: float, theta: tuple[float, ...]) -> dict | None:
    nmin, nmax = BOUNDS[0]
    dmin, dmax = BOUNDS[1]
    c = 6e18 + 2e14*context
    h = 1e9*max(quality_price(q, family)-quality_price(q0, family), 0.0)
    minimum = dmin*(c*nmin+h)
    if budget < minimum*(1-1e-12):
        return None
    nhi = min(nmax, (budget/dmin-h)/c)
    if nhi < nmin:
        return None

    def at(x: float) -> tuple[float, float, float, float]:
        n = math.exp(x)
        d = min(dmax, budget/(c*n+h))
        loss = base_loss(n, d, q, theta)*factor
        cost = d*(c*n+h)
        return loss, n, d, cost

    xs = np.linspace(math.log(nmin), math.log(nhi), 65)
    values = [at(float(x))[0] for x in xs]
    k = int(np.argmin(values))
    options = [(values[0], float(xs[0])), (values[-1], float(xs[-1]))]
    if 0 < k < len(xs)-1:
        opt = minimize_scalar(lambda x: at(x)[0], bounds=(float(xs[k-1]), float(xs[k+1])),
                              method="bounded", options={"xatol": 1e-14})
        if not opt.success:
            raise RuntimeError("independent log-N scalar refinement failed")
        options.append((float(opt.fun), float(opt.x)))
    _, best_x = min(options)
    loss, n, d, cost = at(best_x)
    return {"loss": loss, "n": n, "d": d, "q": q, "cost": cost, "minimum": minimum}


def solve_native(budget: float, context: int, family: str, q0: float,
                 theta: tuple[float, ...], factor: float) -> dict | None:
    def at(q: float) -> dict | None:
        return solve_nd(budget, context, family, q, q0, factor, theta)

    qs = np.linspace(q0, BOUNDS[2][1], 101)
    rows = [at(float(q)) for q in qs]
    valid = [(row["loss"], i, row) for i, row in enumerate(rows) if row is not None]
    if not valid:
        return None
    _, k, best = min(valid)
    lo = float(qs[max(0, k-1)])
    hi = float(qs[min(len(qs)-1, k+1)])
    if hi > lo:
        def objective(q: float) -> float:
            row = at(q)
            return row["loss"] if row is not None else math.inf

        opt = minimize_scalar(objective,
                              bounds=(lo, hi), method="bounded", options={"xatol": 1e-12})
        refined = at(float(opt.x)) if opt.success else None
        if refined is not None and refined["loss"] < best["loss"]:
            best = refined
    return best


def audit(subject: Path) -> dict:
    identity = check_manifest(subject)
    model = ConditionalV8()
    theta = parameters(model)
    policy = json.loads((subject / ".upstream/cyj-v8/outputs/cyj/q2_v8/main_policy.json").read_text(encoding="utf-8"))
    weights = policy["weights"]
    fixed_p = policy["p"]
    q0 = 0.5
    fixed_q = model.qa(fixed_p, "direct_and_near")["Q_B_proxy"]
    fixed_factor = math.exp(model.q1.weighted_effect(fixed_p, weights))
    recipes = []
    for recipe_id, point in zip(model.q1.recipe_ids, model.q1.recipes):
        p = model.q1.p_dict(point)
        if not model.q1.qa_stats(p, "quality_direct_and_near")["eligible"]:
            continue
        q = model.qa(p, "direct_and_near")["Q_B_proxy"]
        if q >= q0-1e-12:
            recipes.append((recipe_id, q, math.exp(model.q1.weighted_effect(p, weights))))

    root = subject / "outputs/chm/q3_conditional_v8"
    file_map = {"fixed": root / "fixed_policy_grid.csv",
                "joint": root / "observed_joint_grid.csv",
                "native": root / "native_Q_sensitivity_grid.csv"}
    rows = {key: load_rows(path) for key, path in file_map.items()}
    expected_keys = {(budget, context, family) for budget in BUDGETS for context in CONTEXTS for family in FAMILIES}
    for name, data in rows.items():
        keys = {(float(r["budget_FLOPs"]), int(r["context_tokens"]), r["quality_family"]) for r in data}
        if len(data) != 36 or keys != expected_keys:
            raise ValueError(f"{name}: missing/duplicate scenario cells")

    summary = {"identity": identity, "eligible_recipe_count": len(recipes), "modes": {}}
    for mode, data in rows.items():
        errors = {"loss": 0.0, "N_B": 0.0, "D_B": 0.0, "Q": 0.0,
                  "cost_relative": 0.0, "cost_component_relative": 0.0,
                  "budget_residual_relative": 0.0}
        mismatches = []
        feasible = 0
        for row in data:
            budget, context, family = float(row["budget_FLOPs"]), int(row["context_tokens"]), row["quality_family"]
            if mode == "fixed":
                solved = solve_nd(budget, context, family, fixed_q, q0, fixed_factor, theta)
                candidate = policy["recipe_index"]
            elif mode == "joint":
                candidates = ((solve_nd(budget, context, family, q, q0, factor, theta), recipe_id)
                              for recipe_id, q, factor in recipes)
                feasible_candidates = [(result, recipe_id) for result, recipe_id in candidates if result is not None]
                solved, candidate = min(feasible_candidates, key=lambda pair: (pair[0]["loss"], pair[1])) if feasible_candidates else (None, None)
                if int(row["eligible_observed_recipes"]) != len(recipes) or int(row["feasible_observed_recipes"]) != len(feasible_candidates):
                    mismatches.append(f"{budget:g}/{context}/{family}: candidate count")
            else:
                solved = solve_native(budget, context, family, q0, theta, fixed_factor)
                candidate = policy["recipe_index"]
            recorded = bool(row["N_params_B"])
            if recorded != (solved is not None):
                mismatches.append(f"{budget:g}/{context}/{family}: feasibility")
                continue
            if solved is None:
                continue
            feasible += 1
            if mode != "native" and row["recipe_index"] != candidate:
                mismatches.append(f"{budget:g}/{context}/{family}: recipe {row['recipe_index']} vs {candidate}")
            loss_key = "conditional_bridge_loss"
            q_key = "Q_score" if mode == "native" else "Q_B_proxy"
            for field, value in (("loss", solved["loss"]), ("N_B", solved["n"]),
                                 ("D_B", solved["d"]), ("Q", solved["q"])):
                published_key = {"loss": loss_key, "N_B": "N_params_B", "D_B": "D_tokens_B", "Q": q_key}[field]
                errors[field] = max(errors[field], abs(float(row[published_key])-value))
            errors["cost_relative"] = max(errors["cost_relative"], abs(float(row["C_total_FLOPs"])-solved["cost"])/budget)
            component_values = {"C_train_FLOPs": 6e18*solved["n"]*solved["d"],
                                "C_attention_FLOPs": 2e14*context*solved["n"]*solved["d"],
                                "C_quality_FLOPs": 1e9*solved["d"]*max(
                                    quality_price(solved["q"], family)-quality_price(q0, family), 0.0)}
            for component, value in component_values.items():
                error = abs(float(row[component])-value)/budget
                errors["cost_component_relative"] = max(errors["cost_component_relative"], error)
                if error > 5e-7:
                    mismatches.append(f"{budget:g}/{context}/{family}: {component}")
            residual = budget-solved["cost"]
            if mode == "native":
                errors["budget_residual_relative"] = max(
                    errors["budget_residual_relative"], abs(float(row["budget_residual_FLOPs"])+residual)/budget)
            else:
                errors["budget_residual_relative"] = max(
                    errors["budget_residual_relative"], abs(budget*(1-float(row["budget_utilization"]))-residual)/budget)
            if abs(float(row[loss_key])-solved["loss"]) > (2e-6 if mode == "native" else 5e-7):
                mismatches.append(f"{budget:g}/{context}/{family}: objective")
            if solved["cost"] > budget*(1+1e-9):
                mismatches.append(f"{budget:g}/{context}/{family}: budget")
        summary["modes"][mode] = {"cells": len(data), "independent_feasible": feasible,
                                  "published_feasible": sum(bool(r["N_params_B"]) for r in data),
                                  "max_absolute_error": errors, "mismatches": mismatches}
    summary["status"] = "PASS" if len(recipes) == 87 and all(not v["mismatches"] for v in summary["modes"].values()) else "FAIL"
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.subject_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "modes": result["modes"]}, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
