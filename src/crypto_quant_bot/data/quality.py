from collections import Counter

from crypto_quant_bot.contracts.data_quality import DataQualityReport
from crypto_quant_bot.contracts.ohlcvt import OHLCVTCandle
from crypto_quant_bot.core.clock import utc_now_iso


def validate_ohlcvt(candles: list[OHLCVTCandle], *, dataset_id: str) -> DataQualityReport:
    errors: list[str] = []
    warnings: list[str] = []
    invalid_rows = 0
    negative_volume = False
    ohlc_inconsistency = False

    timestamps = [candle.timestamp for candle in candles]
    duplicate_rows = sum(count - 1 for count in Counter(timestamps).values() if count > 1)
    monotonic = timestamps == sorted(timestamps)

    if not candles:
        errors.append("dataset_is_empty")

    if duplicate_rows:
        errors.append("duplicate_timestamps")

    if not monotonic:
        errors.append("timestamps_not_monotonic")

    for candle in candles:
        if candle.volume < 0:
            negative_volume = True
            invalid_rows += 1
        if candle.low > candle.high:
            ohlc_inconsistency = True
            invalid_rows += 1
        if not (candle.low <= candle.open <= candle.high):
            ohlc_inconsistency = True
            invalid_rows += 1
        if not (candle.low <= candle.close <= candle.high):
            ohlc_inconsistency = True
            invalid_rows += 1
        if candle.trades < 0:
            invalid_rows += 1
            errors.append("negative_trades")

    if negative_volume:
        errors.append("negative_volume")
    if ohlc_inconsistency:
        errors.append("ohlc_inconsistency")

    quality_flag = "valid" if not errors else "invalid"
    validation_status = "validated_lot1" if not errors else "failed_lot1"

    return DataQualityReport(
        dataset_id=dataset_id,
        checked_at=utc_now_iso(),
        row_count=len(candles),
        missing_rows=0,
        duplicate_rows=duplicate_rows,
        invalid_rows=invalid_rows,
        monotonic_timestamp=monotonic,
        has_negative_volume=negative_volume,
        has_ohlc_inconsistency=ohlc_inconsistency,
        quality_flag=quality_flag,
        validation_status=validation_status,
        errors=errors,
        warnings=warnings,
    )
