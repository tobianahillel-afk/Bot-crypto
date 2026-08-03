import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_5M = ROOT / "data" / "audit" / "final_decision_firewall_lot14_5m.jsonl"
PATH_15M = ROOT / "data" / "audit" / "final_decision_firewall_lot14_15m.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot14_outputs_exist_with_expected_counts():
    assert PATH_5M.exists()
    assert PATH_15M.exists()
    rows_5m = load_jsonl(PATH_5M)
    rows_15m = load_jsonl(PATH_15M)
    assert len(rows_5m) == 36
    assert len(rows_15m) == 12
    assert len(rows_5m) + len(rows_15m) == 48
    assert (ROOT / "reports" / "lot_14_decision_firewall_report.md").exists()


def test_lot14_output_rows_are_blocked_final_decision_snapshots():
    rows = load_jsonl(PATH_5M) + load_jsonl(PATH_15M)
    for row in rows:
        assert row["trading_decision"] == "WAIT"
        assert row["system_decision"] == "BLOCK_TRADING"
        assert row["final_decision"] == "WAIT"
        assert row["final_system_decision"] == "BLOCK_TRADING"
        assert row["decision_firewall_state"] == "ACTIVE"
        assert row["execution_allowed"] is False
        assert row["trade_allowed"] is False
        assert row["used_for_decision"] is False
        assert row["risk_allowed"] is False
        assert row["exposure_allowed"] is False
        assert row["portfolio_state"] == "FROZEN"
        assert row["portfolio_change_allowed"] is False
        assert row["allocation_change_allowed"] is False
        assert row["rebalance_allowed"] is False
        assert row["order_routing_allowed"] is False
        assert row["external_connectivity_allowed"] is False
        assert row["human_review_required"] is True
        assert row["capital_at_risk"] == 0
