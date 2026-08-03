import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_5M = ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl"
PATH_15M = ROOT / "data" / "audit" / "exposure_guard_lot12_15m.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot12_outputs_exist_with_expected_counts():
    assert PATH_5M.exists()
    assert PATH_15M.exists()
    rows_5m = load_jsonl(PATH_5M)
    rows_15m = load_jsonl(PATH_15M)
    assert len(rows_5m) == 36
    assert len(rows_15m) == 12
    assert len(rows_5m) + len(rows_15m) == 48
    assert (ROOT / "reports" / "lot_12_exposure_guard_report.md").exists()


def test_lot12_output_rows_are_blocked_exposure_snapshots():
    rows = load_jsonl(PATH_5M) + load_jsonl(PATH_15M)
    for row in rows:
        assert row["trading_decision"] == "WAIT"
        assert row["system_decision"] == "BLOCK_TRADING"
        assert row["trade_allowed"] is False
        assert row["used_for_decision"] is False
        assert row["exposure_allowed"] is False
        assert row["allocation_allowed"] is False
        assert row["rebalance_allowed"] is False
        assert row["current_exposure_units"] == 0
        assert row["max_exposure_units"] == 0
        assert row["capital_at_risk"] == 0
