from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_TREND_BLOCK_REASONS = [
    "TREND_RANGE_MOMENTUM_ONLY",
    "NO_EXECUTION_ALLOWED",
    "NO_EXTERNAL_CONNECTIVITY",
    "NO_EXCHANGE_CONNECTOR",
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
    "NO_PAPER_TRADING_ACTIVE",
    "NO_LIVE_TRADING_ACTIVE",
    "NO_STRATEGY_ENGINE",
    "EDUCATIONAL_MODE_ONLY",
    "HUMAN_REVIEW_REQUIRED_BEFORE_DECISION_ENGINE",
]

ALLOWED_TREND_STATES = [
    "TREND_CONTEXT_NEUTRAL",
    "TREND_CONTEXT_UPWARD",
    "TREND_CONTEXT_DOWNWARD",
    "TREND_CONTEXT_FLAT",
    "TREND_CONTEXT_MIXED",
    "TREND_CONTEXT_INSUFFICIENT_DATA",
]

ALLOWED_RANGE_STATES = [
    "RANGE_CONTEXT_NEUTRAL",
    "RANGE_CONTEXT_COMPRESSED",
    "RANGE_CONTEXT_EXPANDED",
    "RANGE_CONTEXT_BREAKING_STRUCTURE",
    "RANGE_CONTEXT_MIXED",
    "RANGE_CONTEXT_INSUFFICIENT_DATA",
]

ALLOWED_MOMENTUM_STATES = [
    "MOMENTUM_CONTEXT_NEUTRAL",
    "MOMENTUM_CONTEXT_ACCELERATING",
    "MOMENTUM_CONTEXT_DECELERATING",
    "MOMENTUM_CONTEXT_DIVERGENT",
    "MOMENTUM_CONTEXT_MIXED",
    "MOMENTUM_CONTEXT_INSUFFICIENT_DATA",
]

ALLOWED_COMBINED_CONTEXT_STATES = [
    "TRM_CONTEXT_NEUTRAL",
    "TRM_CONTEXT_TRENDING",
    "TRM_CONTEXT_RANGING",
    "TRM_CONTEXT_VOLATILE",
    "TRM_CONTEXT_COMPRESSED",
    "TRM_CONTEXT_MIXED",
    "TRM_CONTEXT_INSUFFICIENT_DATA",
]


def default_trend_block_reasons() -> list[str]:
    return list(DEFAULT_TREND_BLOCK_REASONS)


def allowed_trend_states() -> list[str]:
    return list(ALLOWED_TREND_STATES)


def allowed_range_states() -> list[str]:
    return list(ALLOWED_RANGE_STATES)


def allowed_momentum_states() -> list[str]:
    return list(ALLOWED_MOMENTUM_STATES)


def allowed_combined_context_states() -> list[str]:
    return list(ALLOWED_COMBINED_CONTEXT_STATES)


@dataclass(frozen=True)
class TrendRangeMomentumPolicy:
    trend_engine_version: str = "lot24_trend_range_momentum_v0"
    policy_version: str = "lot24_trend_range_momentum_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    trend_engine_mode: str = "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    indicator_mode: str = "LOCAL_OFFLINE_INDICATORS_ONLY"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    source_v1_archive_frozen: bool = True
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    trend_block_reasons: list[str] = field(default_factory=default_trend_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendRangeMomentumCheck:
    check_name: str
    status: str
    expected_value: Any
    observed_value: Any
    block_reason: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendRangeMomentumTimeframeSummary:
    timeframe: str
    row_count: int
    first_timestamp: str
    last_timestamp: str
    close_first: float
    close_last: float
    close_change_percent: float
    trend_slope_5: float
    trend_direction_context: str
    range_high_5: float
    range_low_5: float
    range_width_5: float
    range_width_percent: float
    range_position_percent: float
    momentum_3: float
    rate_of_change_3: float
    rsi_5: float
    macd_histogram: float
    bollinger_width_5: float
    atr_5: float
    trend_state: str
    range_state: str
    momentum_state: str
    trend_context_score: float
    range_context_score: float
    momentum_context_score: float
    combined_context_score: float
    combined_context_state: str
    non_executable_summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendRangeMomentumResult:
    trend_engine_version: str = "lot24_trend_range_momentum_v0"
    policy_version: str = "lot24_trend_range_momentum_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    created_at: str = field(default_factory=utc_now_iso)
    trend_engine_mode: str = "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    indicator_mode: str = "LOCAL_OFFLINE_INDICATORS_ONLY"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    source_v1_archive_frozen: bool = True
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    dataset_timeframes: list[str] = field(default_factory=list)
    trend_timeframes: list[str] = field(default_factory=list)
    input_rows_by_timeframe: dict[str, int] = field(default_factory=dict)
    trend_state: str = "TREND_CONTEXT_INSUFFICIENT_DATA"
    range_state: str = "RANGE_CONTEXT_INSUFFICIENT_DATA"
    momentum_state: str = "MOMENTUM_CONTEXT_INSUFFICIENT_DATA"
    trend_context_score: float = 0.0
    range_context_score: float = 0.0
    momentum_context_score: float = 0.0
    combined_context_score: float = 0.0
    combined_context_state: str = "TRM_CONTEXT_INSUFFICIENT_DATA"
    timeframe_summaries: list[TrendRangeMomentumTimeframeSummary] = field(default_factory=list)
    trend_checks: list[TrendRangeMomentumCheck] = field(default_factory=list)
    trend_block_reasons: list[str] = field(default_factory=default_trend_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    trend_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
