"""pair evaluation runs and analyze overall plus metadata-slice deltas."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from eval_delta.errors import ConfigurationError, InputError
from eval_delta.io import resolve_path
from eval_delta.models import (
    ComparisonReport,
    EvalRecord,
    Pairing,
    RecordPair,
    SliceResult,
)
from eval_delta.stats import bootstrap_mean_interval, mean

_MISSING_SLICE = "<missing>"
_TIE_EPSILON = 1e-12


def pair_records(
    baseline: Sequence[EvalRecord],
    candidate: Sequence[EvalRecord],
) -> Pairing:
    """pair records by ID and preserve unmatched IDs for reporting."""
    baseline_by_id = _index_records(baseline, "baseline")
    candidate_by_id = _index_records(candidate, "candidate")
    shared_ids = sorted(baseline_by_id.keys() & candidate_by_id.keys())
    if not shared_ids:
        raise InputError("baseline and candidate runs have no matching record IDs")

    return Pairing(
        pairs=tuple(
            RecordPair(baseline=baseline_by_id[record_id], candidate=candidate_by_id[record_id])
            for record_id in shared_ids
        ),
        baseline_only=tuple(sorted(baseline_by_id.keys() - candidate_by_id.keys())),
        candidate_only=tuple(sorted(candidate_by_id.keys() - baseline_by_id.keys())),
    )


def compare_runs(
    baseline: Sequence[EvalRecord],
    candidate: Sequence[EvalRecord],
    *,
    slice_fields: Sequence[str] = (),
    min_slice_size: int = 3,
    max_regression: float = 0.02,
    confidence: float = 0.95,
    bootstrap_samples: int = 2000,
    seed: int = 17,
) -> ComparisonReport:
    """compare paired scores and flag statistically credible regressions."""
    _validate_settings(
        min_slice_size=min_slice_size,
        max_regression=max_regression,
        confidence=confidence,
        bootstrap_samples=bootstrap_samples,
    )
    pairing = pair_records(baseline, candidate)
    results = [
        _analyze_group(
            pairing.pairs,
            field=None,
            value="overall",
            max_regression=max_regression,
            confidence=confidence,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        )
    ]

    groups: dict[tuple[str, str], list[RecordPair]] = defaultdict(list)
    unique_slice_fields = tuple(dict.fromkeys(slice_fields))
    for pair in pairing.pairs:
        for field in unique_slice_fields:
            raw_value = resolve_path(pair.candidate.data, field, default=_MISSING_SLICE)
            groups[(field, _display_value(raw_value))].append(pair)

    for index, ((field, value), pairs) in enumerate(sorted(groups.items()), start=1):
        if len(pairs) < min_slice_size:
            continue
        results.append(
            _analyze_group(
                pairs,
                field=field,
                value=value,
                max_regression=max_regression,
                confidence=confidence,
                bootstrap_samples=bootstrap_samples,
                seed=seed + index,
            )
        )

    return ComparisonReport(
        paired_count=len(pairing.pairs),
        max_regression=max_regression,
        confidence=confidence,
        bootstrap_samples=bootstrap_samples,
        results=tuple(results),
        baseline_only=pairing.baseline_only,
        candidate_only=pairing.candidate_only,
    )


def _analyze_group(
    pairs: Sequence[RecordPair],
    *,
    field: str | None,
    value: str,
    max_regression: float,
    confidence: float,
    bootstrap_samples: int,
    seed: int,
) -> SliceResult:
    baseline_scores = [pair.baseline.score for pair in pairs]
    candidate_scores = [pair.candidate.score for pair in pairs]
    deltas = [pair.delta for pair in pairs]
    ci_low, ci_high = bootstrap_mean_interval(
        deltas,
        confidence=confidence,
        samples=bootstrap_samples,
        seed=seed,
    )
    mean_delta = mean(deltas)
    wins = sum(delta > _TIE_EPSILON for delta in deltas)
    losses = sum(delta < -_TIE_EPSILON for delta in deltas)
    ties = len(deltas) - wins - losses

    return SliceResult(
        field=field,
        value=value,
        size=len(pairs),
        baseline_mean=mean(baseline_scores),
        candidate_mean=mean(candidate_scores),
        mean_delta=mean_delta,
        ci_low=ci_low,
        ci_high=ci_high,
        wins=wins,
        ties=ties,
        losses=losses,
        regressed=mean_delta < -max_regression and ci_high < 0,
    )


def _validate_settings(
    *,
    min_slice_size: int,
    max_regression: float,
    confidence: float,
    bootstrap_samples: int,
) -> None:
    if min_slice_size < 1:
        raise ConfigurationError("minimum slice size must be at least 1")
    if max_regression < 0:
        raise ConfigurationError("maximum regression must be zero or greater")
    if not 0 < confidence < 1:
        raise ConfigurationError("confidence must be greater than 0 and less than 1")
    if bootstrap_samples < 100:
        raise ConfigurationError("bootstrap samples must be at least 100")


def _display_value(value: Any) -> str:
    if value == _MISSING_SLICE:
        return _MISSING_SLICE
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _index_records(records: Sequence[EvalRecord], run_name: str) -> dict[str, EvalRecord]:
    indexed: dict[str, EvalRecord] = {}
    for record in records:
        if record.record_id in indexed:
            raise InputError(f"{run_name} run contains duplicate record ID '{record.record_id}'")
        indexed[record.record_id] = record
    return indexed
