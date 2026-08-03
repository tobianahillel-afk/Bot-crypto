import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "health_monitor_lot17.json"
CHECKS_PATH = ROOT / "data" / "audit" / "health_checks_lot17.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_17_health_monitor_report.md"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot17_outputs_exist_and_health_checks_are_non_empty():
    assert SNAPSHOT_PATH.exists()
    assert CHECKS_PATH.exists()
    assert REPORT_PATH.exists()
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    checks = load_jsonl(CHECKS_PATH)
    assert snapshot["artifact_count"] > 0
    assert isinstance(snapshot["health_checks"], list)
    assert len(snapshot["health_checks"]) == len(checks)
    assert len(checks) > 0


def test_lot17_health_snapshot_has_expected_states():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["health_state"] == "HEALTHY_FOR_LOCAL_AUDIT"
    assert snapshot["integrity_state"] == "VERIFIED"
    assert snapshot["reproducibility_state"] == "REPRODUCIBLE_LOCALLY"
    assert snapshot["monitoring_mode"] == "LOCAL_STATIC_ONLY"
