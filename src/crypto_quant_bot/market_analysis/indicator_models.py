from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_INDICATOR_BLOCK_REASONS = [
    "TECHNICAL_INDICATORS_ONLY",
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

ALLOWED_INDICATOR_STATES = [
    "INDICATOR_NEUTRAL",
    "INDICATOR_EXTENDED_UP",
    "INDICATOR_EXTENDED_DOWN",
    "INDICATOR_COMPRESSED",
    "INDICATOR_VOLATILE",
    "INDICATOR_MIXED",
    "INDICATOR_INSUFFICIENT_DATA",
]

REQUIRED_INDICATOR_SET = [
    "sma_3",
    "sma_5",
    "ema_3",
    "ema_5",
    "rolling_high_5",
    "rolling_low_5",
    "rolling_range_5",
    "close_vs_sma_5_percent",
    "close_vs_ema_5_percent",
    "rsi_5",
    "macd_fast_3_slow_6",
    "macd_signal_3",
    "macd_histogram",
    "bollinger_mid_5",
    "bollinger_upper_5",
    "bollinger_lower_5",
    "bollinger_width_5",
    "true_range",
    "atr_5",
    "momentum_3",
    "rate_of_change_3",
]


def default_indicator_block_reasons() -> list[str]:
    return list(DEFAULT_INDICATOR_BLOCK_REASONS)


def allowed_indicator_states() -> list[str]:
    return list(ALLOWED_INDICATOR_STATES)


def required_indicator_set() -> list[str]:
    return list(REQUIRED_INDICATOR_SET)


@dataclass(frozen=True)
class TechnicalIndicatorPolicy:
    indicator_version: str = "lot23_technical_indicators_v0"
    policy_version: str = "lot23_technical_indicators_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    indicator_mode: str = "LOCAL_OFFLINE_INDICATORS_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    source_v1_archive_frozen: bool = True
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    indicator_block_reasons: list[str] = field(default_factory=default_indicator_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndicatorCheck:
    check_name: str
    status: str
    expected_value: Any
    observed_value: Any
    block_reason: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndicatorValue:
    indicator_id: str
    value: float | None
    unit: str
    window: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TechnicalIndicatorTimeframeSummary:
    timeframe: str
    row_count: int
    first_timestamp: str
    last_timestamp: str
    close_last: float
    market_context_state: str
    market_context_score: float
    indicator_count: int
    indicator_values: list[IndicatorValue] = field(default_factory=list)
    indicator_state: str = "INDICATOR_INSUFFICIENT_DATA"
    indicator_context_score: float = 0.0
    non_executable_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TechnicalIndicatorResult:
    indicator_version: str = "lot23_technical_indicators_v0"
    policy_version: str = "lot23_technical_indicators_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    created_at: str = field(default_factory=utc_now_iso)
    indicator_mode: str = "LOCAL_OFFLINE_INDICATORS_ONLY"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    source_v1_archive_frozen: bool = True
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    dataset_timeframes: list[str] = field(default_factory=list)
    indicator_timeframes: list[str] = field(default_factory=list)
    input_rows_by_timeframe: dict[str, int] = field(default_factory=dict)
    indicator_set: list[str] = field(default_factory=required_indicator_set)
    indicator_state: str = "INDICATOR_INSUFFICIENT_DATA"
    indicator_context_score: float = 0.0
    timeframe_summaries: list[TechnicalIndicatorTimeframeSummary] = field(default_factory=list)
    indicator_checks: list[IndicatorCheck] = field(default_factory=list)
    indicator_block_reasons: list[str] = field(default_factory=default_indicator_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    indicator_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
