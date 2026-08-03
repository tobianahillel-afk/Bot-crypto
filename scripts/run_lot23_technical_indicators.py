#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis import (
    DATASET_CATALOG_PATH,
    LOT23_ACCEPTANCE_DOC_PATH,
    LOT23_OUTPUT_PATH,
    LOT23_OVERVIEW_DOC_PATH,
    LOT23_REPORT_OUTPUT_PATH,
    LOT23_TIMEFRAMES_OUTPUT_PATH,
    build_technical_indicator_result,
    write_indicator_acceptance_doc,
    write_indicator_overview_doc,
    write_indicator_timeframes_jsonl,
    write_json,
    write_technical_indicators_report,
)

PAIR = "BTC/EUR"


def fail(message: str) -> int:
    print("LOT 23 TECHNICAL INDICATORS: FAIL", flush=True)
    print(message, flush=True)
    return 1


def upsert_catalog(path: Path, dataset_id: str, row_count: int, timeframe: str, timestamp: str) -> None:
    DatasetCatalog(ROOT / DATASET_CATALOG_PATH).upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_id,
            pair=PAIR,
            timeframe=timeframe,
            layer="audit",
            data_version="lot23_v0",
            start_timestamp=timestamp,
            end_timestamp=timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot23_technical_indicators_v0",
            lineage_id=f"lot23_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot23",
            used_for_decision=False,
        )
    )


def main() -> int:
    try:
        snapshot = build_technical_indicator_result(ROOT)
        write_json(ROOT / LOT23_OUTPUT_PATH, snapshot.to_dict())
        write_indicator_timeframes_jsonl(ROOT / LOT23_TIMEFRAMES_OUTPUT_PATH, snapshot.timeframe_summaries)
        write_technical_indicators_report(ROOT / LOT23_REPORT_OUTPUT_PATH, snapshot=snapshot)
        write_indicator_overview_doc(ROOT / LOT23_OVERVIEW_DOC_PATH, snapshot=snapshot)
        write_indicator_acceptance_doc(ROOT / LOT23_ACCEPTANCE_DOC_PATH, snapshot=snapshot)

        upsert_catalog(ROOT / LOT23_OUTPUT_PATH, "technical_indicators_lot23", 1, "multi", snapshot.created_at)
        upsert_catalog(
            ROOT / LOT23_TIMEFRAMES_OUTPUT_PATH,
            "technical_indicators_timeframes_lot23",
            len(snapshot.timeframe_summaries),
            "multi",
            snapshot.created_at,
        )
        catalog_ids = [record.get("dataset_id") for record in DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()]
        if len(catalog_ids) != len(set(catalog_ids)):
            return fail("dataset_catalog contains duplicate dataset_id entries")
        if len(snapshot.timeframe_summaries) != 2:
            return fail("Lot 23 must produce exactly two timeframe summaries")
    except Exception as exc:
        return fail(str(exc))

    print("LOT 23 TECHNICAL INDICATORS: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
