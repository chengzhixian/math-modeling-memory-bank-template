from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


CYJ_SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CYJ_SRC))

from prepare_scaling_data import prepare_b1_rows  # noqa: E402
from scaling_common import (  # noqa: E402
    extrapolation_distance,
    fit_classic,
    group_equal_weights,
    predict_classic,
    regression_metrics,
)


class ClassicScalingHelpersTest(unittest.TestCase):
    def test_group_equal_weights_give_each_group_equal_mass(self) -> None:
        groups = ["small", "small", "large"]
        weights = group_equal_weights(groups)
        self.assertAlmostEqual(float(weights[:2].sum()), 0.5)
        self.assertAlmostEqual(float(weights[2]), 0.5)

    def test_prepare_b1_tail_split_has_no_overlap(self) -> None:
        source_rows = []
        run_id = 0
        for n_value in ("1", "2"):
            for step in range(1, 11):
                run_id += 1
                d_value = float(step)
                source_rows.append(
                    {
                        "run_id": str(run_id),
                        "N_params_B": n_value,
                        "D_tokens_B": str(d_value),
                        "C_FLOPs_1e21": str(0.006 * float(n_value) * d_value),
                        "steps": str(step),
                        "val_loss": str(3.0 - 0.01 * step),
                    }
                )
        prepared, manifest = prepare_b1_rows(source_rows, tail_fraction=0.3)
        self.assertEqual(len(prepared), 20)
        self.assertEqual(len(manifest), 2)
        for group in {row["group_id"] for row in prepared}:
            train_ids = {
                row["sample_id"]
                for row in prepared
                if row["group_id"] == group and row["token_tail_split"] == "train"
            }
            test_ids = {
                row["sample_id"]
                for row in prepared
                if row["group_id"] == group and row["token_tail_split"] == "test"
            }
            self.assertEqual(len(train_ids), 7)
            self.assertEqual(len(test_ids), 3)
            self.assertTrue(train_ids.isdisjoint(test_ids))

    def test_classic_fit_recovers_noiseless_predictions(self) -> None:
        n_grid = np.array([0.1, 0.3, 1.0, 3.0, 10.0, 20.0])
        d_grid = np.array([1.0, 3.0, 10.0, 30.0, 100.0, 300.0])
        n_values = np.repeat(n_grid, d_grid.size)
        d_values = np.tile(d_grid, n_grid.size)
        groups = [f"N={value}" for value in np.repeat(n_grid, d_grid.size)]
        true_parameters = {
            "E": 1.5,
            "A": 0.7,
            "B": 1.2,
            "alpha": 0.25,
            "beta": 0.3,
        }
        losses = predict_classic(true_parameters, n_values, d_values)
        result = fit_classic(
            n_values,
            d_values,
            losses,
            groups,
            seed=7,
            starts=8,
            max_iterations=1800,
        )
        predictions = predict_classic(result.parameters, n_values, d_values)
        metrics = regression_metrics(losses, predictions)
        self.assertLess(metrics["rmse"], 1e-5)
        self.assertTrue(all(value > 0 for value in result.parameters.values()))

    def test_extrapolation_distance_zero_inside_positive_outside(self) -> None:
        distance = extrapolation_distance(
            np.array([1.0, 0.5, 20.0]),
            np.array([10.0, 10.0, 1000.0]),
            n_min=1.0,
            n_max=10.0,
            d_min=5.0,
            d_max=100.0,
        )
        self.assertEqual(float(distance[0]), 0.0)
        self.assertGreater(float(distance[1]), 0.0)
        self.assertGreater(float(distance[2]), 0.0)


if __name__ == "__main__":
    unittest.main()
