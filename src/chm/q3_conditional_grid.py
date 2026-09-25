"""B-native Q3 budget allocation on CYJ v7's frozen B7 support."""
from __future__ import annotations

import csv
import math
from pathlib import Path
import sys

from q3_generic_solver import Support, cost_and_grad, enrich_kkt
from q3_joint_certificate import certify
from q3_quality_cost_geometry import FAMILIES, delta_g
from q3_v7_inputs import load_release


ROOT = Path(__file__).resolve().parents[2]
CONTEXTS = (2048, 8192, 131072)
OFFICIAL_BUDGETS = (1e19, 1e22, 1e24)
EXTRA_BUDGETS = (1e20,)


class B7Adapter:
    def __init__(self, cyj_root: Path = ROOT / ".upstream/cyj-v7"):
        self.release = load_release(cyj_root)
        self.module = sys.modules[self.release.__class__.__module__]
        self.support = Support(*self.module.BOUNDS)
        self.theta = self.module.THETA

    def value_grad(self, n: float, d: float, q: float):
        values = []
        for value, (lo, hi) in zip((n, d, q), (self.support.N, self.support.D, self.support.Q)):
            if value < lo and lo - value <= 8 * max(1.0, abs(lo)) * sys.float_info.epsilon:
                value = lo
            if value > hi and value - hi <= 8 * max(1.0, abs(hi)) * sys.float_info.epsilon:
                value = hi
            values.append(value)
        return self.module.b7(*values)


def solve_scenario(
    model: B7Adapter,
    budget: float,
    context: int,
    family: str,
    q0: float = 0.5,
    tolerance: float = 1e-7,
) -> dict:
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be finite and positive")
    if context not in CONTEXTS or family not in FAMILIES:
        raise ValueError("context or quality family outside declared scenarios")
    if not model.support.Q[0] <= q0 < model.support.Q[1]:
        raise ValueError("Q0 outside B7 support")
    minimum = (6e18 + 2e14 * context) * model.support.N[0] * model.support.D[0]
    common = {
        "budget_FLOPs": budget,
        "context_tokens": context,
        "quality_family": family,
        "Q0_scenario": q0,
        "minimum_cost_FLOPs": minimum,
        "model_scope": "B7_semi_synthetic_conditional",
        "cross_source_empirical_calibration_complete": False,
    }
    if budget < minimum * (1 - 1e-12):
        return {**common, "status": "infeasible_within_B7_support", "B_native_loss": None,
                "N_params_B": None, "D_tokens_B": None, "Q_score": None,
                "kkt_check_pass": None, "global_gap": None}
    certificate = certify(model.theta, (model.support.N, model.support.D, model.support.Q),
                          budget, context, family, q0=q0, tolerance=tolerance)
    if not certificate["feasible"]:
        raise RuntimeError("certificate disagrees with minimum-cost check")
    n, d, q = (certificate["N_params_B"], certificate["D_tokens_B"], certificate["Q_score"])
    solution = enrich_kkt({"N_params_B": n, "D_tokens_B": d, "Q": q}, model,
                          budget, context, q0, family)
    if not solution["kkt_check_pass"]:
        raise RuntimeError("B7 numerical solution failed KKT check")
    train = 6e18 * n * d
    attention = 2e14 * context * n * d
    quality = 1e9 * d * delta_g(q, q0, family)
    total = train + attention + quality
    canonical_cost, _ = cost_and_grad(n, d, q, q0, context, family)
    if abs(total - canonical_cost) > 1e-10 * max(total, 1):
        raise RuntimeError("cost breakdown disagrees with CHM cost function")
    if total > budget * (1 + 1e-8):
        raise RuntimeError("budget violated")
    return {
        **common,
        "status": "conditional_B_native_feasible",
        "N_params_B": n,
        "D_tokens_B": d,
        "Q_score": q,
        "B_native_loss": solution["loss"],
        "C_train_FLOPs": train,
        "C_quality_FLOPs": quality,
        "C_attention_FLOPs": attention,
        "C_total_FLOPs": total,
        "budget_residual_FLOPs": total - budget,
        "budget_utilization": total / budget,
        "active_set": ";".join(sorted(solution["active_set"])),
        "kkt_check_pass": True,
        "kkt_relative_violation": solution["kkt_relative_violation"],
        "global_lower_bound": certificate["global_lower_bound"],
        "global_upper_bound": certificate["feasible_upper_bound"],
        "global_gap": certificate["global_gap"],
        "certificate_kind": "floating_point_B7_reduction",
    }


def main_grid(model: B7Adapter) -> list[dict]:
    """The three requested budget scales plus one intermediate diagnostic scale."""
    budgets = tuple(sorted(OFFICIAL_BUDGETS + EXTRA_BUDGETS))
    return [solve_scenario(model, budget, context, family)
            for budget in budgets for context in CONTEXTS for family in FAMILIES]


def structural_state(row: dict) -> str:
    """Stable regime signature; the all-upper corner absorbs budget equality."""
    flags = set(row["active_set"].split(";"))
    if {"N_max", "D_max", "Q1"} <= flags:
        flags.discard("budget")
    return ";".join(sorted(flags))


