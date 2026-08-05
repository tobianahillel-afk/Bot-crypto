from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar

COMPONENTS = ("trend", "range", "momentum", "volatility", "regime", "confluence")
_ALIGNMENT_STATES = {"MTF_ALIGNED", "MTF_PARTIAL", "MTF_DIVERGENT", "MTF_UNKNOWN"}
_DIVERGENCE_STATES = {
    "MTF_MULTI_COMPONENT_MISMATCH",
    "MTF_DIRECTIONAL_MISMATCH",
    "MTF_REGIME_MISMATCH",
    "MTF_VOLATILITY_MISMATCH",
    "MTF_NO_HARD_DIVERGENCE",
    "MTF_UNKNOWN",
}
_COHERENCE_STATES = {"MTF_COHERENT", "MTF_MIXED", "MTF_INCOHERENT", "MTF_UNKNOWN"}
_CONTEXT_STATES = {
    "MTF_CONTEXT_ALIGNED",
    "MTF_CONTEXT_PARTIAL",
    "MTF_CONTEXT_DIVERGENT",
    "MTF_CONTEXT_UNKNOWN",
}
_UNCERTAINTY_STATES = {"LOW", "MODERATE", "HIGH", "UNKNOWN"}
_VALIDATION_STATES = {"VALID", "UNKNOWN", "BLOCKED", "INVALID"}
_QUALITY_STATES = {"VALID", "STALE", "INCOMPLETE", "INVALID", "UNKNOWN"}


def parse_utc(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field_name} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return parsed


