from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog


def test_dataset_catalog_upsert_and_get(tmp_path):
    catalog = DatasetCatalog(tmp_path / "catalog.json")
    metadata = DatasetMetadata(
        dataset_id="dataset_1",
        dataset_name="Unit Test Dataset",
        row_count=1,
        checksum="abc",
        validation_status="validated_lot1",
    )
    catalog.upsert(metadata)
    loaded = catalog.get("dataset_1")
    assert loaded is not None
    assert loaded["dataset_name"] == "Unit Test Dataset"
    assert loaded["row_count"] == 1
