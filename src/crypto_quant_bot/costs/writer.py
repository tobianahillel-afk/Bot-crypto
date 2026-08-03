import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.contracts.costs import TransactionCostEstimate, TransactionCostRunResult


def _atomic_write_text(path: Path | str, text: str) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_name(f".{file_path.stem}.{os.getpid()}.{uuid4().hex}{file_path.suffix}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(tmp_path, file_path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_json(path: Path | str, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def write_estimates(path: Path | str, estimates: list[TransactionCostEstimate]) -> None:
    text = "\n".join(json.dumps(estimate.to_dict(), ensure_ascii=False, sort_keys=True) for estimate in estimates)
    _atomic_write_text(path, text + ("\n" if estimates else ""))


def write_run_result(path: Path | str, result: TransactionCostRunResult) -> None:
    write_json(path, result.to_dict())


def write_report(path: Path | str, result: TransactionCostRunResult, counts_by_timeframe: dict[str, int]) -> None:
    text = (
        "# Lot 10 Transaction Costs Report\n\n"
        "Transaction Costs, Spread & Slippage Model V0 estime uniquement des coûts hypothétiques neutres.\n\n"
        f"Run id: `{result.run_id}`\n\n"
        f"5m estimates: {counts_by_timeframe.get('5m', 0)}\n\n"
        f"15m estimates: {counts_by_timeframe.get('15m', 0)}\n\n"
        f"Estimate count: {result.estimate_count}\n\n"
        f"Average total cost bps: {result.average_total_cost_bps}\n\n"
        f"Min total cost bps: {result.min_total_cost_bps}\n\n"
        f"Max total cost bps: {result.max_total_cost_bps}\n\n"
        f"Orders created count: {result.orders_created_count}\n\n"
        f"Fills created count: {result.fills_created_count}\n\n"
        f"PnL total: {result.pnl_total}\n\n"
        f"Trade allowed: {str(result.trade_allowed).lower()}\n\n"
        f"Used for decision: {str(result.used_for_decision).lower()}\n\n"
        "Ce lot ne crée aucune stratégie, aucun ordre, aucun fill, aucun PnL exploitable et aucun signal LONG/SHORT.\n"
    )
    _atomic_write_text(path, text)
