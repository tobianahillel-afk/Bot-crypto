from typing import Any
from uuid import uuid4

from crypto_quant_bot.contracts.costs import TransactionCostConfig, TransactionCostEstimate, TransactionCostRunResult
from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.costs.fees import calculate_fee_bps
from crypto_quant_bot.costs.slippage import estimate_slippage_bps
from crypto_quant_bot.costs.spread import estimate_spread_bps

NOTIONAL_AMOUNT = 1000.0
ORDER_TYPE = "hypothetical_noop"
SIDE = "neutral"


def _amount(notional: float, bps: float) -> float:
    return round(notional * bps / 10000.0, 8)


def _market_state_index(rows_by_timeframe: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for timeframe, rows in rows_by_timeframe.items():
        for row in rows:
            market_state_id = str(row.get("market_state_id", ""))
            if market_state_id:
                index[(timeframe, market_state_id)] = row
    return index


def _make_estimate(run_id: str, step: dict[str, Any], market_state: dict[str, Any], config: TransactionCostConfig, raw_config: dict[str, Any], index: int) -> TransactionCostEstimate:
    fee_bps = calculate_fee_bps(ORDER_TYPE, config)
    spread_bps = estimate_spread_bps(market_state, raw_config)
    slippage_bps = estimate_slippage_bps(market_state, raw_config)
    total_cost_bps = round(fee_bps + spread_bps + slippage_bps, 8)
    estimated_fee = _amount(NOTIONAL_AMOUNT, fee_bps)
    estimated_spread = _amount(NOTIONAL_AMOUNT, spread_bps)
    estimated_slippage = _amount(NOTIONAL_AMOUNT, slippage_bps)
    source_ids = list(market_state.get("source_dataset_ids", [])) if isinstance(market_state.get("source_dataset_ids"), list) else []
    source_ids.extend(["backtest_lot9_5m_steps" if step.get("timeframe") == "5m" else "backtest_lot9_15m_steps"])
    created_at = utc_now_iso()
    return TransactionCostEstimate(
        estimate_id=f"{run_id}_cost_estimate_{index:05d}",
        run_id=run_id,
        step_id=str(step.get("step_id", "")),
        pair=str(step.get("pair", config.pair)),
        timeframe=str(step.get("timeframe", "")),
        timestamp=str(step.get("timestamp", "")),
        available_at=str(step.get("available_at", market_state.get("available_at", ""))),
        market_state_id=str(step.get("market_state_id", market_state.get("market_state_id", ""))),
        notional_amount=NOTIONAL_AMOUNT,
        side=SIDE,
        order_type=ORDER_TYPE,
        fee_bps=fee_bps,
        spread_bps=spread_bps,
        slippage_bps=slippage_bps,
        total_cost_bps=total_cost_bps,
        estimated_fee_amount=estimated_fee,
        estimated_spread_cost=estimated_spread,
        estimated_slippage_cost=estimated_slippage,
        estimated_total_cost=round(estimated_fee + estimated_spread + estimated_slippage, 8),
        currency=config.currency,
        source_dataset_ids=sorted(set(source_ids)),
        created_at=created_at,
        source="lot10_transaction_cost_model_v0",
        lineage_id=f"lot10_cost_lineage_{run_id}",
        quality_flag="valid",
        validation_status="validated_lot10",
        trade_allowed=False,
        used_for_decision=False,
    )


def estimate_transaction_costs(config: TransactionCostConfig, raw_config: dict[str, Any], steps_by_timeframe: dict[str, list[dict[str, Any]]], market_states_by_timeframe: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, list[TransactionCostEstimate]], TransactionCostRunResult]:
    run_id = f"lot10_costs_{uuid4()}"
    started_at = utc_now_iso()
    market_states = _market_state_index(market_states_by_timeframe)
    estimates_by_timeframe: dict[str, list[TransactionCostEstimate]] = {}
    all_estimates: list[TransactionCostEstimate] = []
    index = 0
    for timeframe in sorted(steps_by_timeframe):
        estimates_by_timeframe[timeframe] = []
        for step in steps_by_timeframe[timeframe]:
            if step.get("decision") != "WAIT":
                continue
            key = (timeframe, str(step.get("market_state_id", "")))
            market_state = market_states.get(key)
            if market_state is None:
                raise ValueError(f"missing market state for {key}")
            index += 1
            estimate = _make_estimate(run_id, step, market_state, config, raw_config, index)
            estimates_by_timeframe[timeframe].append(estimate)
            all_estimates.append(estimate)
    totals = [float(estimate.total_cost_bps) for estimate in all_estimates]
    finished_at = utc_now_iso()
    result = TransactionCostRunResult(
        run_id=run_id,
        pair=config.pair,
        timeframes=sorted(steps_by_timeframe),
        estimate_count=len(all_estimates),
        started_at=started_at,
        finished_at=finished_at,
        fee_model_version="lot10_fee_model_v0",
        spread_model_version="lot10_spread_model_v0",
        slippage_model_version="lot10_slippage_model_v0",
        average_total_cost_bps=round(sum(totals) / len(totals), 8) if totals else 0,
        max_total_cost_bps=max(totals) if totals else 0,
        min_total_cost_bps=min(totals) if totals else 0,
        trade_allowed=False,
        orders_created_count=0,
        fills_created_count=0,
        pnl_total=0,
        reports=["reports/lot_10_transaction_costs_report.md"],
        source="lot10_transaction_cost_model_v0",
        quality_flag="valid",
        validation_status="validated_lot10",
        used_for_decision=False,
    )
    return estimates_by_timeframe, result
