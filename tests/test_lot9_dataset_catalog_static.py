import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "audit" / "dataset_catalog.json"


def test_dataset_catalog_static_lot9_entries_are_present_and_unique():
    assert CATALOG.exists()
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    records = [record for record in payload if isinstance(record, dict)]
    dataset_ids = [record.get("dataset_id") for record in records]
    assert len(dataset_ids) == len(set(dataset_ids))
    required = {
        "backtest_lot9_5m_steps",
        "backtest_lot9_15m_steps",
        "backtest_lot9_run_config",
        "backtest_lot9_run_result",
    }
    assert required.issubset(set(dataset_ids))
    by_id = {record.get("dataset_id"): record for record in records}
    for dataset_id in required:
        record = by_id[dataset_id]
        assert record.get("layer") == "audit"
        assert record.get("used_for_decision") is False
