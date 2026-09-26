"""Q3 fixed-policy allocations under CYJ's pinned, uncalibrated v8 scenario.

Q is the v8 proxy derived from p. For a fixed Q1/Q2 policy there are only two
remaining decisions, N and D. Loss decreases in D; eliminate it using the
budget and minimize the resulting convex function of log N.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys

from q3_generic_solver import Support, cost_and_grad
from q3_native_q_solver import solve_scenario as solve_native_q
from q3_quality_cost_geometry import CONTEXTS, FAMILIES, delta_g
from q3_v8_inputs import EXPORT, ROOT, load_v8, digest


OFFICIAL_BUDGETS = (1e19, 1e22, 1e24)
EXTRA_BUDGETS = (1e20,)
OUTPUT = ROOT / "outputs/Q3"


class V8NativeQAdapter:
    """Use v8's B1+B7 backbone with Q_B as an independent sensitivity input."""

    def __init__(self, model, bounds):
        self.model = model
        self.support = Support(*bounds)
        self.theta = tuple(model.b1[key] for key in ("E", "A", "B", "alpha", "beta")) + tuple(model.gamma)

    def value_grad(self, n: float, d: float, q: float):
        values = []
        for value, (lo, hi) in zip((n, d, q), (self.support.N, self.support.D, self.support.Q)):
            margin = 8*max(1.0, abs(value))*sys.float_info.epsilon
            if lo-margin <= value < lo:
                value = lo
            if hi < value <= hi+margin:
                value = hi
            values.append(value)
        value, gradient, _ = self.model.base(*values)
        return value, gradient


def main_policy(model, export: Path = EXPORT) -> dict:
    path = Path(export) / "outputs/Q2/main_policy.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["policy"] != "observed_512_plus_quality_direct_and_near":
        raise ValueError("CYJ v8 main p policy changed")
    support = model.q1.support(record["p"], "observed_512")
    quality = model.q1.qa_stats(record["p"], "quality_direct_and_near")
    if support["observed_index"] != record["recipe_index"] or not quality["eligible"]:
        raise ValueError("CYJ v8 main recipe lacks declared Q1 support")
    actual = model.qa(record["p"], record["quality_mapping_policy"])["Q_B_proxy"]
    if not math.isclose(actual, record["Q_B_proxy"], rel_tol=0, abs_tol=1e-12):
        raise ValueError("CYJ v8 main recipe quality proxy changed")
    return record


def _convex_prerequisites(model, bounds) -> None:
    a = model.b1
    g0, gn, gd = model.gamma
    if min(a[k] for k in ("A", "B", "alpha", "beta")) <= 0 or gn > 0 or gd > 0:
        raise ValueError("v8 fixed-quality convexity conditions are not met")
    gain = min(g0 + gn*math.log(n) + gd*math.log(d/100)
               for n in bounds[0] for d in bounds[1])
    if gain <= 0:
        raise ValueError("v8 quality gain changes sign on support")


