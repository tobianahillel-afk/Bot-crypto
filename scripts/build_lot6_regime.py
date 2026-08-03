#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.regime.classifier import classify_regime_points
from crypto_quant_bot.regime.writer import write_regime_points

PAIR = "BTC/EUR"

INPUTS = {
    "5m": {
        "candles": ROOT / "data" / "silver" / "btc_eur_5m_ohlcvt_lot5.jsonl",
        "features": ROOT / "data" / "gold" / "btc_eur_5m_features_lot2.jsonl",
        "pivots": ROOT / "data" / "gold" / "btc_eur_5m_pivots_lot3.jsonl",
        "vwap": ROOT / "data" / "gold" / "btc_eur_5m_vwap_lot4.jsonl",
        "volatility": ROOT / "data" / "gold" / "btc_eur_5m_volatility_lot5.jsonl",
        "range": ROOT / "data" / "gold" / "btc_eur_5m_range_state_lot5.jsonl",
        "output": ROOT / "data" / "gold" / "btc_eur_5m_regime_lot6.jsonl",
        "dataset_id": "btc_eur_5m_regime_lot6",
    },
    "15m": {
        "candles": ROOT / "data" / "silver" / "btc_eur_15m_ohlcvt_lot5.jsonl",
        "features": ROOT / "data" / "gold" / "btc_eur_15m_features_lot2.jsonl",
        "pivots": ROOT / "data" / "gold" / "btc_eur_15m_pivots_lot3.jsonl",
        "vwap": ROOT / "data" / "gold" / "btc_eur_15m_vwap_lot4.jsonl",
        "volatility": ROOT / "data" / "gold" / "btc_eur_15m_volatility_lot5.jsonl",
        "range": ROOT / "data" / "gold" / "btc_eur_15m_range_state_lot5.jsonl",
        "output": ROOT / "data" / "gold" / "btc_eur_15m_regime_lot6.jsonl",
        "dataset_id": "btc_eur_15m_regime_lot6",
    },
}
def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_config() -> dict:
    with (ROOT / "config" / "regime.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def upsert_catalog(timeframe: str, path: Path, row_count: int, dataset_id: str) -> None:
    rows = read_jsonl(path)
    catalog = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json")
    catalog.upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_id,
            pair=PAIR,
            timeframe=timeframe,
            layer="gold",
            data_version="lot6_v1",
            start_timestamp=rows[0]["timestamp"] if rows else "",
            end_timestamp=rows[-1]["timestamp"] if rows else "",
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot6_regime_engine",
            lineage_id=f"lot6_{timeframe}_regime_lineage",
            quality_flag="valid",
            validation_status="validated_lot6",
            used_for_decision=False,
        )
    )


def build_one(timeframe: str, spec: dict, config: dict) -> int:
    for key in ["candles", "vwap", "volatility", "range"]:
        if not spec[key].exists():
            raise FileNotFoundError(spec[key])
    candles = read_jsonl(spec["candles"])
    vwap = read_jsonl(spec["vwap"])
    volatility = read_jsonl(spec["volatility"])
    range_rows = read_jsonl(spec["range"])
    if not (len(candles) == len(volatility) == len(range_rows)):
        raise ValueError(f"input row mismatch for {timeframe}")
    points = classify_regime_points(
        candles,
        volatility,
        range_rows,
        vwap,
        config=config,
        timeframe=timeframe,
        source_dataset_ids=[
            spec["candles"].stem,
            spec["volatility"].stem,
            spec["range"].stem,
            spec["vwap"].stem,
        ],
        lineage_id=f"lot6_{timeframe}_regime_lineage",
    )
    write_regime_points(points, spec["output"])
    upsert_catalog(timeframe, spec["output"], len(points), spec["dataset_id"])
    return len(points)


def write_reports(counts: dict[str, int]) -> None:
    report = ROOT / "reports" / "lot_06_regime_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Lot 6 Regime Report\n\n"
        "Market Regime Engine V1 generated deterministic analysis objects only.\n\n"
        f"5m regime rows: {counts['5m']}\n\n"
        f"15m regime rows: {counts['15m']}\n\n"
        "No trading, no strategy, no backtest, no target, no label and no future_* feature were generated.\n",
        encoding="utf-8",
    )


def main() -> int:
    config = load_config()
    counts = {timeframe: build_one(timeframe, spec, config) for timeframe, spec in INPUTS.items()}
    write_reports(counts)
    print("LOT 6 REGIME BUILD: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
