#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine

REQUIRED_FILES = [
    "src/crypto_quant_bot/contracts/backtest.py",
    "src/crypto_quant_bot/backtest/__init__.py",
    "src/crypto_quant_bot/backtest/loader.py",
    "src/crypto_quant_bot/backtest/replay.py",
    "src/crypto_quant_bot/backtest/noop_policy.py",
    "src/crypto_quant_bot/backtest/metrics.py",
    "src/crypto_quant_bot/backtest/lookahead_guard.py",
    "src/crypto_quant_bot/backtest/writer.py",
    "scripts/run_lot9_backtest_replay.py",
    "scripts/validate_lot9.py",
    "scripts/run_required_chain_until_lot9.sh",
    "data/audit/backtest_lot9_run_config.json",
    "data/audit/backtest_lot9_run_result.json",
    "data/audit/backtest_lot9_5m_steps.jsonl",
    "data/audit/backtest_lot9_15m_steps.jsonl",
    "reports/lot_09_backtest_replay_report.md",
    "reports/lot_09_bis_validation_report.md",
    "reports/lot_09_ter_validation_report.md",
    "docs/BACKTEST_REPLAY_ENGINE_POLICY.md",
    "docs/BACKTEST_NOOP_POLICY.md",
    "docs/BACKTEST_ANTI_LOOKAHEAD_POLICY.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_09.md",
    "docs/LOT_09_REPORT.md",
    "data/audit/dataset_catalog.json",
]

FORBIDDEN_KEY_PARTS = ("future_", "target", "label", "signal")
FORBIDDEN_VALUES = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}



def fail(message: str) -> int:
    print("LOT 9 VALIDATION: FAIL")
    print(message)
    return 1


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"invalid JSONL row in {path}")
            rows.append(row)
    return rows


def has_forbidden_content(obj: Any, *, max_nodes: int = 20000) -> bool:
    stack: list[Any] = [obj]
    seen = 0
    while stack:
        seen += 1
        if seen > max_nodes:
            return True
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                lowered = str(key).lower()
                if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                    return True
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str) and current.upper() in FORBIDDEN_VALUES:
            return True
    return False


def validate_step(step: dict[str, Any], path: Path, row_index: int) -> str | None:
    expected = {
        "decision": "WAIT",
        "trade_allowed": False,
        "orders_created": [],
        "fills_created": [],
        "pnl_impact": 0,
        "used_for_decision": False,
    }
    for key, value in expected.items():
        if step.get(key) != value:
            return f"{path}:{row_index} invalid {key}: {step.get(key)}"
    if step.get("policy_name") != "noop_wait_policy":
        return f"{path}:{row_index} invalid policy"
    if has_forbidden_content(step):
        return f"{path}:{row_index} has forbidden lookahead or trading direction content"
    timestamp = str(step.get("timestamp", ""))
    available_at = str(step.get("available_at", ""))
    if timestamp and available_at and timestamp > available_at:
        return f"{path}:{row_index} timestamp after available_at"
    return None


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 9 artifact: {relative}")
    steps_5m = load_jsonl(ROOT / "data" / "audit" / "backtest_lot9_5m_steps.jsonl")
    steps_15m = load_jsonl(ROOT / "data" / "audit" / "backtest_lot9_15m_steps.jsonl")
    if len(steps_5m) != 36:
        return fail("backtest_lot9_5m_steps.jsonl must contain 36 lines")
    if len(steps_15m) != 12:
        return fail("backtest_lot9_15m_steps.jsonl must contain 12 lines")
    result = load_json(ROOT / "data" / "audit" / "backtest_lot9_run_result.json")
    config = load_json(ROOT / "data" / "audit" / "backtest_lot9_run_config.json")
    if not isinstance(result, dict) or not isinstance(config, dict):
        return fail("invalid Lot 9 JSON outputs")
    if config.get("mode") != "replay_v0" or config.get("policy_name") != "noop_wait_policy" or config.get("trade_allowed") is not False:
        return fail("run_config invariant broken")
    checks = {
        "orders_created_count": 0,
        "fills_created_count": 0,
        "pnl_total": 0,
        "used_for_decision": False,
    }
    for key, expected in checks.items():
        if result.get(key) != expected:
            return fail(f"run_result invalid {key}: {result.get(key)}")
    if result.get("decision_counts", {}).get("WAIT") != 48:
        return fail("decision_counts.WAIT must equal 48")
    if result.get("lookahead_violations") != []:
        return fail("run_result has lookahead violations")
    for path, rows in [
        (ROOT / "data" / "audit" / "backtest_lot9_5m_steps.jsonl", steps_5m),
        (ROOT / "data" / "audit" / "backtest_lot9_15m_steps.jsonl", steps_15m),
    ]:
        previous = None
        for index, step in enumerate(rows, start=1):
            message = validate_step(step, path, index)
            if message:
                return fail(message)
            key = (str(step.get("timestamp", "")), str(step.get("available_at", "")))
            if previous is not None and key < previous:
                return fail(f"non monotone replay step in {path}")
            previous = key
    for timeframe in ["5m", "15m"]:
        for row in load_jsonl(ROOT / "data" / "gold" / f"btc_eur_{timeframe}_market_state_lot7.jsonl"):
            if str(row.get("available_at", "")) < str(row.get("timestamp", "")):
                return fail("market_state available_at before timestamp")
    catalog = load_json(ROOT / "data" / "audit" / "dataset_catalog.json")
    if not isinstance(catalog, list):
        return fail("dataset_catalog.json must be a list")
    catalog_ids_list = [entry.get("dataset_id") for entry in catalog if isinstance(entry, dict)]
    if len(catalog_ids_list) != len(set(catalog_ids_list)):
        return fail("dataset_catalog.json contains duplicate dataset_id entries")
    catalog_ids = set(catalog_ids_list)
    for required_id in {"backtest_lot9_5m_steps", "backtest_lot9_15m_steps", "backtest_lot9_run_config", "backtest_lot9_run_result"}:
        if required_id not in catalog_ids:
            return fail(f"dataset catalog missing {required_id}")
    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text:
        return fail("live_execution invariant broken")
    if "leverage: FORBIDDEN" not in status_text:
        return fail("leverage invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("trade_allowed default invariant broken")
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    if decision.trading_decision != "WAIT" or decision.system_decision != "BLOCK_TRADING" or decision.trade_allowed is not False:
        return fail("Decision Engine invariant broken")
    if risk.trade_allowed is not False:
        return fail("Risk Engine invariant broken")
    print("LOT 9 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
