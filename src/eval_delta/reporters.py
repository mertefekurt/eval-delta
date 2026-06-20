"""render comparison reports for humans and automation."""

from __future__ import annotations

import json
from typing import Any

from eval_delta.models import ComparisonReport, SliceResult


def render_terminal(report: ComparisonReport) -> str:
    """render a compact fixed-width terminal report."""
    confidence_label = f"{report.confidence:.0%} CI"
    rows = [
        [
            "REGRESS" if result.regressed else "PASS",
            result.label,
            str(result.size),
            f"{result.baseline_mean:.3f}",
            f"{result.candidate_mean:.3f}",
            _signed(result.mean_delta),
            f"[{_signed(result.ci_low)}, {_signed(result.ci_high)}]",
            f"{result.wins}/{result.ties}/{result.losses}",
        ]
        for result in report.results
    ]
    headers = ["STATUS", "SLICE", "N", "BASE", "CAND", "DELTA", confidence_label, "W/T/L"]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    lines = [
        f"eval-delta · {report.paired_count} paired records",
        (
            f"regression threshold: {report.max_regression:.3f} · "
            f"confidence: {report.confidence:.0%}"
        ),
        "",
        _terminal_row(headers, widths),
    ]
    lines.extend(_terminal_row(row, widths) for row in rows)
    lines.extend(["", _regression_summary(report)])
    lines.extend(_unmatched_lines(report))
    return "\n".join(lines) + "\n"


def render_json(report: ComparisonReport) -> str:
    """render a stable JSON report."""
    payload: dict[str, Any] = {
        "paired_count": report.paired_count,
        "max_regression": report.max_regression,
        "confidence": report.confidence,
        "bootstrap_samples": report.bootstrap_samples,
        "regression_count": len(report.regressions),
        "baseline_only": list(report.baseline_only),
        "candidate_only": list(report.candidate_only),
        "results": [_result_payload(result) for result in report.results],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_markdown(report: ComparisonReport) -> str:
    """render a Markdown summary suitable for pull requests."""
    lines = [
        "## eval-delta report",
        "",
        (
            f"Compared **{report.paired_count}** paired records with a maximum tolerated "
            f"regression of **{report.max_regression:.3f}**."
        ),
        "",
        "| Status | Slice | N | Baseline | Candidate | Delta | "
        f"{report.confidence:.0%} CI | W/T/L |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for result in report.results:
        status = "🔴 regress" if result.regressed else "🟢 pass"
        lines.append(
            f"| {status} | `{result.label}` | {result.size} | "
            f"{result.baseline_mean:.3f} | {result.candidate_mean:.3f} | "
            f"{_signed(result.mean_delta)} | "
            f"[{_signed(result.ci_low)}, {_signed(result.ci_high)}] | "
            f"{result.wins}/{result.ties}/{result.losses} |"
        )
    lines.extend(["", f"**{_regression_summary(report)}**"])
    lines.extend(f"- {line}" for line in _unmatched_lines(report))
    return "\n".join(lines) + "\n"


def _result_payload(result: SliceResult) -> dict[str, Any]:
    return {
        "label": result.label,
        "field": result.field,
        "value": result.value,
        "size": result.size,
        "baseline_mean": result.baseline_mean,
        "candidate_mean": result.candidate_mean,
        "mean_delta": result.mean_delta,
        "ci_low": result.ci_low,
        "ci_high": result.ci_high,
        "wins": result.wins,
        "ties": result.ties,
        "losses": result.losses,
        "regressed": result.regressed,
    }


def _terminal_row(values: list[str], widths: list[int]) -> str:
    return "  ".join(value.ljust(widths[index]) for index, value in enumerate(values))


def _signed(value: float) -> str:
    return f"{value:+.3f}"


def _regression_summary(report: ComparisonReport) -> str:
    count = len(report.regressions)
    noun = "regression" if count == 1 else "regressions"
    return f"{count} {noun} found"


def _unmatched_lines(report: ComparisonReport) -> list[str]:
    lines: list[str] = []
    if report.baseline_only:
        lines.append(f"baseline-only IDs: {', '.join(report.baseline_only)}")
    if report.candidate_only:
        lines.append(f"candidate-only IDs: {', '.join(report.candidate_only)}")
    return lines
