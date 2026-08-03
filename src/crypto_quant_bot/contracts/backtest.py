from dataclasses import dataclass, field
from typing import Any

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class BacktestRunConfig(BaseContract):
    run_id: str = ""
    pair: str = "BTC/EUR"
    timeframes: list[str] = field(default_factory=lambda: ["5m", "15m"])
    start_timestamp: str = ""
    end_timestamp: str = ""
    mode: str = "replay_v0"
    policy_name: str = "noop_wait_policy"
    data_sources: list[str] = field(default_factory=list)
    config_version: str = "lot9_replay_v0"
    trade_allowed: bool = False


@dataclass(frozen=True)
class BacktestStep(BaseContract):
    run_id: str = ""
    step_id: str = ""
    pair: str = "BTC/EUR"
    timeframe: str = "5m"
    timestamp: str = ""
    market_state_id: str = ""
    observed_market_state_available_at: str = ""
    policy_name: str = "noop_wait_policy"
    decision: str = "WAIT"
    trade_allowed: bool = False
    orders_created: list[dict[str, Any]] = field(default_factory=list)
    fills_created: list[dict[str, Any]] = field(default_factory=list)
    pnl_impact: int | float = 0
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestRunResult(BaseContract):
    run_id: str = ""
    pair: str = "BTC/EUR"
    timeframes: list[str] = field(default_factory=lambda: ["5m", "15m"])
    step_count: int = 0
    start_timestamp: str = ""
    end_timestamp: str = ""
    started_at: str = ""
    finished_at: str = ""
    policy_name: str = "noop_wait_policy"
    decision_counts: dict[str, int] = field(default_factory=dict)
    orders_created_count: int = 0
    fills_created_count: int = 0
    pnl_total: int | float = 0
    lookahead_violations: list[dict[str, Any]] = field(default_factory=list)
    reports: list[str] = field(default_factory=list)
