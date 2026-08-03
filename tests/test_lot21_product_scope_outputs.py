import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "audit" / "product_scope_lot21.json"
CAPABILITIES_PATH = ROOT / "data" / "audit" / "product_scope_capabilities_lot21.jsonl"
ROADMAP_PATH = ROOT / "data" / "audit" / "product_scope_roadmap_lot21.jsonl"
FREEZE_REPORT_PATH = ROOT / "reports" / "lot_21_v1_archive_freeze_report.md"
REPORT_PATH = ROOT / "reports" / "lot_21_product_scope_report.md"
VALIDATION_REPORT_PATH = ROOT / "reports" / "lot_21_validation_report.md"
DOC_PATHS = [
    ROOT / "docs" / "LOT_21_PRODUCT_SCOPE.md",
    ROOT / "docs" / "V2_PRODUCT_ROADMAP.md",
    ROOT / "docs" / "FUNCTIONAL_COVERAGE_REGISTRY.md",
    ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_21.md",
]


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot21_artifacts_are_present():
    required = [
        REGISTRY_PATH,
        CAPABILITIES_PATH,
        ROADMAP_PATH,
        FREEZE_REPORT_PATH,
        REPORT_PATH,
        VALIDATION_REPORT_PATH,
        *DOC_PATHS,
    ]
    for path in required:
        assert path.exists(), f"missing Lot 21 artifact: {path}"


def test_lot21_registry_core_fields_are_locked():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert registry["project_name"] == "Crypto Quant Bot V3.1-Ops"
    assert registry["project_identity"] == "SAME_PROJECT_NO_V4"
    assert registry["project_mode"] == "EDUCATIONAL_AUDIT_ONLY"
    assert registry["v1_closure_state"] == "V1_DEFENSIVE_AUDIT_CLOSED"
    assert registry["v2_scope_state"] == "OPENED_AS_PLANNING_ONLY"
    assert registry["scope_state"] == "FUNCTIONAL_SCOPE_LOCKED"
    assert registry["source_v1_archive_path"] == "dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
    assert registry["source_v1_archive_frozen"] is True
    assert isinstance(registry["source_v1_archive_sha256"], str)
    assert len(registry["source_v1_archive_sha256"]) == 64
    assert registry["source_v1_archive_size_bytes"] > 0
    assert registry["execution_allowed"] is False
    assert registry["trade_allowed"] is False
    assert registry["external_connectivity_allowed"] is False
    assert registry["live_execution"] == "DISABLED"
    assert registry["leverage"] == "FORBIDDEN"
    assert isinstance(registry["scope_checksum"], str)
    assert len(registry["scope_checksum"]) == 64


def test_lot21_registry_counts_match_generated_jsonl_files():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    capabilities = _load_jsonl(CAPABILITIES_PATH)
    roadmap_rows = _load_jsonl(ROADMAP_PATH)
    assert registry["capability_count"] == len(capabilities)
    assert registry["phase_count"] == len(registry["roadmap_phases"])
    assert registry["future_lot_count"] == len(roadmap_rows) == 126


def test_lot21_freeze_report_mentions_the_frozen_archive():
    text = FREEZE_REPORT_PATH.read_text(encoding="utf-8")
    assert "source_v1_archive_path = dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz" in text
    assert "source_v1_archive_frozen = true" in text
    assert "source_v1_archive_sha256 =" in text
