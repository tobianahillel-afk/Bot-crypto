from pathlib import Path

from crypto_quant_bot.audit.available_at import audit_available_at
from crypto_quant_bot.audit.lookahead import read_jsonl

ROOT = Path(__file__).resolve().parents[1]


def test_lot8_market_state_available_at_is_coherent():
    for relative in [
        "data/gold/btc_eur_5m_market_state_lot7.jsonl",
        "data/gold/btc_eur_15m_market_state_lot7.jsonl",
    ]:
        path = ROOT / relative
        assert audit_available_at(read_jsonl(path), path) == []


def test_lot8_available_at_detector_flags_future_component():
    rows = [
        {
            "timestamp": "2026-05-25T00:00:00Z",
            "available_at": "2026-05-25T00:05:00Z",
            "component_available_at": {"x": "2026-05-25T00:10:00Z"},
            "used_for_decision": False,
        }
    ]
    violations = audit_available_at(rows, "memory.jsonl")
    assert violations
    assert any("component_available_at" in item["path"] for item in violations)
