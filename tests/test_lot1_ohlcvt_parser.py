from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv


def test_parse_official_ohlcvt_fixture_returns_at_least_six_candles():
    fixture = ROOT / "tests/fixtures/btc_eur_ohlcvt_sample.csv"
    candles = parse_ohlcvt_csv(fixture, pair="BTC/EUR", timeframe="1m", source="test_fixture")
    assert len(candles) >= 6
    assert len(candles) == 6
    assert candles[0].pair == "BTC/EUR"
    assert candles[0].timeframe == "1m"
    assert candles[0].open == 60000.0
    assert candles[-1].trades == 44
    assert candles[0].used_for_decision is False
