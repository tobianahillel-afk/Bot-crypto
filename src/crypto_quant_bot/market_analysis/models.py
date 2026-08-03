from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_ANALYSIS_BLOCK_REASONS = [
    "MARKET_ANALYSIS_ONLY",
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

ALLOWED_CONTEXT_LABELS = [
    "CONTEXT_NEUTRAL",
    "CONTEXT_TRENDING",
    "CONTEXT_RANGING",
    "CONTEXT_VOLATILE",
    "CONTEXT_LOW_ACTIVITY",
    "CONTEXT_MIXED",
    "CONTEXT_INSUFFICIENT_DATA",
]


def default_analysis_block_reasons() -> list[str]:
    return list(DEFAULT_ANALYSIS_BLOCK_REASONS)


def allowed_context_labels() -> list[str]:
    return list(ALLOWED_CONTEXT_LABELS)


@dataclass(frozen=True)
class MarketAnalysisPolicy:
    analysis_version: str = "lot22_market_analysis_v0"
    policy_version: str = "lot22_market_analysis_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    source_v1_archive_frozen: bool = True
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    analysis_block_reasons: list[str] = field(default_factory=default_analysis_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketAnalysisInput:
    timeframe: str
    candles_path: str
    lot2_features_path: str
    pivots_path: str
    vwap_path: str
    volatility_path: str
    regime_path: str
    market_state_path: str
    row_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketAnalysisCheck:
    check_name: str
    status: str
    expected_value: Any
    observed_value: Any
    block_reason: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketTimeframeSummary:
    timeframe: str
    row_count: int
    first_timestamp: str
    last_timestamp: str
    close_first: float
    close_last: float
    close_change_absolute: float
    close_change_percent: float
    range_high: float
    range_low: float
    range_percent: float
    volatility_level: str
    regime_state: str
    market_state: str
    vwap_relation: str
    pivot_context: str
    volume_context: str
    trend_context: str
    range_context: str
    context_score: float
    context_label: str
    non_executable_summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketContextSnapshot:
    analysis_version: str
    policy_version: str
    project_name: str
    project_mode: str
    created_at: str
    analysis_mode: str
    execution_allowed: bool
    trade_allowed: bool
    external_connectivity_allowed: bool
    live_execution: str
    leverage: str
    source_v1_archive_frozen: bool
    v2_scope_state: str
    dataset_timeframes: list[str] = field(default_factory=list)
    analysis_timeframes: list[str] = field(default_factory=list)
    input_rows_by_timeframe: dict[str, int] = field(default_factory=dict)
    market_context_state: str = "CONTEXT_INSUFFICIENT_DATA"
    market_context_score: float = 0.0
    trend_context: str = ""
    volatility_context: str = ""
    volume_context: str = ""
    range_context: str = ""
    regime_context: str = ""
    confidence_context: str = ""
    analysis_block_reasons: list[str] = field(default_factory=default_analysis_block_reasons)
    timeframe_summaries: list[MarketTimeframeSummary] = field(default_factory=list)
    analysis_checks: list[MarketAnalysisCheck] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    analysis_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketAnalysisResult:
    analysis_version: str = "lot22_market_analysis_v0"
    policy_version: str = "lot22_market_analysis_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    timeframe_count: int = 0
    output_paths: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
