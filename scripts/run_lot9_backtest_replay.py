#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.backtest.loader import load_market_states
from crypto_quant_bot.backtest.replay import run_replay
from crypto_quant_bot.backtest.writer import write_report, write_run_config, write_run_result, write_steps
from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file

PAIR = "BTC/EUR"
INPUTS = {
    "5m": ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl",
    "15m": ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl",
}
OUTPUTS = {
    "run_config": ROOT / "data" / "audit" / "backtest_lot9_run_config.json",
    "run_result": ROOT / "data" / "audit" / "backtest_lot9_run_result.json",
    "5m": ROOT / "data" / "audit" / "backtest_lot9_5m_steps.jsonl",
    "15m": ROOT / "data" / "audit" / "backtest_lot9_15m_steps.jsonl",
    "report": ROOT / "reports" / "lot_09_backtest_replay_report.md",
}



def upsert_catalog(relative_path: Path, dataset_id: str, dataset_name: str, timeframe: str, row_count: int, start_timestamp: str, end_timestamp: str) -> None:
    path = ROOT / relative_path
    DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            pair=PAIR,
            timeframe=timeframe,
            layer="audit",
            data_version="lot9_v0",
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot9_backtest_replay_v0",
            lineage_id=f"lot9_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot9",
            used_for_decision=False,
        )
    )


def main() -> int:
    for path in INPUTS.values():
        if not path.exists():
            print(f"missing input: {path}")
            return 1
    market_states = {timeframe: load_market_states(path) for timeframe, path in INPUTS.items()}
    config, steps_by_timeframe, result = run_replay(PAIR, market_states)
    write_run_config(OUTPUTS["run_config"], config)
    write_run_result(OUTPUTS["run_result"], result)
    counts = {}
    for timeframe, steps in steps_by_timeframe.items():
        write_steps(OUTPUTS[timeframe], steps)
        counts[timeframe] = len(steps)
    write_report(OUTPUTS["report"], config, result, counts)
    for timeframe, steps in steps_by_timeframe.items():
        relative = OUTPUTS[timeframe].relative_to(ROOT)
        start = steps[0].timestamp if steps else ""
        end = steps[-1].timestamp if steps else ""
        upsert_catalog(relative, f"backtest_lot9_{timeframe}_steps", f"backtest_lot9_{timeframe}_steps", timeframe, len(steps), start, end)
    upsert_catalog(OUTPUTS["run_config"].relative_to(ROOT), "backtest_lot9_run_config", "backtest_lot9_run_config", "multi", 1, config.start_timestamp, config.end_timestamp)
    upsert_catalog(OUTPUTS["run_result"].relative_to(ROOT), "backtest_lot9_run_result", "backtest_lot9_run_result", "multi", 1, result.start_timestamp, result.end_timestamp)
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        print("LOT 9 BACKTEST REPLAY: FAIL")
        print("dataset_catalog contains duplicate dataset_id entries")
        return 1
    if counts.get("5m") != 36 or counts.get("15m") != 12:
        print("LOT 9 BACKTEST REPLAY: FAIL")
        print(f"unexpected counts: {counts}")
        return 1
    if result.decision_counts.get("WAIT") != 48 or result.orders_created_count != 0 or result.fills_created_count != 0 or result.pnl_total != 0:
        print("LOT 9 BACKTEST REPLAY: FAIL")
        print(result.to_dict())
        return 1
    if result.lookahead_violations:
        print("LOT 9 BACKTEST REPLAY: FAIL")
        print(result.lookahead_violations[:1])
        return 1
    print("LOT 9 BACKTEST REPLAY: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
