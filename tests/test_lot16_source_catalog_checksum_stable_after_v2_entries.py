import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.lineage import compute_lot16_source_catalog_checksum


def load_catalog() -> list[dict]:
    payload = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return payload


def test_lot16_source_catalog_checksum_ignores_post_lot16_v2_entries():
    catalog = load_catalog()
    baseline = compute_lot16_source_catalog_checksum(catalog)
    future_entries = [
        {
            "dataset_id": "synthetic_scope_registry",
            "dataset_name": "synthetic_scope_registry",
            "data_version": "lot22_vtest",
            "source": "lot22_planning_only",
            "validation_status": "validated_lot22",
            "lineage_id": "lot22_synthetic_scope_registry",
            "layer": "audit",
            "pair": "BTC/EUR",
            "timeframe": "multi",
            "used_for_decision": False,
        },
        {
            "dataset_id": "future_catalog_extension",
            "dataset_name": "future_catalog_extension",
            "data_version": "catalog_vtest",
            "source": "planning_scope_for_lot21",
            "validation_status": "planning_only_lot21",
            "lineage_id": "future_scope_lot21_lineage",
            "layer": "audit",
            "pair": "BTC/EUR",
            "timeframe": "multi",
            "used_for_decision": False,
        },
    ]
    assert compute_lot16_source_catalog_checksum(catalog + future_entries) == baseline


def test_lot16_source_catalog_checksum_ignores_lot16_self_entries_and_is_deterministic():
    catalog = load_catalog()
    baseline = compute_lot16_source_catalog_checksum(catalog)
    lot16_shadow_entry = {
        "dataset_id": "synthetic_shadow_entry",
        "dataset_name": "synthetic_shadow_entry",
        "data_version": "lot16_shadow_v0",
        "source": "lot16_shadow_manifest",
        "validation_status": "validated_lot16",
        "lineage_id": "lot16_shadow_lineage",
        "layer": "audit",
        "pair": "BTC/EUR",
        "timeframe": "multi",
        "used_for_decision": False,
    }
    mutated = catalog + [lot16_shadow_entry]
    assert compute_lot16_source_catalog_checksum(mutated) == baseline
    assert compute_lot16_source_catalog_checksum(list(reversed(mutated))) == baseline


def test_current_manifest_matches_the_current_stable_source_catalog_checksum():
    catalog = load_catalog()
    manifest = json.loads((ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json").read_text(encoding="utf-8"))
    assert manifest["source_catalog_checksum"] == compute_lot16_source_catalog_checksum(catalog)