def require_text_fields(instance: object, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        value = getattr(instance, field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")


def require_unique_codes(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{field_name} must contain non-empty strings")


def validate_score(value: float | None, field_name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric or null")
    if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{field_name} must be finite within [0, 1]")


class TupleListSerializable:
    _tuple_fields: ClassVar[tuple[str, ...]] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for field_name in self._tuple_fields:
            payload[field_name] = list(getattr(self, field_name))
        return payload


def _validate_context_dimensions(state: TimeframeMarketContextStateV1) -> None:
    if state.timeframe not in {"5m", "15m"}:
        raise ValueError("Lot 26 v1 accepts only 5m and 15m context states")
    if state.scale_id != f"timebar-{state.timeframe}":
        raise ValueError("scale_id and timeframe are inconsistent")
    if state.data_resolution != state.timeframe:
        raise ValueError("data_resolution and timeframe are inconsistent")
    if state.decision_clock != "CLOSED_LOCAL_BAR":
        raise ValueError("Lot 26 v1 decision_clock must be CLOSED_LOCAL_BAR")
    dimensions = (state.forecast_horizon, state.signal_ttl, state.holding_horizon)
    if any(value is not None for value in dimensions):
        raise ValueError("forecast_horizon, signal_ttl and holding_horizon must remain null")


def _validate_context_time(state: TimeframeMarketContextStateV1) -> None:
    opened = parse_utc(state.bar_open_time, "bar_open_time")
    closed = parse_utc(state.bar_close_time, "bar_close_time")
    event = parse_utc(state.event_time, "event_time")
    available = parse_utc(state.available_at, "available_at")
    decision = parse_utc(state.decision_time, "decision_time")
    parse_utc(state.generated_at, "generated_at")
    if not opened < closed:
        raise ValueError("bar_open_time must be before bar_close_time")
    if event > closed or closed > available or available > decision:
        raise ValueError("context temporal ordering is invalid")


def _validate_context_payload(state: TimeframeMarketContextStateV1) -> None:
    if state.revision_id < 0 or state.sequence_id < 0:
        raise ValueError("revision_id and sequence_id must be non-negative")
    if state.validation_state not in _VALIDATION_STATES:
        raise ValueError("unknown validation_state")
    for key, value in state.component_scores.items():
        if key not in COMPONENTS:
            raise ValueError(f"unknown component score: {key}")
        validate_score(value, f"component_scores.{key}")
    require_unique_codes(state.reason_codes, "reason_codes")
    if state.analysis_only is not True:
        raise ValueError("analysis_only must remain true")
    if state.used_for_decision is not False or state.execution_allowed is not False:
        raise ValueError("decision and execution permissions must remain false")


@dataclass(frozen=True, slots=True)
class TimeframeMarketContextStateV1(TupleListSerializable):
    _tuple_fields: ClassVar[tuple[str, ...]] = ("reason_codes",)
    state_id: str
    instrument_id: str
    timeframe: str
    scale_id: str
    data_resolution: str
    feature_lookback: str | None
    forecast_horizon: None
    decision_clock: str
    signal_ttl: None
    holding_horizon: None
    bar_open_time: str
    bar_close_time: str
    event_time: str
    available_at: str
    decision_time: str
    generated_at: str
    source_bar_id: str
    revision_id: int
    sequence_id: int
    lineage_id: str
    config_version: str
    code_commit: str
    validation_state: str
    trend_state: str
    range_state: str
    momentum_state: str
    volatility_state: str
    regime_state: str
    confluence_state: str
    component_scores: dict[str, float | None] = field(default_factory=dict)
    reason_codes: tuple[str, ...] = ()
    analysis_only: bool = True
    used_for_decision: bool = False
    execution_allowed: bool = False
    schema_version: str = "timeframe-market-context-state-v1"

    def __post_init__(self) -> None:
        fields = (
            "state_id", "instrument_id", "timeframe", "scale_id", "data_resolution",
            "decision_clock", "source_bar_id", "lineage_id", "config_version", "code_commit",
            "trend_state", "range_state", "momentum_state", "volatility_state",
            "regime_state", "confluence_state",
        )
        require_text_fields(self, fields)
        if self.schema_version != "timeframe-market-context-state-v1":
            raise ValueError("unsupported timeframe context schema_version")
        _validate_context_dimensions(self)
        _validate_context_time(self)
        _validate_context_payload(self)


def _validate_availability_time(item: ClosedBarAvailabilityV1) -> None:
    opened = parse_utc(item.bar_open_time, "bar_open_time")
    closed = parse_utc(item.bar_close_time, "bar_close_time")
    available = parse_utc(item.available_at, "available_at")
    decision = parse_utc(item.decision_time, "decision_time")
    if not opened < closed <= available <= decision:
        raise ValueError("closed-bar temporal ordering is invalid")


@dataclass(frozen=True, slots=True)
class ClosedBarAvailabilityV1(TupleListSerializable):
    _tuple_fields: ClassVar[tuple[str, ...]] = ("reason_codes",)
    availability_id: str
    state_id: str
    instrument_id: str
    timeframe: str
    scale_id: str
    source_bar_id: str
    bar_open_time: str
    bar_close_time: str
    available_at: str
    decision_time: str
    is_closed: bool
    is_complete: bool
    quality_state: str
    revision_id: int
    sequence_id: int
    lineage_id: str
    reason_codes: tuple[str, ...] = ()
    schema_version: str = "closed-bar-availability-v1"

    def __post_init__(self) -> None:
        fields = (
            "availability_id", "state_id", "instrument_id", "timeframe",
            "scale_id", "source_bar_id", "lineage_id",
        )
        require_text_fields(self, fields)
        if self.schema_version != "closed-bar-availability-v1":
            raise ValueError("unsupported closed-bar availability schema_version")
        if self.scale_id != f"timebar-{self.timeframe}":
            raise ValueError("scale_id and timeframe are inconsistent")
        _validate_availability_time(self)
        if self.revision_id < 0 or self.sequence_id < 0:
            raise ValueError("revision_id and sequence_id must be non-negative")
        if self.quality_state not in _QUALITY_STATES:
            raise ValueError("unknown quality_state")
        require_unique_codes(self.reason_codes, "reason_codes")

    @property
    def consumable(self) -> bool:
        return self.is_closed and self.is_complete and self.quality_state == "VALID"


def _validate_alignment_states(state: MultiTimeframeAlignmentStateV1) -> None:
    allowed = (
        (state.alignment_state, _ALIGNMENT_STATES, "alignment_state"),
        (state.divergence_state, _DIVERGENCE_STATES, "divergence_state"),
        (state.coherence_state, _COHERENCE_STATES, "coherence_state"),
        (state.combined_context_state, _CONTEXT_STATES, "combined_context_state"),
        (state.uncertainty_state, _UNCERTAINTY_STATES, "uncertainty_state"),
    )
    for value, choices, field_name in allowed:
        if value not in choices:
            raise ValueError(f"unknown {field_name}")


def _validate_alignment_scores(state: MultiTimeframeAlignmentStateV1) -> None:
    if set(state.component_alignment_scores) != set(COMPONENTS):
        raise ValueError("component_alignment_scores must contain exactly six components")
    for key, value in state.component_alignment_scores.items():
        validate_score(value, f"component_alignment_scores.{key}")
    if not 0 <= state.available_component_count <= len(COMPONENTS):
        raise ValueError("available_component_count is out of bounds")
    validate_score(state.weighted_coverage_ratio, "weighted_coverage_ratio")
    validate_score(state.overall_agreement_score, "overall_agreement_score")
    if any(value not in COMPONENTS for value in state.hard_mismatch_components):
        raise ValueError("unknown hard mismatch component")
    require_unique_codes(state.hard_mismatch_components, "hard_mismatch_components")
    require_unique_codes(state.reason_codes, "reason_codes")


def _validate_alignment_safety(state: MultiTimeframeAlignmentStateV1) -> None:
    permissions = (
        state.used_for_decision,
        state.forecast_generation_allowed,
        state.probability_claims_allowed,
        state.signal_generation_allowed,
        state.order_routing_allowed,
        state.execution_allowed,
        state.trade_allowed,
    )
    if state.analysis_only is not True:
        raise ValueError("analysis_only must remain true")
    if any(value is not False for value in permissions) or state.approved_size != 0:
        raise ValueError("all decision, forecast and execution permissions must remain disabled")


@dataclass(frozen=True, slots=True)
class MultiTimeframeAlignmentStateV1(TupleListSerializable):
    _tuple_fields: ClassVar[tuple[str, ...]] = ("hard_mismatch_components", "reason_codes")
    alignment_id: str
    instrument_id: str
    local_scale_id: str
    higher_scale_id: str
    local_timeframe: str
    higher_timeframe: str
    decision_trigger: str
    decision_time: str
    local_state_id: str
    higher_state_id: str
    local_bar_close_time: str
    higher_bar_close_time: str
    join_method: str
    component_alignment_scores: dict[str, float | None]
    available_component_count: int
    weighted_coverage_ratio: float
    overall_agreement_score: float | None
    alignment_state: str
    divergence_state: str
    coherence_state: str
    combined_context_state: str
    hard_mismatch_components: tuple[str, ...]
    reason_codes: tuple[str, ...]
    uncertainty_state: str
    lineage_id: str
    scale_registry_version: str
    decision_clock_policy_version: str
    config_version: str
    config_checksum: str
    code_commit: str
    output_checksum: str
    analysis_only: bool = True
    used_for_decision: bool = False
    forecast_generation_allowed: bool = False
    probability_claims_allowed: bool = False
    signal_generation_allowed: bool = False
    order_routing_allowed: bool = False
    execution_allowed: bool = False
    trade_allowed: bool = False
    approved_size: int = 0
    schema_version: str = "multi-timeframe-alignment-state-v1"

    def __post_init__(self) -> None:
        fields = (
            "alignment_id", "instrument_id", "local_scale_id", "higher_scale_id",
            "decision_trigger", "local_state_id", "higher_state_id", "lineage_id",
            "scale_registry_version", "decision_clock_policy_version", "config_version",
            "config_checksum", "code_commit", "output_checksum",
        )
        require_text_fields(self, fields)
        if self.schema_version != "multi-timeframe-alignment-state-v1":
            raise ValueError("unsupported alignment schema_version")
        edge = (self.local_scale_id, self.higher_scale_id, self.local_timeframe, self.higher_timeframe)
        if edge != ("timebar-5m", "timebar-15m", "5m", "15m"):
            raise ValueError("Lot 26 v1 accepts only the 5m to 15m edge")
        if self.decision_trigger != "CLOSED_LOCAL_BAR" or self.join_method != "ASOF_BACKWARD":
            raise ValueError("invalid Lot 26 trigger or join method")
        parse_utc(self.decision_time, "decision_time")
        parse_utc(self.local_bar_close_time, "local_bar_close_time")
        parse_utc(self.higher_bar_close_time, "higher_bar_close_time")
        _validate_alignment_scores(self)
        _validate_alignment_states(self)
        _validate_alignment_safety(self)
