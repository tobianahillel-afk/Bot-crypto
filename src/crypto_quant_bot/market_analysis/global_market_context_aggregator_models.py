from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

SOURCE_IDS = (
    "lot22_market_analysis",
    "lot23_technical_indicators",
    "lot24_trend_range_momentum",
    "lot25_volatility_regime_confluence",
    "lot26_multi_timeframe_alignment",
)
SEMANTIC_CATEGORIES = ("TRENDING", "RANGE", "MIXED", "CONFLICT")
GLOBAL_STATES = {
    "GLOBAL_CONTEXT_TRENDING",
    "GLOBAL_CONTEXT_RANGE",
    "GLOBAL_CONTEXT_MIXED",
    "GLOBAL_CONTEXT_UNKNOWN",
}
QUALITY_STATES = {"VALID", "MISSING", "INVALID", "STALE"}


def parse_utc(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field_name} must be an ISO-8601 UTC timestamp ending in Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return parsed


def validate_score(value: float | None, field_name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric or null")
    if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{field_name} must be finite within [0, 1]")


def require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def require_unique(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{field_name} must contain non-empty strings")


def _validate_included_contribution(item: SourceContributionV1) -> None:
    if not item.included:
        if item.effective_contribution != 0.0:
            raise ValueError("excluded source contribution must be zero")
        return
    required = (
        item.source_schema_version,
        item.source_checksum,
        item.source_state,
        item.semantic_category,
        item.source_score,
        item.event_time,
        item.age_seconds,
    )
    if any(value is None for value in required) or item.quality_state != "VALID":
        raise ValueError("included source contribution is incomplete")


@dataclass(frozen=True, slots=True)
class SourceContributionV1:
    source_id: str
    source_schema_version: str | None
    source_artifact: str
    source_checksum: str | None
    source_state: str | None
    semantic_category: str | None
    source_score: float | None
    configured_weight: float
    effective_contribution: float
    quality_state: str
    event_time: str | None
    age_seconds: float | None
    included: bool
    reason_codes: tuple[str, ...]
    schema_version: str = "global-context-source-contribution-v1"

    def __post_init__(self) -> None:
        require_text(self.source_id, "source_id")
        require_text(self.source_artifact, "source_artifact")
        if self.source_id not in SOURCE_IDS:
            raise ValueError("unknown source_id")
        if self.quality_state not in QUALITY_STATES:
            raise ValueError("unknown quality_state")
        validate_score(self.source_score, "source_score")
        validate_score(self.configured_weight, "configured_weight")
        validate_score(self.effective_contribution, "effective_contribution")
        if self.configured_weight <= 0.0:
            raise ValueError("configured_weight must be positive")
        if self.semantic_category is not None and self.semantic_category not in SEMANTIC_CATEGORIES:
            raise ValueError("unknown semantic_category")
        if self.event_time is not None:
            parse_utc(self.event_time, "event_time")
        if self.age_seconds is not None and self.age_seconds < 0:
            raise ValueError("age_seconds must be non-negative")
        require_unique(self.reason_codes, "reason_codes")
        _validate_included_contribution(self)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reason_codes"] = list(self.reason_codes)
        return payload


def _validate_global_scores(state: GlobalMarketContextAggregatorStateV1) -> None:
    if set(state.category_support) != set(SEMANTIC_CATEGORIES):
        raise ValueError("category_support must contain every semantic category")
    for category, value in state.category_support.items():
        validate_score(value, f"category_support.{category}")
    validate_score(state.aggregate_evidence_score, "aggregate_evidence_score")
    validate_score(state.weighted_coverage_ratio, "weighted_coverage_ratio")
    validate_score(state.missing_source_weight, "missing_source_weight")
    if not 0 <= state.available_source_count <= len(SOURCE_IDS):
        raise ValueError("available_source_count is out of bounds")


def _validate_global_sources(state: GlobalMarketContextAggregatorStateV1) -> None:
    if len(state.contributions) != len(SOURCE_IDS):
        raise ValueError("contributions must contain all configured sources")
    if {item.source_id for item in state.contributions} != set(SOURCE_IDS):
        raise ValueError("contributions contain invalid sources")
    require_unique(state.alternative_states, "alternative_states")
    require_unique(state.conflict_states, "conflict_states")
    require_unique(state.reason_codes, "reason_codes")


def _validate_global_safety(state: GlobalMarketContextAggregatorStateV1) -> None:
    permissions = (
        state.used_for_decision,
        state.forecast_generation_allowed,
        state.probability_claims_allowed,
        state.signal_generation_allowed,
        state.order_routing_allowed,
        state.execution_allowed,
        state.trade_allowed,
    )
    if state.analysis_only is not True or any(value is not False for value in permissions):
        raise ValueError("all executable permissions must remain disabled")
    if state.approved_size != 0:
        raise ValueError("approved_size must remain zero")


@dataclass(frozen=True, slots=True)
class GlobalMarketContextAggregatorStateV1:
    context_id: str
    instrument_id: str
    decision_time: str
    dominant_state: str
    alternative_states: tuple[str, ...]
    category_support: dict[str, float]
    aggregate_evidence_score: float | None
    weighted_coverage_ratio: float
    available_source_count: int
    missing_source_weight: float
    conflict_states: tuple[str, ...]
    confidence_interval: dict[str, float] | None
    contributions: tuple[SourceContributionV1, ...]
    lineage_id: str
    config_version: str
    config_checksum: str
    code_commit: str
    output_checksum: str
    reason_codes: tuple[str, ...]
    validation_state: str
    analysis_only: bool = True
    used_for_decision: bool = False
    forecast_generation_allowed: bool = False
    probability_claims_allowed: bool = False
    signal_generation_allowed: bool = False
    order_routing_allowed: bool = False
    execution_allowed: bool = False
    trade_allowed: bool = False
    approved_size: int = 0
    schema_version: str = "global-market-context-aggregator-state-v1"

    def __post_init__(self) -> None:
        for field_name in (
            "context_id",
            "instrument_id",
            "lineage_id",
            "config_version",
            "config_checksum",
            "code_commit",
            "output_checksum",
        ):
            require_text(getattr(self, field_name), field_name)
        parse_utc(self.decision_time, "decision_time")
        if self.dominant_state not in GLOBAL_STATES:
            raise ValueError("unknown dominant_state")
        if self.validation_state not in {"VALID", "UNKNOWN", "BLOCKED"}:
            raise ValueError("unknown validation_state")
        _validate_global_scores(self)
        _validate_global_sources(self)
        _validate_global_safety(self)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["alternative_states"] = list(self.alternative_states)
        payload["conflict_states"] = list(self.conflict_states)
        payload["contributions"] = [item.to_dict() for item in self.contributions]
        payload["reason_codes"] = list(self.reason_codes)
        return payload
