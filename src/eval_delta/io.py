"""load and validate evaluation records from JSON and JSONL files."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from eval_delta.errors import InputError
from eval_delta.models import EvalRecord

_MISSING = object()


def resolve_path(data: Any, path: str, default: Any = _MISSING) -> Any:
    """resolve a dot-separated path through dictionaries and lists."""
    current = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index < len(current):
                current = current[index]
                continue
        if default is not _MISSING:
            return default
        raise InputError(f"field '{path}' is missing")
    return current


def load_records(
    path: str | Path,
    *,
    id_field: str = "id",
    score_field: str = "score",
) -> tuple[EvalRecord, ...]:
    """load records and enforce stable IDs plus finite numeric scores."""
    source_path = Path(path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read '{source_path}': {exc}") from exc

    if not text.strip():
        raise InputError(f"'{source_path}' is empty")

    payloads = _parse_payloads(text, source_path)
    records: list[EvalRecord] = []
    seen_ids: set[str] = set()

    for position, payload in payloads:
        if not isinstance(payload, dict):
            raise InputError(f"{source_path}:{position}: each record must be a JSON object")

        try:
            raw_id = resolve_path(payload, id_field)
            raw_score = resolve_path(payload, score_field)
        except InputError as exc:
            raise InputError(f"{source_path}:{position}: {exc}") from exc

        if isinstance(raw_id, bool) or not isinstance(raw_id, (str, int)):
            raise InputError(
                f"{source_path}:{position}: field '{id_field}' must be a string or integer"
            )
        record_id = str(raw_id).strip()
        if not record_id:
            raise InputError(f"{source_path}:{position}: field '{id_field}' cannot be empty")
        if record_id in seen_ids:
            raise InputError(f"{source_path}:{position}: duplicate record ID '{record_id}'")

        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
            raise InputError(f"{source_path}:{position}: field '{score_field}' must be numeric")
        score = float(raw_score)
        if not math.isfinite(score):
            raise InputError(f"{source_path}:{position}: field '{score_field}' must be finite")

        seen_ids.add(record_id)
        records.append(
            EvalRecord(
                record_id=record_id,
                score=score,
                data=payload,
                source=str(source_path),
                position=position,
            )
        )

    return tuple(records)


def _parse_payloads(text: str, source_path: Path) -> list[tuple[int, Any]]:
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        return _parse_jsonl(text, source_path)

    if isinstance(document, list):
        return list(enumerate(document, start=1))
    if isinstance(document, dict) and isinstance(document.get("records"), list):
        return list(enumerate(document["records"], start=1))
    if isinstance(document, dict):
        return [(1, document)]
    raise InputError(f"'{source_path}' must contain a JSON object, array, or JSONL records")


def _parse_jsonl(text: str, source_path: Path) -> list[tuple[int, Any]]:
    payloads: list[tuple[int, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputError(f"{source_path}:{line_number}: invalid JSON: {exc.msg}") from exc
        payloads.append((line_number, payload))

    if not payloads:
        raise InputError(f"'{source_path}' contains no records")
    return payloads