def solve_fixed_p(model, bounds, p: dict, weights: dict, *, p_policy: str,
                  mapping_policy: str, budget: float, context: int, family: str,
                  q0: float = 0.5, recipe_index: str | None = None,
                  quality_bridge_scale: float = 1.0,
                  mixture_bridge_lambda: float = 1.0) -> dict:
    if not math.isfinite(budget) or budget <= 0 or context not in CONTEXTS or family not in FAMILIES:
        raise ValueError("invalid Q3 scenario")
    if not math.isfinite(q0) or not 0 < q0 <= 1:
        raise ValueError("invalid Q0")
    if not math.isfinite(quality_bridge_scale) or not 0 < quality_bridge_scale <= 2:
        raise ValueError("invalid A-to-B quality bridge scale")
    if not math.isfinite(mixture_bridge_lambda) or mixture_bridge_lambda < 0:
        raise ValueError("invalid mixture bridge strength")
    _convex_prerequisites(model, bounds)
    model.q1.support(p, p_policy)
    model.q1.weight_vector(weights)
    proxy = model.qa(p, mapping_policy, quality_bridge_scale)
    q = proxy["Q_B_proxy"]
    n_min, n_max = bounds[0]
    d_min, d_max = bounds[1]
    c = 6e18 + 2e14*context
    common = {"budget_FLOPs": budget, "context_tokens": context, "quality_family": family,
              "Q0_scenario": q0, "Q_B_proxy": q, "Q_A_mapped": proxy["Q_A_mapped"],
              "mapped_coverage": proxy["mapped_coverage"], "p_policy": p_policy,
              "quality_mapping_policy": mapping_policy, "recipe_index": recipe_index,
              "cross_source_empirical_calibration_complete": False,
              "Q1_p_source": "CYJ_v8_Q1_v2_derived_policy",
              "uncertainty_scope": "no_joint_A_B_or_bridge_interval"}
    if q < q0 - 1e-12:
        return {**common, "status": "policy_quality_below_Q0", "minimum_cost_FLOPs": None,
                "N_params_B": None, "D_tokens_B": None, "conditional_bridge_loss": None}
    h = 1e9*delta_g(q, q0, family)
    minimum = d_min*(c*n_min+h)
    if budget < minimum*(1-1e-12):
        return {**common, "status": "infeasible_within_v8_support", "minimum_cost_FLOPs": minimum,
                "N_params_B": None, "D_tokens_B": None, "conditional_bridge_loss": None}
    n_hi = min(n_max, (budget/d_min-h)/c)
    if n_hi < n_min:
        raise RuntimeError("minimum-cost check disagrees with feasible N range")

    def at(x: float) -> tuple[float, float, float, float]:
        n = min(n_hi, max(n_min, math.exp(x)))
        d_unconstrained = budget/(c*n+h)
        d = min(d_max, max(d_min, d_unconstrained))
        if d_unconstrained < d_min*(1-1e-12):
            raise RuntimeError("fixed-p reduction left the supported D range")
        base, grad, _ = model.base(n, d, q)
        dy_dx = 0.0 if d_unconstrained >= d_max else -c*n/(c*n+h)
        slope = n*grad[0] + d*grad[1]*dy_dx
        return base, slope, n, d

    left, right = math.log(n_min), math.log(n_hi)
    left_value, left_slope, _, _ = at(left)
    right_value, right_slope, _, _ = at(right)
    if left_slope >= 0:
        x, lower = left, left_value
    elif right_slope <= 0:
        x, lower = right, right_value
    else:
        for _ in range(75):
            middle = (left+right)/2
            if at(middle)[1] < 0:
                left = middle
            else:
                right = middle
        x = min((left, right), key=lambda value: at(value)[0])
        vl, gl, _, _ = at(left)
        vr, gr, _, _ = at(right)
        width = right-left
        lower = max(vl+min(0.0, gl*width), vr+min(0.0, -gr*width))
    base, slope, n, d = at(x)
    if quality_bridge_scale == 1.0 and mixture_bridge_lambda == 1.0:
        predicted = model.predict_baseline_v8(n, d, p, weights, p_policy=p_policy,
                                              quality_mapping_policy=mapping_policy)
    else:
        predicted = model.evaluate(n, d, p, weights, p_policy=p_policy,
                                   quality_mapping_policy=mapping_policy,
                                   quality_mode="q1_quality_bridge_sensitivity",
                                   quality_bridge_scale=quality_bridge_scale,
                                   mixture_bridge_lambda=mixture_bridge_lambda)
    if not math.isclose(predicted["NDQ_loss"], base, rel_tol=1e-12):
        raise RuntimeError("v8 producer and CHM fixed-p objective differ")
    cost, _ = cost_and_grad(n, d, q, q0, context, family)
    train = 6e18*n*d
    attention = 2e14*context*n*d
    quality = d*h
    if not math.isclose(train+attention+quality, cost, rel_tol=1e-12):
        raise RuntimeError("Q3 three-part cost does not sum")
    if cost > budget*(1+1e-9) or lower > base+1e-9:
        raise RuntimeError("Q3 fixed-p solution failed feasibility or bound")
    active = []
    if math.isclose(n, n_min, rel_tol=1e-8): active.append("N_min")
    if math.isclose(n, n_max, rel_tol=1e-8): active.append("N_max")
    if math.isclose(d, d_min, rel_tol=1e-8): active.append("D_min")
    if math.isclose(d, d_max, rel_tol=1e-8): active.append("D_max")
    if math.isclose(cost, budget, rel_tol=1e-8): active.append("budget")
    factor = predicted["mixture_bridge_factor"]
    return {**common, "status": "conditional_v8_fixed_policy_feasible",
            "minimum_cost_FLOPs": minimum, "N_params_B": n, "D_tokens_B": d,
            "B1_backbone_loss": predicted["B1_backbone_loss"],
            "v8_NDQ_proxy_loss": base, "conditional_bridge_loss": predicted["Loss"],
            "Q1_weighted_effect": predicted["Q1_weighted_effect"], "bridge_factor": factor,
            "C_train_FLOPs": train, "C_attention_FLOPs": attention,
            "C_quality_FLOPs": quality, "C_total_FLOPs": cost,
            "budget_utilization": cost/budget, "active_set": ";".join(active),
            "fixed_p_convex_lower_bound": lower*factor,
            "fixed_p_convex_gap": (base-lower)*factor,
            "fixed_p_logN_slope": slope,
            "numeric_certificate_kind": "convex_logN_reduction_floating_point"}


