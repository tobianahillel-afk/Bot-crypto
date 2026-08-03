#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    run_result = ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json"
    estimates_5m = ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl"
    estimates_15m = ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl"
    for path in [run_result, estimates_5m, estimates_15m]:
        if not path.exists():
            print(f"missing passive smoke artifact: {path}", flush=True)
            return 1
    result = json.loads(run_result.read_text(encoding="utf-8"))
    rows_5m = _read_jsonl(estimates_5m)
    rows_15m = _read_jsonl(estimates_15m)
    checks = [
        (len(rows_5m) == 36, "5m estimates count"),
        (len(rows_15m) == 12, "15m estimates count"),
        (result.get("estimate_count") == 48, "estimate_count"),
        (result.get("orders_created_count") == 0, "orders_created_count"),
        (result.get("fills_created_count") == 0, "fills_created_count"),
        (result.get("pnl_total") == 0, "pnl_total"),
        (result.get("trade_allowed") is False, "trade_allowed"),
        (result.get("used_for_decision") is False, "used_for_decision"),
    ]
    for ok, label in checks:
        if not ok:
            print(f"passive smoke check failed: {label}", flush=True)
            return 1
    for row in rows_5m + rows_15m:
        if row.get("side") != "neutral" or row.get("order_type") != "hypothetical_noop":
            print("passive smoke check failed: neutral noop invariant", flush=True)
            return 1
        if row.get("trade_allowed") is not False or row.get("used_for_decision") is not False:
            print("passive smoke check failed: safety flag", flush=True)
            return 1
        if float(row.get("total_cost_bps", -1)) < 0:
            print("passive smoke check failed: negative cost", flush=True)
            return 1
    print("LOT 10 PASSIVE SMOKE SUBSET: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
