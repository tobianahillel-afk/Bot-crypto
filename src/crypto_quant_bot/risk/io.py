from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crypto_quant_bot.risk.models import RiskSnapshot


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"invalid JSONL row in {path}")
                rows.append(payload)
    return rows


def write_jsonl(path: Path, snapshots: list[RiskSnapshot]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for snapshot in snapshots:
            json.dump(snapshot.to_dict(), handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
    tmp_path.replace(path)


def write_report(
    path: Path,
    *,
    counts: dict[str, int],
    total: int,
    run_result: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    average_cost = run_result.get("average_total_cost_bps", 0)
    max_cost = run_result.get("max_total_cost_bps", 0)
    min_cost = run_result.get("min_total_cost_bps", 0)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(
        "# Lot 11 Risk Engine Report\n\n"
        "Risk Engine & Decision Firewall V0 consumes Lot 10 transaction cost outputs as documentary context only.\n\n"
        f"5m risk snapshots: {counts.get('5m', 0)}\n\n"
        f"15m risk snapshots: {counts.get('15m', 0)}\n\n"
        f"Total risk snapshots: {total}\n\n"
        "TradingDecision: WAIT\n\n"
        "SystemDecision: BLOCK_TRADING\n\n"
        "trade_allowed: false\n\n"
        "used_for_decision: false\n\n"
        "live_execution: DISABLED\n\n"
        "leverage: FORBIDDEN\n\n"
        "Risk Engine blocks by default and produces no executable trading decision.\n\n"
        "Lot 10 transaction costs are documentary only and are not used to open a position.\n\n"
        f"Documentary average total cost bps: {average_cost}\n\n"
        f"Documentary max total cost bps: {max_cost}\n\n"
        f"Documentary min total cost bps: {min_cost}\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)
