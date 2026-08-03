#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.data.data_writer import write_jsonl
from crypto_quant_bot.data.metadata import build_dataset_metadata
from crypto_quant_bot.data.ohlcvt_parser import parse_ohlcvt_csv
from crypto_quant_bot.data.quality import validate_ohlcvt

PAIR = "BTC/EUR"
TIMEFRAME = "1m"
SOURCE = "tests_fixture_lot1bis"
DATASET_ID = "btc_eur_1m_ohlcvt_sample_lot1bis"
FIXTURE = ROOT / "tests/fixtures/btc_eur_ohlcvt_sample.csv"
BRONZE_PATH = ROOT / "data/bronze/btc_eur_ohlcvt_sample_lot1bis.jsonl"
CATALOG_PATH = ROOT / "data/audit/dataset_catalog.json"
QUALITY_JSON_PATH = ROOT / "data/audit/lot_01_data_quality_report.json"
QUALITY_MD_PATH = ROOT / "reports/lot_01_data_quality_report.md"



def write_quality_report_md(report, metadata, bronze_path: Path) -> None:
    QUALITY_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_MD_PATH.write_text(
        "\n".join(
            [
                "# Lot 1 Data Quality Report",
                "",
                f"Dataset ID: {metadata.dataset_id}",
                f"Dataset name: {metadata.dataset_name}",
                f"Pair: {metadata.pair}",
                f"Timeframe: {metadata.timeframe}",
                f"Source: {metadata.source}",
                f"Bronze path: {bronze_path}",
                f"Rows: {report.row_count}",
                f"Quality flag: {report.quality_flag}",
                f"Duplicate rows: {report.duplicate_rows}",
                f"Invalid rows: {report.invalid_rows}",
                f"Negative volume: {report.has_negative_volume}",
                f"OHLC inconsistency: {report.has_ohlc_inconsistency}",
                f"Checksum: {metadata.checksum}",
                f"Errors: {report.errors}",
                f"Warnings: {report.warnings}",
                "",
                "Decision: VALID" if report.quality_flag == "valid" else "Decision: INVALID",
                "",
            ]
        ),
        encoding="utf-8",
    )


def ingest_fixture() -> dict:
    if not FIXTURE.exists():
        raise FileNotFoundError(f"Missing fixture: {FIXTURE}")

    candles = parse_ohlcvt_csv(FIXTURE, pair=PAIR, timeframe=TIMEFRAME, source=SOURCE)
    report = validate_ohlcvt(candles, dataset_id=DATASET_ID)
    if report.quality_flag != "valid":
        raise RuntimeError(f"Fixture quality is not valid: {report.errors}")

    write_jsonl(candles, BRONZE_PATH)
    metadata = build_dataset_metadata(
        dataset_id=DATASET_ID,
        dataset_name="BTC/EUR OHLCVT official Lot 1-bis fixture",
        path=BRONZE_PATH,
        candles=candles,
        pair=PAIR,
        timeframe=TIMEFRAME,
        source=SOURCE,
        layer="bronze",
        data_version="v1-lot1bis",
    )

    catalog = DatasetCatalog(CATALOG_PATH)
    catalog.upsert(metadata)

    QUALITY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_JSON_PATH.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_quality_report_md(report, metadata, BRONZE_PATH)

    return {
        "dataset_id": metadata.dataset_id,
        "parsed_candles": len(candles),
        "quality_flag": report.quality_flag,
        "bronze_path": str(BRONZE_PATH),
        "catalog_path": str(CATALOG_PATH),
        "quality_report": str(QUALITY_MD_PATH),
        "bronze_checksum": sha256_file(BRONZE_PATH),
    }


def main() -> int:
    ingest_fixture()
    print("LOT 1 FIXTURE INGESTION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
