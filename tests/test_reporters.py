from __future__ import annotations

import json

from eval_delta.models import ComparisonReport, SliceResult
from eval_delta.reporters import render_json, render_markdown, render_terminal


def sample_report() -> ComparisonReport:
    return ComparisonReport(
        paired_count=4,
        max_regression=0.05,
        confidence=0.95,
        bootstrap_samples=500,
        results=(
            SliceResult(
                field=None,
                value="overall",
                size=4,
                baseline_mean=0.8,
                candidate_mean=0.7,
                mean_delta=-0.1,
                ci_low=-0.12,
                ci_high=-0.08,
                wins=0,
                ties=0,
                losses=4,
                regressed=True,
            ),
        ),
        baseline_only=("old-only",),
        candidate_only=(),
    )


def test_terminal_report_contains_gate_summary():
    rendered = render_terminal(sample_report())

    assert "REGRESS" in rendered
    assert "1 regression found" in rendered
    assert "baseline-only IDs: old-only" in rendered


def test_json_report_is_machine_readable():
    payload = json.loads(render_json(sample_report()))

    assert payload["regression_count"] == 1
    assert payload["results"][0]["label"] == "overall"


def test_markdown_report_contains_table():
    rendered = render_markdown(sample_report())

    assert "## eval-delta report" in rendered
    assert "| 🔴 regress | `overall` |" in rendered
