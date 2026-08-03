#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.exposure.guard import ExposureGuard
from crypto_quant_bot.portfolio.freeze import PortfolioFreeze
from crypto_quant_bot.portfolio.io import load_jsonl
from crypto_quant_bot.portfolio.models import DEFAULT_PORTFOLIO_BLOCK_REASONS
from crypto_quant_bot.risk.engine import RiskEngine

REQUIRED_FILES = [
    "src/crypto_quant_bot/portfolio/__init__.py",
    "src/crypto_quant_bot/portfolio/models.py",
    "src/crypto_quant_bot/portfolio/freeze.py",
    "src/crypto_quant_bot/portfolio/io.py",
    "scripts/run_lot13_portfolio_freeze.py",
    "scripts/validate_lot13.py",
    "scripts/validate_all_until_lot13.py",
    "scripts/run_required_chain_until_lot13.sh",
    "scripts/diagnose_lot13_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot13.py",
    "data/audit/portfolio_freeze_lot13_5m.jsonl",
    "data/audit/portfolio_freeze_lot13_15m.jsonl",
    "reports/lot_13_portfolio_freeze_report.md",
    "reports/lot_13_validation_report.md",
    "docs/LOT_13_PORTFOLIO_FREEZE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_13.md",
]
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
EXPECTED_CATALOG_IDS = {"portfolio_freeze_lot13_5m", "portfolio_freeze_lot13_15m"}
FORBIDDEN_KEY_PARTS = (
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
FORBIDDEN_VALUES = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}


def fail(message: str) -> int:
    print("LOT 13 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def read_text_limited(path: Path, *, max_bytes: int = 200_000) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def has_forbidden_content(obj: Any, *, max_nodes: int = 30_000) -> bool:
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
                if lowered == "portfolio_block_reasons":
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
        "portfolio_state": "FROZEN",
        "allocation_state": "DISABLED",
        "rebalance_state": "DISABLED",
        "portfolio_change_allowed": False,
        "allocation_change_allowed": False,
        "allocation_allowed": False,
        "rebalance_allowed": False,
        "new_exposure_allowed": False,
        "exposure_allowed": False,
        "current_exposure_units": 0,
        "max_exposure_units": 0,
        "capital_at_risk": 0,
    }
    for key, value in expected.items():
        if row.get(key) != value:
            return f"{path}:{index} invalid {key}: {row.get(key)}"
    if row.get("timeframe") != timeframe:
        return f"{path}:{index} invalid timeframe"
    if set(DEFAULT_PORTFOLIO_BLOCK_REASONS) - set(row.get("portfolio_block_reasons", [])):
        return f"{path}:{index} missing required portfolio_block_reasons"
    checks = row.get("portfolio_checks")
    if not isinstance(checks, list) or len(checks) < len(DEFAULT_PORTFOLIO_BLOCK_REASONS):
        return f"{path}:{index} invalid portfolio_checks"
    if not row.get("timestamp") or not row.get("created_at"):
        return f"{path}:{index} missing timestamp or created_at"
    if has_forbidden_content(row):
        return f"{path}:{index} contains forbidden trading content"
    return None


def validate_report_text(path: Path) -> str | None:
    text = read_text_limited(path)
    lowered = text.lower()
    if "trade_allowed=true" in lowered:
        return "report contains trade_allowed=true"
    if "allocation_allowed=true" in lowered:
        return "report contains allocation_allowed=true"
    if "rebalance_allowed=true" in lowered:
        return "report contains rebalance_allowed=true"
    if "exposure_allowed=true" in lowered:
        return "report contains exposure_allowed=true"
    if "live_execution=enabled" in lowered:
        return "report contains live_execution=ENABLED"
    if "paper_trading" in lowered:
        return "report contains forbidden paper_trading token"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 13 artifact: {relative}")
    rows_5m = load_jsonl(ROOT / "data" / "audit" / "portfolio_freeze_lot13_5m.jsonl", max_lines=EXPECTED_COUNTS["5m"])
    rows_15m = load_jsonl(ROOT / "data" / "audit" / "portfolio_freeze_lot13_15m.jsonl", max_lines=EXPECTED_COUNTS["15m"])
    if len(rows_5m) != EXPECTED_COUNTS["5m"]:
        return fail("portfolio_freeze_lot13_5m.jsonl must contain 36 lines")
    if len(rows_15m) != EXPECTED_COUNTS["15m"]:
        return fail("portfolio_freeze_lot13_15m.jsonl must contain 12 lines")
    if len(rows_5m) + len(rows_15m) != 48:
        return fail("Lot 13 total portfolio freeze snapshots must equal 48")
    for path, timeframe, rows in [
        (ROOT / "data" / "audit" / "portfolio_freeze_lot13_5m.jsonl", "5m", rows_5m),
        (ROOT / "data" / "audit" / "portfolio_freeze_lot13_15m.jsonl", "15m", rows_15m),
    ]:
        for index, row in enumerate(rows, start=1):
            message = validate_row(row, timeframe, index, path)
            if message:
                return fail(message)
    report_message = validate_report_text(ROOT / "reports" / "lot_13_portfolio_freeze_report.md")
    if report_message:
        return fail(report_message)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 13 entries")
    portfolio = PortfolioFreeze().evaluate_default()
    risk = RiskEngine().evaluate_default()
    exposure = ExposureGuard().evaluate_default()
    if (
        portfolio.trade_allowed is not False
        or portfolio.used_for_decision is not False
        or portfolio.portfolio_state != "FROZEN"
        or portfolio.allocation_state != "DISABLED"
        or portfolio.rebalance_state != "DISABLED"
        or portfolio.portfolio_change_allowed is not False
        or portfolio.allocation_change_allowed is not False
        or portfolio.allocation_allowed is not False
        or portfolio.rebalance_allowed is not False
        or portfolio.new_exposure_allowed is not False
        or portfolio.exposure_allowed is not False
        or portfolio.current_exposure_units != 0
        or portfolio.max_exposure_units != 0
        or portfolio.capital_at_risk != 0
    ):
        return fail("Portfolio Freeze invariant broken")
    if risk.trade_allowed is not False or risk.live_execution != "DISABLED" or risk.leverage != "FORBIDDEN":
        return fail("Risk Engine invariant broken")
    if exposure.trade_allowed is not False or exposure.exposure_allowed is not False:
        return fail("Exposure Guard invariant broken")
    print("LOT 13 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
