import copy
import hashlib
import json
import runpy
from pathlib import Path

from crypto_quant_bot.lineage import (
    LOT16_SOURCE_CATALOG_SCOPE,
    compute_lot16_source_catalog_checksum,
    normalize_lot16_source_catalog_records,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"
CATALOG_PATH = ROOT / "data" / "audit" / "dataset_catalog.json"
DIAGNOSE_PATH = ROOT / "scripts" / "diagnose_lot16_source_catalog_checksum.py"
RUN_PATH = ROOT / "scripts" / "run_lot16_reproducibility_manifest.py"
VALIDATE_PATH = ROOT / "scripts" / "validate_lot16.py"
BACKUP_PATHS = [
    ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json",
    ROOT / "data" / "audit" / "reproducibility_artifacts_lot16.jsonl",
    ROOT / "data" / "audit" / "dataset_catalog.json",
    ROOT / "reports" / "lot_16_reproducibility_report.md",
    ROOT / "reports" / "lot_16_validation_report.md",
]


def _load_catalog() -> list[dict]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return payload


def _run_script(path: Path) -> int:
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def _snapshot(paths: list[Path]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths if path.exists()}


def _restore(snapshot: dict[Path, bytes]) -> None:
    for path in BACKUP_PATHS:
        if path in snapshot:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(snapshot[path])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_compute_lot16_source_catalog_checksum_exists_and_manifest_tracks_scope_fields():
    catalog = _load_catalog()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert callable(compute_lot16_source_catalog_checksum)
    assert manifest["source_catalog_scope"] == LOT16_SOURCE_CATALOG_SCOPE
    assert manifest["reproducibility_scope_lot16"] == LOT16_SOURCE_CATALOG_SCOPE
    assert manifest["source_catalog_entry_count"] == len(normalize_lot16_source_catalog_records(catalog))


def test_run_lot16_and_validate_lot16_use_the_same_canonical_function():
    run_text = RUN_PATH.read_text(encoding="utf-8")
    validate_text = VALIDATE_PATH.read_text(encoding="utf-8")
    assert "compute_lot16_source_catalog_checksum" in run_text
    assert "compute_lot16_source_catalog_checksum" in validate_text
    assert "count_lot16_source_catalog_entries" in run_text
    assert "count_lot16_source_catalog_entries" in validate_text


def test_checksum_is_stable_for_future_entries_and_lot16_self_entries():
    catalog = _load_catalog()
    baseline = compute_lot16_source_catalog_checksum(catalog)
    future_entries = [
        {
            "dataset_id": "synthetic_health_projection_lot17",
            "dataset_name": "synthetic_health_projection_lot17",
            "data_version": "lot17_vtest",
            "source": "lot17_future_extension",
            "validation_status": "validated_lot17",
            "used_for_decision": False,
        },
        {
            "dataset_id": "synthetic_scope_projection_lot24",
            "dataset_name": "synthetic_scope_projection_lot24",
            "data_version": "lot24_vtest",
            "source": "lot24_future_extension",
            "validation_status": "validated_lot24",
            "used_for_decision": False,
        },
        {
            "dataset_id": "synthetic_auxiliary_lot16",
            "dataset_name": "synthetic_auxiliary_lot16",
            "data_version": "lot16_aux_v0",
            "source": "lot16_auxiliary_non_source",
            "validation_status": "validated_lot16",
            "used_for_decision": False,
        },
    ]
    assert compute_lot16_source_catalog_checksum(catalog + future_entries) == baseline


def test_checksum_ignores_runtime_only_duplicate_but_changes_for_historical_source_change():
    catalog = _load_catalog()
    baseline = compute_lot16_source_catalog_checksum(catalog)
    target = next(record for record in catalog if str(record.get("dataset_id", "")).startswith("transaction_cost_lot10_5m"))
    runtime_only_duplicate = copy.deepcopy(target)
    runtime_only_duplicate["id"] = "duplicate_runtime_only"
    runtime_only_duplicate["created_at"] = "2099-01-01T00:00:00+00:00"
    runtime_only_duplicate["available_at"] = "2099-01-01T00:00:00+00:00"
    runtime_only_duplicate["lineage_id"] = "duplicate_runtime_only_lineage"
    assert compute_lot16_source_catalog_checksum(catalog + [runtime_only_duplicate]) == baseline

    mutated_catalog = []
    for record in catalog:
        if record.get("dataset_id") == target.get("dataset_id"):
            updated = copy.deepcopy(record)
            updated["checksum"] = "changed_source_checksum"
            mutated_catalog.append(updated)
        else:
            mutated_catalog.append(copy.deepcopy(record))
    assert compute_lot16_source_catalog_checksum(mutated_catalog) != baseline


def test_diagnose_lot16_source_catalog_checksum_passes_without_changing_archive():
    archive_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
    before_sha = _sha256(archive_path)
    snapshot = _snapshot(BACKUP_PATHS)
    try:
        assert _run_script(RUN_PATH) == 0
        assert _run_script(VALIDATE_PATH) == 0
        assert _run_script(DIAGNOSE_PATH) == 0
    finally:
        _restore(snapshot)
    assert _sha256(archive_path) == before_sha
