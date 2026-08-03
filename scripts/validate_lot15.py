#!/usr/bin/env python3
from __future__ import annotations

import string
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.ledger import DEFAULT_LEDGER_BLOCK_REASONS, build_entry_checksum
from crypto_quant_bot.ledger.io import load_jsonl, read_text_limited, write_validation_report

REQUIRED_FILES = [
    "src/crypto_quant_bot/ledger/__init__.py",
    "src/crypto_quant_bot/ledger/models.py",
    "src/crypto_quant_bot/ledger/audit_trail.py",
    "src/crypto_quant_bot/ledger/io.py",
    "scripts/run_lot15_decision_ledger.py",
    "scripts/validate_lot15.py",
    "scripts/validate_all_until_lot15.py",
    "scripts/run_required_chain_until_lot15.sh",
    "scripts/diagnose_lot15_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot15.py",
    "data/audit/decision_ledger_lot15_5m.jsonl",
    "data/audit/decision_ledger_lot15_15m.jsonl",
    "reports/lot_15_decision_ledger_report.md",
    "docs/LOT_15_DECISION_LEDGER.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_15.md",
]
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
EXPECTED_CATALOG_IDS = {"decision_ledger_lot15_5m", "decision_ledger_lot15_15m"}
ALLOWED_KEY_NAMES = {
    "ledger_block_reasons",
    "order_routing_allowed",
    "ledger_entry_id",
    "entry_checksum",
    "previous_entry_checksum",
}
ALLOWED_STRING_VALUES = {"ORDER_ROUTING_NOT_ALLOWED"}
HEX_DIGITS = set(string.hexdigits)


def fail(message: str) -> int:
    print("LOT 15 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def has_forbidden_content(obj: Any, *, max_nodes: int = 50_000) -> bool:
    forbidden_key_parts = (
        "order",
        "order_id",
        "fill",
        "pnl",
        "profit",
        "loss",
        "position",
        "target",
        "label",
        "future",
        "long",
        "short",
        "buy",
        "sell",
        "entry",
        "exit",
        "stop_loss",
        "take_profit",
        "paper_trading",
    )
    forbidden_values = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}
    stack = [obj]
    seen = 0
    while stack:
        seen += 1
        if seen > max_nodes:
            return True
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                lowered = str(key).lower()
                if lowered in ALLOWED_KEY_NAMES:
                    stack.append(value)
                    continue
                if any(part in lowered for part in forbidden_key_parts):
                    return True
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            if current in ALLOWED_STRING_VALUES:
                continue
            lowered = current.lower()
            if any(part in lowered for part in forbidden_key_parts):
                return True
            if current.upper() in forbidden_values:
                return True
    return False


def validate_checksum(value: str) -> bool:
    return len(value) == 64 and all(char in HEX_DIGITS for char in value)


def validate_row(row: dict[str, Any], *, timeframe: str, index: int, path: Path) -> str | None:
    expected = {
        "trading_decision": "WAIT",
        "system_decision": "BLOCK_TRADING",
        "final_decision": "WAIT",
        "final_system_decision": "BLOCK_TRADING",
        "decision_firewall_state": "ACTIVE",
        "execution_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
        "risk_allowed": False,
        "exposure_allowed": False,
        "portfolio_change_allowed": False,
        "allocation_change_allowed": False,
        "rebalance_allowed": False,
        "order_routing_allowed": False,
        "external_connectivity_allowed": False,
        "human_review_required": True,
        "ledger_state": "RECORDED",
        "audit_trail_state": "ACTIVE",
        "immutability_mode": "APPEND_ONLY_SIMULATED",
    }
    for key, value in expected.items():
        if row.get(key) != value:
            return f"{path}:{index} invalid {key}: {row.get(key)}"
    if row.get("timeframe") != timeframe or row.get("source_timeframe") != timeframe:
        return f"{path}:{index} invalid timeframe linkage"
    if not row.get("timestamp") or not row.get("source_timestamp") or not row.get("created_at"):
        return f"{path}:{index} missing timestamp fields"
    if row.get("source_decision_id") in {None, ""}:
        return f"{path}:{index} missing source_decision_id"
    if row.get("ledger_sequence") != index:
        return f"{path}:{index} invalid ledger_sequence"
    reasons = row.get("ledger_block_reasons")
    if not isinstance(reasons, list) or set(DEFAULT_LEDGER_BLOCK_REASONS) - set(reasons):
        return f"{path}:{index} missing required ledger_block_reasons"
    checks = row.get("ledger_checks")
    if not isinstance(checks, list) or len(checks) < len(DEFAULT_LEDGER_BLOCK_REASONS):
        return f"{path}:{index} invalid ledger_checks"
    source_artifacts = row.get("source_artifacts")
    if not isinstance(source_artifacts, list) or len(source_artifacts) != 6:
        return f"{path}:{index} invalid source_artifacts"
    source_checksums = row.get("source_checksums")
    if not isinstance(source_checksums, dict) or len(source_checksums) != 6:
        return f"{path}:{index} invalid source_checksums"
    if set(source_artifacts) != set(source_checksums):
        return f"{path}:{index} source_artifacts/source_checksums mismatch"
    entry_checksum = row.get("entry_checksum", "")
    if not isinstance(entry_checksum, str) or not validate_checksum(entry_checksum):
        return f"{path}:{index} invalid entry_checksum"
    if build_entry_checksum(row) != entry_checksum:
        return f"{path}:{index} inconsistent entry_checksum"
    if has_forbidden_content(row):
        return f"{path}:{index} contains forbidden trading content"
    return None


