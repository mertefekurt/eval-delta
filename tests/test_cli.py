from __future__ import annotations

import json

from eval_delta.cli import main


def write_run(path, scores):
    path.write_text(
        "\n".join(
            json.dumps({"id": record_id, "score": score}) for record_id, score in scores.items()
        ),
        encoding="utf-8",
    )


def test_cli_returns_one_for_regression(tmp_path, capsys):
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    write_run(baseline, {"a": 0.9, "b": 0.8, "c": 0.85})
    write_run(candidate, {"a": 0.5, "b": 0.4, "c": 0.45})

    exit_code = main(
        [
            str(baseline),
            str(candidate),
            "--bootstrap-samples",
            "100",
            "--max-regression",
            "0.05",
        ]
    )

    assert exit_code == 1
    assert "REGRESS" in capsys.readouterr().out


def test_cli_returns_zero_for_clean_run(tmp_path):
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    write_run(baseline, {"a": 0.5, "b": 0.6})
    write_run(candidate, {"a": 0.6, "b": 0.7})

    assert main([str(baseline), str(candidate), "--bootstrap-samples", "100"]) == 0


def test_cli_returns_two_for_invalid_input(tmp_path, capsys):
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    baseline.write_text("not json", encoding="utf-8")
    write_run(candidate, {"a": 0.7})

    exit_code = main([str(baseline), str(candidate)])

    assert exit_code == 2
    assert "error:" in capsys.readouterr().err


def test_cli_can_require_complete_pairs(tmp_path, capsys):
    baseline = tmp_path / "baseline.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    write_run(baseline, {"a": 0.5, "b": 0.6})
    write_run(candidate, {"a": 0.7})

    exit_code = main(
        [
            str(baseline),
            str(candidate),
            "--bootstrap-samples",
            "100",
            "--require-complete-pairs",
        ]
    )

    assert exit_code == 2
    assert "complete pairing required" in capsys.readouterr().err
