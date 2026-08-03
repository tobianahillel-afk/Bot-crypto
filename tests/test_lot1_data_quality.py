from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.data.quality import validate_ohlcvt


def test_data_quality_report_valid_for_official_fixture():
    fixture = ROOT / "tests/fixtures/btc_eur_ohlcvt_sample.csv"
    candles = parse_ohlcvt_csv(fixture, pair="BTC/EUR", timeframe="1m", source="test_fixture")
    report = validate_ohlcvt(candles, dataset_id="test_dataset")
    assert report.row_count == 6
    assert report.duplicate_rows == 0
    assert report.invalid_rows == 0
    assert report.monotonic_timestamp is True
    assert report.has_negative_volume is False
    assert report.has_ohlc_inconsistency is False
    assert report.quality_flag == "valid"


def test_invalid_fixture_is_detected_as_invalid_or_degraded():
    fixture = ROOT / "tests/fixtures/btc_eur_ohlcvt_invalid.csv"
    candles = parse_ohlcvt_csv(fixture, pair="BTC/EUR", timeframe="1m", source="invalid_fixture")
    report = validate_ohlcvt(candles, dataset_id="invalid_dataset")
    assert report.quality_flag in {"invalid", "degraded"}
    assert report.duplicate_rows > 0
    assert report.invalid_rows > 0
    assert report.has_negative_volume is True
    assert report.has_ohlc_inconsistency is True
    assert "negative_trades" in report.errors
