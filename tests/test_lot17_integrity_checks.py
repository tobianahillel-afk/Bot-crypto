import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.health import build_dataset_catalog_checksum, build_health_checksum
from crypto_quant_bot.health.monitor import EXPECTED_CRITICAL_COUNTS
from crypto_quant_bot.lineage import build_manifest_checksum, build_source_catalog_checksum


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot17_snapshot_checksum_and_catalog_checksum_are_valid():
    snapshot = json.loads((ROOT / "data" / "audit" / "health_monitor_lot17.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    assert snapshot["health_checksum"] == build_health_checksum(snapshot)
    assert snapshot["dataset_catalog_checksum"] == build_dataset_catalog_checksum(catalog)


def test_lot17_snapshot_confirms_lot16_manifest_and_critical_counts():
    snapshot = json.loads((ROOT / "data" / "audit" / "health_monitor_lot17.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json").read_text(encoding="utf-8"))
    artifacts = load_jsonl(ROOT / "data" / "audit" / "reproducibility_artifacts_lot16.jsonl")
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    assert snapshot["artifact_count"] == len(artifacts)
    assert manifest["critical_counts"] == EXPECTED_CRITICAL_COUNTS
    assert manifest["manifest_checksum"] == build_manifest_checksum(manifest)
    assert manifest["source_catalog_checksum"] == build_source_catalog_checksum(catalog)
