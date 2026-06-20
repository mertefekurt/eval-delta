"""small deterministic statistical helpers for paired score deltas."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from eval_delta.errors import ConfigurationError


def mean(values: Sequence[float]) -> float:
    """return the arithmetic mean of a non-empty sequence."""
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)


def bootstrap_mean_interval(
    values: Sequence[float],
    *,
    confidence: float,
    samples: int,
    seed: int,
) -> tuple[float, float]:
    """estimate a percentile interval for the mean using paired resampling."""
    if not values:
        raise ValueError("bootstrap requires at least one value")
    if not 0 < confidence < 1:
        raise ConfigurationError("confidence must be greater than 0 and less than 1")
    if samples < 100:
        raise ConfigurationError("bootstrap samples must be at least 100")
    if len(values) == 1:
        return values[0], values[0]

    generator = random.Random(seed)
    size = len(values)
    estimates = [
        sum(values[generator.randrange(size)] for _ in range(size)) / size for _ in range(samples)
    ]
    estimates.sort()
    tail = (1 - confidence) / 2
    return _quantile(estimates, tail), _quantile(estimates, 1 - tail)


def _quantile(sorted_values: Sequence[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
