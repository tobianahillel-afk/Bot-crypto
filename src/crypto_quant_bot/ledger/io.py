from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.ledger.models import DecisionLedgerEntry, DecisionLedgerResult

MAX_TEXT_BYTES = 200_000
MAX_JSONL_BYTES = 5_000_000
MAX_JSONL_LINES = 512


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
                    raise ValueError(f"invalid jsonl row in {path}")
                rows.append(payload)
    return rows


def read_text_limited(path: Path, *, max_bytes: int = MAX_TEXT_BYTES) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


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


def write_jsonl(path: Path, entries: list[DecisionLedgerEntry]) -> None:
    lines = [json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True) for entry in entries]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_report(path: Path, *, result: DecisionLedgerResult) -> None:
    counts = result.counts_by_timeframe
    _atomic_replace_text(
        path,
        "# Lot 15 Decision Ledger Report\n\n"
        "Decision Ledger & Immutable Audit Trail V0 records blocked Lot 14 decisions as a local audit journal only.\n\n"
        f"5m recorded decisions: {counts.get('5m', 0)}\n\n"
        f"15m recorded decisions: {counts.get('15m', 0)}\n\n"
        f"Total recorded decisions: {result.total_entries}\n\n"
        "final_decision: WAIT\n\n"
        "final_system_decision: BLOCK_TRADING\n\n"
        "execution_allowed: false\n\n"
        "trade_allowed: false\n\n"
        "risk_allowed: false\n\n"
        "exposure_allowed: false\n\n"
        "portfolio_change_allowed: false\n\n"
        "allocation_change_allowed: false\n\n"
        "rebalance_allowed: false\n\n"
        "external_connectivity_allowed: false\n\n"
        "human_review_required: true\n\n"
        "ledger_state: RECORDED\n\n"
        "audit_trail_state: ACTIVE\n\n"
        "immutability_mode: APPEND_ONLY_SIMULATED\n\n"
        "Lot 7, Lot 10, Lot 11, Lot 12, Lot 13 and Lot 14 remain documentary context only.\n\n"
        "The journal stays local, educational and non executable.\n",
    )


def write_validation_report(path: Path, *, counts: dict[str, int], total: int) -> None:
    _atomic_replace_text(
        path,
        "# Lot 15 Validation Report\n\n"
        "Status: PASS\n\n"
        f"5m recorded decisions: {counts.get('5m', 0)}\n\n"
        f"15m recorded decisions: {counts.get('15m', 0)}\n\n"
        f"Total recorded decisions: {total}\n\n"
        "Decision Ledger remains audit-only, blocked and non executable.\n\n"
        "final_decision: WAIT\n\n"
        "final_system_decision: BLOCK_TRADING\n\n"
        "execution_allowed: false\n\n"
        "trade_allowed: false\n\n"
        "external_connectivity_allowed: false\n\n"
        "human_review_required: true\n",
    )
