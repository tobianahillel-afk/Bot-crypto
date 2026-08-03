from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.exposure.models import ExposureSnapshot


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"invalid JSONL row in {path}")
                rows.append(payload)
    return rows


def _atomic_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_jsonl(path: Path, snapshots: list[ExposureSnapshot]) -> None:
    lines: list[str] = []
    for snapshot in snapshots:
        lines.append(json.dumps(snapshot.to_dict(), ensure_ascii=False, sort_keys=True))
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_report(
    path: Path,
    *,
    counts: dict[str, int],
    total: int,
) -> None:
    _atomic_replace_text(
        path,
        "# Lot 12 Exposure Guard Report\n\n"
        "Exposure Guard & Capital Safety Snapshot V0 consumes Lot 7, Lot 10 and Lot 11 outputs as documentary context only.\n\n"
        f"5m exposure snapshots: {counts.get('5m', 0)}\n\n"
        f"15m exposure snapshots: {counts.get('15m', 0)}\n\n"
        f"Total exposure snapshots: {total}\n\n"
        "TradingDecision: WAIT\n\n"
        "SystemDecision: BLOCK_TRADING\n\n"
        "trade_allowed: false\n\n"
        "used_for_decision: false\n\n"
        "exposure_allowed: false\n\n"
        "allocation_allowed: false\n\n"
        "rebalance_allowed: false\n\n"
        "current_exposure_units: 0\n\n"
        "max_exposure_units: 0\n\n"
        "capital_at_risk: 0\n\n"
        "Exposure Guard blocks by default and authorizes no active exposure.\n\n"
        "The project remains educational only, with no exchange connection and no executable action.\n",
    )
