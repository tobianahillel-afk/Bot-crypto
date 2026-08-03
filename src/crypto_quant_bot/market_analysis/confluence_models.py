from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso

DEFAULT_VRC_BLOCK_REASONS = [
    "VOLATILITY_REGIME_CONFLUENCE_ONLY",
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

ALLOWED_VOLATILITY_STATES = [
    "VOLATILITY_CONTEXT_NEUTRAL",
    "VOLATILITY_CONTEXT_LOW",
    "VOLATILITY_CONTEXT_MODERATE",
    "VOLATILITY_CONTEXT_HIGH",
    "VOLATILITY_CONTEXT_EXPANDING",
    "VOLATILITY_CONTEXT_COMPRESSING",
    "VOLATILITY_CONTEXT_MIXED",
    "VOLATILITY_CONTEXT_INSUFFICIENT_DATA",
]

ALLOWED_REGIME_STATES = [
    "REGIME_CONTEXT_NEUTRAL",
    "REGIME_CONTEXT_TRENDING",
    "REGIME_CONTEXT_RANGING",
    "REGIME_CONTEXT_VOLATILE",
    "REGIME_CONTEXT_COMPRESSED",
    "REGIME_CONTEXT_MIXED",
    "REGIME_CONTEXT_INSUFFICIENT_DATA",
]

ALLOWED_CONFLUENCE_STATES = [
    "CONFLUENCE_CONTEXT_NEUTRAL",
    "CONFLUENCE_CONTEXT_ALIGNED",
    "CONFLUENCE_CONTEXT_PARTIAL",
    "CONFLUENCE_CONTEXT_DIVERGENT",
    "CONFLUENCE_CONTEXT_WEAK",
    "CONFLUENCE_CONTEXT_MIXED",
    "CONFLUENCE_CONTEXT_INSUFFICIENT_DATA",
]

ALLOWED_VRC_COMBINED_STATES = [
    "VRC_CONTEXT_NEUTRAL",
    "VRC_CONTEXT_ALIGNED_TREND",
    "VRC_CONTEXT_ALIGNED_RANGE",
    "VRC_CONTEXT_VOLATILE_MIXED",
    "VRC_CONTEXT_COMPRESSED",
    "VRC_CONTEXT_DIVERGENT",
    "VRC_CONTEXT_MIXED",
    "VRC_CONTEXT_INSUFFICIENT_DATA",
]


def default_vrc_block_reasons() -> list[str]:
    return list(DEFAULT_VRC_BLOCK_REASONS)


@dataclass(frozen=True)
class VolatilityRegimeConfluencePolicy:
    vrc_engine_version: str = "lot25_volatility_regime_confluence_v0"
    policy_version: str = "lot25_volatility_regime_confluence_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    vrc_engine_mode: str = "LOCAL_OFFLINE_VOLATILITY_REGIME_CONFLUENCE_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    indicator_mode: str = "LOCAL_OFFLINE_INDICATORS_ONLY"
    trend_engine_mode: str = "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    source_v1_archive_frozen: bool = True
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    vrc_block_reasons: list[str] = field(default_factory=default_vrc_block_reasons)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VolatilityRegimeConfluenceCheck:
    check_name: str
    status: str
    expected_value: Any
    observed_value: Any
    block_reason: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VolatilityRegimeConfluenceTimeframeSummary:
    timeframe: str
    row_count: int
    first_timestamp: str
    last_timestamp: str
    atr_5: float
    true_range_latest: float
    bollinger_width_5: float
    rolling_range_5: float
    range_width_percent: float
    volatility_expansion_score: float
    volatility_compression_score: float
    volatility_state: str
    volatility_context_score: float
    market_regime_source_state: str
    trend_state: str
    range_state: str
    momentum_state: str
    technical_indicator_state: str
    regime_state: str
    regime_context_score: float
    confluence_components: dict[str, Any]
    confluence_agreement_score: float
    confluence_divergence_score: float
    confluence_state: str
    confluence_context_score: float
    combined_context_score: float
    combined_context_state: str
    non_executable_summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VolatilityRegimeConfluenceResult:
    vrc_engine_version: str = "lot25_volatility_regime_confluence_v0"
    policy_version: str = "lot25_volatility_regime_confluence_v0"
    project_name: str = "Crypto Quant Bot V3.1-Ops"
    project_mode: str = "EDUCATIONAL_AUDIT_ONLY"
    created_at: str = field(default_factory=utc_now_iso)
    vrc_engine_mode: str = "LOCAL_OFFLINE_VOLATILITY_REGIME_CONFLUENCE_ONLY"
    analysis_mode: str = "LOCAL_OFFLINE_ANALYSIS_ONLY"
    indicator_mode: str = "LOCAL_OFFLINE_INDICATORS_ONLY"
    trend_engine_mode: str = "LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY"
    execution_allowed: bool = False
    trade_allowed: bool = False
    external_connectivity_allowed: bool = False
    live_execution: str = "DISABLED"
    leverage: str = "FORBIDDEN"
    source_v1_archive_frozen: bool = True
    v2_scope_state: str = "OPENED_AS_PLANNING_ONLY"
    dataset_timeframes: list[str] = field(default_factory=list)
    vrc_timeframes: list[str] = field(default_factory=list)
    input_rows_by_timeframe: dict[str, int] = field(default_factory=dict)
    volatility_state: str = "VOLATILITY_CONTEXT_INSUFFICIENT_DATA"
    regime_state: str = "REGIME_CONTEXT_INSUFFICIENT_DATA"
    confluence_state: str = "CONFLUENCE_CONTEXT_INSUFFICIENT_DATA"
    volatility_context_score: float = 0.0
    regime_context_score: float = 0.0
    confluence_context_score: float = 0.0
    combined_context_score: float = 0.0
    combined_context_state: str = "VRC_CONTEXT_INSUFFICIENT_DATA"
    timeframe_summaries: list[VolatilityRegimeConfluenceTimeframeSummary] = field(default_factory=list)
    vrc_checks: list[VolatilityRegimeConfluenceCheck] = field(default_factory=list)
    vrc_block_reasons: list[str] = field(default_factory=default_vrc_block_reasons)
    source_artifacts: list[str] = field(default_factory=list)
    vrc_checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
