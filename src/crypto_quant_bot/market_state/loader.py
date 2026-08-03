import json
from pathlib import Path
from typing import Any


class InvalidJsonlError(ValueError):
    def __init__(self, path: Path, line_number: int, detail: str, line_preview: str) -> None:
        self.path = path
        self.line_number = line_number
        self.detail = detail
        self.line_preview = line_preview
        super().__init__(
            f"invalid JSONL in {path} at line {line_number}: {detail}; "
            f"line_preview={line_preview!r}"
        )


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            if not raw_line.strip():
                continue
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                preview = raw_line.rstrip("\n")[:120]
                raise InvalidJsonlError(file_path, line_number, exc.msg, preview) from exc
            if not isinstance(payload, dict):
                preview = raw_line.rstrip("\n")[:120]
                raise InvalidJsonlError(file_path, line_number, "expected JSON object", preview)
            rows.append(payload)
    return rows


def index_by_timestamp(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("timestamp")): row for row in rows if row.get("timestamp") is not None}


def group_by_timestamp(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        timestamp = row.get("timestamp")
        if timestamp is None:
            continue
        grouped.setdefault(str(timestamp), []).append(row)
    return grouped
