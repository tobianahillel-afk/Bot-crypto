import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot10_outputs_static_counts_and_safety_flags():
    run_result_path = ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json"
    estimates_5m_path = ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl"
    estimates_15m_path = ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl"
    assert run_result_path.exists()
    assert estimates_5m_path.exists()
    assert estimates_15m_path.exists()
    result = json.loads(run_result_path.read_text(encoding="utf-8"))
    rows_5m = _read_jsonl(estimates_5m_path)
    rows_15m = _read_jsonl(estimates_15m_path)
    assert len(rows_5m) == 36
    assert len(rows_15m) == 12
    assert result["estimate_count"] == 48
    assert result["orders_created_count"] == 0
    assert result["fills_created_count"] == 0
    assert result["pnl_total"] == 0
    assert result["trade_allowed"] is False
    assert result["used_for_decision"] is False
    for row in rows_5m + rows_15m:
        assert row["total_cost_bps"] >= 0
        assert row["trade_allowed"] is False
        assert row["used_for_decision"] is False
        assert row["side"] == "neutral"
        assert row["order_type"] == "hypothetical_noop"
