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


def test_lot9_outputs_have_no_forbidden_fields_or_directions():
    rows = read_jsonl(ROOT / "data" / "audit" / "backtest_lot9_5m_steps.jsonl") + read_jsonl(ROOT / "data" / "audit" / "backtest_lot9_15m_steps.jsonl")
    forbidden_key_tokens = ["future_", "target", "label", "signal"]
    forbidden_values = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}
    for row in rows:
        for key, value in walk(row):
            lowered = key.lower()
            assert not any(token in lowered for token in forbidden_key_tokens)
            if isinstance(value, str):
                assert value.upper() not in forbidden_values


def test_lot9_safety_invariants_remain_unchanged():
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