def validate_report_text(path: Path) -> str | None:
    text = read_text_limited(path)
    lowered = text.lower()
    forbidden_fragments = [
        "trade_allowed=true",
        "execution_allowed=true",
        "risk_allowed=true",
        "exposure_allowed=true",
        "portfolio_change_allowed=true",
        "allocation_change_allowed=true",
        "rebalance_allowed=true",
        "external_connectivity_allowed=true",
        "live_execution=enabled",
        "paper_trading",
    ]
    for fragment in forbidden_fragments:
        if fragment in lowered:
            return f"report contains forbidden fragment: {fragment}"
    return None


def validate_chain(rows: list[dict[str, Any]], *, path: Path) -> str | None:
    previous = ""
    for index, row in enumerate(rows, start=1):
        current_previous = row.get("previous_entry_checksum", "")
        if index == 1:
            if current_previous not in {"", None}:
                return f"{path}:{index} first previous_entry_checksum must be empty"
        elif current_previous != previous:
            return f"{path}:{index} previous_entry_checksum mismatch"
        previous = str(row.get("entry_checksum", ""))
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 15 artifact: {relative}")
    rows_5m = load_jsonl(ROOT / "data" / "audit" / "decision_ledger_lot15_5m.jsonl", max_lines=EXPECTED_COUNTS["5m"])
    rows_15m = load_jsonl(ROOT / "data" / "audit" / "decision_ledger_lot15_15m.jsonl", max_lines=EXPECTED_COUNTS["15m"])
    if len(rows_5m) != EXPECTED_COUNTS["5m"]:
        return fail("decision_ledger_lot15_5m.jsonl must contain 36 lines")
    if len(rows_15m) != EXPECTED_COUNTS["15m"]:
        return fail("decision_ledger_lot15_15m.jsonl must contain 12 lines")
    total = len(rows_5m) + len(rows_15m)
    if total != 48:
        return fail("Lot 15 total ledger rows must equal 48")
    for path, timeframe, rows in [
        (ROOT / "data" / "audit" / "decision_ledger_lot15_5m.jsonl", "5m", rows_5m),
        (ROOT / "data" / "audit" / "decision_ledger_lot15_15m.jsonl", "15m", rows_15m),
    ]:
        chain_message = validate_chain(rows, path=path)
        if chain_message:
            return fail(chain_message)
        for index, row in enumerate(rows, start=1):
            message = validate_row(row, timeframe=timeframe, index=index, path=path)
            if message:
                return fail(message)
    report_message = validate_report_text(ROOT / "reports" / "lot_15_decision_ledger_report.md")
    if report_message:
        return fail(report_message)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 15 entries")
    write_validation_report(
        ROOT / "reports" / "lot_15_validation_report.md",
        counts={"5m": len(rows_5m), "15m": len(rows_15m)},
        total=total,
    )
    print("LOT 15 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
