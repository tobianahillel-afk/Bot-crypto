import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.compliance import DEFAULT_COMPLIANCE_BLOCK_REASONS
from crypto_quant_bot.compliance.no_trading_audit import COMPLIANCE_INVARIANTS, FinalNoTradingComplianceAudit


def test_lot18_default_policy_keeps_project_fully_blocked():
    policy = FinalNoTradingComplianceAudit(ROOT).default_policy()
    assert policy.project_name == "Crypto Quant Bot V3.1-Ops"
    assert policy.project_mode == "EDUCATIONAL_AUDIT_ONLY"
    assert policy.compliance_state == "COMPLIANT"
    assert policy.no_trading_state == "ENFORCED"
    assert policy.execution_state == "DISABLED"
    assert policy.connectivity_state == "DISABLED"
    assert policy.trade_allowed is False
    assert policy.execution_allowed is False
    assert policy.external_connectivity_allowed is False
    for reason in DEFAULT_COMPLIANCE_BLOCK_REASONS:
        assert reason in policy.compliance_block_reasons


def test_lot18_snapshot_keeps_required_invariants_and_catalog_ids():
    snapshot = json.loads((ROOT / "data" / "audit" / "no_trading_compliance_lot18.json").read_text(encoding="utf-8"))
    for key, value in COMPLIANCE_INVARIANTS.items():
        assert snapshot["invariants"][key] == value
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "no_trading_compliance_lot18" in ids
    assert "no_trading_compliance_checks_lot18" in ids
