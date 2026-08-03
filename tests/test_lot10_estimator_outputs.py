import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot10_outputs_exist_and_counts_are_expected():
    rows_5m = read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl")
    rows_15m = read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl")
    result = json.loads((ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json").read_text(encoding="utf-8"))
    assert len(rows_5m) == 36
    assert len(rows_15m) == 12
    assert result["estimate_count"] == 48
    assert result["orders_created_count"] == 0
    assert result["fills_created_count"] == 0
    assert result["pnl_total"] == 0
    assert result["trade_allowed"] is False
    assert result["used_for_decision"] is False
    assert (ROOT / "reports" / "lot_10_transaction_costs_report.md").exists()


def test_lot10_cost_math_is_consistent():
    rows = read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl") + read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl")
    for row in rows:
        assert row["side"] == "neutral"
        assert row["order_type"] == "hypothetical_noop"
        assert row["fee_bps"] >= 0
        assert row["spread_bps"] >= 0
        assert row["slippage_bps"] >= 0
        assert round(row["fee_bps"] + row["spread_bps"] + row["slippage_bps"], 8) == round(row["total_cost_bps"], 8)
        assert round(row["estimated_fee_amount"] + row["estimated_spread_cost"] + row["estimated_slippage_cost"], 8) == round(row["estimated_total_cost"], 8)
        assert row["trade_allowed"] is False
        assert row["used_for_decision"] is False
