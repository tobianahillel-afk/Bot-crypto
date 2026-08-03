import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "market_analysis_lot22.json"


def test_lot22_invariants_remain_no_trading():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["execution_allowed"] is False
    assert snapshot["trade_allowed"] is False
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["live_execution"] == "DISABLED"
    assert snapshot["leverage"] == "FORBIDDEN"
    assert snapshot["source_v1_archive_frozen"] is True
    assert snapshot["v2_scope_state"] == "OPENED_AS_PLANNING_ONLY"


def test_lot22_context_scores_are_bounded():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert 0.0 <= snapshot["market_context_score"] <= 1.0
    for summary in snapshot["timeframe_summaries"]:
        assert 0.0 <= summary["context_score"] <= 1.0


def test_lot22_input_rows_are_positive():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["input_rows_by_timeframe"]["5m"] > 0
    assert snapshot["input_rows_by_timeframe"]["15m"] > 0
