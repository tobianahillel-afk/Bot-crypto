#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.portfolio.freeze import PortfolioFreeze
from crypto_quant_bot.portfolio.io import load_jsonl, write_jsonl, write_report

PAIR = "BTC/EUR"
EXPECTED_COUNTS = {"5m": 36, "15m": 12}
COST_INPUTS = {
    "5m": ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl",
    "15m": ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl",
}
RISK_INPUTS = {
    "5m": ROOT / "data" / "audit" / "risk_engine_lot11_5m.jsonl",
    "15m": ROOT / "data" / "audit" / "risk_engine_lot11_15m.jsonl",
}
EXPOSURE_INPUTS = {
    "5m": ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl",
    "15m": ROOT / "data" / "audit" / "exposure_guard_lot12_15m.jsonl",
}
OUTPUTS = {
    "5m": ROOT / "data" / "audit" / "portfolio_freeze_lot13_5m.jsonl",
    "15m": ROOT / "data" / "audit" / "portfolio_freeze_lot13_15m.jsonl",
    "report": ROOT / "reports" / "lot_13_portfolio_freeze_report.md",
}


def fail(message: str) -> int:
    print("LOT 13 PORTFOLIO FREEZE: FAIL", flush=True)
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
            data_version="lot13_v0",
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot13_portfolio_freeze_v0",
            lineage_id=f"lot13_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot13",
            used_for_decision=False,
        )
    )


def main() -> int:
    for mapping in [COST_INPUTS, RISK_INPUTS, EXPOSURE_INPUTS]:
        for path in mapping.values():
            if not path.exists():
                return fail(f"missing input: {path}")
    freezer = PortfolioFreeze(policy_version="lot13_portfolio_freeze_v0")
    counts: dict[str, int] = {}
    total = 0
    for timeframe in ["5m", "15m"]:
        cost_rows = load_jsonl(COST_INPUTS[timeframe], max_lines=EXPECTED_COUNTS[timeframe])
        risk_rows = load_jsonl(RISK_INPUTS[timeframe], max_lines=EXPECTED_COUNTS[timeframe])
        exposure_rows = load_jsonl(EXPOSURE_INPUTS[timeframe], max_lines=EXPECTED_COUNTS[timeframe])
        if len(cost_rows) != EXPECTED_COUNTS[timeframe]:
            return fail(f"unexpected Lot 10 documentary count for {timeframe}: {len(cost_rows)}")
        if len(risk_rows) != EXPECTED_COUNTS[timeframe]:
            return fail(f"unexpected Lot 11 documentary count for {timeframe}: {len(risk_rows)}")
        if len(exposure_rows) != EXPECTED_COUNTS[timeframe]:
            return fail(f"unexpected Lot 12 documentary count for {timeframe}: {len(exposure_rows)}")
        snapshots = freezer.build_snapshots(
            timeframe,
            cost_rows=cost_rows,
            risk_rows=risk_rows,
            exposure_rows=exposure_rows,
            source_artifacts=[
                f"transaction_cost_lot10_{timeframe}_estimates",
                f"risk_engine_lot11_{timeframe}",
                f"exposure_guard_lot12_{timeframe}",
            ],
        )
        write_jsonl(OUTPUTS[timeframe], snapshots)
        counts[timeframe] = len(snapshots)
        total += len(snapshots)
        start_timestamp = snapshots[0].timestamp if snapshots else ""
        end_timestamp = snapshots[-1].timestamp if snapshots else ""
        upsert_catalog(
            OUTPUTS[timeframe],
            f"portfolio_freeze_lot13_{timeframe}",
            timeframe,
            len(snapshots),
            start_timestamp,
            end_timestamp,
        )
    write_report(OUTPUTS["report"], counts=counts, total=total)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if counts.get("5m") != 36 or counts.get("15m") != 12 or total != 48:
        return fail(f"unexpected snapshot counts: {counts}, total={total}")
    print("LOT 13 PORTFOLIO FREEZE: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
