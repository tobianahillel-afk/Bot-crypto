import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.ledger import DEFAULT_LEDGER_BLOCK_REASONS, DecisionLedgerAuditTrail


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot15_default_policy_keeps_all_paths_blocked():
    policy = DecisionLedgerAuditTrail().default_policy()
    assert policy.trading_decision == "WAIT"
    assert policy.system_decision == "BLOCK_TRADING"
    assert policy.final_decision == "WAIT"
    assert policy.final_system_decision == "BLOCK_TRADING"
    assert policy.decision_firewall_state == "ACTIVE"
    assert policy.execution_allowed is False
    assert policy.trade_allowed is False
    assert policy.used_for_decision is False
    assert policy.risk_allowed is False
    assert policy.exposure_allowed is False
    assert policy.portfolio_change_allowed is False
    assert policy.allocation_change_allowed is False
    assert policy.rebalance_allowed is False
    assert policy.order_routing_allowed is False
    assert policy.external_connectivity_allowed is False
    assert policy.human_review_required is True
    assert policy.ledger_state == "RECORDED"
    assert policy.audit_trail_state == "ACTIVE"
    assert policy.immutability_mode == "APPEND_ONLY_SIMULATED"
    for reason in DEFAULT_LEDGER_BLOCK_REASONS:
        assert reason in policy.ledger_block_reasons


def test_lot15_dataset_catalog_contains_unique_outputs():
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "decision_ledger_lot15_5m" in ids
    assert "decision_ledger_lot15_15m" in ids


def test_lot15_rows_include_all_required_block_reasons():
    rows = load_jsonl(ROOT / "data" / "audit" / "decision_ledger_lot15_5m.jsonl")
    assert rows
    for reason in DEFAULT_LEDGER_BLOCK_REASONS:
        assert reason in rows[0]["ledger_block_reasons"]
