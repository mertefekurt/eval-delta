"""command-line interface and exit-code policy."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from eval_delta import __version__
from eval_delta.analyzer import compare_runs
from eval_delta.errors import EvalDeltaError, InputError
from eval_delta.io import load_records
from eval_delta.reporters import render_json, render_markdown, render_terminal

_REPORTERS = {
    "terminal": render_terminal,
    "json": render_json,
    "markdown": render_markdown,
}


def build_parser() -> argparse.ArgumentParser:
    """build the CLI parser."""
    parser = argparse.ArgumentParser(
        prog="eval-delta",
        description=(
            "compare paired LLM evaluation runs and detect overall or slice-level regressions"
        ),
    )
    parser.add_argument("baseline", type=Path, help="baseline JSON or JSONL evaluation file")
    parser.add_argument("candidate", type=Path, help="candidate JSON or JSONL evaluation file")
    parser.add_argument("--id-field", default="id", help="dot path to each record ID")
    parser.add_argument("--score-field", default="score", help="dot path to each numeric score")
    parser.add_argument(
        "--slice-field",
        action="append",
        default=[],
        help="candidate metadata path to analyze; repeat for multiple fields",
    )
    parser.add_argument(
        "--min-slice-size",
        type=int,
        default=3,
        help="minimum paired records required for a metadata slice",
    )
    parser.add_argument(
        "--max-regression",
        type=float,
        default=0.02,
        help="largest tolerated mean score drop",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="bootstrap confidence level between 0 and 1",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=2000,
        help="number of seeded bootstrap resamples",
    )
    parser.add_argument("--seed", type=int, default=17, help="bootstrap random seed")
    parser.add_argument(
        "--require-complete-pairs",
        action="store_true",
        help="reject IDs that are present in only one input",
    )
    parser.add_argument(
        "--format",
        choices=tuple(_REPORTERS),
        default="terminal",
        help="report format",
    )
    parser.add_argument("--output", type=Path, help="write the report to this path")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """run the CLI and return a script-friendly exit code."""
    args = build_parser().parse_args(argv)
    try:
        baseline = load_records(
            args.baseline,
            id_field=args.id_field,
            score_field=args.score_field,
        )
        candidate = load_records(
            args.candidate,
            id_field=args.id_field,
            score_field=args.score_field,
        )
        report = compare_runs(
            baseline,
            candidate,
            slice_fields=args.slice_field,
            min_slice_size=args.min_slice_size,
            max_regression=args.max_regression,
            confidence=args.confidence,
            bootstrap_samples=args.bootstrap_samples,
            seed=args.seed,
        )
        if args.require_complete_pairs and (report.baseline_only or report.candidate_only):
            raise InputError(
                "complete pairing required but one or more IDs exist in only one input"
            )
        rendered = _REPORTERS[args.format](report)
        _write_report(rendered, args.output)
    except EvalDeltaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot write report: {exc}", file=sys.stderr)
        return 2

    return 1 if report.regressions else 0


def entrypoint() -> int:
    """console-script entry point."""
    return main()


def _write_report(rendered: str, output: Path | None) -> None:
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