def transition_pairs(rows: list[dict]) -> list[dict]:
    """Bracket active-set changes only between feasible neighboring budgets."""
    groups: dict[tuple[int, str], list[dict]] = {}
    for row in rows:
        key = (row["context_tokens"], row["quality_family"])
        groups.setdefault(key, []).append(row)
    brackets = []
    for (context, family), group in sorted(groups.items()):
        feasible = sorted((r for r in group if r["status"] == "conditional_B_native_feasible"),
                          key=lambda r: r["budget_FLOPs"])
        for left, right in zip(feasible, feasible[1:]):
            if structural_state(left) != structural_state(right):
                brackets.append({"context_tokens": context, "quality_family": family,
                                 "budget_left": left["budget_FLOPs"],
                                 "budget_right": right["budget_FLOPs"],
                                 "active_left": structural_state(left),
                                 "active_right": structural_state(right)})
    return brackets


def refine_transition(left: dict, right: dict, solve_at_budget,
                      relative_width: float = 1e-5) -> dict:
    """Bisect one observed active-set change on a logarithmic budget axis."""
    if structural_state(left) == structural_state(right):
        raise ValueError("transition endpoints have the same active set")
    if not 0 < relative_width < 1:
        raise ValueError("invalid relative width")
    lo, hi = left, right
    while hi["budget_FLOPs"] / lo["budget_FLOPs"] - 1 > relative_width:
        middle = solve_at_budget(math.sqrt(lo["budget_FLOPs"] * hi["budget_FLOPs"]))
        if middle["status"] != "conditional_B_native_feasible":
            raise RuntimeError("transition refinement left feasible support")
        if structural_state(middle) == structural_state(lo):
            lo = middle
        elif structural_state(middle) == structural_state(hi):
            hi = middle
        else:
            raise RuntimeError("unresolved intermediate active set; refine the scan grid")
    return {"context_tokens": lo["context_tokens"], "quality_family": lo["quality_family"],
            "budget_left": lo["budget_FLOPs"], "budget_right": hi["budget_FLOPs"],
            "active_left": structural_state(lo), "active_right": structural_state(hi),
            "relative_width": hi["budget_FLOPs"] / lo["budget_FLOPs"] - 1}


def scan_group(model: B7Adapter, context: int, family: str, points: int = 161,
               tolerance: float = 1e-6) -> list[dict]:
    if points < 3 or points % 2 != 1:
        raise ValueError("scan points must be odd and at least 3")
    rows = [solve_scenario(model, 10 ** (19 + 5 * i / (points - 1)), context,
                           family, tolerance=tolerance) for i in range(points)]
    feasible = [r["B_native_loss"] for r in rows if r["B_native_loss"] is not None]
    if any(b > a + 1e-7 for a, b in zip(feasible, feasible[1:])):
        raise RuntimeError("B-native loss increased with budget")
    return rows


def midpoint_refine(rows: list[dict], solve_at_budget) -> list[dict]:
    """Probe every gap, including equal-endpoint gaps hiding a short state."""
    if len(rows) < 2:
        raise ValueError("need at least two scan rows")
    refined = []
    for left, right in zip(rows, rows[1:]):
        refined.append(left)
        refined.append(solve_at_budget(math.sqrt(left["budget_FLOPs"] * right["budget_FLOPs"])))
    refined.append(rows[-1])
    return refined


def scan_all(model: B7Adapter, initial_points: int = 161) -> tuple[list[dict], list[dict], list[dict]]:
    """Dense scan, coarse/fine signature agreement, then transition bracketing."""
    rows, transitions, resolution = [], [], []
    for context in CONTEXTS:
        for family in FAMILIES:
            group = scan_group(model, context, family, points=initial_points)
            refinements = 0
            while True:
                solve = lambda budget: solve_scenario(model, budget, context, family,
                                                      tolerance=1e-6)
                fine_group = midpoint_refine(group, solve)
                full = [(x["active_left"], x["active_right"]) for x in transition_pairs(fine_group)]
                coarse = [(x["active_left"], x["active_right"]) for x in transition_pairs(group)]
                refinements += 1
                if full == coarse:
                    group = fine_group
                    break
                if len(fine_group) >= 1281:
                    raise RuntimeError(f"unresolved transition resolution: {context}/{family}")
                group = fine_group
            resolution.append({"context_tokens": context, "quality_family": family,
                               "fine_points": len(group), "coarse_points": (len(group) + 1) // 2,
                               "refinements": refinements,
                               "transition_signatures_agree": True})
            by_budget = {r["budget_FLOPs"]: r for r in group}
            for pair in transition_pairs(group):
                transitions.append(refine_transition(by_budget[pair["budget_left"]],
                                                     by_budget[pair["budget_right"]], solve))
            rows.extend(group)
    return rows, transitions, resolution


def write_table(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("cannot write empty table")
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def generate_tables(out_dir: Path = ROOT / "outputs/chm/q3_conditional_v1") -> None:
    model = B7Adapter()
    main = main_grid(model)
    scan, transitions, resolution = scan_all(model)
    write_table(out_dir / "optimization.csv", main)
    write_table(out_dir / "budget_scan.csv", scan)
    write_table(out_dir / "transitions.csv", transitions)
    write_table(out_dir / "resolution_check.csv", resolution)


if __name__ == "__main__":
    generate_tables()
