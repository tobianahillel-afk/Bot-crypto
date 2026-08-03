from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.portfolio.models import PortfolioFreezeSnapshot

MAX_JSON_BYTES = 2_000_000
MAX_JSONL_BYTES = 5_000_000
MAX_JSONL_LINES = 512


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"json payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path, *, max_lines: int = MAX_JSONL_LINES) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_JSONL_BYTES:
        raise ValueError(f"jsonl payload too large: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_lines:
                raise ValueError(f"too many jsonl rows in {path}")
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


def write_jsonl(path: Path, snapshots: list[PortfolioFreezeSnapshot]) -> None:
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
        "# Lot 13 Portfolio Freeze Report\n\n"
        "Portfolio Freeze & Allocation Firewall V0 consumes Lot 10, Lot 11 and Lot 12 outputs as documentary context only.\n\n"
        f"5m portfolio freeze snapshots: {counts.get('5m', 0)}\n\n"
        f"15m portfolio freeze snapshots: {counts.get('15m', 0)}\n\n"
        f"Total portfolio freeze snapshots: {total}\n\n"
        "TradingDecision: WAIT\n\n"
        "SystemDecision: BLOCK_TRADING\n\n"
        "trade_allowed: false\n\n"
        "used_for_decision: false\n\n"
        "portfolio_state: FROZEN\n\n"
        "allocation_state: DISABLED\n\n"
        "rebalance_state: DISABLED\n\n"
        "portfolio_change_allowed: false\n\n"
        "allocation_change_allowed: false\n\n"
        "allocation_allowed: false\n\n"
        "rebalance_allowed: false\n\n"
        "new_exposure_allowed: false\n\n"
        "exposure_allowed: false\n\n"
        "current_exposure_units: 0\n\n"
        "max_exposure_units: 0\n\n"
        "capital_at_risk: 0\n\n"
        "Portfolio Freeze blocks by default and authorizes no portfolio change.\n\n"
        "Lot 10, Lot 11 and Lot 12 remain documentary context only.\n\n"
        "The project remains educational only, with live execution disabled and leverage forbidden.\n",
    )
