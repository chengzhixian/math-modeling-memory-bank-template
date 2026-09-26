"""Independent, read-only checks of the second-round Q4 release tables.

Run from the repository root with the pinned Q4 Python environment.
This script never imports the Q4 production module or rewrites outputs.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
Q3 = ROOT / "outputs/Q3"
Q4 = ROOT / "outputs/Q4"


def close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    if not np.isfinite(actual) or abs(actual - expected) > tolerance:
        raise AssertionError(f"{label}: {actual} != {expected}")


def score_from_source(mapping: pd.Series, loss: float, n: float, scale: float, offset: float):
    if not np.isfinite(loss) or not np.isfinite(n):
        return None, "infeasible_or_missing_upstream"
    mapped = scale * loss + offset
    if not mapping.N_min_B <= n <= mapping.N_max_B:
        return None, "N_out_of_support"
    if not mapping.loss_min <= mapped <= mapping.loss_max:
        return None, "Loss_out_of_support"
    z = np.clip(mapping.a + mapping.bLoss * mapped, -40, 40)
    return float(100 / (1 + np.exp(-z))), "conditional_affine_coordinate_assumption"


def check_maximum() -> dict:
    versions = pd.read_csv(Q4 / "prepared/leaderboard_all_versions.csv")
    versions = versions[versions.model_class.isin(["pretrained", "chat", "domain_finetuned"])].copy()
    versions.date = pd.to_datetime(versions.date, utc=True)
    backtest = pd.read_csv(Q4 / "frontier_maximum_backtest.csv")
    for key, group in backtest.groupby(["type", "test_start", "test_end"]):
        typ, start, end = key
        history = versions[versions.type.eq(typ)]
        before = history[history.date < pd.Timestamp(start, tz="UTC")]
        through = history[history.date < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]
        assert len(before) and len(through)
        close(float(group.prior_historical_record.iloc[0]), float(before.S.max()), f"{key} prior")
        close(float(group.actual_cumulative_record.iloc[0]), float(through.S.max()), f"{key} actual")
        assert (group.actual_cumulative_record >= group.prior_historical_record).all()
    scenarios = pd.read_csv(Q4 / "frontier_maximum_scenarios.csv")
    for row in scenarios.itertuples(index=False):
        history = versions[(versions.type == row.type) &
                           (versions.date <= pd.Timestamp(row.origin, tz="UTC"))]
        close(row.historical_record_score, float(history.S.max()), "scenario record")
        for suffix in ("lower", "center", "upper"):
            gap = getattr(row, f"tail_gap_{suffix}")
            predicted = min(100, max(row.historical_record_score, row.q90_score + max(0, gap)))
            close(getattr(row, f"conditional_record_{suffix}"), predicted, "scenario boundary")
    return {"backtest_rows": len(backtest), "distinct_windows": len(backtest.drop_duplicates(
        ["type", "test_start", "test_end"])), "scenario_rows": len(scenarios)}


def check_bridge() -> dict:
    definitions = [
        ("fixed_recipe", "fixed_policy_grid.csv", "Q_B_proxy"),
        ("observed_joint_recipe", "observed_joint_grid.csv", "Q_B_proxy"),
        ("independent_native_Q", "native_Q_sensitivity_grid.csv", "Q_score"),
    ]
    source = {}
    for mode, name, quality in definitions:
        table = pd.read_csv(Q3 / name)
        assert len(table) == 36
        source[mode] = (table, quality)
    mappings = pd.read_csv(Q4 / "bridge_source_coordinate_models.csv").set_index("coordinate_id")
    stress = pd.read_csv(Q4 / "q3_source_coordinate_stress.csv")
    assert len(stress) == 3 * 36 * len(mappings) * 27
    status_counts = {}
    maximum_score_difference = 0.0
    for row in stress.itertuples(index=False):
        table, quality_column = source[row.policy_mode]
        upstream = table.iloc[int(row.source_policy_row)]
        assert row.producer_status == upstream.status
        assert row.policy_mode in source
        if np.isfinite(upstream.N_params_B):
            close(row.N_params_B, upstream.N_params_B, "upstream N")
            close(row.Q_coordinate_value, upstream[quality_column], "upstream Q")
        mapping = mappings.loc[row.coordinate_id]
        value, status = score_from_source(mapping,
            upstream.conditional_bridge_loss + row.upstream_loss_stress_delta_assumed,
            upstream.N_params_B, row.coordinate_scale_assumed, row.coordinate_offset_assumed)
        baseline, baseline_status = score_from_source(mapping,
            upstream.get("B1_backbone_loss", np.nan), upstream.N_params_B,
            row.coordinate_scale_assumed, row.coordinate_offset_assumed)
        assert row.status == status and row.reference_status == baseline_status
        if value is None:
            assert pd.isna(row.conditional_score)
        else:
            difference = abs(value - row.conditional_score)
            maximum_score_difference = max(maximum_score_difference, difference)
            close(row.conditional_score, value, "source score")
        if value is None or baseline is None:
            assert pd.isna(row.conditional_gain_vs_backbone)
        else:
            close(row.conditional_gain_vs_backbone, value - baseline, "source gain")
        assert pd.isna(row.empirically_calibrated_score)
        status_counts[status] = status_counts.get(status, 0) + 1
    return {"stress_rows": len(stress), "mode_rows": stress.groupby("policy_mode").size().to_dict(),
            "status_counts": status_counts, "maximum_score_difference": maximum_score_difference}


def main() -> None:
    print(json.dumps({"maximum": check_maximum(), "bridge": check_bridge()},
                     ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
