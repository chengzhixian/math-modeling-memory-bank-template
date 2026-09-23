"""Shared numerical helpers for CYJ's classic scaling-law baseline.

The implementation deliberately depends only on NumPy.  The bundled runtime
does not contain SciPy, so the positive nonlinear model is fitted with a small,
deterministic multi-start Nelder-Mead implementation instead of silently
changing environments.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Iterable

import numpy as np


PARAMETER_NAMES = ("E", "A", "B", "alpha", "beta")
LOG_PARAMETER_BOUNDS = np.log(
    np.array(
        [
            [0.05, 10.0],
            [1e-4, 100.0],
            [1e-4, 100.0],
            [0.005, 2.0],
            [0.005, 2.0],
        ],
        dtype=float,
    )
)


@dataclass(frozen=True)
class FitResult:
    parameters: dict[str, float]
    objective: float
    iterations: int
    converged: bool
    starts: int
    seed: int
    huber_delta: float
    best_start_index: int
    candidate_objectives: list[float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def predict_classic(
    parameters: dict[str, float], n_values: np.ndarray, d_values: np.ndarray
) -> np.ndarray:
    n_values = np.asarray(n_values, dtype=float)
    d_values = np.asarray(d_values, dtype=float)
    return (
        parameters["E"]
        + parameters["A"] * np.power(n_values, -parameters["alpha"])
        + parameters["B"] * np.power(d_values, -parameters["beta"])
    )


def group_equal_weights(groups: Iterable[str]) -> np.ndarray:
    group_array = np.asarray(list(groups), dtype=str)
    if group_array.size == 0:
        raise ValueError("groups must not be empty")
    unique, counts = np.unique(group_array, return_counts=True)
    count_by_group = dict(zip(unique, counts, strict=True))
    weights = np.array(
        [1.0 / (len(unique) * count_by_group[group]) for group in group_array],
        dtype=float,
    )
    return weights / weights.sum()


def huber(values: np.ndarray, delta: float) -> np.ndarray:
    absolute = np.abs(values)
    return np.where(
        absolute <= delta,
        0.5 * np.square(values),
        delta * (absolute - 0.5 * delta),
    )


def classic_objective(
    log_parameters: np.ndarray,
    n_values: np.ndarray,
    d_values: np.ndarray,
    losses: np.ndarray,
    weights: np.ndarray,
    huber_delta: float,
) -> float:
    log_parameters = np.asarray(log_parameters, dtype=float)
    if log_parameters.shape != (5,):
        return float("inf")
    if np.any(log_parameters < LOG_PARAMETER_BOUNDS[:, 0]) or np.any(
        log_parameters > LOG_PARAMETER_BOUNDS[:, 1]
    ):
        return float("inf")
    values = np.exp(log_parameters)
    parameters = dict(zip(PARAMETER_NAMES, values, strict=True))
    predictions = predict_classic(parameters, n_values, d_values)
    if np.any(~np.isfinite(predictions)) or np.any(predictions <= 0):
        return float("inf")
    residuals = np.log(predictions) - np.log(losses)
    return float(np.sum(weights * huber(residuals, huber_delta)))


def nelder_mead(
    objective: Callable[[np.ndarray], float],
    start: np.ndarray,
    *,
    step: float = 0.15,
    max_iterations: int = 1600,
    x_tolerance: float = 1e-8,
    f_tolerance: float = 1e-12,
) -> tuple[np.ndarray, float, int, bool]:
    start = np.asarray(start, dtype=float)
    dimensions = start.size
    simplex = np.tile(start, (dimensions + 1, 1))
    for index in range(dimensions):
        simplex[index + 1, index] += step
    values = np.array([objective(point) for point in simplex], dtype=float)

    reflection = 1.0
    expansion = 2.0
    contraction = 0.5
    shrink = 0.5

    for iteration in range(1, max_iterations + 1):
        order = np.argsort(values)
        simplex = simplex[order]
        values = values[order]
        if np.max(np.abs(simplex[1:] - simplex[0])) <= x_tolerance and (
            np.max(np.abs(values[1:] - values[0])) <= f_tolerance
        ):
            return simplex[0], float(values[0]), iteration, True

        centroid = simplex[:-1].mean(axis=0)
        reflected = centroid + reflection * (centroid - simplex[-1])
        reflected_value = objective(reflected)

        if reflected_value < values[0]:
            expanded = centroid + expansion * (reflected - centroid)
            expanded_value = objective(expanded)
            if expanded_value < reflected_value:
                simplex[-1], values[-1] = expanded, expanded_value
            else:
                simplex[-1], values[-1] = reflected, reflected_value
            continue

        if reflected_value < values[-2]:
            simplex[-1], values[-1] = reflected, reflected_value
            continue

        if reflected_value < values[-1]:
            contracted = centroid + contraction * (reflected - centroid)
            contracted_threshold = reflected_value
        else:
            contracted = centroid + contraction * (simplex[-1] - centroid)
            contracted_threshold = values[-1]
        contracted_value = objective(contracted)
        if contracted_value < contracted_threshold:
            simplex[-1], values[-1] = contracted, contracted_value
            continue

        best = simplex[0].copy()
        simplex[1:] = best + shrink * (simplex[1:] - best)
        values[1:] = [objective(point) for point in simplex[1:]]

    order = np.argsort(values)
    best_index = int(order[0])
    return simplex[best_index], float(values[best_index]), max_iterations, False


def fit_classic(
    n_values: np.ndarray,
    d_values: np.ndarray,
    losses: np.ndarray,
    groups: Iterable[str],
    *,
    seed: int = 20260924,
    starts: int = 16,
    huber_delta: float = 0.05,
    max_iterations: int = 1600,
) -> FitResult:
    n_values = np.asarray(n_values, dtype=float)
    d_values = np.asarray(d_values, dtype=float)
    losses = np.asarray(losses, dtype=float)
    if not (n_values.shape == d_values.shape == losses.shape):
        raise ValueError("N, D, and Loss must have identical shapes")
    if n_values.ndim != 1 or n_values.size < 6:
        raise ValueError("at least six one-dimensional observations are required")
    if np.any(n_values <= 0) or np.any(d_values <= 0) or np.any(losses <= 0):
        raise ValueError("N, D, and Loss must all be positive")
    if starts < 1:
        raise ValueError("starts must be positive")

    weights = group_equal_weights(groups)
    objective = lambda point: classic_objective(  # noqa: E731
        point, n_values, d_values, losses, weights, huber_delta
    )
    rng = np.random.default_rng(seed)
    minimum_loss = float(losses.min())
    base = np.log(
        np.array(
            [
                max(0.05, minimum_loss * 0.75),
                max(0.05, float(np.ptp(losses))),
                max(0.05, float(np.ptp(losses))),
                0.2,
                0.2,
            ]
        )
    )
    starts_to_run = [np.clip(base, LOG_PARAMETER_BOUNDS[:, 0], LOG_PARAMETER_BOUNDS[:, 1])]
    for _ in range(starts - 1):
        starts_to_run.append(
            rng.uniform(LOG_PARAMETER_BOUNDS[:, 0], LOG_PARAMETER_BOUNDS[:, 1])
        )

    candidates: list[tuple[np.ndarray, float, int, bool, int]] = []
    for start_index, initial in enumerate(starts_to_run):
        point, value, iterations, converged = nelder_mead(
            objective, initial, max_iterations=max_iterations
        )
        if np.isfinite(value):
            candidates.append((point, value, iterations, converged, start_index))
    if not candidates:
        raise RuntimeError("all optimizer starts failed")

    candidates.sort(key=lambda item: item[1])
    best_point, best_value, iterations, converged, best_start_index = candidates[0]
    parameter_values = np.exp(best_point)
    parameters = {
        name: float(value)
        for name, value in zip(PARAMETER_NAMES, parameter_values, strict=True)
    }
    return FitResult(
        parameters=parameters,
        objective=float(best_value),
        iterations=iterations,
        converged=converged,
        starts=starts,
        seed=seed,
        huber_delta=huber_delta,
        best_start_index=best_start_index,
        candidate_objectives=[float(item[1]) for item in candidates],
    )


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    residual = predicted - actual
    ss_residual = float(np.sum(np.square(residual)))
    ss_total = float(np.sum(np.square(actual - actual.mean())))
    return {
        "rmse": float(np.sqrt(np.mean(np.square(residual)))),
        "mae": float(np.mean(np.abs(residual))),
        "mape": float(np.mean(np.abs(residual / actual))),
        "r2": float(1.0 - ss_residual / ss_total) if ss_total > 0 else float("nan"),
        "log_rmse": float(
            np.sqrt(np.mean(np.square(np.log(predicted) - np.log(actual))))
        ),
    }


def fit_log_linear_baseline(
    n_values: np.ndarray,
    d_values: np.ndarray,
    losses: np.ndarray,
    groups: Iterable[str],
) -> tuple[dict[str, float], np.ndarray]:
    design = np.column_stack(
        [np.ones_like(n_values), np.log(n_values), np.log(d_values)]
    )
    weights = group_equal_weights(groups)
    weighted_design = design * np.sqrt(weights)[:, None]
    weighted_losses = losses * np.sqrt(weights)
    coefficients, *_ = np.linalg.lstsq(weighted_design, weighted_losses, rcond=None)
    predictions = design @ coefficients
    return (
        {
            "intercept": float(coefficients[0]),
            "log_N": float(coefficients[1]),
            "log_D": float(coefficients[2]),
        },
        predictions,
    )


def extrapolation_distance(
    n_values: np.ndarray,
    d_values: np.ndarray,
    *,
    n_min: float,
    n_max: float,
    d_min: float,
    d_max: float,
) -> np.ndarray:
    log_n = np.log(np.asarray(n_values, dtype=float))
    log_d = np.log(np.asarray(d_values, dtype=float))
    n_low, n_high = np.log(n_min), np.log(n_max)
    d_low, d_high = np.log(d_min), np.log(d_max)
    n_distance = np.maximum(n_low - log_n, 0) + np.maximum(log_n - n_high, 0)
    d_distance = np.maximum(d_low - log_d, 0) + np.maximum(log_d - d_high, 0)
    return np.sqrt(np.square(n_distance) + np.square(d_distance))
