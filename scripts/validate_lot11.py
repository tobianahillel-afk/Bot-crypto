#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.engine import RiskEngine
from crypto_quant_bot.risk.models import DEFAULT_RISK_BLOCK_REASONS

REQUIRED_FILES = [
    "src/crypto_quant_bot/risk/__init__.py",
    "src/crypto_quant_bot/risk/models.py",
    "src/crypto_quant_bot/risk/engine.py",
    "src/crypto_quant_bot/risk/io.py",
    "scripts/run_lot11_risk_engine.py",
    "scripts/validate_lot11.py",
    "scripts/validate_all_until_lot11.py",
    "scripts/run_required_chain_until_lot11.sh",
    "scripts/diagnose_lot11_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot11.py",
    "data/audit/risk_engine_lot11_5m.jsonl",
    "data/audit/risk_engine_lot11_15m.jsonl",
    "reports/lot_11_risk_engine_report.md",
    "reports/lot_11_validation_report.md",
    "docs/LOT_11_RISK_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_11.md",
]
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
EXPECTED_CATALOG_IDS = {"risk_engine_lot11_5m", "risk_engine_lot11_15m"}
FORBIDDEN_KEY_PARTS = ("order", "fill", "pnl", "position", "target", "label", "future", "long", "short", "buy", "sell")
FORBIDDEN_VALUES = {"LONG", "SHORT", "BUY", "SELL"}


def fail(message: str) -> int:
    print("LOT 11 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


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


def has_forbidden_content(obj: Any, *, max_nodes: int = 20000) -> bool:
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
                if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                    return True
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str) and current.upper() in FORBIDDEN_VALUES:
            return True
    return False


def validate_row(row: dict[str, Any], timeframe: str, index: int, path: Path) -> str | None:
    expected = {
        "trading_decision": "WAIT",
        "system_decision": "BLOCK_TRADING",
        "trade_allowed": False,
        "used_for_decision": False,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
    }
    for key, value in expected.items():
        if row.get(key) != value:
            return f"{path}:{index} invalid {key}: {row.get(key)}"
    if row.get("timeframe") != timeframe:
        return f"{path}:{index} invalid timeframe"
    if set(DEFAULT_RISK_BLOCK_REASONS) - set(row.get("risk_block_reasons", [])):
        return f"{path}:{index} missing required risk_block_reasons"
    if not isinstance(row.get("risk_checks"), list) or len(row["risk_checks"]) < len(DEFAULT_RISK_BLOCK_REASONS):
        return f"{path}:{index} invalid risk_checks"
    if not row.get("timestamp") or not row.get("created_at"):
        return f"{path}:{index} missing timestamp or created_at"
    if has_forbidden_content(row):
        return f"{path}:{index} contains forbidden trading content"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 11 artifact: {relative}")
    rows_5m = load_jsonl(ROOT / "data" / "audit" / "risk_engine_lot11_5m.jsonl")
    rows_15m = load_jsonl(ROOT / "data" / "audit" / "risk_engine_lot11_15m.jsonl")
    if len(rows_5m) != EXPECTED_COUNTS["5m"]:
        return fail("risk_engine_lot11_5m.jsonl must contain 36 lines")
    if len(rows_15m) != EXPECTED_COUNTS["15m"]:
        return fail("risk_engine_lot11_15m.jsonl must contain 12 lines")
    if len(rows_5m) + len(rows_15m) != 48:
        return fail("Lot 11 total risk snapshots must equal 48")
    for path, timeframe, rows in [
        (ROOT / "data" / "audit" / "risk_engine_lot11_5m.jsonl", "5m", rows_5m),
        (ROOT / "data" / "audit" / "risk_engine_lot11_15m.jsonl", "15m", rows_15m),
    ]:
        for index, row in enumerate(rows, start=1):
            message = validate_row(row, timeframe, index, path)
            if message:
                return fail(message)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 11 entries")
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    if decision.trading_decision != "WAIT" or decision.system_decision != "BLOCK_TRADING" or decision.trade_allowed is not False:
        return fail("Decision Engine invariant broken")
    if risk.trade_allowed is not False or risk.live_execution != "DISABLED" or risk.leverage != "FORBIDDEN" or risk.used_for_decision is not False:
        return fail("Risk Engine invariant broken")
    print("LOT 11 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
