#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "data/audit/feature_registry_audit_lot8.json",
    "data/audit/no_lookahead_audit_lot8.json",
    "data/audit/backtest_lot9_run_result.json",
    "data/audit/backtest_lot9_5m_steps.jsonl",
    "data/audit/backtest_lot9_15m_steps.jsonl",
    "data/audit/transaction_cost_lot10_run_result.json",
    "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
    "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
]


def _count_lines(rel: str) -> int:
    path = ROOT / rel
    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    print("=== DIAGNOSE LOT10 CHAIN artifacts ===", flush=True)
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).exists()]
    if missing:
        for rel in missing:
            print(f"missing: {rel}", flush=True)
        return 1

    lot8_feature = json.loads((ROOT / "data/audit/feature_registry_audit_lot8.json").read_text(encoding="utf-8"))
    lot8_lookahead = json.loads((ROOT / "data/audit/no_lookahead_audit_lot8.json").read_text(encoding="utf-8"))
    lot9 = json.loads((ROOT / "data/audit/backtest_lot9_run_result.json").read_text(encoding="utf-8"))
    lot10 = json.loads((ROOT / "data/audit/transaction_cost_lot10_run_result.json").read_text(encoding="utf-8"))

    checks = [
        (lot8_feature.get("validation_status") == "validated_lot8", "Lot 8 feature audit not validated"),
        (lot8_lookahead.get("validation_status") == "validated_lot8", "Lot 8 lookahead audit not validated"),
        (lot9.get("orders_created_count") == 0, "Lot 9 orders count changed"),
        (lot9.get("fills_created_count") == 0, "Lot 9 fills count changed"),
        (lot9.get("pnl_total") == 0, "Lot 9 pnl changed"),
        (lot10.get("estimate_count") == 48, "Lot 10 estimate count invalid"),
        (lot10.get("orders_created_count") == 0, "Lot 10 orders count changed"),
        (lot10.get("fills_created_count") == 0, "Lot 10 fills count changed"),
        (lot10.get("pnl_total") == 0, "Lot 10 pnl changed"),
        (lot10.get("trade_allowed") is False, "Lot 10 trade_allowed changed"),
        (lot10.get("used_for_decision") is False, "Lot 10 used_for_decision changed"),
        (_count_lines("data/audit/backtest_lot9_5m_steps.jsonl") == 36, "Lot 9 5m step count invalid"),
        (_count_lines("data/audit/backtest_lot9_15m_steps.jsonl") == 12, "Lot 9 15m step count invalid"),
        (_count_lines("data/audit/transaction_cost_lot10_5m_estimates.jsonl") == 36, "Lot 10 5m estimate count invalid"),
        (_count_lines("data/audit/transaction_cost_lot10_15m_estimates.jsonl") == 12, "Lot 10 15m estimate count invalid"),
    ]
    for ok, message in checks:
        if not ok:
            print(message, flush=True)
            return 1
    print("DIAGNOSE LOT10 CHAIN: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
