from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from types import MappingProxyType
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

from .order_flow_delta_and_cvd_engine_validation import (
    CALCULATION_DECIMAL_PRECISION,
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    VALIDATION_STATE,
    WINDOW_POLICY_VERSION,
    WINDOW_SIZE_US,
    decimal_text,
    event_window_bounds,
    frozen_decimal_context,
    parse_utc_timestamp,
    require,
    require_git_sha,
    require_integer,
    require_reason_codes,
    require_sha256,
    require_text,
    session_id_for_event,
    validate_causal_times,
    validate_ratio,
    validate_run_context,
    validate_safety,
)

EXPECTED_GATE_CHECKSUM = "15ca4d69e59a0898f32eb9cbe558571ecf00ae496ec5d41075da1124393d4468"
EXPECTED_GATE_MERGE = "390d0779f2be257fa8134faf8f02193a760a09c3"
EXPECTED_LOT44_STATE = "1a461cef0bedc0e2b34185ff538a64b1b53373b12b0633b749a34cee2b3c5541"
EXPECTED_LOT44_AUDIT = "03ceda1c49746509f95e7f2ed039e8cc321e8e3cb4adbb946f1aef4ed3eba07d"
EXPECTED_LOT44_CONFIDENCE = "7cb11e078d7f0d9ed0858229d8c6fe31a7cf653a238b280b05dbdd84d1250f05"
EXPECTED_LOT44_CONFIG = "dac06cb3235f3a09cbbb9b41098d7cf2593b94171659f50ef840d1633bfa95b7"
EXPECTED_LOT44_POST_MERGE = "b8b531b2fcb09a30728549cc480d54d9be71504356468704c102ff085c39ea9a"


