import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "audit" / "dataset_catalog.json"


def _records() -> list[dict]:
    assert CATALOG.exists()
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return [record for record in payload if isinstance(record, dict)]


def test_dataset_catalog_has_unique_dataset_ids_after_repeated_lot9_runs():
    records = _records()
    dataset_ids = [record.get("dataset_id") for record in records]
    assert all(isinstance(dataset_id, str) and dataset_id for dataset_id in dataset_ids)
    assert len(dataset_ids) == len(set(dataset_ids))


def test_dataset_catalog_keeps_lot9_artifacts_idempotently_registered():
    ids = {record.get("dataset_id") for record in _records()}
    assert "backtest_lot9_5m_steps" in ids
    assert "backtest_lot9_15m_steps" in ids
    assert "backtest_lot9_run_config" in ids
    assert "backtest_lot9_run_result" in ids
