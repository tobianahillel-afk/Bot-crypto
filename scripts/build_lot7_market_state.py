#!/usr/bin/env python3
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.audit.writer import _atomic_write_text
from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.contracts.market_state import MarketStatePoint
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_state.assembler import assemble_market_states
from crypto_quant_bot.market_state.loader import group_by_timestamp, index_by_timestamp, read_jsonl
from crypto_quant_bot.market_state.writer import write_market_states

PAIR = "BTC/EUR"

INPUTS = {
    "5m": {
        "candles": ROOT / "data" / "silver" / "btc_eur_5m_ohlcvt_lot5.jsonl",
        "features": ROOT / "data" / "gold" / "btc_eur_5m_features_lot2.jsonl",
        "pivots": ROOT / "data" / "gold" / "btc_eur_5m_pivots_lot3.jsonl",
        "zones": ROOT / "data" / "gold" / "btc_eur_5m_price_zones_lot3.jsonl",
        "vwap": ROOT / "data" / "gold" / "btc_eur_5m_vwap_lot4.jsonl",
        "anchored_vwap": ROOT / "data" / "gold" / "btc_eur_5m_anchored_vwap_lot4.jsonl",
        "volatility": ROOT / "data" / "gold" / "btc_eur_5m_volatility_lot5.jsonl",
        "range": ROOT / "data" / "gold" / "btc_eur_5m_range_state_lot5.jsonl",
        "regime": ROOT / "data" / "gold" / "btc_eur_5m_regime_lot6.jsonl",
        "output": ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl",
        "dataset_id": "btc_eur_5m_market_state_lot7",
    },
    "15m": {
        "candles": ROOT / "data" / "silver" / "btc_eur_15m_ohlcvt_lot5.jsonl",
        "features": ROOT / "data" / "gold" / "btc_eur_15m_features_lot2.jsonl",
        "pivots": ROOT / "data" / "gold" / "btc_eur_15m_pivots_lot3.jsonl",
        "zones": ROOT / "data" / "gold" / "btc_eur_15m_price_zones_lot3.jsonl",
        "vwap": ROOT / "data" / "gold" / "btc_eur_15m_vwap_lot4.jsonl",
        "anchored_vwap": ROOT / "data" / "gold" / "btc_eur_15m_anchored_vwap_lot4.jsonl",
        "volatility": ROOT / "data" / "gold" / "btc_eur_15m_volatility_lot5.jsonl",
        "range": ROOT / "data" / "gold" / "btc_eur_15m_range_state_lot5.jsonl",
        "regime": ROOT / "data" / "gold" / "btc_eur_15m_regime_lot6.jsonl",
        "output": ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl",
        "dataset_id": "btc_eur_15m_market_state_lot7",
    },
}


def _point_timestamp(point: MarketStatePoint) -> str:
    return str(point.timestamp)


def upsert_catalog(timeframe: str, path: Path, points: list[MarketStatePoint], dataset_id: str) -> None:
    catalog = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json")
    catalog.upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_id,
            pair=PAIR,
            timeframe=timeframe,
            layer="gold",
            data_version="lot7_v1",
            start_timestamp=_point_timestamp(points[0]) if points else "",
            end_timestamp=_point_timestamp(points[-1]) if points else "",
            row_count=len(points),
            checksum=sha256_file(path),
            source="lot7_market_state_engine",
            lineage_id=f"lot7_{timeframe}_market_state_lineage",
            quality_flag="valid",
            validation_status="validated_lot7",
            used_for_decision=False,
        )
    )


def build_one(timeframe: str, spec: dict) -> int:
    for name, path in spec.items():
        if name in {"output", "dataset_id"}:
            continue
        if not path.exists():
            raise FileNotFoundError(path)
    candles = read_jsonl(spec["candles"])
    points = assemble_market_states(
        pair=PAIR,
        timeframe=timeframe,
        candles=candles,
        features_by_timestamp=index_by_timestamp(read_jsonl(spec["features"])),
        pivots=read_jsonl(spec["pivots"]),
        zones=read_jsonl(spec["zones"]),
        vwap_by_timestamp=index_by_timestamp(read_jsonl(spec["vwap"])),
        anchored_vwap_by_timestamp=group_by_timestamp(read_jsonl(spec["anchored_vwap"])),
        volatility_by_timestamp=index_by_timestamp(read_jsonl(spec["volatility"])),
        range_by_timestamp=index_by_timestamp(read_jsonl(spec["range"])),
        regime_by_timestamp=index_by_timestamp(read_jsonl(spec["regime"])),
        source_dataset_ids=[
            spec["candles"].stem,
            spec["features"].stem,
            spec["pivots"].stem,
            spec["zones"].stem,
            spec["vwap"].stem,
            spec["anchored_vwap"].stem,
            spec["volatility"].stem,
            spec["range"].stem,
            spec["regime"].stem,
        ],
        lineage_id=f"lot7_{timeframe}_market_state_lineage",
    )
    write_market_states(points, spec["output"])
    upsert_catalog(timeframe, spec["output"], points, spec["dataset_id"])
    return len(points)


def write_report(counts: dict[str, int]) -> None:
    report = ROOT / "reports" / "lot_07_market_state_report.md"
    _atomic_write_text(
        report,
        "# Lot 7 Market State Report\n\n"
        "Market State Engine V1 assembled deterministic analysis objects only.\n\n"
        f"5m market_state rows: {counts['5m']}\n\n"
        f"15m market_state rows: {counts['15m']}\n\n"
        "No trading, no strategy, no backtest, no target, no label and no future_* feature were generated.\n",
    )


def main() -> int:
    counts = {timeframe: build_one(timeframe, spec) for timeframe, spec in INPUTS.items()}
    write_report(counts)
    print("LOT 7 MARKET STATE BUILD: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
