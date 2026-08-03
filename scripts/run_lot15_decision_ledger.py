#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.ledger import DecisionLedgerAuditTrail
from crypto_quant_bot.ledger.io import load_jsonl, write_jsonl, write_report

PAIR = "BTC/EUR"
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
CONTEXT_INPUTS = {
    "5m": {
        "btc_eur_5m_market_state_lot7": ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl",
        "transaction_cost_lot10_5m_estimates": ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl",
        "risk_engine_lot11_5m": ROOT / "data" / "audit" / "risk_engine_lot11_5m.jsonl",
        "exposure_guard_lot12_5m": ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl",
        "portfolio_freeze_lot13_5m": ROOT / "data" / "audit" / "portfolio_freeze_lot13_5m.jsonl",
        "final_decision_firewall_lot14_5m": ROOT / "data" / "audit" / "final_decision_firewall_lot14_5m.jsonl",
    },
    "15m": {
        "btc_eur_15m_market_state_lot7": ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl",
        "transaction_cost_lot10_15m_estimates": ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl",
        "risk_engine_lot11_15m": ROOT / "data" / "audit" / "risk_engine_lot11_15m.jsonl",
        "exposure_guard_lot12_15m": ROOT / "data" / "audit" / "exposure_guard_lot12_15m.jsonl",
        "portfolio_freeze_lot13_15m": ROOT / "data" / "audit" / "portfolio_freeze_lot13_15m.jsonl",
        "final_decision_firewall_lot14_15m": ROOT / "data" / "audit" / "final_decision_firewall_lot14_15m.jsonl",
    },
}
OUTPUTS = {
    "5m": ROOT / "data" / "audit" / "decision_ledger_lot15_5m.jsonl",
    "15m": ROOT / "data" / "audit" / "decision_ledger_lot15_15m.jsonl",
    "report": ROOT / "reports" / "lot_15_decision_ledger_report.md",
}


def fail(message: str) -> int:
    print("LOT 15 DECISION LEDGER: FAIL", flush=True)
    print(message, flush=True)
    return 1


def validate_firewall_row(row: dict[str, object], *, timeframe: str, index: int) -> str | None:
    expected = {
        "trading_decision": "WAIT",
        "system_decision": "BLOCK_TRADING",
        "final_decision": "WAIT",
        "final_system_decision": "BLOCK_TRADING",
        "decision_firewall_state": "ACTIVE",
        "execution_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
        "risk_allowed": False,
        "exposure_allowed": False,
        "portfolio_change_allowed": False,
        "allocation_change_allowed": False,
        "rebalance_allowed": False,
        "order_routing_allowed": False,
        "external_connectivity_allowed": False,
        "human_review_required": True,
    }
    if row.get("timeframe") != timeframe:
        return f"Lot 14 source row {index} has unexpected timeframe"
    for key, value in expected.items():
        if row.get(key) != value:
            return f"Lot 14 source row {index} invalid {key}: {row.get(key)}"
    return None


def ensure_documentary_context(timeframe: str) -> tuple[list[dict[str, object]], list[str], dict[str, str]] | str:
    paths = CONTEXT_INPUTS[timeframe]
    rows_by_dataset: dict[str, list[dict[str, object]]] = {}
    for dataset_id, path in paths.items():
        if not path.exists():
            return f"missing documentary input: {path}"
        rows = load_jsonl(path, max_lines=EXPECTED_COUNTS[timeframe])
        if len(rows) != EXPECTED_COUNTS[timeframe]:
            return f"unexpected documentary count for {dataset_id}: {len(rows)}"
        rows_by_dataset[dataset_id] = rows
    firewall_dataset_id = f"final_decision_firewall_lot14_{timeframe}"
    firewall_rows = rows_by_dataset[firewall_dataset_id]
    for index, row in enumerate(firewall_rows, start=1):
        message = validate_firewall_row(row, timeframe=timeframe, index=index)
        if message:
            return message
    source_artifacts = list(paths.keys())
    source_checksums = {dataset_id: sha256_file(path) for dataset_id, path in paths.items()}
    return firewall_rows, source_artifacts, source_checksums


def upsert_catalog(path: Path, dataset_id: str, timeframe: str, row_count: int, start_timestamp: str, end_timestamp: str) -> None:
    DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_id,
            pair=PAIR,
            timeframe=timeframe,
            layer="audit",
            data_version="lot15_v0",
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot15_decision_ledger_v0",
            lineage_id=f"lot15_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot15",
            used_for_decision=False,
        )
    )


def main() -> int:
    ledger = DecisionLedgerAuditTrail()
    counts: dict[str, int] = {}
    all_source_artifacts: list[str] = []
    output_paths: list[str] = []
    for timeframe in ["5m", "15m"]:
        context = ensure_documentary_context(timeframe)
        if isinstance(context, str):
            return fail(context)
        firewall_rows, source_artifacts, source_checksums = context
        entries = ledger.build_entries(
            timeframe,
            firewall_rows=firewall_rows,
            source_artifacts=source_artifacts,
            source_checksums=source_checksums,
        )
        if len(entries) != EXPECTED_COUNTS[timeframe]:
            return fail(f"unexpected ledger count for {timeframe}: {len(entries)}")
        write_jsonl(OUTPUTS[timeframe], entries)
        dataset_id = f"decision_ledger_lot15_{timeframe}"
        upsert_catalog(
            OUTPUTS[timeframe],
            dataset_id,
            timeframe,
            len(entries),
            entries[0].timestamp if entries else "",
            entries[-1].timestamp if entries else "",
        )
        counts[timeframe] = len(entries)
        all_source_artifacts.extend(source_artifacts)
        output_paths.append(str(OUTPUTS[timeframe]))
    result = ledger.build_result(
        counts_by_timeframe=counts,
        source_artifacts=sorted(set(all_source_artifacts)),
        output_paths=output_paths,
    )
    write_report(OUTPUTS["report"], result=result)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if counts.get("5m") != 36 or counts.get("15m") != 12 or result.total_entries != 48:
        return fail(f"unexpected ledger counts: {counts}, total={result.total_entries}")
    print("LOT 15 DECISION LEDGER: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
