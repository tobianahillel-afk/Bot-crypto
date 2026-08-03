#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.risk.engine import RiskEngine
from crypto_quant_bot.risk.io import load_json, load_jsonl, write_jsonl, write_report

PAIR = "BTC/EUR"
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
INPUTS = {
    "run_result": ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json",
    "5m": ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl",
    "15m": ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl",
}
OUTPUTS = {
    "5m": ROOT / "data" / "audit" / "risk_engine_lot11_5m.jsonl",
    "15m": ROOT / "data" / "audit" / "risk_engine_lot11_15m.jsonl",
    "report": ROOT / "reports" / "lot_11_risk_engine_report.md",
}


def fail(message: str) -> int:
    print("LOT 11 RISK ENGINE: FAIL", flush=True)
    print(message, flush=True)
    return 1


def upsert_catalog(path: Path, dataset_id: str, timeframe: str, row_count: int, start_timestamp: str, end_timestamp: str) -> None:
    DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_id,
            pair=PAIR,
            timeframe=timeframe,
            layer="audit",
            data_version="lot11_v0",
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot11_risk_engine_v0",
            lineage_id=f"lot11_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot11",
            used_for_decision=False,
        )
    )


def main() -> int:
    for path in INPUTS.values():
        if not path.exists():
            return fail(f"missing input: {path}")
    run_result = load_json(INPUTS["run_result"])
    if not isinstance(run_result, dict):
        return fail("invalid Lot 10 run result payload")
    estimates_by_timeframe = {
        timeframe: load_jsonl(path)
        for timeframe, path in INPUTS.items()
        if timeframe in {"5m", "15m"}
    }
    engine = RiskEngine(policy_version="lot11_risk_engine_v0")
    counts: dict[str, int] = {}
    total = 0
    for timeframe, rows in estimates_by_timeframe.items():
        if len(rows) != EXPECTED_COUNTS[timeframe]:
            return fail(f"unexpected Lot 10 documentary count for {timeframe}: {len(rows)}")
        artifacts = [
            "transaction_cost_lot10_run_result",
            f"transaction_cost_lot10_{timeframe}_estimates",
        ]
        snapshots = engine.build_snapshots_from_documentary_rows(timeframe, rows, source_artifacts=artifacts)
        write_jsonl(OUTPUTS[timeframe], snapshots)
        counts[timeframe] = len(snapshots)
        total += len(snapshots)
        start_timestamp = snapshots[0].timestamp if snapshots else ""
        end_timestamp = snapshots[-1].timestamp if snapshots else ""
        upsert_catalog(
            OUTPUTS[timeframe],
            f"risk_engine_lot11_{timeframe}",
            timeframe,
            len(snapshots),
            start_timestamp,
            end_timestamp,
        )
    write_report(OUTPUTS["report"], counts=counts, total=total, run_result=run_result)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if counts.get("5m") != 36 or counts.get("15m") != 12 or total != 48:
        return fail(f"unexpected snapshot counts: {counts}, total={total}")
    print("LOT 11 RISK ENGINE: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