@dataclass(frozen=True, slots=True)
class Lot45RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        validate_run_context(
            self.run_id,
            self.runtime_mode,
            self.config_version,
            self.code_commit,
            self.correlation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot45-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot45LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    entry_gate_merge_commit: str
    lot44_state_checksum: str
    lot44_audit_checksum: str
    lot44_confidence_checksum: str
    lot44_config_checksum: str
    lot44_post_merge_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        _validate_lineage_checksums(self)
        require_git_sha(self.entry_gate_merge_commit, "entry_gate_merge_commit")
        require(
            self.entry_gate_merge_commit == EXPECTED_GATE_MERGE,
            "entry_gate_merge_commit certified value changed",
        )
        parse_utc_timestamp(self.available_at, "available_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot45-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "entry_gate_merge_commit": self.entry_gate_merge_commit,
            "lot44_state_checksum": self.lot44_state_checksum,
            "lot44_audit_checksum": self.lot44_audit_checksum,
            "lot44_confidence_checksum": self.lot44_confidence_checksum,
            "lot44_config_checksum": self.lot44_config_checksum,
            "lot44_post_merge_checksum": self.lot44_post_merge_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class OrderFlowWindowV1:
    window_start: str
    window_end: str
    event_time: str
    receive_time: str
    session_id: str
    trades_total: int
    buy_trades_total: int
    sell_trades_total: int
    unknown_trades_total: int
    total_volume: Decimal
    buy_volume: Decimal
    sell_volume: Decimal
    unknown_volume: Decimal
    signed_delta: Decimal
    signed_imbalance: Decimal
    classification_coverage: Decimal
    confidence_weighted_volume: Decimal
    confidence_weighted_coverage: Decimal
    delta_impulse: Decimal
    window_checksum: str

    def __post_init__(self) -> None:
        _validate_window_times(self)
        _validate_window_counts(self)
        _validate_window_volumes(self)
        _validate_window_metrics(self)
        require_sha256(self.window_checksum, "window_checksum")
        expected_checksum = canonical_checksum(self.payload_without_checksum())
        if self.window_checksum == "0" * 64:
            object.__setattr__(self, "window_checksum", expected_checksum)
        else:
            require(
                self.window_checksum == expected_checksum,
                "window checksum canonical mismatch",
            )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("window_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-flow-window-v1",
            "window_start": self.window_start,
            "window_end": self.window_end,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "session_id": self.session_id,
            "trades_total": self.trades_total,
            "buy_trades_total": self.buy_trades_total,
            "sell_trades_total": self.sell_trades_total,
            "unknown_trades_total": self.unknown_trades_total,
            "total_volume": decimal_text(self.total_volume),
            "buy_volume": decimal_text(self.buy_volume),
            "sell_volume": decimal_text(self.sell_volume),
            "unknown_volume": decimal_text(self.unknown_volume),
            "signed_delta": decimal_text(self.signed_delta),
            "signed_imbalance": decimal_text(self.signed_imbalance),
            "classification_coverage": decimal_text(self.classification_coverage),
            "confidence_weighted_volume": decimal_text(self.confidence_weighted_volume),
            "confidence_weighted_coverage": decimal_text(
                self.confidence_weighted_coverage
            ),
            "delta_impulse": decimal_text(self.delta_impulse),
            "window_checksum": self.window_checksum,
        }


@dataclass(frozen=True, slots=True)
class OrderFlowStateV1:
    windows: tuple[OrderFlowWindowV1, ...]
    trades_total: int
    buy_trades_total: int
    sell_trades_total: int
    unknown_trades_total: int
    total_volume: Decimal
    buy_volume: Decimal
    sell_volume: Decimal
    unknown_volume: Decimal
    signed_delta: Decimal
    unknown_volume_ratio: Decimal
    classification_coverage: Decimal
    confidence_weighted_volume: Decimal
    confidence_weighted_coverage: Decimal
    order_flow_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "windows", tuple(self.windows))
        _validate_flow_window_sequence(self.windows)
        _validate_flow_counts(self)
        _validate_flow_volumes(self)
        _validate_flow_metrics(self)
        require_sha256(self.order_flow_checksum, "order_flow_checksum")
        expected_checksum = canonical_checksum(self.payload_without_checksum())
        if self.order_flow_checksum == "0" * 64:
            object.__setattr__(self, "order_flow_checksum", expected_checksum)
        else:
            require(
                self.order_flow_checksum == expected_checksum,
                "order-flow checksum canonical mismatch",
            )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("order_flow_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-flow-state-v1",
            "windows": [item.to_dict() for item in self.windows],
            "trades_total": self.trades_total,
            "buy_trades_total": self.buy_trades_total,
            "sell_trades_total": self.sell_trades_total,
            "unknown_trades_total": self.unknown_trades_total,
            "total_volume": decimal_text(self.total_volume),
            "buy_volume": decimal_text(self.buy_volume),
            "sell_volume": decimal_text(self.sell_volume),
            "unknown_volume": decimal_text(self.unknown_volume),
            "signed_delta": decimal_text(self.signed_delta),
            "unknown_volume_ratio": decimal_text(self.unknown_volume_ratio),
            "classification_coverage": decimal_text(self.classification_coverage),
            "confidence_weighted_volume": decimal_text(self.confidence_weighted_volume),
            "confidence_weighted_coverage": decimal_text(
                self.confidence_weighted_coverage
            ),
            "order_flow_checksum": self.order_flow_checksum,
        }


@dataclass(frozen=True, slots=True)
class CVDPointV1:
    event_time: str
    session_id: str
    window_checksum: str
    signed_delta: Decimal
    cvd: Decimal

    def __post_init__(self) -> None:
        parse_utc_timestamp(self.event_time, "CVD event_time")
        require_text(self.session_id, "session_id")
        require(
            self.session_id
            == session_id_for_event(self.event_time, SESSION_POLICY_VERSION),
            "CVD session_id does not match event-time session policy",
        )
        require_sha256(self.window_checksum, "window_checksum")
        require(self.signed_delta.is_finite(), "CVD signed delta must be finite")
        require(self.cvd.is_finite(), "CVD must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "cvd-point-v1",
            "event_time": self.event_time,
            "session_id": self.session_id,
            "window_checksum": self.window_checksum,
            "signed_delta": decimal_text(self.signed_delta),
            "cvd": decimal_text(self.cvd),
        }


@dataclass(frozen=True, slots=True)
class CVDSeriesV1:
    session_policy_version: str
    points: tuple[CVDPointV1, ...]
    cvd_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        require(
            self.session_policy_version == SESSION_POLICY_VERSION,
            "CVD session policy version changed",
        )
        _validate_cvd_points(self.points)
        require_sha256(self.cvd_checksum, "cvd_checksum")
        expected_checksum = canonical_checksum(self.payload_without_checksum())
        if self.cvd_checksum == "0" * 64:
            object.__setattr__(self, "cvd_checksum", expected_checksum)
        else:
            require(
                self.cvd_checksum == expected_checksum,
                "CVD checksum canonical mismatch",
            )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("cvd_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "cvd-series-v1",
            "session_policy_version": self.session_policy_version,
            "points": [item.to_dict() for item in self.points],
            "cvd_checksum": self.cvd_checksum,
        }


@dataclass(frozen=True, slots=True)
class OrderFlowDeltaCVDEngineStateV1:
    run_context: Lot45RunContextV1
    lineage: Lot45LineageEnvelopeV1
    event_time: str
    receive_time: str
    generated_at: str
    validation_state: str
    policy_version: str
    window_policy_version: str
    session_policy_version: str
    order_flow: OrderFlowStateV1
    cvd_series: CVDSeriesV1
    reason_codes: tuple[str, ...]
    safety: Mapping[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))
        validate_causal_times(self.event_time, self.receive_time, self.generated_at)
        _validate_state_versions(self)
        _validate_state_time_envelope(self)
        _validate_state_cvd_binding(self)
        require_reason_codes(self.reason_codes)
        validate_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")
        expected_checksum = canonical_checksum(self.payload_without_checksum())
        if self.output_checksum == "0" * 64:
            object.__setattr__(self, "output_checksum", expected_checksum)
        else:
            require(
                self.output_checksum == expected_checksum,
                "output_checksum canonical mismatch",
            )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-flow-delta-cvd-engine-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "policy_version": self.policy_version,
            "window_policy_version": self.window_policy_version,
            "session_policy_version": self.session_policy_version,
            "order_flow": self.order_flow.to_dict(),
            "cvd_series": self.cvd_series.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class OrderFlowDeltaCVDEngineAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    entry_gate_checksum: str
    lot44_state_checksum: str
    lot44_audit_checksum: str
    lot44_confidence_checksum: str
    lot44_post_merge_checksum: str
    order_flow_checksum: str
    cvd_checksum: str
    validation_state: str
    safety: Mapping[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))
        require_git_sha(self.code_commit, "code_commit")
        _validate_audit_checksums(self)
        require(
            self.validation_state == VALIDATION_STATE,
            "Lot45 audit validation state changed",
        )
        validate_safety(self.safety)
        expected_checksum = canonical_checksum(self.payload_without_checksum())
        if self.audit_checksum == "0" * 64:
            object.__setattr__(self, "audit_checksum", expected_checksum)
        else:
            require(
                self.audit_checksum == expected_checksum,
                "audit_checksum canonical mismatch",
            )

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-flow-delta-cvd-engine-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot44_state_checksum": self.lot44_state_checksum,
            "lot44_audit_checksum": self.lot44_audit_checksum,
            "lot44_confidence_checksum": self.lot44_confidence_checksum,
            "lot44_post_merge_checksum": self.lot44_post_merge_checksum,
            "order_flow_checksum": self.order_flow_checksum,
            "cvd_checksum": self.cvd_checksum,
            "validation_state": self.validation_state,
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }


