import csv
from pathlib import Path
from uuid import uuid4

from crypto_quant_bot.contracts.ohlcvt import OHLCVTCandle


class OHLCVTParseError(ValueError):
    pass


def _get(row: dict[str, str], *names: str) -> str:
    for name in names:
        if name in row and row[name] != "":
            return row[name]
    raise OHLCVTParseError(f"missing required column among {names}")


def parse_ohlcvt_csv(
    path: Path | str,
    *,
    pair: str,
    timeframe: str,
    source: str,
    lineage_id: str | None = None,
) -> list[OHLCVTCandle]:
    csv_path = Path(path)
    lineage = lineage_id or str(uuid4())
    candles: list[OHLCVTCandle] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=2):
            try:
                timestamp = _get(row, "timestamp", "time", "datetime")
                candle = OHLCVTCandle(
                    pair=pair,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=float(_get(row, "open", "o")),
                    high=float(_get(row, "high", "h")),
                    low=float(_get(row, "low", "l")),
                    close=float(_get(row, "close", "c")),
                    volume=float(_get(row, "volume", "v")),
                    trades=int(float(_get(row, "trades", "trade_count", "count"))),
                    source=source,
                    lineage_id=lineage,
                    quality_flag="valid",
                    validation_status="parsed_lot1",
                    used_for_decision=False,
                )
            except (TypeError, ValueError, OHLCVTParseError) as exc:
                raise OHLCVTParseError(f"invalid OHLCVT row at line {index}: {exc}") from exc
            candles.append(candle)

    return candles