def main_grid(model=None, bounds=None, policy=None) -> list[dict]:
    if model is None:
        model, bounds = load_v8()
    if policy is None:
        policy = main_policy(model)
    return [solve_fixed_p(model, bounds, policy["p"], policy["weights"],
                          p_policy="observed_512", mapping_policy=policy["quality_mapping_policy"],
                          budget=budget, context=context, family=family,
                          recipe_index=policy["recipe_index"])
            for budget in sorted(OFFICIAL_BUDGETS+EXTRA_BUDGETS)
            for context in CONTEXTS for family in FAMILIES]


def observed_joint_grid(model, bounds, fixed_rows: list[dict], q0: float = 0.5,
                        quality_bridge_scale: float = 1.0,
                        mixture_bridge_lambda: float = 1.0) -> list[dict]:
    """Exactly enumerate eligible A4 recipes; each fixed-p N/D solve is convex.

    This is a conditional finite-policy result, not a continuous-hull optimum.
    """
    mapping = "direct_and_near"
    weights = {target: 1/len(model.q1.targets) for target in model.q1.targets}
    candidates = []
    for recipe_id, vector in zip(model.q1.recipe_ids, model.q1.recipes):
        p = model.q1.p_dict(vector)
        if not model.q1.qa_stats(p, "quality_direct_and_near")["eligible"]:
            continue
        if model.qa(p, mapping, quality_bridge_scale)["Q_B_proxy"] < q0-1e-12:
            continue
        candidates.append((recipe_id, p))
    if not candidates:
        raise RuntimeError("no Q1 observed recipe meets Q3 quality policy")
    joint = []
    for fixed in fixed_rows:
        rows = [solve_fixed_p(model, bounds, p, weights, p_policy="observed_512",
                              mapping_policy=mapping, budget=fixed["budget_FLOPs"],
                              context=fixed["context_tokens"], family=fixed["quality_family"],
                              q0=q0, recipe_index=recipe_id,
                              quality_bridge_scale=quality_bridge_scale,
                              mixture_bridge_lambda=mixture_bridge_lambda)
                for recipe_id, p in candidates]
        feasible = [row for row in rows if row["status"] == "conditional_v8_fixed_policy_feasible"]
        common = {"budget_FLOPs": fixed["budget_FLOPs"],
                  "context_tokens": fixed["context_tokens"],
                  "quality_family": fixed["quality_family"],
                  "Q0_scenario": q0,
                  "eligible_observed_recipes": len(candidates),
                  "feasible_observed_recipes": len(feasible),
                  "candidate_set": "A4_observed_512_Q1_direct_and_near_Qproxy_at_least_Q0",
                  "cross_source_empirical_calibration_complete": False,
                  "claim_scope": "conditional_finite_recipe_optimum_not_continuous_hull_or_empirical_bridge"}
        if not feasible:
            joint.append({**common, "status": "infeasible_within_v8_support"})
            continue
        best = min(feasible, key=lambda row: (row["conditional_bridge_loss"], row["recipe_index"]))
        joint.append({**common, **{key: best[key] for key in (
            "status", "recipe_index", "N_params_B", "D_tokens_B", "Q_B_proxy",
            "Q_A_mapped", "mapped_coverage", "B1_backbone_loss", "v8_NDQ_proxy_loss",
            "conditional_bridge_loss", "Q1_weighted_effect", "bridge_factor",
            "C_train_FLOPs", "C_attention_FLOPs", "C_quality_FLOPs", "C_total_FLOPs",
            "budget_utilization", "active_set", "fixed_p_convex_gap")},
            "fixed_Q2_recipe_172_status": fixed["status"],
            "fixed_Q2_recipe_172_loss": fixed.get("conditional_bridge_loss"),
            "fixed_policy_regret": (fixed["conditional_bridge_loss"]-best["conditional_bridge_loss"]
                                    if fixed["status"] == "conditional_v8_fixed_policy_feasible" else None)})
    return joint


