import json
from pathlib import Path

import pytest

from crypto_quant_bot.closure import CLOSURE_INVARIANTS, ClosurePolicy
from crypto_quant_bot.data.catalog import DatasetCatalog

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "audit" / "v1_closure_lot20.json"
CATALOG_PATH = ROOT / "data" / "audit" / "dataset_catalog.json"


def require_lot20_snapshot() -> None:
    if not SNAPSHOT_PATH.exists():
        pytest.skip("Lot 20 snapshot is generated after run_lot20_v1_closure.py")


def test_lot20_policy_defaults_are_defensive():
    policy = ClosurePolicy()
    assert policy.project_name == "Crypto Quant Bot V3.1-Ops"
    assert policy.project_mode == "EDUCATIONAL_AUDIT_ONLY"
    assert policy.closure_state == "V1_DEFENSIVE_AUDIT_CLOSED"
    assert policy.archive_state == "ARCHIVE_CREATED"
    assert policy.archive_created is True
    assert policy.live_execution == "DISABLED"
    assert policy.leverage == "FORBIDDEN"
    assert policy.trade_allowed is False
    assert policy.execution_allowed is False
    assert policy.external_connectivity_allowed is False


def test_lot20_snapshot_invariants_and_catalog_entries():
    require_lot20_snapshot()
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    invariants = snapshot["invariants"]
    for key, value in CLOSURE_INVARIANTS.items():
        assert invariants[key] == value
    assert "tests/test_pytest_suite_has_no_active_extended_subprocesses.py" in snapshot["included_paths"]
    assert "tests/test_pytest_suite_has_no_active_" + "long" + "_subprocesses.py" not in snapshot["included_paths"]
    catalog_ids = {record.get("dataset_id") for record in DatasetCatalog(CATALOG_PATH).load()}
    assert "v1_closure_lot20" in catalog_ids
    assert "v1_closure_checks_lot20" in catalog_ids
