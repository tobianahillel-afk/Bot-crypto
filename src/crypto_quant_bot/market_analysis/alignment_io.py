from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError

MAX_JSON_BYTES = 5_000_000
MAX_JSONL_ROWS = 100_000


def load_json(path: Path | str) -> Any:
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    if target.stat().st_size > MAX_JSON_BYTES:
        raise Lot26ValidationError(f"Lot26 JSON input too large: {target}")
    return json.loads(target.read_text(encoding="utf-8"))


def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    if target.stat().st_size > MAX_JSON_BYTES:
        raise Lot26ValidationError(f"Lot26 JSONL input too large: {target}")
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            if index > MAX_JSONL_ROWS:
                raise Lot26ValidationError("Lot26 JSONL row limit exceeded")
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise Lot26ValidationError("Lot26 JSONL rows must be objects")
            rows.append(row)
    return rows


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def write_json_atomic(path: Path | str, payload: object) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write(Path(path), text)


def write_jsonl_atomic(path: Path | str, rows: list[dict[str, Any]]) -> None:
    text = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    _atomic_write(Path(path), text)
