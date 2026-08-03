#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.product_scope import (
    DATASET_CATALOG_PATH,
    LOT21_ACCEPTANCE_DOC_PATH,
    LOT21_CAPABILITIES_OUTPUT_PATH,
    LOT21_COVERAGE_DOC_PATH,
    LOT21_OUTPUT_PATH,
    LOT21_OVERVIEW_DOC_PATH,
    LOT21_REPORT_OUTPUT_PATH,
    LOT21_ROADMAP_DOC_PATH,
    LOT21_ROADMAP_OUTPUT_PATH,
    build_product_scope_registry,
    build_scope_result,
    write_acceptance_doc,
    write_capabilities_jsonl,
    write_coverage_doc,
    write_json,
    write_overview_doc,
    write_roadmap_doc,
    write_roadmap_jsonl,
    write_scope_report,
)

PAIR = "BTC/EUR"


def fail(message: str) -> int:
    print("LOT 21 PRODUCT SCOPE: FAIL", flush=True)
    print(message, flush=True)
    return 1


def upsert_catalog(path: Path, dataset_id: str, row_count: int, timestamp: str) -> None:
    DatasetCatalog(ROOT / DATASET_CATALOG_PATH).upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_id,
            pair=PAIR,
            timeframe="multi",
            layer="audit",
            data_version="lot21_v0",
            start_timestamp=timestamp,
            end_timestamp=timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot21_product_scope_v0",
            lineage_id=f"lot21_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot21",
            used_for_decision=False,
        )
    )


def main() -> int:
    try:
        registry = build_product_scope_registry(ROOT)
        write_json(ROOT / LOT21_OUTPUT_PATH, registry.to_dict())
        write_capabilities_jsonl(ROOT / LOT21_CAPABILITIES_OUTPUT_PATH, registry.capabilities)
        write_roadmap_jsonl(ROOT / LOT21_ROADMAP_OUTPUT_PATH, registry.roadmap_lots)
        write_scope_report(ROOT / LOT21_REPORT_OUTPUT_PATH, registry=registry)
        write_overview_doc(ROOT / LOT21_OVERVIEW_DOC_PATH, registry=registry)
        write_acceptance_doc(ROOT / LOT21_ACCEPTANCE_DOC_PATH, registry=registry)
        write_roadmap_doc(ROOT / LOT21_ROADMAP_DOC_PATH, registry=registry)
        write_coverage_doc(ROOT / LOT21_COVERAGE_DOC_PATH, registry=registry)

        upsert_catalog(ROOT / LOT21_OUTPUT_PATH, "product_scope_lot21", 1, registry.created_at)
        upsert_catalog(
            ROOT / LOT21_CAPABILITIES_OUTPUT_PATH,
            "product_scope_capabilities_lot21",
            len(registry.capabilities),
            registry.created_at,
        )
        upsert_catalog(
            ROOT / LOT21_ROADMAP_OUTPUT_PATH,
            "product_scope_roadmap_lot21",
            len(registry.roadmap_lots),
            registry.created_at,
        )
        catalog_ids = [record.get("dataset_id") for record in DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()]
        if len(catalog_ids) != len(set(catalog_ids)):
            return fail("dataset_catalog contains duplicate dataset_id entries")

        result = build_scope_result(ROOT, registry)
        if result.capability_count != registry.capability_count:
            return fail("scope result capability_count mismatch")
        if result.phase_count != registry.phase_count:
            return fail("scope result phase_count mismatch")
        if result.future_lot_count != registry.future_lot_count:
            return fail("scope result future_lot_count mismatch")
    except Exception as exc:
        return fail(str(exc))

    print("LOT 21 PRODUCT SCOPE: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
