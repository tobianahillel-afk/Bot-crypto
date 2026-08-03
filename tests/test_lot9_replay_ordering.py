from pathlib import Path

from crypto_quant_bot.backtest.loader import load_market_states
from crypto_quant_bot.backtest.replay import run_replay

ROOT = Path(__file__).resolve().parents[1]


def test_replay_steps_are_monotone_by_timeframe():
    states = {
        "5m": load_market_states(ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl"),
        "15m": load_market_states(ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl"),
    }
    config, steps_by_timeframe, result = run_replay("BTC/EUR", states)
    assert config.mode == "replay_v0"
    assert result.lookahead_violations == []
    assert len(steps_by_timeframe["5m"]) == 36
    assert len(steps_by_timeframe["15m"]) == 12
    for steps in steps_by_timeframe.values():
        previous = None
        for step in steps:
            key = (step.timestamp, step.available_at)
            if previous is not None:
                assert key >= previous
            previous = key
