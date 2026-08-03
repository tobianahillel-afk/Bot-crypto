#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts.dataset import DatasetMetadata
from crypto_quant_bot.costs.config import load_raw_transaction_cost_config, load_transaction_cost_config
from crypto_quant_bot.costs.estimator import estimate_transaction_costs
from crypto_quant_bot.costs.writer import write_estimates, write_report, write_run_result
from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file

PAIR = "BTC/EUR"
CONFIG_PATH = ROOT / "config" / "transaction_costs.yaml"
STEP_INPUTS = {
    "5m": ROOT / "data" / "audit" / "backtest_lot9_5m_steps.jsonl",
    "15m": ROOT / "data" / "audit" / "backtest_lot9_15m_steps.jsonl",
}
MARKET_STATE_INPUTS = {
    "5m": ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl",
    "15m": ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl",
}
OUTPUTS = {
    "run_result": ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json",
    "5m": ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl",
    "15m": ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl",
    "report": ROOT / "reports" / "lot_10_transaction_costs_report.md",
}



def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"invalid JSONL row in {path}")
            rows.append(payload)
    return rows


def upsert_catalog(relative_path: Path, dataset_id: str, dataset_name: str, timeframe: str, row_count: int, start_timestamp: str, end_timestamp: str) -> None:
    path = ROOT / relative_path
    DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").upsert(
        DatasetMetadata(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            pair=PAIR,
            timeframe=timeframe,
            layer="audit",
            data_version="lot10_v0",
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            row_count=row_count,
            checksum=sha256_file(path),
            source="lot10_transaction_cost_model_v0",
            lineage_id=f"lot10_{dataset_id}_lineage",
            quality_flag="valid",
            validation_status="validated_lot10",
            used_for_decision=False,
        )
    )


def main() -> int:
    inputs = [CONFIG_PATH, *STEP_INPUTS.values(), *MARKET_STATE_INPUTS.values()]
    for path in inputs:
        if not path.exists():
            print(f"missing input: {path}", flush=True)
            return 1
    config = load_transaction_cost_config(CONFIG_PATH)
    raw_config = load_raw_transaction_cost_config(CONFIG_PATH)
    steps_by_timeframe = {timeframe: load_jsonl(path) for timeframe, path in STEP_INPUTS.items()}
    market_states_by_timeframe = {timeframe: load_jsonl(path) for timeframe, path in MARKET_STATE_INPUTS.items()}
    estimates_by_timeframe, result = estimate_transaction_costs(config, raw_config, steps_by_timeframe, market_states_by_timeframe)
    counts = {}
    for timeframe, estimates in estimates_by_timeframe.items():
        write_estimates(OUTPUTS[timeframe], estimates)
        counts[timeframe] = len(estimates)
    write_run_result(OUTPUTS["run_result"], result)
    write_report(OUTPUTS["report"], result, counts)
    for timeframe, estimates in estimates_by_timeframe.items():
        start = estimates[0].timestamp if estimates else ""
        end = estimates[-1].timestamp if estimates else ""
        upsert_catalog(
            OUTPUTS[timeframe].relative_to(ROOT),
            f"transaction_cost_lot10_{timeframe}_estimates",
            f"transaction_cost_lot10_{timeframe}_estimates",
            timeframe,
            len(estimates),
            start,
            end,
        )
    upsert_catalog(
        OUTPUTS["run_result"].relative_to(ROOT),
        "transaction_cost_lot10_run_result",
        "transaction_cost_lot10_run_result",
        "multi",
        1,
        result.started_at,
        result.finished_at,
    )
    catalog_records = DatasetCatalog(ROOT / "data" / "audit" / "dataset_catalog.json").load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        print("LOT 10 TRANSACTION COSTS: FAIL", flush=True)
        print("dataset_catalog contains duplicate dataset_id entries", flush=True)
        return 1
    if counts.get("5m") != 36 or counts.get("15m") != 12:
        print("LOT 10 TRANSACTION COSTS: FAIL", flush=True)
        print(f"unexpected counts: {counts}", flush=True)
        return 1
    if result.estimate_count != 48 or result.orders_created_count != 0 or result.fills_created_count != 0 or result.pnl_total != 0:
        print("LOT 10 TRANSACTION COSTS: FAIL", flush=True)
        print(result.to_dict(), flush=True)
        return 1
    if result.trade_allowed is not False or result.used_for_decision is not False:
        print("LOT 10 TRANSACTION COSTS: FAIL", flush=True)
        print("safety invariant broken", flush=True)
        return 1
    print("LOT 10 TRANSACTION COSTS: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