def _validate_lineage_checksums(lineage: Lot45LineageEnvelopeV1) -> None:
    expected = {
        "entry_gate_checksum": EXPECTED_GATE_CHECKSUM,
        "lot44_state_checksum": EXPECTED_LOT44_STATE,
        "lot44_audit_checksum": EXPECTED_LOT44_AUDIT,
        "lot44_confidence_checksum": EXPECTED_LOT44_CONFIDENCE,
        "lot44_config_checksum": EXPECTED_LOT44_CONFIG,
        "lot44_post_merge_checksum": EXPECTED_LOT44_POST_MERGE,
    }
    for field, expected_value in expected.items():
        value = getattr(lineage, field)
        require_sha256(value, field)
        require(value == expected_value, f"{field} certified value changed")


def _validate_window_times(window: OrderFlowWindowV1) -> None:
    start = parse_utc_timestamp(window.window_start, "window_start")
    end = parse_utc_timestamp(window.window_end, "window_end")
    event = parse_utc_timestamp(window.event_time, "window event_time")
    receive = parse_utc_timestamp(window.receive_time, "window receive_time")
    require(start < end, "window_start must precede window_end")
    require(start <= event < end, "window event_time must be inside event-time window")
    expected_start, expected_end = event_window_bounds(window.event_time, WINDOW_SIZE_US)
    require(
        window.window_start == expected_start and window.window_end == expected_end,
        "window bounds do not match Lot45 event-time tumbling policy",
    )
    require(event <= receive, "window receive_time precedes event_time")
    require_text(window.session_id, "session_id")
    require(
        window.session_id
        == session_id_for_event(window.event_time, SESSION_POLICY_VERSION),
        "window session_id does not match event-time session policy",
    )


