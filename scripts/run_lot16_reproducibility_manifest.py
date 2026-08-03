#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.lineage import (
    ARTIFACT_SPECS,
    LineageManifestBuilder,
    compute_lot16_source_catalog_checksum,
    count_lot16_source_catalog_entries,
    LOT16_SOURCE_CATALOG_SCOPE,
    normalize_lot16_source_catalog_records,
    SOURCE_REPORT_PATHS,
)
from crypto_quant_bot.lineage.io import count_lines, load_json, write_json, write_jsonl, write_report

SOURCE_CATALOG_PATH = "data/audit/dataset_catalog.json"
MANIFEST_OUTPUT = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"
ARTIFACTS_OUTPUT = ROOT / "data" / "audit" / "reproducibility_artifacts_lot16.jsonl"
REPORT_OUTPUT = ROOT / "reports" / "lot_16_reproducibility_report.md"

CRITICAL_COUNT_PATHS = {
    "lot12": {
        "5m": ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl",
        "15m": ROOT / "data" / "audit" / "exposure_guard_lot12_15m.jsonl",
    },
    "lot13": {
        "5m": ROOT / "data" / "audit" / "portfolio_freeze_lot13_5m.jsonl",
        "15m": ROOT / "data" / "audit" / "portfolio_freeze_lot13_15m.jsonl",
    },
    "lot14": {
        "5m": ROOT / "data" / "audit" / "final_decision_firewall_lot14_5m.jsonl",
        "15m": ROOT / "data" / "audit" / "final_decision_firewall_lot14_15m.jsonl",
    },
    "lot15": {
        "5m": ROOT / "data" / "audit" / "decision_ledger_lot15_5m.jsonl",
        "15m": ROOT / "data" / "audit" / "decision_ledger_lot15_15m.jsonl",
    },
}
EXPECTED_COUNT = {"5m": 36, "15m": 12, "total": 48}


def fail(message: str) -> int:
    print("LOT 16 REPRODUCIBILITY MANIFEST: FAIL", flush=True)
    print(message, flush=True)
    return 1


def build_source_artifacts() -> list[str]:
    return [SOURCE_CATALOG_PATH] + SOURCE_REPORT_PATHS + [str(spec["path"]) for spec in ARTIFACT_SPECS]


def compute_critical_counts() -> dict[str, dict[str, int]] | str:
    counts: dict[str, dict[str, int]] = {}
    for lot_name, mapping in CRITICAL_COUNT_PATHS.items():
        lot_counts: dict[str, int] = {}
        for timeframe, path in mapping.items():
            if not path.exists():
                return f"missing critical artifact: {path}"
            lot_counts[timeframe] = count_lines(path)
        lot_counts["total"] = lot_counts["5m"] + lot_counts["15m"]
        if lot_counts != EXPECTED_COUNT:
            return f"unexpected critical counts for {lot_name}: {lot_counts}"
        counts[lot_name] = lot_counts
    return counts


def upsert_catalog(path: Path, dataset_id: str, row_count: int) -> None:
    DatasetCatalog(ROOT / SOURCE_CATALOG_PATH).upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_id,
            pair="BTC/EUR",
            timeframe="multi",
            layer="audit",
            data_version="lot16_v0",
            start_timestamp="",
            end_timestamp="",
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot16_reproducibility_manifest_v0",
            lineage_id=f"lot16_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot16",
            used_for_decision=False,
        )
    )


def main() -> int:
    source_catalog = ROOT / SOURCE_CATALOG_PATH
    if not source_catalog.exists():
        return fail(f"missing source catalog: {source_catalog}")
    payload = load_json(source_catalog)
    try:
        source_catalog_entries = normalize_lot16_source_catalog_records(payload)
    except TypeError as exc:
        return fail(str(exc))
    if not source_catalog_entries:
        return fail("dataset_catalog.json produced no canonical Lot 16 source entries")
    source_artifacts = build_source_artifacts()
    for relative in source_artifacts:
        if not (ROOT / relative).exists():
            return fail(f"missing explicit source artifact: {relative}")
    critical_counts = compute_critical_counts()
    if isinstance(critical_counts, str):
        return fail(critical_counts)
    builder = LineageManifestBuilder(ROOT)
    artifacts = builder.build_artifacts()
    write_jsonl(ARTIFACTS_OUTPUT, artifacts)
    manifest = builder.build_manifest(
        source_catalog_path=SOURCE_CATALOG_PATH,
        source_catalog_scope=LOT16_SOURCE_CATALOG_SCOPE,
        source_catalog_entry_count=len(source_catalog_entries),
        source_catalog_checksum=compute_lot16_source_catalog_checksum(payload),
        artifacts=artifacts,
        critical_counts=critical_counts,
        source_artifacts=source_artifacts,
    )
    write_report(REPORT_OUTPUT, manifest=manifest)
    write_json(MANIFEST_OUTPUT, manifest.to_dict())
    upsert_catalog(MANIFEST_OUTPUT, "reproducibility_manifest_lot16", 1)
    upsert_catalog(ARTIFACTS_OUTPUT, "reproducibility_artifacts_lot16", len(artifacts))
    post_upsert_payload = load_json(source_catalog)
    if compute_lot16_source_catalog_checksum(post_upsert_payload) != manifest.source_catalog_checksum:
        return fail("post-upsert source_catalog_checksum mismatch")
    if count_lot16_source_catalog_entries(post_upsert_payload) != manifest.source_catalog_entry_count:
        return fail("post-upsert source_catalog_entry_count mismatch")
    catalog_ids = [record.get("dataset_id") for record in DatasetCatalog(ROOT / SOURCE_CATALOG_PATH).load()]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    print("LOT 16 REPRODUCIBILITY MANIFEST: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
