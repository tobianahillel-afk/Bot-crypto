import json
from pathlib import Path

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine

ROOT = Path(__file__).resolve().parents[1]


def walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key), value
            yield from walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item)


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot10_outputs_have_no_forbidden_trading_or_leakage_fields():
    rows = read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl") + read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl")
    forbidden_key_tokens = ["future_", "target", "label", "long_signal", "short_signal", "trade_signal", "entry_signal", "exit_signal", "buy", "sell"]
    forbidden_values = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}
    for row in rows:
        for key, value in walk(row):
            lowered = key.lower()
            assert not any(token in lowered for token in forbidden_key_tokens)
            assert lowered != "signal"
            if isinstance(value, str):
                assert value.upper() not in forbidden_values


def test_lot10_safety_invariants_remain_unchanged():
    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    assert "live_execution: DISABLED" in status_text
    assert "leverage: FORBIDDEN" in status_text
    assert "trade_allowed_default: false" in risk_text
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    assert decision.trading_decision == "WAIT"
    assert decision.system_decision == "BLOCK_TRADING"
    assert decision.trade_allowed is False
    assert risk.trade_allowed is False


def test_lot10_dataset_catalog_contains_unique_lot10_outputs():
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    for dataset_id in [
        "transaction_cost_lot10_5m_estimates",
        "transaction_cost_lot10_15m_estimates",
        "transaction_cost_lot10_run_result",
    ]:
        assert dataset_id in ids
