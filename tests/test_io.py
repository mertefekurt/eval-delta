from __future__ import annotations

import json

import pytest

from eval_delta.errors import InputError
from eval_delta.io import load_records, resolve_path


def test_loads_jsonl_with_nested_fields(tmp_path):
    path = tmp_path / "run.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"sample": {"id": "a"}, "metrics": {"quality": 0.75}}),
                json.dumps({"sample": {"id": "b"}, "metrics": {"quality": 0.80}}),
            ]
        ),
        encoding="utf-8",
    )

    records = load_records(path, id_field="sample.id", score_field="metrics.quality")

    assert [record.record_id for record in records] == ["a", "b"]
    assert [record.score for record in records] == [0.75, 0.80]


def test_loads_records_wrapper(tmp_path):
    path = tmp_path / "run.json"
    path.write_text(
        json.dumps({"records": [{"id": "a", "score": 1}, {"id": "b", "score": 0}]}),
        encoding="utf-8",
    )

    records = load_records(path)

    assert len(records) == 2


def test_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "duplicates.json"
    path.write_text(
        json.dumps([{"id": "same", "score": 0.4}, {"id": "same", "score": 0.8}]),
        encoding="utf-8",
    )

    with pytest.raises(InputError, match="duplicate record ID"):
        load_records(path)


def test_rejects_non_numeric_scores(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"id": "a", "score": "high"}), encoding="utf-8")

    with pytest.raises(InputError, match="must be numeric"):
        load_records(path)


def test_resolve_path_supports_list_indexes():
    payload = {"metrics": [{"score": 0.91}]}

    assert resolve_path(payload, "metrics.0.score") == 0.91
