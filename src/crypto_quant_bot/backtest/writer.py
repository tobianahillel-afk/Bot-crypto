import json
from pathlib import Path
from typing import Any

from crypto_quant_bot.contracts.backtest import BacktestRunConfig, BacktestRunResult, BacktestStep


def write_json(path: Path | str, payload: dict[str, Any]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_steps(path: Path | str, steps: list[BacktestStep]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(step.to_dict(), ensure_ascii=False, sort_keys=True) for step in steps)
    file_path.write_text(text + ("\n" if steps else ""), encoding="utf-8")


def write_run_config(path: Path | str, config: BacktestRunConfig) -> None:
    write_json(path, config.to_dict())


def write_run_result(path: Path | str, result: BacktestRunResult) -> None:
    write_json(path, result.to_dict())


def write_report(path: Path | str, config: BacktestRunConfig, result: BacktestRunResult, counts_by_timeframe: dict[str, int]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "# Lot 9 Backtest Replay Report\n\n"
        "Backtest Replay Engine V0 rejoue les MarketState validés avec une policy neutre NOOP / WAIT.\n\n"
        f"Run id: `{result.run_id}`\n\n"
        f"Mode: `{config.mode}`\n\n"
        f"Policy: `{result.policy_name}`\n\n"
        f"5m steps: {counts_by_timeframe.get('5m', 0)}\n\n"
        f"15m steps: {counts_by_timeframe.get('15m', 0)}\n\n"
        f"Total steps: {result.step_count}\n\n"
        f"Decision counts: `{result.decision_counts}`\n\n"
        f"Orders created count: {result.orders_created_count}\n\n"
        f"Fills created count: {result.fills_created_count}\n\n"
        f"PnL total: {result.pnl_total}\n\n"
        f"Lookahead violations: {len(result.lookahead_violations)}\n\n"
        "Ce lot ne crée aucune stratégie, aucun ordre, aucun target, aucun label et aucun signal LONG/SHORT exploitable.\n"
    )
    file_path.write_text(text, encoding="utf-8")
