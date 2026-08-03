#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.health import write_json, write_jsonl, write_report
from crypto_quant_bot.health.monitor import (
    DATASET_CATALOG_PATH,
    HEALTH_CHECKS_OUTPUT_PATH,
    HEALTH_MONITOR_OUTPUT_PATH,
    HEALTH_REPORT_OUTPUT_PATH,
    LocalHealthMonitor,
)

PAIR = "BTC/EUR"


def fail(message: str) -> int:
    print("LOT 17 HEALTH MONITOR: FAIL", flush=True)
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
            data_version="lot17_v0",
            start_timestamp=timestamp,
            end_timestamp=timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot17_health_monitor_v0",
            lineage_id=f"lot17_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot17",
            used_for_decision=False,
        )
    )


def main() -> int:
    monitor = LocalHealthMonitor(ROOT)
    snapshot = monitor.build_snapshot()
    required_flags = [
        snapshot.dataset_catalog_readable,
        snapshot.lot16_manifest_readable,
        snapshot.lot16_artifacts_readable,
        snapshot.required_artifacts_present,
        snapshot.required_reports_present,
        snapshot.required_scripts_present,
        snapshot.required_diagnostics_present,
        snapshot.critical_counts_valid,
        snapshot.checksum_references_valid,
    ]
    if not all(required_flags):
        return fail("health monitor prerequisites are not all satisfied")
    if snapshot.health_state != "HEALTHY_FOR_LOCAL_AUDIT":
        return fail(f"unexpected health_state: {snapshot.health_state}")
    if snapshot.integrity_state != "VERIFIED":
        return fail(f"unexpected integrity_state: {snapshot.integrity_state}")
    if snapshot.reproducibility_state != "REPRODUCIBLE_LOCALLY":
        return fail(f"unexpected reproducibility_state: {snapshot.reproducibility_state}")
    if snapshot.artifact_count <= 0:
        return fail("artifact_count must be positive")
    if not snapshot.health_checks:
        return fail("health_checks must be non empty")
    if not snapshot.health_checksum:
        return fail("health_checksum missing")
    write_jsonl(ROOT / HEALTH_CHECKS_OUTPUT_PATH, snapshot.health_checks)
    write_report(ROOT / HEALTH_REPORT_OUTPUT_PATH, snapshot=snapshot)
    write_json(ROOT / HEALTH_MONITOR_OUTPUT_PATH, snapshot.to_dict())
    upsert_catalog(ROOT / HEALTH_MONITOR_OUTPUT_PATH, "health_monitor_lot17", 1, snapshot.created_at)
    upsert_catalog(
        ROOT / HEALTH_CHECKS_OUTPUT_PATH,
        "health_checks_lot17",
        len(snapshot.health_checks),
        snapshot.created_at,
    )
    catalog_ids = [record.get("dataset_id") for record in DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    print("LOT 17 HEALTH MONITOR: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
