import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.release import DEFAULT_RELEASE_BLOCK_REASONS
from crypto_quant_bot.release.candidate import RELEASE_INVARIANTS, DefensiveReleaseCandidate


def test_lot19_default_policy_keeps_project_fully_blocked():
    policy = DefensiveReleaseCandidate(ROOT).default_policy()
    assert policy.project_name == "Crypto Quant Bot V3.1-Ops"
    assert policy.project_mode == "EDUCATIONAL_AUDIT_ONLY"
    assert policy.release_candidate_state == "READY_FOR_LOCAL_AUDIT_REVIEW"
    assert policy.acceptance_state == "ACCEPTANCE_BUNDLE_GENERATED"
    assert policy.packaging_state == "NO_ARCHIVE_CREATED"
    assert policy.archive_created is False
    assert policy.compliance_state == "COMPLIANT"
    assert policy.no_trading_state == "ENFORCED"
    assert policy.trade_allowed is False
    assert policy.execution_allowed is False
    assert policy.external_connectivity_allowed is False
    for reason in DEFAULT_RELEASE_BLOCK_REASONS:
        assert reason in policy.release_block_reasons


def test_lot19_snapshot_keeps_required_invariants_and_catalog_ids():
    snapshot = json.loads((ROOT / "data" / "audit" / "release_candidate_lot19.json").read_text(encoding="utf-8"))
    for key, value in RELEASE_INVARIANTS.items():
        assert snapshot["invariants"][key] == value
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "release_candidate_lot19" in ids
    assert "release_candidate_checks_lot19" in ids