def _validate_window_counts(window: OrderFlowWindowV1) -> None:
    values = {
        "trades_total": window.trades_total,
        "buy_trades_total": window.buy_trades_total,
        "sell_trades_total": window.sell_trades_total,
        "unknown_trades_total": window.unknown_trades_total,
    }
    for field, count in values.items():
        require_integer(count, field)
    require(window.trades_total > 0, "order-flow window cannot be empty")
    classified_total = (
        window.buy_trades_total + window.sell_trades_total + window.unknown_trades_total
    )
    require(window.trades_total == classified_total, "order-flow trade count conservation failed")


def _validate_window_volumes(window: OrderFlowWindowV1) -> None:
    volumes = {
        "total_volume": window.total_volume,
        "buy_volume": window.buy_volume,
        "sell_volume": window.sell_volume,
        "unknown_volume": window.unknown_volume,
        "confidence_weighted_volume": window.confidence_weighted_volume,
    }
    for field, volume in volumes.items():
        require(volume.is_finite() and volume >= 0, f"{field} must be finite non-negative")
    require(window.total_volume > 0, "order-flow total volume must be positive")
    with frozen_decimal_context() as context:
        context.prec = CALCULATION_DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        classified_total = window.buy_volume + window.sell_volume + window.unknown_volume
        classified_volume = window.buy_volume + window.sell_volume
        expected_delta = window.buy_volume - window.sell_volume
    require(window.total_volume == classified_total, "order-flow volume conservation failed")
    require(
        window.confidence_weighted_volume <= classified_volume,
        "confidence-weighted volume cannot exceed classified volume",
    )
    require(
        window.signed_delta == expected_delta,
        "signed delta must equal buy minus sell volume",
    )


def _validate_window_metrics(window: OrderFlowWindowV1) -> None:
    with frozen_decimal_context() as context:
        context.prec = CALCULATION_DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        expected_imbalance = window.signed_delta / window.total_volume
        expected_coverage = (window.buy_volume + window.sell_volume) / window.total_volume
        expected_weighted = window.confidence_weighted_volume / window.total_volume
    require(window.signed_imbalance == expected_imbalance, "signed imbalance mismatch")
    require(window.classification_coverage == expected_coverage, "classification coverage mismatch")
    require(
        window.confidence_weighted_coverage == expected_weighted,
        "confidence-weighted coverage mismatch",
    )
    validate_ratio(window.classification_coverage, "classification_coverage")
    validate_ratio(window.confidence_weighted_coverage, "confidence_weighted_coverage")
    require(
        window.confidence_weighted_coverage <= window.classification_coverage,
        "weighted confidence cannot exceed classified-volume coverage",
    )
    require(window.delta_impulse.is_finite(), "delta impulse must be finite")


