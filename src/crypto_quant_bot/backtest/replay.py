from typing import Any
from uuid import uuid4

from crypto_quant_bot.backtest.loader import sort_market_states
from crypto_quant_bot.backtest.lookahead_guard import check_market_state_no_lookahead, check_step_no_lookahead
from crypto_quant_bot.backtest.metrics import compute_replay_metrics
from crypto_quant_bot.backtest.noop_policy import POLICY_NAME, apply_noop_wait_policy
from crypto_quant_bot.contracts.backtest import BacktestRunConfig, BacktestRunResult, BacktestStep
from crypto_quant_bot.core.clock import utc_now_iso


def _make_step(run_id: str, index: int, market_state: dict[str, Any]) -> BacktestStep:
    policy = apply_noop_wait_policy(market_state)
    available_at = str(market_state.get("available_at", ""))
    return BacktestStep(
        run_id=run_id,
        step_id=f"{run_id}_step_{index:05d}",
        pair=str(market_state.get("pair", "BTC/EUR")),
        timeframe=str(market_state.get("timeframe", "")),
        timestamp=str(market_state.get("timestamp", "")),
        available_at=available_at,
        market_state_id=str(market_state.get("market_state_id", "")),
        observed_market_state_available_at=available_at,
        policy_name=policy["policy_name"],
        decision=policy["decision"],
        trade_allowed=policy["trade_allowed"],
        orders_created=policy["orders_created"],
        fills_created=policy["fills_created"],
        pnl_impact=policy["pnl_impact"],
        warnings=policy["warnings"],
        source="lot9_backtest_replay_v0",
        lineage_id=f"lot9_replay_lineage_{run_id}",
        quality_flag="valid",
        validation_status="validated_lot9",
        used_for_decision=False,
    )


def run_replay(pair: str, market_states_by_timeframe: dict[str, list[dict[str, Any]]]) -> tuple[BacktestRunConfig, dict[str, list[BacktestStep]], BacktestRunResult]:
    run_id = f"lot9_replay_{uuid4()}"
    started_at = utc_now_iso()
    ordered_steps: dict[str, list[BacktestStep]] = {}
    all_steps: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    lookahead_violations: list[dict[str, Any]] = []
    step_index = 0
    for timeframe in sorted(market_states_by_timeframe):
        rows = sort_market_states(market_states_by_timeframe[timeframe])
        previous_key: tuple[str, str] | None = None
        ordered_steps[timeframe] = []
        for row in rows:
            key = (str(row.get("timestamp", "")), str(row.get("available_at", "")))
            if previous_key is not None and key < previous_key:
                lookahead_violations.append({"timeframe": timeframe, "rule": "monotone timestamp/available_at per timeframe", "value": key, "reference": previous_key})
            previous_key = key
            step_index += 1
            step = _make_step(run_id, step_index, row)
            step_dict = step.to_dict()
            row_violations = check_market_state_no_lookahead(row, step.available_at)
            row_violations.extend(check_step_no_lookahead(step_dict))
            for violation in row_violations:
                violation = dict(violation)
                violation["timeframe"] = timeframe
                violation["timestamp"] = row.get("timestamp", "")
                violation["market_state_id"] = row.get("market_state_id", "")
                lookahead_violations.append(violation)
            ordered_steps[timeframe].append(step)
            all_steps.append(step_dict)
            all_rows.append(row)
    metrics = compute_replay_metrics(all_steps, lookahead_violations)
    timestamps = [str(row.get("timestamp", "")) for row in all_rows if row.get("timestamp")]
    data_sources = [f"data/gold/btc_eur_{timeframe}_market_state_lot7.jsonl" for timeframe in sorted(market_states_by_timeframe)]
    config = BacktestRunConfig(
        run_id=run_id,
        pair=pair,
        timeframes=sorted(market_states_by_timeframe),
        start_timestamp=min(timestamps) if timestamps else "",
        end_timestamp=max(timestamps) if timestamps else "",
        mode="replay_v0",
        policy_name=POLICY_NAME,
        data_sources=data_sources,
        created_at=started_at,
        config_version="lot9_replay_v0",
        trade_allowed=False,
        source="lot9_backtest_replay_v0",
        quality_flag="valid",
        validation_status="validated_lot9",
        used_for_decision=False,
    )
    finished_at = utc_now_iso()
    result = BacktestRunResult(
        run_id=run_id,
        pair=pair,
        timeframes=sorted(market_states_by_timeframe),
        step_count=metrics["step_count"],
        start_timestamp=config.start_timestamp,
        end_timestamp=config.end_timestamp,
        started_at=started_at,
        finished_at=finished_at,
        policy_name=POLICY_NAME,
        decision_counts=metrics["decision_counts"],
        orders_created_count=metrics["orders_created_count"],
        fills_created_count=metrics["fills_created_count"],
        pnl_total=metrics["pnl_total"],
        lookahead_violations=lookahead_violations,
        reports=["reports/lot_09_backtest_replay_report.md"],
        source="lot9_backtest_replay_v0",
        quality_flag="valid" if not lookahead_violations else "invalid",
        validation_status="validated_lot9" if not lookahead_violations else "failed_lot9",
        used_for_decision=False,
    )
    return config, ordered_steps, result
