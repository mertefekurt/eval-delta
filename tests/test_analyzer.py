from __future__ import annotations

import pytest

from eval_delta.analyzer import compare_runs, pair_records
from eval_delta.errors import InputError
from eval_delta.models import EvalRecord


def record(record_id: str, score: float, language: str) -> EvalRecord:
    return EvalRecord(
        record_id=record_id,
        score=score,
        data={"id": record_id, "score": score, "metadata": {"language": language}},
        source="test",
        position=1,
    )


def test_pairing_reports_unmatched_ids():
    baseline = [record("a", 0.5, "en"), record("b", 0.5, "en")]
    candidate = [record("b", 0.7, "en"), record("c", 0.7, "en")]

    pairing = pair_records(baseline, candidate)

    assert [pair.baseline.record_id for pair in pairing.pairs] == ["b"]
    assert pairing.baseline_only == ("a",)
    assert pairing.candidate_only == ("c",)


def test_pairing_rejects_duplicate_ids_from_library_callers():
    baseline = [record("a", 0.5, "en"), record("a", 0.6, "en")]
    candidate = [record("a", 0.7, "en")]

    with pytest.raises(InputError, match="baseline run contains duplicate"):
        pair_records(baseline, candidate)


def test_detects_slice_regression_hidden_by_aggregate():
    baseline = [
        record("en-1", 0.60, "en"),
        record("en-2", 0.70, "en"),
        record("tr-1", 0.90, "tr"),
        record("tr-2", 0.80, "tr"),
    ]
    candidate = [
        record("en-1", 0.80, "en"),
        record("en-2", 0.90, "en"),
        record("tr-1", 0.70, "tr"),
        record("tr-2", 0.60, "tr"),
    ]

    report = compare_runs(
        baseline,
        candidate,
        slice_fields=["metadata.language"],
        min_slice_size=2,
        max_regression=0.05,
        bootstrap_samples=500,
    )

    by_label = {result.label: result for result in report.results}
    assert by_label["overall"].regressed is False
    assert by_label["metadata.language=en"].regressed is False
    assert by_label["metadata.language=tr"].regressed is True


def test_ignores_slices_below_minimum_size():
    baseline = [record("a", 0.8, "en"), record("b", 0.8, "tr")]
    candidate = [record("a", 0.7, "en"), record("b", 0.7, "tr")]

    report = compare_runs(
        baseline,
        candidate,
        slice_fields=["metadata.language"],
        min_slice_size=2,
        bootstrap_samples=100,
    )

    assert [result.label for result in report.results] == ["overall"]


def test_counts_wins_ties_and_losses():
    baseline = [
        record("a", 0.5, "en"),
        record("b", 0.5, "en"),
        record("c", 0.5, "en"),
    ]
    candidate = [
        record("a", 0.6, "en"),
        record("b", 0.5, "en"),
        record("c", 0.4, "en"),
    ]

    report = compare_runs(baseline, candidate, bootstrap_samples=100)

    overall = report.results[0]
    assert (overall.wins, overall.ties, overall.losses) == (1, 1, 1)