def native_q_sensitivity_grid(model, bounds, policy: dict) -> list[dict]:
    """Independently allocate Q_B; v8 labels this mode sensitivity, not baseline."""
    adapter = V8NativeQAdapter(model, bounds)
    rows = []
    for budget in sorted(OFFICIAL_BUDGETS+EXTRA_BUDGETS):
        for context in CONTEXTS:
            for family in FAMILIES:
                solved = solve_native_q(adapter, budget, context, family)
                base = solved.pop("B_native_loss")
                solved["model_scope"] = "CYJ_v8_native_QB_sensitivity"
                solved["recipe_index"] = policy["recipe_index"]
                solved["p_policy"] = "observed_512"
                solved["cross_source_empirical_calibration_complete"] = False
                if solved["status"] == "conditional_B_native_feasible":
                    for key, (lo, hi) in zip(("N_params_B", "D_tokens_B", "Q_score"), bounds):
                        value = solved[key]
                        if value < lo and lo-value <= 8*max(1.0, abs(lo))*sys.float_info.epsilon:
                            solved[key] = lo
                        if value > hi and value-hi <= 8*max(1.0, abs(hi))*sys.float_info.epsilon:
                            solved[key] = hi
                    result = model.evaluate(solved["N_params_B"], solved["D_tokens_B"],
                                            policy["p"], policy["weights"],
                                            p_policy="observed_512",
                                            quality_mode="native_QB_sensitivity",
                                            native_QB=solved["Q_score"])
                    if not math.isclose(result["NDQ_loss"], base, rel_tol=1e-10):
                        raise RuntimeError("CYJ v8 native Q result differs from CHM optimizer")
                    solved["status"] = "conditional_v8_native_Q_sensitivity_feasible"
                    solved["v8_NDQ_native_loss"] = base
                    solved["conditional_bridge_loss"] = result["Loss"]
                    solved["bridge_factor"] = result["mixture_bridge_factor"]
                else:
                    solved["status"] = "infeasible_within_v8_native_Q_support"
                    solved["v8_NDQ_native_loss"] = None
                    solved["conditional_bridge_loss"] = None
                rows.append(solved)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate(out_dir: Path = OUTPUT) -> dict:
    model, bounds = load_v8()
    policy = main_policy(model)
    rows = main_grid(model, bounds, policy)
    write_csv(out_dir / "fixed_policy_grid.csv", rows)
    joint = observed_joint_grid(model, bounds, rows)
    write_csv(out_dir / "observed_joint_grid.csv", joint)
    native = native_q_sensitivity_grid(model, bounds, policy)
    write_csv(out_dir / "native_Q_sensitivity_grid.csv", native)
    return {"rows": len(rows), "feasible": sum(r["status"] == "conditional_v8_fixed_policy_feasible" for r in rows),
            "policy_recipe": policy["recipe_index"],
            "grid_sha256": digest(out_dir / "fixed_policy_grid.csv"),
            "joint_feasible": sum(r["status"] == "conditional_v8_fixed_policy_feasible" for r in joint),
            "joint_grid_sha256": digest(out_dir / "observed_joint_grid.csv"),
            "native_Q_feasible": sum(r["status"] == "conditional_v8_native_Q_sensitivity_feasible" for r in native),
            "native_Q_grid_sha256": digest(out_dir / "native_Q_sensitivity_grid.csv")}


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False))
