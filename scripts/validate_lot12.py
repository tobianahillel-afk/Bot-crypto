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
from crypto_quant_bot.exposure.guard import ExposureGuard
from crypto_quant_bot.exposure.models import DEFAULT_EXPOSURE_BLOCK_REASONS
from crypto_quant_bot.risk.engine import RiskEngine

REQUIRED_FILES = [
    "src/crypto_quant_bot/exposure/__init__.py",
    "src/crypto_quant_bot/exposure/models.py",
    "src/crypto_quant_bot/exposure/guard.py",
    "src/crypto_quant_bot/exposure/io.py",
    "scripts/run_lot12_exposure_guard.py",
    "scripts/validate_lot12.py",
    "scripts/validate_all_until_lot12.py",
    "scripts/run_required_chain_until_lot12.sh",
    "scripts/diagnose_lot12_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot12.py",
    "data/audit/exposure_guard_lot12_5m.jsonl",
    "data/audit/exposure_guard_lot12_15m.jsonl",
    "reports/lot_12_exposure_guard_report.md",
    "reports/lot_12_validation_report.md",
    "docs/LOT_12_EXPOSURE_GUARD.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_12.md",
]
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
EXPECTED_CATALOG_IDS = {"exposure_guard_lot12_5m", "exposure_guard_lot12_15m"}
FORBIDDEN_KEY_PARTS = (
    "order",
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
FORBIDDEN_VALUES = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}


def fail(message: str) -> int:
    print("LOT 12 VALIDATION: FAIL", flush=True)
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
                if lowered == "exposure_block_reasons":
                    stack.append(value)
                    continue
                if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                    return True
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            if current == "NO_ORDER_ROUTER":
                continue
            lowered = current.lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                return True
            if current.upper() in FORBIDDEN_VALUES:
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
        "exposure_allowed": False,
        "allocation_allowed": False,
        "rebalance_allowed": False,
        "current_exposure_units": 0,
        "max_exposure_units": 0,
        "capital_at_risk": 0,
    }
    for key, value in expected.items():
        if row.get(key) != value:
            return f"{path}:{index} invalid {key}: {row.get(key)}"
    if row.get("timeframe") != timeframe:
        return f"{path}:{index} invalid timeframe"
    if set(DEFAULT_EXPOSURE_BLOCK_REASONS) - set(row.get("exposure_block_reasons", [])):
        return f"{path}:{index} missing required exposure_block_reasons"
    checks = row.get("exposure_checks")
    if not isinstance(checks, list) or len(checks) < len(DEFAULT_EXPOSURE_BLOCK_REASONS):
        return f"{path}:{index} invalid exposure_checks"
    if not row.get("timestamp") or not row.get("created_at"):
        return f"{path}:{index} missing timestamp or created_at"
    if has_forbidden_content(row):
        return f"{path}:{index} contains forbidden trading content"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 12 artifact: {relative}")
    rows_5m = load_jsonl(ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl")
    rows_15m = load_jsonl(ROOT / "data" / "audit" / "exposure_guard_lot12_15m.jsonl")
    if len(rows_5m) != EXPECTED_COUNTS["5m"]:
        return fail("exposure_guard_lot12_5m.jsonl must contain 36 lines")
    if len(rows_15m) != EXPECTED_COUNTS["15m"]:
        return fail("exposure_guard_lot12_15m.jsonl must contain 12 lines")
    if len(rows_5m) + len(rows_15m) != 48:
        return fail("Lot 12 total exposure snapshots must equal 48")
    for path, timeframe, rows in [
        (ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl", "5m", rows_5m),
        (ROOT / "data" / "audit" / "exposure_guard_lot12_15m.jsonl", "15m", rows_15m),
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
        return fail("dataset_catalog missing Lot 12 entries")
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    exposure = ExposureGuard().evaluate_default()
    if decision.trading_decision != "WAIT" or decision.system_decision != "BLOCK_TRADING" or decision.trade_allowed is not False:
        return fail("Decision Engine invariant broken")
    if risk.trade_allowed is not False or risk.live_execution != "DISABLED" or risk.leverage != "FORBIDDEN":
        return fail("Risk Engine invariant broken")
    if (
        exposure.trade_allowed is not False
        or exposure.exposure_allowed is not False
        or exposure.allocation_allowed is not False
        or exposure.rebalance_allowed is not False
        or exposure.current_exposure_units != 0
        or exposure.max_exposure_units != 0
        or exposure.capital_at_risk != 0
    ):
        return fail("Exposure Guard invariant broken")
    print("LOT 12 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
