import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "no_trading_compliance_lot18.json"
CHECKS_PATH = ROOT / "data" / "audit" / "no_trading_compliance_checks_lot18.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_18_no_trading_compliance_report.md"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot18_outputs_exist_and_checks_are_non_empty():
    assert SNAPSHOT_PATH.exists()
    assert CHECKS_PATH.exists()
    assert REPORT_PATH.exists()
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    checks = load_jsonl(CHECKS_PATH)
    assert isinstance(snapshot["compliance_checks"], list)
    assert len(snapshot["compliance_checks"]) == len(checks)
    assert len(checks) > 0


def test_lot18_snapshot_has_expected_states():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["compliance_state"] == "COMPLIANT"
    assert snapshot["no_trading_state"] == "ENFORCED"
    assert snapshot["execution_state"] == "DISABLED"
    assert snapshot["connectivity_state"] == "DISABLED"
    assert snapshot["artifact_integrity_state"] == "VERIFIED"
    assert snapshot["health_state"] == "HEALTHY_FOR_LOCAL_AUDIT"
    assert snapshot["reproducibility_state"] == "REPRODUCIBLE_LOCALLY"
