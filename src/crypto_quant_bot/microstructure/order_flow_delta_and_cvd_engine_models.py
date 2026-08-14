from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from .order_flow_delta_and_cvd_engine_validation import (
    CONFIG_VERSION,
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    VALIDATION_STATE,
    WINDOW_POLICY_VERSION,
    decimal_text,
    parse_utc_timestamp,
    require,
    require_git_sha,
    require_integer,
    require_reason_codes,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_ratio,
    validate_run_context,
    validate_safety,
)


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
        for field, value in (
            ("entry_gate_checksum", self.entry_gate_checksum),
            ("lot44_state_checksum", self.lot44_state_checksum),
            ("lot44_audit_checksum", self.lot44_audit_checksum),
            ("lot44_confidence_checksum", self.lot44_confidence_checksum),
            ("lot44_config_checksum", self.lot44_config_checksum),
            ("lot44_post_merge_checksum", self.lot44_post_merge_checksum),
        ):
            require_sha256(value, field)
        require_git_sha(self.entry_gate_merge_commit, "entry_gate_merge_commit")
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
    confidence_weighted_coverage: Decimal
    delta_impulse: Decimal
    window_checksum: str

    def __post_init__(self) -> None:
        start = parse_utc_timestamp(self.window_start, "window_start")
        end = parse_utc_timestamp(self.window_end, "window_end")
        event = parse_utc_timestamp(self.event_time, "window event_time")
        receive = parse_utc_timestamp(self.receive_time, "window receive_time")
        require(start < end, "window_start must precede window_end")
        require(start <= event < end, "window event_time must be inside event-time window")
        require(event <= receive, "window receive_time precedes event_time")
        require_text(self.session_id, "session_id")
        for field, value in (
            ("trades_total", self.trades_total),
            ("buy_trades_total", self.buy_trades_total),
            ("sell_trades_total", self.sell_trades_total),
            ("unknown_trades_total", self.unknown_trades_total),
        ):
            require_integer(value, field)
        require(self.trades_total > 0, "order-flow window cannot be empty")
        require(
            self.trades_total
            == self.buy_trades_total + self.sell_trades_total + self.unknown_trades_total,
            "order-flow trade count conservation failed",
        )
        for field, value in (
            ("total_volume", self.total_volume),
            ("buy_volume", self.buy_volume),
            ("sell_volume", self.sell_volume),
            ("unknown_volume", self.unknown_volume),
        ):
            require(value.is_finite() and value >= 0, f"{field} must be finite non-negative")
        require(self.total_volume > 0, "order-flow total volume must be positive")
        require(
            self.total_volume == self.buy_volume + self.sell_volume + self.unknown_volume,
            "order-flow volume conservation failed",
        )
        require(
            self.signed_delta == self.buy_volume - self.sell_volume,
            "signed delta must equal buy minus sell volume",
        )
        require(
            self.signed_imbalance == self.signed_delta / self.total_volume,
            "signed imbalance must equal signed delta divided by total volume",
        )
        expected_coverage = (self.buy_volume + self.sell_volume) / self.total_volume
        require(
            self.classification_coverage == expected_coverage,
            "classification coverage mismatch",
        )
        validate_ratio(self.classification_coverage, "classification_coverage")
        validate_ratio(
            self.confidence_weighted_coverage,
            "confidence_weighted_coverage",
        )
        require(
            self.confidence_weighted_coverage <= self.classification_coverage,
            "weighted confidence cannot exceed classified-volume coverage",
        )
        require(self.delta_impulse.is_finite(), "delta impulse must be finite")
        require_sha256(self.window_checksum, "window_checksum")

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
    confidence_weighted_coverage: Decimal
    order_flow_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "windows", tuple(self.windows))
        require(bool(self.windows), "order-flow windows cannot be empty")
        starts = [parse_utc_timestamp(item.window_start, "window_start") for item in self.windows]
        require(starts == sorted(starts), "order-flow windows must be event-time ordered")
        require(len(starts) == len(set(starts)), "order-flow windows must be unique")
        expected_impulse = Decimal("0")
        previous_delta = Decimal("0")
        previous_session: str | None = None
        for item in self.windows:
            if previous_session != item.session_id:
                expected_impulse = item.signed_delta
            else:
                expected_impulse = item.signed_delta - previous_delta
            require(item.delta_impulse == expected_impulse, "window delta impulse mismatch")
            previous_delta = item.signed_delta
            previous_session = item.session_id
        aggregates = {
            "trades_total": sum(item.trades_total for item in self.windows),
            "buy_trades_total": sum(item.buy_trades_total for item in self.windows),
            "sell_trades_total": sum(item.sell_trades_total for item in self.windows),
            "unknown_trades_total": sum(item.unknown_trades_total for item in self.windows),
        }
        for field, expected in aggregates.items():
            require(getattr(self, field) == expected, f"{field} aggregate mismatch")
        total_volume = sum((item.total_volume for item in self.windows), Decimal("0"))
        buy_volume = sum((item.buy_volume for item in self.windows), Decimal("0"))
        sell_volume = sum((item.sell_volume for item in self.windows), Decimal("0"))
        unknown_volume = sum((item.unknown_volume for item in self.windows), Decimal("0"))
        require(self.total_volume == total_volume, "total volume aggregate mismatch")
        require(self.buy_volume == buy_volume, "buy volume aggregate mismatch")
        require(self.sell_volume == sell_volume, "sell volume aggregate mismatch")
        require(self.unknown_volume == unknown_volume, "unknown volume aggregate mismatch")
        require(
            self.total_volume == self.buy_volume + self.sell_volume + self.unknown_volume,
            "aggregate volume conservation failed",
        )
        require(self.signed_delta == self.buy_volume - self.sell_volume, "aggregate delta mismatch")
        require(
            self.unknown_volume_ratio == self.unknown_volume / self.total_volume,
            "unknown volume ratio mismatch",
        )
        require(
            self.classification_coverage
            == (self.buy_volume + self.sell_volume) / self.total_volume,
            "aggregate classification coverage mismatch",
        )
        expected_weighted = sum(
            (
                item.confidence_weighted_coverage * item.total_volume
                for item in self.windows
            ),
            Decimal("0"),
        ) / self.total_volume
        require(
            self.confidence_weighted_coverage == expected_weighted,
            "aggregate confidence-weighted coverage mismatch",
        )
        validate_ratio(self.unknown_volume_ratio, "unknown_volume_ratio")
        validate_ratio(self.classification_coverage, "classification_coverage")
        validate_ratio(
            self.confidence_weighted_coverage,
            "confidence_weighted_coverage",
        )
        require_sha256(self.order_flow_checksum, "order_flow_checksum")

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
        require(bool(self.points), "CVD points cannot be empty")
        event_times = [parse_utc_timestamp(item.event_time, "CVD event_time") for item in self.points]
        require(event_times == sorted(event_times), "CVD points must be event-time ordered")
        require(len(event_times) == len(set(event_times)), "CVD event times must be unique")
        current_session: str | None = None
        running = Decimal("0")
        for point in self.points:
            if point.session_id != current_session:
                current_session = point.session_id
                running = Decimal("0")
            running += point.signed_delta
            require(point.cvd == running, "CVD recurrence mismatch")
        require_sha256(self.cvd_checksum, "cvd_checksum")

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
        require(self.validation_state == VALIDATION_STATE, "Lot45 validation state changed")
        require(self.policy_version == POLICY_VERSION, "Lot45 policy version changed")
        require(
            self.window_policy_version == WINDOW_POLICY_VERSION,
            "Lot45 window policy version changed",
        )
        require(
            self.session_policy_version == SESSION_POLICY_VERSION,
            "Lot45 session policy version changed",
        )
        max_event = max(
            parse_utc_timestamp(item.event_time, "window event_time")
            for item in self.order_flow.windows
        )
        max_receive = max(
            parse_utc_timestamp(item.receive_time, "window receive_time")
            for item in self.order_flow.windows
        )
        require(
            parse_utc_timestamp(self.event_time, "state event_time") == max_event,
            "Lot45 state event_time must equal latest source event",
        )
        require(
            parse_utc_timestamp(self.receive_time, "state receive_time") == max_receive,
            "Lot45 state receive_time must equal latest source receive time",
        )
        require(
            [point.window_checksum for point in self.cvd_series.points]
            == [window.window_checksum for window in self.order_flow.windows],
            "CVD points must bind one-to-one to order-flow windows",
        )
        require_reason_codes(self.reason_codes)
        validate_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

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
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("entry_gate_checksum", self.entry_gate_checksum),
            ("lot44_state_checksum", self.lot44_state_checksum),
            ("lot44_audit_checksum", self.lot44_audit_checksum),
            ("lot44_confidence_checksum", self.lot44_confidence_checksum),
            ("lot44_post_merge_checksum", self.lot44_post_merge_checksum),
            ("order_flow_checksum", self.order_flow_checksum),
            ("cvd_checksum", self.cvd_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        require(self.validation_state == VALIDATION_STATE, "Lot45 audit validation state changed")
        validate_safety(self.safety)

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