def _validate_flow_window_sequence(windows: tuple[OrderFlowWindowV1, ...]) -> None:
    require(bool(windows), "order-flow windows cannot be empty")
    starts = [parse_utc_timestamp(item.window_start, "window_start") for item in windows]
    require(starts == sorted(starts), "order-flow windows must be event-time ordered")
    require(len(starts) == len(set(starts)), "order-flow windows must be unique")
    with frozen_decimal_context() as context:
        context.prec = CALCULATION_DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        previous_delta = Decimal("0")
        previous_session: str | None = None
        for item in windows:
            expected = item.signed_delta
            if previous_session == item.session_id:
                expected -= previous_delta
            require(item.delta_impulse == expected, "window delta impulse mismatch")
            previous_delta = item.signed_delta
            previous_session = item.session_id


def _validate_flow_counts(state: OrderFlowStateV1) -> None:
    fields = (
        "trades_total",
        "buy_trades_total",
        "sell_trades_total",
        "unknown_trades_total",
    )
    for field in fields:
        require_integer(getattr(state, field), field)
    expected = {
        "trades_total": sum(item.trades_total for item in state.windows),
        "buy_trades_total": sum(item.buy_trades_total for item in state.windows),
        "sell_trades_total": sum(item.sell_trades_total for item in state.windows),
        "unknown_trades_total": sum(item.unknown_trades_total for item in state.windows),
    }
    for field, value in expected.items():
        require(getattr(state, field) == value, f"{field} aggregate mismatch")


def _validate_flow_volumes(state: OrderFlowStateV1) -> None:
    with frozen_decimal_context() as context:
        context.prec = CALCULATION_DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        expected = {
            "total_volume": sum((item.total_volume for item in state.windows), Decimal("0")),
            "buy_volume": sum((item.buy_volume for item in state.windows), Decimal("0")),
            "sell_volume": sum((item.sell_volume for item in state.windows), Decimal("0")),
            "unknown_volume": sum((item.unknown_volume for item in state.windows), Decimal("0")),
            "confidence_weighted_volume": sum(
                (item.confidence_weighted_volume for item in state.windows),
                Decimal("0"),
            ),
        }
        classified_total = state.buy_volume + state.sell_volume + state.unknown_volume
        classified_volume = state.buy_volume + state.sell_volume
        expected_delta = state.buy_volume - state.sell_volume
    for field, value in expected.items():
        require(getattr(state, field) == value, f"{field} aggregate mismatch")
    require(
        state.total_volume == classified_total,
        "aggregate volume conservation failed",
    )
    require(
        state.confidence_weighted_volume <= classified_volume,
        "aggregate confidence-weighted volume cannot exceed classified volume",
    )
    require(state.signed_delta == expected_delta, "aggregate delta mismatch")


def _validate_flow_metrics(state: OrderFlowStateV1) -> None:
    with frozen_decimal_context() as context:
        context.prec = CALCULATION_DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        expected_unknown = state.unknown_volume / state.total_volume
        expected_coverage = (state.buy_volume + state.sell_volume) / state.total_volume
        expected_weighted = state.confidence_weighted_volume / state.total_volume
    require(state.unknown_volume_ratio == expected_unknown, "unknown volume ratio mismatch")
    require(state.classification_coverage == expected_coverage, "aggregate coverage mismatch")
    require(state.confidence_weighted_coverage == expected_weighted, "aggregate weighted coverage mismatch")
    validate_ratio(state.unknown_volume_ratio, "unknown_volume_ratio")
    validate_ratio(state.classification_coverage, "classification_coverage")
    validate_ratio(state.confidence_weighted_coverage, "confidence_weighted_coverage")


