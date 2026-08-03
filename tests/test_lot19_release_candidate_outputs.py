import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "release_candidate_lot19.json"
CHECKS_PATH = ROOT / "data" / "audit" / "release_candidate_checks_lot19.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_19_release_candidate_report.md"
ACCEPTANCE_PATH = ROOT / "reports" / "lot_19_acceptance_bundle.md"
VALIDATION_PATH = ROOT / "reports" / "lot_19_validation_report.md"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot19_outputs_exist_and_checks_are_non_empty():
    assert SNAPSHOT_PATH.exists()
    assert CHECKS_PATH.exists()
    assert REPORT_PATH.exists()
    assert ACCEPTANCE_PATH.exists()
    assert VALIDATION_PATH.exists()
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    checks = load_jsonl(CHECKS_PATH)
    assert isinstance(snapshot["release_checks"], list)
    assert len(snapshot["release_checks"]) == len(checks)
    assert len(checks) > 0


def test_lot19_snapshot_has_expected_states():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["release_candidate_state"] == "READY_FOR_LOCAL_AUDIT_REVIEW"
    assert snapshot["acceptance_state"] == "ACCEPTANCE_BUNDLE_GENERATED"
    assert snapshot["packaging_state"] == "NO_ARCHIVE_CREATED"
    assert snapshot["archive_created"] is False
    assert snapshot["compliance_state"] == "COMPLIANT"
    assert snapshot["no_trading_state"] == "ENFORCED"
    assert snapshot["health_state"] == "HEALTHY_FOR_LOCAL_AUDIT"
    assert snapshot["reproducibility_state"] == "REPRODUCIBLE_LOCALLY"
    assert snapshot["pytest_state"] == "EXPECTED_GREEN"
    assert snapshot["exact_chain_state"] == "EXPECTED_GREEN"
    assert snapshot["live_execution"] == "DISABLED"
    assert snapshot["leverage"] == "FORBIDDEN"
    assert snapshot["trading_decision"] == "WAIT"
    assert snapshot["system_decision"] == "BLOCK_TRADING"
    assert snapshot["final_decision"] == "WAIT"
    assert snapshot["final_system_decision"] == "BLOCK_TRADING"
    assert snapshot["trade_allowed"] is False
    assert snapshot["execution_allowed"] is False
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["exchange_connector_present"] is False
    assert snapshot["order_router_present"] is False
    assert snapshot["api" + "_" + "key_present"] is False
    assert snapshot["web" + "socket_present"] is False
    assert snapshot["paper_trading_present"] is False
    assert snapshot["strategy_present"] is False
    assert snapshot["forbidden_semantics_present"] is False
    assert snapshot["critical_counts_valid"] is True
    assert snapshot["health_monitor_valid"] is True
    assert snapshot["no_trading_compliance_valid"] is True
    assert snapshot["reproducibility_manifest_valid"] is True
    assert snapshot["dataset_catalog_valid"] is True
    assert snapshot["required_artifacts_present"] is True
    assert snapshot["required_reports_present"] is True
    assert snapshot["required_scripts_present"] is True
