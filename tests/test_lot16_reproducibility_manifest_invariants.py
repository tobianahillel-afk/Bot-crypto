import json
from pathlib import Path

from crypto_quant_bot.lineage import LOT16_SOURCE_CATALOG_SCOPE

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"


def test_lot16_manifest_keeps_reproducibility_invariants():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["project_name"] == "Crypto Quant Bot V3.1-Ops"
    assert manifest["project_mode"] == "EDUCATIONAL_AUDIT_ONLY"
    assert manifest["reproducibility_state"] == "REPRODUCIBLE_LOCALLY"
    assert manifest["lineage_state"] == "RECORDED"
    assert manifest["external_connectivity_allowed"] is False
    assert manifest["execution_allowed"] is False
    assert manifest["trade_allowed"] is False
    assert manifest["reproducibility_scope_lot16"] == LOT16_SOURCE_CATALOG_SCOPE
    assert manifest["source_catalog_scope"] == LOT16_SOURCE_CATALOG_SCOPE
    assert manifest["source_catalog_entry_count"] > 0


def test_lot16_manifest_contains_expected_critical_counts():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expected = {"5m": 36, "15m": 12, "total": 48}
    for lot_name in ["lot12", "lot13", "lot14", "lot15"]:
        assert manifest["critical_counts"][lot_name] == expected


def test_lot16_dataset_catalog_contains_unique_outputs():
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "reproducibility_manifest_lot16" in ids
    assert "reproducibility_artifacts_lot16" in ids