def _validate_cvd_points(points: tuple[CVDPointV1, ...]) -> None:
    require(bool(points), "CVD points cannot be empty")
    event_times = [parse_utc_timestamp(item.event_time, "CVD event_time") for item in points]
    require(event_times == sorted(event_times), "CVD points must be event-time ordered")
    require(len(event_times) == len(set(event_times)), "CVD event times must be unique")
    with frozen_decimal_context() as context:
        context.prec = CALCULATION_DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        current_session: str | None = None
        running = Decimal("0")
        for point in points:
            expected_session = session_id_for_event(point.event_time, SESSION_POLICY_VERSION)
            require(
                point.session_id == expected_session,
                "CVD session_id does not match event-time session policy",
            )
            if point.session_id != current_session:
                current_session = point.session_id
                running = Decimal("0")
            running += point.signed_delta
            require(point.cvd == running, "CVD recurrence mismatch")


def _validate_state_versions(state: OrderFlowDeltaCVDEngineStateV1) -> None:
    require(state.validation_state == VALIDATION_STATE, "Lot45 validation state changed")
    require(state.policy_version == POLICY_VERSION, "Lot45 policy version changed")
    require(state.window_policy_version == WINDOW_POLICY_VERSION, "Lot45 window policy changed")
    require(state.session_policy_version == SESSION_POLICY_VERSION, "Lot45 session policy changed")


def _validate_state_time_envelope(state: OrderFlowDeltaCVDEngineStateV1) -> None:
    max_event = max(
        parse_utc_timestamp(item.event_time, "window event_time")
        for item in state.order_flow.windows
    )
    max_receive = max(
        parse_utc_timestamp(item.receive_time, "window receive_time")
        for item in state.order_flow.windows
    )
    actual_event = parse_utc_timestamp(state.event_time, "state event_time")
    actual_receive = parse_utc_timestamp(state.receive_time, "state receive_time")
    lineage_available = parse_utc_timestamp(
        state.lineage.available_at,
        "lineage available_at",
    )
    generated = parse_utc_timestamp(state.generated_at, "state generated_at")
    require(actual_event == max_event, "Lot45 state event_time must equal latest source event")
    require(actual_receive == max_receive, "Lot45 state receive_time must equal latest source receive time")
    require(
        lineage_available <= generated,
        "Lot45 lineage available_at cannot exceed generated_at",
    )


def _validate_state_cvd_binding(state: OrderFlowDeltaCVDEngineStateV1) -> None:
    windows = state.order_flow.windows
    points = state.cvd_series.points
    require(len(points) == len(windows), "CVD points must bind one-to-one to windows")
    for point, window in zip(points, windows, strict=True):
        require(
            point.window_checksum == window.window_checksum,
            "CVD point window checksum mismatch",
        )
        require(point.event_time == window.event_time, "CVD point event_time mismatch")
        require(point.session_id == window.session_id, "CVD point session_id mismatch")
        require(point.signed_delta == window.signed_delta, "CVD point signed delta mismatch")
        require(
            canonical_checksum(window.payload_without_checksum()) == window.window_checksum,
            "window checksum canonical mismatch",
        )
    require(
        canonical_checksum(state.order_flow.payload_without_checksum())
        == state.order_flow.order_flow_checksum,
        "order-flow checksum canonical mismatch",
    )
    require(
        canonical_checksum(state.cvd_series.payload_without_checksum())
        == state.cvd_series.cvd_checksum,
        "CVD checksum canonical mismatch",
    )


def _validate_audit_checksums(audit: OrderFlowDeltaCVDEngineAuditV1) -> None:
    values = {
        "state_output_checksum": audit.state_output_checksum,
        "config_checksum": audit.config_checksum,
        "entry_gate_checksum": audit.entry_gate_checksum,
        "lot44_state_checksum": audit.lot44_state_checksum,
        "lot44_audit_checksum": audit.lot44_audit_checksum,
        "lot44_confidence_checksum": audit.lot44_confidence_checksum,
        "lot44_post_merge_checksum": audit.lot44_post_merge_checksum,
        "order_flow_checksum": audit.order_flow_checksum,
        "cvd_checksum": audit.cvd_checksum,
        "audit_checksum": audit.audit_checksum,
    }
    for field, value in values.items():
        require_sha256(value, field)
