#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.market_state.loader import InvalidJsonlError, read_jsonl
from crypto_quant_bot.risk.risk_engine import RiskEngine

MARKET_STATE_5M = ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl"
MARKET_STATE_15M = ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl"
ALLOWED_QUALITY = {"valid", "degraded", "invalid"}



def fail(message: str) -> int:
    print("LOT 7 VALIDATION: FAIL")
    print(message)
    return 1
def contains_forbidden(obj: Any) -> bool:
    if isinstance(obj, dict):
        for key, value in obj.items():
            lowered = str(key).lower()
            if lowered.startswith("future_") or lowered.startswith("target") or lowered == "label":
                return True
            if contains_forbidden(value):
                return True
        return False
    if isinstance(obj, list):
        return any(contains_forbidden(item) for item in obj)
    if isinstance(obj, str):
        return obj.upper() in {"LONG", "SHORT"}
    return False


def check_rows(path: Path, expected_count: int) -> str | None:
    try:
        rows = read_jsonl(path)
    except InvalidJsonlError as exc:
        return str(exc)
    if len(rows) != expected_count:
        return f"invalid row count for {path}: {len(rows)}"
    for row in rows:
        if contains_forbidden(row):
            return f"forbidden future/target/label/signal content in {path}"
        if row.get("used_for_decision") is not False:
            return "used_for_decision must be false"
        for required in ["candle", "volatility_state", "range_state", "regime_state"]:
            if not isinstance(row.get(required), dict) or not row.get(required):
                return f"missing required component: {required}"
        if not isinstance(row.get("nearest_pivots"), list) or len(row["nearest_pivots"]) > 3:
            return "nearest_pivots invalid"
        if not isinstance(row.get("nearest_zones"), list) or len(row["nearest_zones"]) > 3:
            return "nearest_zones invalid"
        if not isinstance(row.get("component_available_at"), dict):
            return "component_available_at missing"
        available_at = row.get("available_at")
        if not isinstance(available_at, str) or not available_at:
            return "available_at missing"
        for value in row["component_available_at"].values():
            if isinstance(value, str) and value > available_at:
                return "market state available_at is before a component available_at"
        for pivot in row["nearest_pivots"]:
            usable_from = pivot.get("usable_from")
            if isinstance(usable_from, str) and usable_from > available_at:
                return "pivot used before usable_from"
        for zone in row["nearest_zones"]:
            usable_from = zone.get("usable_from")
            if isinstance(usable_from, str) and usable_from > available_at:
                return "zone used before usable_from"
        data_quality = row.get("data_quality")
        if not isinstance(data_quality, dict) or data_quality.get("status") not in ALLOWED_QUALITY:
            return "invalid data_quality status"
    return None


def main() -> int:
    required_files = [
        ROOT / "src" / "crypto_quant_bot" / "contracts" / "market_state.py",
        ROOT / "src" / "crypto_quant_bot" / "market_state" / "__init__.py",
        ROOT / "src" / "crypto_quant_bot" / "market_state" / "loader.py",
        ROOT / "src" / "crypto_quant_bot" / "market_state" / "assembler.py",
        ROOT / "src" / "crypto_quant_bot" / "market_state" / "nearest.py",
        ROOT / "src" / "crypto_quant_bot" / "market_state" / "quality.py",
        ROOT / "src" / "crypto_quant_bot" / "market_state" / "writer.py",
        ROOT / "scripts" / ("build_" + "lot7_" + "market_state" + ".py"),
        MARKET_STATE_5M,
        MARKET_STATE_15M,
        ROOT / "reports" / "lot_07_market_state_report.md",
        ROOT / "docs" / "MARKET_STATE_ENGINE_POLICY.md",
        ROOT / "docs" / "MARKET_STATE_ANTI_LOOKAHEAD_POLICY.md",
        ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_07.md",
        ROOT / "docs" / "LOT_07_REPORT.md",
    ]
    for path in required_files:
        if not path.exists():
            return fail(f"missing Lot 7 artifact: {path}")

    for path, expected_count in [(MARKET_STATE_5M, 36), (MARKET_STATE_15M, 12)]:
        error = check_rows(path, expected_count)
        if error:
            return fail(error)

    catalog_text = (ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8")
    if "btc_eur_5m_market_state_lot7" not in catalog_text or "btc_eur_15m_market_state_lot7" not in catalog_text:
        return fail("dataset catalog missing Lot 7 entries")

    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text or "leverage: FORBIDDEN" not in status_text:
        return fail("module status safety invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("risk default invariant broken")
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    if decision.trading_decision != "WAIT" or decision.system_decision != "BLOCK_TRADING" or decision.trade_allowed is not False:
        return fail("decision safety invariant broken")
    if risk.trade_allowed is not False:
        return fail("risk safety invariant broken")

    print("LOT 7 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
