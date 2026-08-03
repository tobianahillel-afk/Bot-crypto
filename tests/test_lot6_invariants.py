import json
from pathlib import Path

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"unknown", "trend_up", "trend_down", "range", "compressed", "expanding", "volatile", "mixed"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_lot6_rows_have_no_forbidden_fields_and_scores_are_bounded():
    rows = read_jsonl(ROOT / "data/gold/btc_eur_5m_regime_lot6.jsonl") + read_jsonl(ROOT / "data/gold/btc_eur_15m_regime_lot6.jsonl")
    for row in rows:
        assert row["regime_state"] in ALLOWED
        assert isinstance(row["components"], dict)
        for key in row:
            assert not key.startswith("future_")
            assert key not in {"target", "label"}
        for key in ["trend_score", "range_score", "volatility_score", "confidence_score", "compression_score", "expansion_score"]:
            value = row.get(key)
            assert value is None or 0 <= float(value) <= 1
        value = row.get("direction_score")
        assert value is None or -1 <= float(value) <= 1


def test_lot6_safety_invariants_unchanged():
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    status = (ROOT / "config/module_status_matrix.yaml").read_text(encoding="utf-8")
    assert decision.trading_decision == "WAIT"
    assert decision.system_decision == "BLOCK_TRADING"
    assert decision.trade_allowed is False
    assert risk.trade_allowed is False
    assert "live_execution: DISABLED" in status
    assert "leverage: FORBIDDEN" in status
