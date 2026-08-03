#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv

fixture = ROOT / "tests/fixtures/btc_eur_ohlcvt_sample.csv"
candles = parse_ohlcvt_csv(fixture, pair="BTC/EUR", timeframe="1m", source="tests_fixture_lot1bis")
print(f"parsed_candles={len(candles)}")
print(f"first_timestamp={candles[0].timestamp}")
print(f"last_timestamp={candles[-1].timestamp}")
