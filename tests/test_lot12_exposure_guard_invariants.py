import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.exposure.guard import ExposureGuard
from crypto_quant_bot.exposure.models import DEFAULT_EXPOSURE_BLOCK_REASONS


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot12_default_guard_blocks_all_exposure():
    exposure = ExposureGuard().evaluate_default()
    assert exposure.trade_allowed is False
    assert exposure.used_for_decision is False
    assert exposure.exposure_allowed is False
    assert exposure.allocation_allowed is False
    assert exposure.rebalance_allowed is False
    assert exposure.current_exposure_units == 0
    assert exposure.max_exposure_units == 0
    assert exposure.capital_at_risk == 0
    for reason in DEFAULT_EXPOSURE_BLOCK_REASONS:
        assert reason in exposure.exposure_block_reasons


def test_lot12_dataset_catalog_contains_unique_outputs():
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "exposure_guard_lot12_5m" in ids
    assert "exposure_guard_lot12_15m" in ids


def test_lot12_rows_include_all_required_block_reasons():
    rows = load_jsonl(ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl")
    assert rows
    for reason in DEFAULT_EXPOSURE_BLOCK_REASONS:
        assert reason in rows[0]["exposure_block_reasons"]
