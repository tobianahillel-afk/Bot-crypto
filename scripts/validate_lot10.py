#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "config/transaction_costs.yaml",
    "src/crypto_quant_bot/contracts/costs.py",
    "src/crypto_quant_bot/costs/__init__.py",
    "src/crypto_quant_bot/costs/config.py",
    "src/crypto_quant_bot/costs/fees.py",
    "src/crypto_quant_bot/costs/spread.py",
    "src/crypto_quant_bot/costs/slippage.py",
    "src/crypto_quant_bot/costs/estimator.py",
    "src/crypto_quant_bot/costs/writer.py",
    "scripts/run_lot10_transaction_costs.py",
    "scripts/validate_lot10.py",
    "data/audit/transaction_cost_lot10_run_result.json",
    "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
    "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
    "reports/lot_10_transaction_costs_report.md",
    "docs/TRANSACTION_COST_MODEL_POLICY.md",
    "docs/FEE_MODEL_POLICY.md",
    "docs/SPREAD_SLIPPAGE_MODEL_POLICY.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_10.md",
    "docs/LOT_10_REPORT.md",
    "data/audit/dataset_catalog.json",
]
FORBIDDEN_KEY_PARTS = ("future_", "target", "label", "long_signal", "short_signal", "trade_signal", "entry_signal", "exit_signal", "buy", "sell")
FORBIDDEN_VALUES = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}



def fail(message: str) -> int:
    print("LOT 10 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
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
                if lowered == "signal":
                    return True
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str) and current.upper() in FORBIDDEN_VALUES:
            return True
    return False


def validate_estimate(row: dict[str, Any], path: Path, index: int) -> str | None:
    expected = {
        "side": "neutral",
        "order_type": "hypothetical_noop",
        "trade_allowed": False,
        "used_for_decision": False,
    }
    for key, value in expected.items():
        if row.get(key) != value:
            return f"{path}:{index} invalid {key}: {row.get(key)}"
    if has_forbidden_content(row):
        return f"{path}:{index} contains forbidden trading or leakage content"
    fee = float(row.get("fee_bps", -1))
    spread = float(row.get("spread_bps", -1))
    slippage = float(row.get("slippage_bps", -1))
    total = float(row.get("total_cost_bps", -1))
    if fee < 0 or spread < 0 or slippage < 0 or total < 0:
        return f"{path}:{index} negative cost"
    if total > 500:
        return f"{path}:{index} total_cost_bps too high"
    if round(fee + spread + slippage, 8) != round(total, 8):
        return f"{path}:{index} total_cost_bps mismatch"
    amount_total = float(row.get("estimated_total_cost", -1))
    amount_sum = round(float(row.get("estimated_fee_amount", 0)) + float(row.get("estimated_spread_cost", 0)) + float(row.get("estimated_slippage_cost", 0)), 8)
    if round(amount_total, 8) != amount_sum:
        return f"{path}:{index} estimated_total_cost mismatch"
    timestamp = str(row.get("timestamp", ""))
    available_at = str(row.get("available_at", ""))
    if timestamp and available_at and timestamp > available_at:
        return f"{path}:{index} timestamp after available_at"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 10 artifact: {relative}")
    rows_5m = load_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl")
    rows_15m = load_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl")
    if len(rows_5m) != 36:
        return fail("transaction_cost_lot10_5m_estimates.jsonl must contain 36 lines")
    if len(rows_15m) != 12:
        return fail("transaction_cost_lot10_15m_estimates.jsonl must contain 12 lines")
    result = load_json(ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json")
    if not isinstance(result, dict):
        return fail("invalid Lot 10 run result")
    expected_result = {
        "estimate_count": 48,
        "orders_created_count": 0,
        "fills_created_count": 0,
        "pnl_total": 0,
        "trade_allowed": False,
        "used_for_decision": False,
    }
    for key, value in expected_result.items():
        if result.get(key) != value:
            return fail(f"run_result invalid {key}: {result.get(key)}")
    if has_forbidden_content(result):
        return fail("run_result contains forbidden trading or leakage content")
    for path, rows in [
        (ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl", rows_5m),
        (ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl", rows_15m),
    ]:
        for index, row in enumerate(rows, start=1):
            message = validate_estimate(row, path, index)
            if message:
                return fail(message)
    catalog = load_json(ROOT / "data" / "audit" / "dataset_catalog.json")
    if not isinstance(catalog, list):
        return fail("dataset_catalog.json must be a list")
    catalog_ids_list = [entry.get("dataset_id") for entry in catalog if isinstance(entry, dict)]
    if len(catalog_ids_list) != len(set(catalog_ids_list)):
        return fail("dataset_catalog.json contains duplicate dataset_id entries")
    catalog_ids = set(catalog_ids_list)
    for required_id in {"transaction_cost_lot10_5m_estimates", "transaction_cost_lot10_15m_estimates", "transaction_cost_lot10_run_result"}:
        if required_id not in catalog_ids:
            return fail(f"dataset catalog missing {required_id}")
    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text:
        return fail("live_execution invariant broken")
    if "leverage: FORBIDDEN" not in status_text:
        return fail("leverage invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("trade_allowed default invariant broken")
    veto_text = (ROOT / "config" / "veto_consequence_matrix.yaml").read_text(encoding="utf-8")
    if "WAIT" not in veto_text:
        return fail("Decision Engine WAIT invariant broken")
    if "BLOCK_TRADING" not in veto_text:
        return fail("Risk Engine block invariant broken")
    print("LOT 10 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
