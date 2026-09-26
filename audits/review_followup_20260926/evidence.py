"""Read-only follow-up calculations for the a19039b review findings.

Run from the repository root with .venv/Scripts/python.exe.
"""
from __future__ import annotations

import csv
import calendar
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/cyj"))
from ndqp_scenarios_v8 import ConditionalV8  # noqa: E402


def rows(path: str) -> list[dict]:
    with (ROOT / path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def q2_joint_contrasts() -> list[dict]:
    model = ConditionalV8()
    center = np.mean(model.q1.recipes, axis=0)
    weights = {target: 1 / len(model.q1.targets) for target in model.q1.targets}
    # Fixed donor, reference mix, N/D and step define an operational comparison.
    donor = "pile_cc"
    pairs = [("gutenberg_pg_19", "europarl"), ("arxiv", "freelaw"),
             ("arxiv", "github"), ("wikipedia_en", "freelaw")]
    output = []
    for left, right in pairs:
        for step, quality_scale, mixture_lambda in ((0.002, 1.0, 1.0),
                                                    (0.005, 1.0, 1.0),
                                                    (0.01, 1.0, 1.0),
                                                    (0.005, 0.5, 1.0),
                                                    (0.005, 1.5, 1.0),
                                                    (0.005, 1.0, 0.0),
                                                    (0.005, 1.0, 2.0)):
            def loss(left_on: bool, right_on: bool) -> float:
                point = center.copy()
                for name, active in ((left, left_on), (right, right_on)):
                    if active:
                        point[model.q1.domains.index(name)] += step
                        point[model.q1.domains.index(donor)] -= step
                return model.evaluate(
                    1.0, 100.0, model.q1.p_dict(point), weights,
                    p_policy="convex_hull", quality_bridge_scale=quality_scale,
                    quality_mode="q1_quality_bridge_sensitivity" if quality_scale != 1.0 else "q1_quality_baseline",
                    mixture_bridge_lambda=mixture_lambda)["Loss"]

            try:
                l00, l10, l01, l11 = loss(False, False), loss(True, False), loss(False, True), loss(True, True)
                contrast = l11 - l10 - l01 + l00
                output.append({"left": left, "right": right, "donor": donor,
                               "step": step, "quality_scale": quality_scale,
                               "mixture_lambda": mixture_lambda,
                               "joint_minus_separate_loss": contrast,
                               "label": "complementary_under_fixed_donor" if contrast < -1e-10 else
                                        "substitutive_under_fixed_donor" if contrast > 1e-10 else "locally_neutral",
                               "delta_left": l10 - l00, "delta_right": l01 - l00,
                               "delta_joint": l11 - l00})
            except ValueError as exc:
                output.append({"left": left, "right": right, "donor": donor,
                               "step": step, "quality_scale": quality_scale,
                               "mixture_lambda": mixture_lambda, "status": str(exc)})
    return output


def q4_frontier_tops() -> list[dict]:
    data = rows("outputs/Q4/prepared/leaderboard_sample.csv")
    output = []
    for kind in ("pretrained", "non_pretrained"):
        accepted = {"pretrained"} if kind == "pretrained" else {"chat", "domain_finetuned"}
        subset = [r for r in data if r["model_class"] in accepted and r["S"] and r["date"]]
        latest = max(datetime.fromisoformat(r["date"]) for r in subset)
        month_index = latest.year * 12 + latest.month - 1 - 2
        year, month_zero = divmod(month_index, 12)
        month = month_zero + 1
        cutoff = latest.replace(year=year, month=month,
                                day=min(latest.day, calendar.monthrange(year, month)[1]))
        recent = [r for r in subset if datetime.fromisoformat(r["date"]) > cutoff]
        output.append({"type": kind, "n": len(subset), "latest_submission": latest.strftime("%Y-%m-%d"),
                       "all_time_max": max(float(r["S"]) for r in subset),
                       "recent_two_month_max": max(float(r["S"]) for r in recent),
                       "recent_two_month_q90": float(np.quantile([float(r["S"]) for r in recent], .9)),
                       "recent_n": len(recent)})
    return output


def q4_bridge_examples() -> list[dict]:
    bridge = rows("outputs/Q4/q3_bridge_conclusion_sensitivity.csv")
    grid = rows("outputs/Q3/fixed_policy_grid.csv")
    output = []
    for coordinate in ("Qwen2 Technical Report (Alibaba, 2024), validation loss",
                       "Qwen2.5 Technical Report (Alibaba, 2024), validation loss"):
        for budget in (1e22, 1e24):
            selected = [r for r in bridge if r["coordinate_id"] == coordinate
                        and float(r["budget_FLOPs"]) == budget
                        and r["context_tokens"] == "8192" and r["quality_family"] == "power"]
            if not selected:
                continue
            row = selected[0]
            upstream = grid[int(row["policy_row"])]
            output.append({"coordinate": coordinate, "budget": budget, "context": 8192,
                           "policy": "fixed_recipe_172_power", "N_B": upstream["N_params_B"],
                           "D_B": upstream["D_tokens_B"], "Q_proxy": upstream["Q_B_proxy"],
                           "conditional_Loss": upstream["conditional_bridge_loss"],
                           "status": row["nominal_status"], "score": row["nominal_score"],
                           "score_range": [row["score_min"], row["score_max"]],
                           "gain_range": [row["gain_min"], row["gain_max"]],
                           "gain_sign_robust": row["gain_sign_robust_within_supported_grid"]})
    return output


def main() -> None:
    result = {"q2_joint_contrasts": q2_joint_contrasts(),
              "q4_frontier_tops": q4_frontier_tops(),
              "q4_bridge_examples": q4_bridge_examples()}
    target = Path(__file__).with_name("computed_evidence.json")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target.relative_to(ROOT)),
                      "contrast_rows": len(result["q2_joint_contrasts"]),
                      "bridge_rows": len(result["q4_bridge_examples"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
