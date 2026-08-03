#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.decision.firewall import DecisionFirewall
from crypto_quant_bot.decision.io import load_jsonl
from crypto_quant_bot.decision.models import DEFAULT_DECISION_BLOCK_REASONS
from crypto_quant_bot.exposure.guard import ExposureGuard
from crypto_quant_bot.portfolio.freeze import PortfolioFreeze
from crypto_quant_bot.risk.engine import RiskEngine

REQUIRED_FILES = [
    "src/crypto_quant_bot/decision/__init__.py",
    "src/crypto_quant_bot/decision/models.py",
    "src/crypto_quant_bot/decision/firewall.py",
    "src/crypto_quant_bot/decision/io.py",
    "scripts/run_lot14_decision_firewall.py",
    "scripts/validate_lot14.py",
    "scripts/validate_all_until_lot14.py",
    "scripts/run_required_chain_until_lot14.sh",
    "scripts/diagnose_lot14_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot14.py",
    "data/audit/final_decision_firewall_lot14_5m.jsonl",
    "data/audit/final_decision_firewall_lot14_15m.jsonl",
    "reports/lot_14_decision_firewall_report.md",
    "reports/lot_14_validation_report.md",
    "docs/LOT_14_DECISION_FIREWALL.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_14.md",
]
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
EXPECTED_CATALOG_IDS = {"final_decision_firewall_lot14_5m", "final_decision_firewall_lot14_15m"}
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
ALLOWED_ORDER_KEYS = {"order_routing_allowed"}


def fail(message: str) -> int:
    print("LOT 14 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def read_text_limited(path: Path, *, max_bytes: int = 200_000) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def has_forbidden_content(obj: Any, *, max_nodes: int = 40_000) -> bool:
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
                if lowered == "decision_block_reasons" or lowered in ALLOWED_ORDER_KEYS:
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
        "final_decision": "WAIT",
        "final_system_decision": "BLOCK_TRADING",
        "decision_firewall_state": "ACTIVE",
        "execution_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
        "risk_allowed": False,
        "exposure_allowed": False,
        "portfolio_state": "FROZEN",
        "capital_at_risk": 0,
        "portfolio_change_allowed": False,
        "allocation_change_allowed": False,
        "rebalance_allowed": False,
        "order_routing_allowed": False,
        "external_connectivity_allowed": False,
        "human_review_required": True,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
    }
    for key, value in expected.items():
        if row.get(key) != value:
            return f"{path}:{index} invalid {key}: {row.get(key)}"
    if row.get("timeframe") != timeframe:
        return f"{path}:{index} invalid timeframe"
    if set(DEFAULT_DECISION_BLOCK_REASONS) - set(row.get("decision_block_reasons", [])):
        return f"{path}:{index} missing required decision_block_reasons"
    checks = row.get("decision_checks")
    if not isinstance(checks, list) or len(checks) < len(DEFAULT_DECISION_BLOCK_REASONS):
        return f"{path}:{index} invalid decision_checks"
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
    if "execution_allowed=true" in lowered:
        return "report contains execution_allowed=true"
    if "risk_allowed=true" in lowered:
        return "report contains risk_allowed=true"
    if "exposure_allowed=true" in lowered:
        return "report contains exposure_allowed=true"
    if "portfolio_change_allowed=true" in lowered:
        return "report contains portfolio_change_allowed=true"
    if "allocation_change_allowed=true" in lowered:
        return "report contains allocation_change_allowed=true"
    if "rebalance_allowed=true" in lowered:
        return "report contains rebalance_allowed=true"
    if "external_connectivity_allowed=true" in lowered:
        return "report contains external_connectivity_allowed=true"
    if "live_execution=enabled" in lowered:
        return "report contains live_execution=ENABLED"
    if "paper_trading" in lowered:
        return "report contains forbidden paper_trading token"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 14 artifact: {relative}")
    rows_5m = load_jsonl(ROOT / "data" / "audit" / "final_decision_firewall_lot14_5m.jsonl", max_lines=EXPECTED_COUNTS["5m"])
    rows_15m = load_jsonl(ROOT / "data" / "audit" / "final_decision_firewall_lot14_15m.jsonl", max_lines=EXPECTED_COUNTS["15m"])
    if len(rows_5m) != EXPECTED_COUNTS["5m"]:
        return fail("final_decision_firewall_lot14_5m.jsonl must contain 36 lines")
    if len(rows_15m) != EXPECTED_COUNTS["15m"]:
        return fail("final_decision_firewall_lot14_15m.jsonl must contain 12 lines")
    if len(rows_5m) + len(rows_15m) != 48:
        return fail("Lot 14 total final decision snapshots must equal 48")
    for path, timeframe, rows in [
        (ROOT / "data" / "audit" / "final_decision_firewall_lot14_5m.jsonl", "5m", rows_5m),
        (ROOT / "data" / "audit" / "final_decision_firewall_lot14_15m.jsonl", "15m", rows_15m),
    ]:
        for index, row in enumerate(rows, start=1):
            message = validate_row(row, timeframe, index, path)
            if message:
                return fail(message)
    report_message = validate_report_text(ROOT / "reports" / "lot_14_decision_firewall_report.md")
    if report_message:
        return fail(report_message)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 14 entries")
    firewall = DecisionFirewall().evaluate_default()
    portfolio = PortfolioFreeze().evaluate_default()
    risk = RiskEngine().evaluate_default()
    exposure = ExposureGuard().evaluate_default()
    if (
        firewall.trade_allowed is not False
        or firewall.final_decision != "WAIT"
        or firewall.final_system_decision != "BLOCK_TRADING"
        or firewall.decision_firewall_state != "ACTIVE"
        or firewall.execution_allowed is not False
        or firewall.used_for_decision is not False
        or firewall.risk_allowed is not False
        or firewall.exposure_allowed is not False
        or firewall.portfolio_state != "FROZEN"
        or firewall.capital_at_risk != 0
        or firewall.portfolio_change_allowed is not False
        or firewall.allocation_change_allowed is not False
        or firewall.rebalance_allowed is not False
        or firewall.order_routing_allowed is not False
        or firewall.external_connectivity_allowed is not False
        or firewall.human_review_required is not True
    ):
        return fail("Decision Firewall invariant broken")
    if portfolio.trade_allowed is not False or portfolio.portfolio_state != "FROZEN" or portfolio.capital_at_risk != 0:
        return fail("Portfolio Freeze invariant broken")
    if risk.trade_allowed is not False or risk.live_execution != "DISABLED" or risk.leverage != "FORBIDDEN":
        return fail("Risk Engine invariant broken")
    if exposure.trade_allowed is not False or exposure.exposure_allowed is not False:
        return fail("Exposure Guard invariant broken")
    print("LOT 14 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
