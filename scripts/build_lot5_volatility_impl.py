#!/usr/bin/env python3
from pathlib import Path
import sys
import os
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.data.data_writer import write_jsonl
from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.data.quality import validate_ohlcvt
from crypto_quant_bot.timeframes.resampler import resample_ohlcvt
from crypto_quant_bot.volatility.engine import compute_volatility_points
from crypto_quant_bot.volatility.range_state import compute_range_state_points
from crypto_quant_bot.volatility.writer import write_range_state_points, write_volatility_points

FIXTURE = ROOT / "tests" / "fixtures" / "btc_eur_ohlcvt_1m_180_pivots.csv"
SILVER_5M = ROOT / "data" / "silver" / "btc_eur_5m_ohlcvt_lot5.jsonl"
SILVER_15M = ROOT / "data" / "silver" / "btc_eur_15m_ohlcvt_lot5.jsonl"
VOL_5M = ROOT / "data" / "gold" / "btc_eur_5m_volatility_lot5.jsonl"
VOL_15M = ROOT / "data" / "gold" / "btc_eur_15m_volatility_lot5.jsonl"
RANGE_5M = ROOT / "data" / "gold" / "btc_eur_5m_range_state_lot5.jsonl"
RANGE_15M = ROOT / "data" / "gold" / "btc_eur_15m_range_state_lot5.jsonl"
CATALOG = ROOT / "data" / "audit" / "dataset_catalog.json"
REPORT_VOL = ROOT / "reports" / "lot_05_volatility_report.md"
REPORT_RANGE = ROOT / "reports" / "lot_05_range_state_report.md"


def _record_time(record) -> str:
    for attr in ("timestamp", "available_at"):
        value = getattr(record, attr, "")
        if value:
            return value
    return ""


def metadata_for(dataset_id: str, dataset_name: str, path: Path, records: list, timeframe: str, layer: str, source: str) -> DatasetMetadata:
    start = _record_time(records[0]) if records else ""
    end = _record_time(records[-1]) if records else ""
    lineage = records[0].lineage_id if records else ""
    return DatasetMetadata(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        pair="BTC/EUR",
        timeframe=timeframe,
        source=source,
        layer=layer,
        data_version="lot5_v1",
        start_timestamp=start,
        end_timestamp=end,
        row_count=len(records),
        checksum=sha256_file(path),
        lineage_id=lineage,
        quality_flag="valid",
        validation_status="validated_lot5",
        used_for_decision=False,
    )


def main() -> int:
    candles_1m = parse_ohlcvt_csv(FIXTURE, pair="BTC/EUR", timeframe="1m", source="lot5_fixture")
    quality = validate_ohlcvt(candles_1m, dataset_id="btc_eur_1m_180_fixture_lot5")
    if len(candles_1m) != 180 or quality.quality_flag != "valid":
        print("LOT 5 VOLATILITY BUILD: FAIL")
        return 1

    candles_5m = resample_ohlcvt(candles_1m, target_timeframe="5m", lineage_id="lot5_5m_lineage")
    candles_15m = resample_ohlcvt(candles_1m, target_timeframe="15m", lineage_id="lot5_15m_lineage")
    if len(candles_5m) != 36 or len(candles_15m) != 12:
        print("LOT 5 VOLATILITY BUILD: FAIL")
        return 1

    write_jsonl(candles_5m, SILVER_5M)
    write_jsonl(candles_15m, SILVER_15M)

    volatility_5m, tr_5m = compute_volatility_points(candles_5m, source_dataset_id="btc_eur_5m_ohlcvt_lot5", lineage_id="lot5_5m_volatility_lineage")
    volatility_15m, tr_15m = compute_volatility_points(candles_15m, source_dataset_id="btc_eur_15m_ohlcvt_lot5", lineage_id="lot5_15m_volatility_lineage")
    range_5m = compute_range_state_points(candles_5m, true_range_values=tr_5m, source_dataset_id="btc_eur_5m_ohlcvt_lot5", lineage_id="lot5_5m_range_state_lineage")
    range_15m = compute_range_state_points(candles_15m, true_range_values=tr_15m, source_dataset_id="btc_eur_15m_ohlcvt_lot5", lineage_id="lot5_15m_range_state_lineage")

    write_volatility_points(volatility_5m, VOL_5M)
    write_volatility_points(volatility_15m, VOL_15M)
    write_range_state_points(range_5m, RANGE_5M)
    write_range_state_points(range_15m, RANGE_15M)

    catalog = DatasetCatalog(CATALOG)
    for args in [
        ("btc_eur_5m_ohlcvt_lot5", "BTC/EUR 5m OHLCVT Lot 5", SILVER_5M, candles_5m, "5m", "silver", "lot5_resampler"),
        ("btc_eur_15m_ohlcvt_lot5", "BTC/EUR 15m OHLCVT Lot 5", SILVER_15M, candles_15m, "15m", "silver", "lot5_resampler"),
        ("btc_eur_5m_volatility_lot5", "BTC/EUR 5m volatility Lot 5", VOL_5M, volatility_5m, "5m", "gold", "lot5_volatility_engine"),
        ("btc_eur_15m_volatility_lot5", "BTC/EUR 15m volatility Lot 5", VOL_15M, volatility_15m, "15m", "gold", "lot5_volatility_engine"),
        ("btc_eur_5m_range_state_lot5", "BTC/EUR 5m range state Lot 5", RANGE_5M, range_5m, "5m", "gold", "lot5_range_state_engine"),
        ("btc_eur_15m_range_state_lot5", "BTC/EUR 15m range state Lot 5", RANGE_15M, range_15m, "15m", "gold", "lot5_range_state_engine"),
    ]:
        catalog.upsert(metadata_for(*args))

    REPORT_VOL.write_text(
        "# Lot 5 Volatility Report\n\n"
        f"Input candles 1m: {len(candles_1m)}\n\n"
        f"5m candles: {len(candles_5m)}\n\n"
        f"15m candles: {len(candles_15m)}\n\n"
        f"5m volatility points: {len(volatility_5m)}\n\n"
        f"15m volatility points: {len(volatility_15m)}\n\n"
        "Features: realized_volatility_3, realized_volatility_6, true_range, atr_3, atr_6, hl_range, oc_range, close_to_close_abs_return.\n\n"
        "Anti-look-ahead: each point uses only candles available at or before its own available_at.\n\n"
        "No trading, no strategy, no backtest, no WebSocket, no API.\n",
        encoding="utf-8",
    )
    REPORT_RANGE.write_text(
        "# Lot 5 Range State Report\n\n"
        f"5m range state points: {len(range_5m)}\n\n"
        f"15m range state points: {len(range_15m)}\n\n"
        "Features: rolling_high_6, rolling_low_6, rolling_range_6, rolling_mid_6, close_position_in_range_6, range_width_pct, compression_score, expansion_score, range_state.\n\n"
        "Range states: unknown, compressed, normal, expanding.\n\n"
        "Anti-look-ahead: rolling windows use only current and past candles.\n\n"
        "No trading, no strategy, no backtest, no WebSocket, no API.\n",
        encoding="utf-8",
    )

    print("LOT 5 VOLATILITY BUILD: PASS")
    print(f"input_1m={len(candles_1m)}")
    print(f"silver_5m={len(candles_5m)}")
    print(f"silver_15m={len(candles_15m)}")
    print(f"volatility_5m={len(volatility_5m)}")
    print(f"volatility_15m={len(volatility_15m)}")
    print(f"range_state_5m={len(range_5m)}")
    print(f"range_state_15m={len(range_15m)}")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(0.05)
    raise SystemExit(exit_code)
