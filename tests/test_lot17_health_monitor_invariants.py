import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.health import DEFAULT_HEALTH_BLOCK_REASONS
from crypto_quant_bot.health.monitor import HEALTH_INVARIANTS, LocalHealthMonitor


def test_lot17_default_policy_keeps_all_paths_blocked():
    policy = LocalHealthMonitor(ROOT).default_policy()
    assert policy.project_name == "Crypto Quant Bot V3.1-Ops"
    assert policy.project_mode == "EDUCATIONAL_AUDIT_ONLY"
    assert policy.health_state == "HEALTHY_FOR_LOCAL_AUDIT"
    assert policy.integrity_state == "VERIFIED"
    assert policy.reproducibility_state == "REPRODUCIBLE_LOCALLY"
    assert policy.monitoring_mode == "LOCAL_STATIC_ONLY"
    assert policy.external_connectivity_allowed is False
    assert policy.execution_allowed is False
    assert policy.trade_allowed is False
    for reason in DEFAULT_HEALTH_BLOCK_REASONS:
        assert reason in policy.health_block_reasons


def test_lot17_snapshot_keeps_required_invariants_and_catalog_ids():
    snapshot = json.loads((ROOT / "data" / "audit" / "health_monitor_lot17.json").read_text(encoding="utf-8"))
    for key, value in HEALTH_INVARIANTS.items():
        assert snapshot["invariants"][key] == value
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "health_monitor_lot17" in ids
    assert "health_checks_lot17" in ids
