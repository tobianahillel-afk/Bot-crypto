import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.decision.firewall import DecisionFirewall
from crypto_quant_bot.decision.models import DEFAULT_DECISION_BLOCK_REASONS


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot14_default_decision_firewall_blocks_all_execution():
    firewall = DecisionFirewall().evaluate_default()
    assert firewall.trading_decision == "WAIT"
    assert firewall.system_decision == "BLOCK_TRADING"
    assert firewall.final_decision == "WAIT"
    assert firewall.final_system_decision == "BLOCK_TRADING"
    assert firewall.decision_firewall_state == "ACTIVE"
    assert firewall.execution_allowed is False
    assert firewall.trade_allowed is False
    assert firewall.used_for_decision is False
    assert firewall.risk_allowed is False
    assert firewall.exposure_allowed is False
    assert firewall.portfolio_state == "FROZEN"
    assert firewall.portfolio_change_allowed is False
    assert firewall.allocation_change_allowed is False
    assert firewall.rebalance_allowed is False
    assert firewall.order_routing_allowed is False
    assert firewall.external_connectivity_allowed is False
    assert firewall.human_review_required is True
    assert firewall.capital_at_risk == 0
    for reason in DEFAULT_DECISION_BLOCK_REASONS:
        assert reason in firewall.decision_block_reasons


def test_lot14_dataset_catalog_contains_unique_outputs():
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "final_decision_firewall_lot14_5m" in ids
    assert "final_decision_firewall_lot14_15m" in ids


def test_lot14_rows_include_all_required_block_reasons():
    rows = load_jsonl(ROOT / "data" / "audit" / "final_decision_firewall_lot14_5m.jsonl")
    assert rows
    for reason in DEFAULT_DECISION_BLOCK_REASONS:
        assert reason in rows[0]["decision_block_reasons"]
