from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from .order_flow_delta_and_cvd_engine_validation import (
    CLASSIFICATIONS,
    POLICY_VERSION,
    VALIDATION_STATE,
    decimal_text,
    parse_utc_timestamp,
    require,
    require_integer,
    require_sha256,
    require_text,
    validate_causal_times,
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
        require_text(self.run_id, "run_id")
        require_text(self.correlation_id, "correlation_id")
        validate_run_context(self.runtime_mode, self.config_version, self.code_commit)

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
    lot44_state_checksum: str
    lot44_audit_checksum: str
    lot44_confidence_checksum: str
    lot44_code_commit: str
    available_at: str

    def __post_init__(self) -> None:
        require_sha256(self.lot44_state_checksum, "lot44_state_checksum")
        require_sha256(self.lot44_audit_checksum, "lot44_audit_checksum")
        require_sha256(self.lot44_confidence_checksum, "lot44_confidence_checksum")
        require_text(self.lot44_code_commit, "lot44_code_commit")
        parse_utc_timestamp(self.available_at, "lineage available_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot45-lineage-envelope-v1",
            "lot44_state_checksum": self.lot44_state_checksum,
            "lot44_audit_checksum": self.lot44_audit_checksum,
            "lot44_confidence_checksum": self.lot44_confidence_checksum,
            "lot44_code_commit": self.lot44_code_commit,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class OrderFlowStateV1:
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
    order_flow_checksum: str

    def __post_init__(self) -> None:
        for field, value in (
            ("trades_total", self.trades_total),
            ("buy_trades_total", self.buy_trades_total),
            ("sell_trades_total", self.sell_trades_total),
            ("unknown_trades_total", self.unknown_trades_total),
        ):
            require_integer(value, field)
        require(
            self.trades_total == self.buy_trades_total + self.sell_trades_total + self.unknown_trades_total,
            "Lot45 trade count conservation failed",
        )
        for field, value in (
            ("total_volume", self.total_volume),
            ("buy_volume", self.buy_volume),
            ("sell_volume", self.sell_volume),
            ("unknown_volume", self.unknown_volume),
            ("signed_delta", self.signed_delta),
            ("unknown_volume_ratio", self.unknown_volume_ratio),
        ):
            require(value.is_finite(), f"{field} must be finite")
        require(self.total_volume > 0, "Lot45 total volume must be positive")
        require(self.buy_volume >= 0 and self.sell_volume >= 0 and self.unknown_volume >= 0, "Lot45 volumes must be non-negative")
        require(self.total_volume == self.buy_volume + self.sell_volume + self.unknown_volume, "Lot45 volume conservation failed")
        require(self.signed_delta == self.buy_volume - self.sell_volume, "Lot45 signed delta changed")
        require(self.unknown_volume_ratio == self.unknown_volume / self.total_volume, "Lot45 unknown volume ratio mismatch")
        require(Decimal(0) <= self.unknown_volume_ratio <= Decimal(1), "Lot45 unknown ratio outside [0,1]")
        require_sha256(self.order_flow_checksum, "order_flow_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("order_flow_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "order-flow-state-v1",
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
            "order_flow_checksum": self.order_flow_checksum,
        }


@dataclass(frozen=True, slots=True)
class CVDPointV1:
    sequence: int
    trade_id: str
    event_time: str
    receive_time: str
    aggressor_classification: str
    quantity: Decimal
    signed_trade_delta: Decimal
    cumulative_delta: Decimal

    def __post_init__(self) -> None:
        require_integer(self.sequence, "sequence")
        require_text(self.trade_id, "trade_id")
        require(self.aggressor_classification in CLASSIFICATIONS, "unknown Lot45 aggressor classification")
        validate_causal_times(self.event_time, self.receive_time, self.receive_time)
        require(self.quantity.is_finite() and self.quantity > 0, "Lot45 point quantity must be positive")
        require(self.signed_trade_delta.is_finite(), "Lot45 point delta must be finite")
        require(self.cumulative_delta.is_finite(), "Lot45 cumulative delta must be finite")
        expected = {
            "BUY_AGGRESSOR": self.quantity,
            "SELL_AGGRESSOR": -self.quantity,
            "UNKNOWN": Decimal("0"),
        }[self.aggressor_classification]
        require(self.signed_trade_delta == expected, "Lot45 signed trade delta inconsistent with classification")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "cvd-point-v1",
            "sequence": self.sequence,
            "trade_id": self.trade_id,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "aggressor_classification": self.aggressor_classification,
            "quantity": decimal_text(self.quantity),
            "signed_trade_delta": decimal_text(self.signed_trade_delta),
            "cumulative_delta": decimal_text(self.cumulative_delta),
        }


@dataclass(frozen=True, slots=True)
class CVDSeriesV1:
    policy_version: str
    starting_cvd: Decimal
    points: tuple[CVDPointV1, ...]
    final_cvd: Decimal
    cvd_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        require(self.policy_version == POLICY_VERSION, "Lot45 CVD policy version changed")
        require(self.starting_cvd == Decimal("0"), "Lot45 CVD must start at zero")
        require(bool(self.points), "Lot45 CVD series cannot be empty")
        require(tuple(point.sequence for point in self.points) == tuple(range(len(self.points))), "Lot45 CVD sequence is not contiguous")
        require(len({point.trade_id for point in self.points}) == len(self.points), "Lot45 CVD trade ids must be unique")
        running = self.starting_cvd
        for point in self.points:
            running += point.signed_trade_delta
            require(point.cumulative_delta == running, "Lot45 CVD cumulative path mismatch")
        require(self.final_cvd == running, "Lot45 final CVD mismatch")
        require_sha256(self.cvd_checksum, "cvd_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("cvd_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "cvd-series-v1",
            "policy_version": self.policy_version,
            "starting_cvd": decimal_text(self.starting_cvd),
            "points": [point.to_dict() for point in self.points],
            "final_cvd": decimal_text(self.final_cvd),
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
    order_flow: OrderFlowStateV1
    cvd: CVDSeriesV1
    reason_codes: tuple[str, ...]
    safety: Mapping[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(self.reason_codes))
        validate_causal_times(self.event_time, self.receive_time, self.generated_at)
        require(self.validation_state == VALIDATION_STATE, "Lot45 validation state changed")
        require(self.order_flow.trades_total == len(self.cvd.points), "Lot45 order-flow/CVD trade count mismatch")
        require(self.order_flow.signed_delta == self.cvd.final_cvd - self.cvd.starting_cvd, "Lot45 order-flow/CVD delta mismatch")
        require(self.event_time == max(point.event_time for point in self.cvd.points), "Lot45 state event_time must match point maximum")
        require(self.receive_time == max(point.receive_time for point in self.cvd.points), "Lot45 state receive_time must match point maximum")
        generated = parse_utc_timestamp(self.generated_at, "generated_at")
        require(all(parse_utc_timestamp(point.receive_time, "point receive_time") <= generated for point in self.cvd.points), "Lot45 point unavailable at state generation")
        require(bool(self.reason_codes) and len(set(self.reason_codes)) == len(self.reason_codes), "Lot45 reason codes invalid")
        validate_safety(self.safety)
        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))
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
            "order_flow": self.order_flow.to_dict(),
            "cvd": self.cvd.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class OrderFlowDeltaCVDEngineAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    lot44_state_checksum: str
    lot44_audit_checksum: str
    lot44_confidence_checksum: str
    validation_state: str
    safety: Mapping[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_text(self.code_commit, "code_commit")
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("lot44_state_checksum", self.lot44_state_checksum),
            ("lot44_audit_checksum", self.lot44_audit_checksum),
            ("lot44_confidence_checksum", self.lot44_confidence_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        require(self.validation_state == VALIDATION_STATE, "Lot45 audit validation state changed")
        validate_safety(self.safety)
        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))

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
            "lot44_state_checksum": self.lot44_state_checksum,
            "lot44_audit_checksum": self.lot44_audit_checksum,
            "lot44_confidence_checksum": self.lot44_confidence_checksum,
            "validation_state": self.validation_state,
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
