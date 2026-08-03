import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog


def build_metadata(dataset_id: str, dataset_name: str, row_count: int) -> DatasetMetadata:
    return DatasetMetadata(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        row_count=row_count,
        checksum=f"checksum-{dataset_id}-{row_count}",
        validation_status="validated_test",
    )


def test_dataset_catalog_upsert_is_idempotent_for_same_dataset_id(tmp_path):
    catalog_path = tmp_path / "audit" / "dataset_catalog.json"
    catalog = DatasetCatalog(catalog_path)

    catalog.upsert(build_metadata("dataset_a", "First Name", 1))
    catalog.upsert(build_metadata("dataset_a", "Updated Name", 2))
    catalog.upsert(build_metadata("dataset_a", "Updated Name", 2))

    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["dataset_id"] == "dataset_a"
    assert payload[0]["dataset_name"] == "Updated Name"
    assert payload[0]["row_count"] == 2


def test_dataset_catalog_save_and_upsert_leave_no_required_tmp_files_after_success(tmp_path):
    catalog_path = tmp_path / "audit" / "dataset_catalog.json"
    catalog = DatasetCatalog(catalog_path)

    catalog.save([build_metadata("dataset_a", "Dataset A", 1).to_dict()])
    catalog.upsert(build_metadata("dataset_b", "Dataset B", 3))
    catalog.upsert(build_metadata("dataset_b", "Dataset B", 3))

    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert {entry["dataset_id"] for entry in payload} == {"dataset_a", "dataset_b"}

    tmp_files = list(catalog_path.parent.glob(".dataset_catalog.*.tmp"))
    assert tmp_files == []


def test_dataset_catalog_remains_readable_after_multiple_successive_writes(tmp_path):
    catalog_path = tmp_path / "audit" / "dataset_catalog.json"
    catalog = DatasetCatalog(catalog_path)

    for index in range(5):
        catalog.save(
            [
                build_metadata("dataset_a", "Dataset A", index + 1).to_dict(),
                build_metadata("dataset_b", "Dataset B", index + 2).to_dict(),
            ]
        )
        loaded = catalog.load()
        assert isinstance(loaded, list)
        assert {entry["dataset_id"] for entry in loaded} == {"dataset_a", "dataset_b"}
        assert json.loads(catalog_path.read_text(encoding="utf-8")) == loaded
