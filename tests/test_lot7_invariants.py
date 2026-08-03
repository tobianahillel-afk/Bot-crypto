from pathlib import Path
import json

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine

ROOT = Path(__file__).resolve().parents[1]


def walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key), value
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot7_no_forbidden_fields_or_signals():
    for path in [
        ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl",
        ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl",
    ]:
        for row in read_jsonl(path):
            for key, value in walk(row):
                lowered = key.lower()
                assert not lowered.startswith("future_")
                assert not lowered.startswith("target")
                assert lowered != "label"
                assert not (isinstance(value, str) and value.upper() in {"LONG", "SHORT"})
            assert row["data_quality"]["status"] in {"valid", "degraded", "invalid"}
            assert row["used_for_decision"] is False


def test_lot7_defensive_invariants_remain():
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    assert decision.trading_decision == "WAIT"
    assert decision.system_decision == "BLOCK_TRADING"
    assert decision.trade_allowed is False
    assert risk.trade_allowed is False
    assert "live_execution: DISABLED" in (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    assert "leverage: FORBIDDEN" in (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
