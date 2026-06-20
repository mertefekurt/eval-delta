"""typed domain models used by analysis and reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvalRecord:
    record_id: str
    score: float
    data: dict[str, Any]
    source: str
    position: int


@dataclass(frozen=True)
class RecordPair:
    baseline: EvalRecord
    candidate: EvalRecord

    @property
    def delta(self) -> float:
        return self.candidate.score - self.baseline.score


@dataclass(frozen=True)
class Pairing:
    pairs: tuple[RecordPair, ...]
    baseline_only: tuple[str, ...]
    candidate_only: tuple[str, ...]


@dataclass(frozen=True)
class SliceResult:
    field: str | None
    value: str
    size: int
    baseline_mean: float
    candidate_mean: float
    mean_delta: float
    ci_low: float
    ci_high: float
    wins: int
    ties: int
    losses: int
    regressed: bool

    @property
    def label(self) -> str:
        if self.field is None:
            return "overall"
        return f"{self.field}={self.value}"


@dataclass(frozen=True)
class ComparisonReport:
    paired_count: int
    max_regression: float
    confidence: float
    bootstrap_samples: int
    results: tuple[SliceResult, ...]
    baseline_only: tuple[str, ...]
    candidate_only: tuple[str, ...]

    @property
    def regressions(self) -> tuple[SliceResult, ...]:
        return tuple(result for result in self.results if result.regressed)
