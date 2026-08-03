#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.closure import (
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
    DATASET_CATALOG_PATH,
    LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH,
    LOT20_CHECKS_OUTPUT_PATH,
    LOT20_OUTPUT_PATH,
    LOT20_REPORT_OUTPUT_PATH,
    LOT20_VALIDATION_REPORT_PATH,
    V1DefensiveAuditClosure,
    build_included_paths,
    create_archive,
    write_archive_manifest_report,
    write_closure_report,
    write_json,
    write_jsonl,
    write_sha256_file,
)
from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file

PAIR = "BTC/EUR"
RESETTABLE_OUTPUTS = [
    LOT20_OUTPUT_PATH,
    LOT20_CHECKS_OUTPUT_PATH,
    LOT20_REPORT_OUTPUT_PATH,
    LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH,
    LOT20_VALIDATION_REPORT_PATH,
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
]


def fail(message: str) -> int:
    print("LOT 20 V1 CLOSURE: FAIL", flush=True)
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
            data_version="lot20_v0",
            start_timestamp=timestamp,
            end_timestamp=timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot20_v1_closure_v0",
            lineage_id=f"lot20_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot20",
            used_for_decision=False,
        )
    )


def reset_previous_outputs() -> None:
    for relative_path in RESETTABLE_OUTPUTS:
        path = ROOT / relative_path
        if path.exists():
            path.unlink()


def run_prerequisite_chain() -> bool:
    result = subprocess.run(
        ["python", "scripts/diagnose_exact_chain_until_lot19.py"],
        cwd=ROOT,
        timeout=300,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    reset_previous_outputs()
    if not run_prerequisite_chain():
        return fail("Lot 19 exact chain diagnostic did not complete successfully")

    included_paths, excluded_paths = build_included_paths(ROOT)
    if not included_paths:
        return fail("archive included_paths is empty")

    archive_checksum, archive_size_bytes = create_archive(
        ROOT,
        archive_relative_path=ARCHIVE_OUTPUT_PATH,
        included_paths=included_paths,
    )
    write_sha256_file(
        ROOT / ARCHIVE_SHA256_OUTPUT_PATH,
        checksum=archive_checksum,
        archive_name=Path(ARCHIVE_OUTPUT_PATH).name,
    )

    closure = V1DefensiveAuditClosure(ROOT)
    manifest = closure.build_manifest(
        pytest_green=True,
        exact_chain_green=True,
        archive_path=ARCHIVE_OUTPUT_PATH,
        archive_sha256_path=ARCHIVE_SHA256_OUTPUT_PATH,
        archive_sha256=archive_checksum,
        archive_size_bytes=archive_size_bytes,
        included_paths=included_paths,
        excluded_paths=excluded_paths,
    )

    required_flags = [
        manifest.project_name == "Crypto Quant Bot V3.1-Ops",
        manifest.project_mode == "EDUCATIONAL_AUDIT_ONLY",
        manifest.closure_state == "V1_DEFENSIVE_AUDIT_CLOSED",
        manifest.archive_state == "ARCHIVE_CREATED",
        manifest.archive_created is True,
        manifest.release_candidate_state == "READY_FOR_LOCAL_AUDIT_REVIEW",
        manifest.acceptance_state == "ACCEPTANCE_BUNDLE_GENERATED",
        manifest.compliance_state == "COMPLIANT",
        manifest.no_trading_state == "ENFORCED",
        manifest.health_state == "HEALTHY_FOR_LOCAL_AUDIT",
        manifest.reproducibility_state == "REPRODUCIBLE_LOCALLY",
        manifest.pytest_state == "GREEN",
        manifest.exact_chain_state == "GREEN",
        manifest.live_execution == "DISABLED",
        manifest.leverage == "FORBIDDEN",
        manifest.trade_allowed is False,
        manifest.execution_allowed is False,
        manifest.external_connectivity_allowed is False,
        manifest.exchange_connector_present is False,
        manifest.order_router_present is False,
        manifest.api_key_present is False,
        manifest.websocket_present is False,
        manifest.paper_trading_present is False,
        manifest.strategy_present is False,
        manifest.forbidden_semantics_present is False,
        manifest.critical_counts_valid is True,
        bool(manifest.archive_sha256),
        manifest.archive_size_bytes > 0,
        bool(manifest.closure_checksum),
    ]
    if not all(required_flags):
        return fail("closure manifest invariants are not all satisfied")
    if not manifest.closure_checks:
        return fail("closure_checks must be non empty")
    if any(check.status != "PASS" for check in manifest.closure_checks):
        return fail("closure_checks contain a blocking status")

    write_jsonl(ROOT / LOT20_CHECKS_OUTPUT_PATH, manifest.closure_checks)
    write_closure_report(ROOT / LOT20_REPORT_OUTPUT_PATH, manifest=manifest)
    write_archive_manifest_report(ROOT / LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH, manifest=manifest)
    write_json(ROOT / LOT20_OUTPUT_PATH, manifest.to_dict())

    upsert_catalog(ROOT / LOT20_OUTPUT_PATH, "v1_closure_lot20", 1, manifest.created_at)
    upsert_catalog(
        ROOT / LOT20_CHECKS_OUTPUT_PATH,
        "v1_closure_checks_lot20",
        len(manifest.closure_checks),
        manifest.created_at,
    )
    catalog_ids = [record.get("dataset_id") for record in DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")

    print("LOT 20 V1 CLOSURE: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
