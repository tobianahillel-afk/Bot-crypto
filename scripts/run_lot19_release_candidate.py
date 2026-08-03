#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.release import (
    DATASET_CATALOG_PATH,
    LOT19_ACCEPTANCE_OUTPUT_PATH,
    LOT19_CHECKS_OUTPUT_PATH,
    LOT19_OUTPUT_PATH,
    LOT19_REPORT_OUTPUT_PATH,
    DefensiveReleaseCandidate,
    write_acceptance_bundle,
    write_json,
    write_jsonl,
    write_release_report,
)

PAIR = "BTC/EUR"


def fail(message: str) -> int:
    print("LOT 19 RELEASE CANDIDATE: FAIL", flush=True)
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
            data_version="lot19_v0",
            start_timestamp=timestamp,
            end_timestamp=timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot19_release_candidate_v0",
            lineage_id=f"lot19_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot19",
            used_for_decision=False,
        )
    )


def main() -> int:
    candidate = DefensiveReleaseCandidate(ROOT)
    snapshot = candidate.build_snapshot()
    required_flags = [
        snapshot.release_candidate_state == "READY_FOR_LOCAL_AUDIT_REVIEW",
        snapshot.acceptance_state == "ACCEPTANCE_BUNDLE_GENERATED",
        snapshot.packaging_state == "NO_ARCHIVE_CREATED",
        not snapshot.archive_created,
        snapshot.compliance_state == "COMPLIANT",
        snapshot.no_trading_state == "ENFORCED",
        snapshot.health_state == "HEALTHY_FOR_LOCAL_AUDIT",
        snapshot.integrity_state == "VERIFIED",
        snapshot.reproducibility_state == "REPRODUCIBLE_LOCALLY",
        snapshot.pytest_state == "EXPECTED_GREEN",
        snapshot.exact_chain_state == "EXPECTED_GREEN",
        snapshot.live_execution == "DISABLED",
        snapshot.leverage == "FORBIDDEN",
        snapshot.trading_decision == "WAIT",
        snapshot.system_decision == "BLOCK_TRADING",
        snapshot.final_decision == "WAIT",
        snapshot.final_system_decision == "BLOCK_TRADING",
        not snapshot.trade_allowed,
        not snapshot.execution_allowed,
        not snapshot.external_connectivity_allowed,
        not snapshot.exchange_connector_present,
        not snapshot.order_router_present,
        not snapshot.api_key_present,
        not snapshot.websocket_present,
        not snapshot.paper_trading_present,
        not snapshot.strategy_present,
        not snapshot.forbidden_semantics_present,
        snapshot.critical_counts_valid,
        snapshot.health_monitor_valid,
        snapshot.no_trading_compliance_valid,
        snapshot.reproducibility_manifest_valid,
        snapshot.dataset_catalog_valid,
        snapshot.required_artifacts_present,
        snapshot.required_reports_present,
        snapshot.required_scripts_present,
    ]
    if not all(required_flags):
        return fail("release candidate prerequisites are not all satisfied")
    if not snapshot.release_checks:
        return fail("release_checks must be non empty")
    if not snapshot.release_checksum:
        return fail("release_checksum missing")
    write_jsonl(ROOT / LOT19_CHECKS_OUTPUT_PATH, snapshot.release_checks)
    write_release_report(ROOT / LOT19_REPORT_OUTPUT_PATH, snapshot=snapshot)
    write_acceptance_bundle(ROOT / LOT19_ACCEPTANCE_OUTPUT_PATH, snapshot=snapshot)
    write_json(ROOT / LOT19_OUTPUT_PATH, snapshot.to_dict())
    upsert_catalog(ROOT / LOT19_OUTPUT_PATH, "release_candidate_lot19", 1, snapshot.created_at)
    upsert_catalog(
        ROOT / LOT19_CHECKS_OUTPUT_PATH,
        "release_candidate_checks_lot19",
        len(snapshot.release_checks),
        snapshot.created_at,
    )
    catalog_ids = [record.get("dataset_id") for record in DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    print("LOT 19 RELEASE CANDIDATE: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
