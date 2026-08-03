import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot9_outputs_exist_and_match_expected_counts():
    steps_5m = read_jsonl(ROOT / "data" / "audit" / "backtest_lot9_5m_steps.jsonl")
    steps_15m = read_jsonl(ROOT / "data" / "audit" / "backtest_lot9_15m_steps.jsonl")
    result = json.loads((ROOT / "data" / "audit" / "backtest_lot9_run_result.json").read_text(encoding="utf-8"))
    assert len(steps_5m) == 36
    assert len(steps_15m) == 12
    assert result["step_count"] == 48
    assert result["decision_counts"]["WAIT"] == 48
    assert result["orders_created_count"] == 0
    assert result["fills_created_count"] == 0
    assert result["pnl_total"] == 0
    assert result["lookahead_violations"] == []
    assert (ROOT / "reports" / "lot_09_backtest_replay_report.md").exists()


def test_lot9_steps_are_all_wait_and_trade_disabled():
    rows = read_jsonl(ROOT / "data" / "audit" / "backtest_lot9_5m_steps.jsonl") + read_jsonl(ROOT / "data" / "audit" / "backtest_lot9_15m_steps.jsonl")
    for row in rows:
        assert row["decision"] == "WAIT"
        assert row["trade_allowed"] is False
        assert row["orders_created"] == []
        assert row["fills_created"] == []
        assert row["pnl_impact"] == 0
        assert row["used_for_decision"] is False
