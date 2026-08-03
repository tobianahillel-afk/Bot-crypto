import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"
ARTIFACTS_PATH = ROOT / "data" / "audit" / "reproducibility_artifacts_lot16.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_16_reproducibility_report.md"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot16_outputs_exist_and_artifact_count_matches_jsonl():
    assert MANIFEST_PATH.exists()
    assert ARTIFACTS_PATH.exists()
    assert REPORT_PATH.exists()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = load_jsonl(ARTIFACTS_PATH)
    assert manifest["artifact_count"] == len(rows)
    assert isinstance(manifest["artifacts"], list)
    assert len(manifest["artifacts"]) == len(rows)


def test_lot16_manifest_contains_required_top_level_fields():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for field in [
        "manifest_version",
        "policy_version",
        "project_name",
        "project_mode",
        "created_at",
        "reproducibility_state",
        "lineage_state",
        "source_catalog_path",
        "reproducibility_scope_lot16",
        "source_catalog_scope",
        "source_catalog_entry_count",
        "source_catalog_checksum",
        "artifact_count",
        "artifacts",
        "critical_counts",
        "replay_commands",
        "validation_commands",
        "lineage_checks",
        "lineage_block_reasons",
        "invariants",
        "source_artifacts",
        "manifest_checksum",
    ]:
        assert field in manifest
