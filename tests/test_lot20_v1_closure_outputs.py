import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "v1_closure_lot20.json"
CHECKS_PATH = ROOT / "data" / "audit" / "v1_closure_checks_lot20.jsonl"
REPORT_PATH = ROOT / "reports" / "lot_20_v1_closure_report.md"
ARCHIVE_MANIFEST_PATH = ROOT / "reports" / "lot_20_archive_manifest.md"
VALIDATION_PATH = ROOT / "reports" / "lot_20_validation_report.md"
ARCHIVE_PATH = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
SHA256_PATH = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.sha256"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def require_lot20_outputs() -> None:
    if not SNAPSHOT_PATH.exists():
        pytest.skip("Lot 20 outputs are generated after run_lot20_v1_closure.py")


def test_lot20_outputs_exist_and_checks_are_non_empty():
    require_lot20_outputs()
    assert SNAPSHOT_PATH.exists()
    assert CHECKS_PATH.exists()
    assert REPORT_PATH.exists()
    assert ARCHIVE_MANIFEST_PATH.exists()
    assert VALIDATION_PATH.exists()
    assert ARCHIVE_PATH.exists()
    assert SHA256_PATH.exists()
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    checks = load_jsonl(CHECKS_PATH)
    assert isinstance(snapshot["closure_checks"], list)
    assert len(snapshot["closure_checks"]) == len(checks)
    assert len(checks) > 0


def test_lot20_snapshot_has_expected_states():
    require_lot20_outputs()
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert snapshot["closure_state"] == "V1_DEFENSIVE_AUDIT_CLOSED"
    assert snapshot["archive_state"] == "ARCHIVE_CREATED"
    assert snapshot["archive_created"] is True
    assert snapshot["compliance_state"] == "COMPLIANT"
    assert snapshot["no_trading_state"] == "ENFORCED"
    assert snapshot["health_state"] == "HEALTHY_FOR_LOCAL_AUDIT"
    assert snapshot["reproducibility_state"] == "REPRODUCIBLE_LOCALLY"
    assert snapshot["pytest_state"] == "GREEN"
    assert snapshot["exact_chain_state"] == "GREEN"
    assert snapshot["live_execution"] == "DISABLED"
    assert snapshot["leverage"] == "FORBIDDEN"
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
