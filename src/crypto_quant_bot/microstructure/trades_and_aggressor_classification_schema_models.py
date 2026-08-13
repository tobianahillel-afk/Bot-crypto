from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from .trades_and_aggressor_classification_schema_validation import (
    CLASSIFICATIONS,
    CONFIDENCE_SEMANTICS,
    METHODS,
    decimal_text,
    require,
    require_git_sha,
    require_integer,
    require_reason_codes,
    require_sha256,
    require_text,
    validate_causal_times,
    validate_run_context,
    validate_safety,
)


@dataclass(frozen=True, slots=True)
class Lot44RunContextV1:
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
            "schema_version": "lot44-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot44LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    lot43_state_checksum: str
    lot43_audit_checksum: str
    lot43_resilience_checksum: str
    lot43_post_merge_checksum: str
    trade_fixture_checksum: str
    order_book_snapshot_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        for field, value in (
            ("entry_gate_checksum", self.entry_gate_checksum),
            ("lot43_state_checksum", self.lot43_state_checksum),
            ("lot43_audit_checksum", self.lot43_audit_checksum),
            ("lot43_resilience_checksum", self.lot43_resilience_checksum),
            ("lot43_post_merge_checksum", self.lot43_post_merge_checksum),
            ("trade_fixture_checksum", self.trade_fixture_checksum),
            ("order_book_snapshot_checksum", self.order_book_snapshot_checksum),
        ):
            require_sha256(value, field)
        validate_causal_times(self.available_at, self.available_at, self.available_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot44-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "lot43_state_checksum": self.lot43_state_checksum,
            "lot43_audit_checksum": self.lot43_audit_checksum,
            "lot43_resilience_checksum": self.lot43_resilience_checksum,
            "lot43_post_merge_checksum": self.lot43_post_merge_checksum,
            "trade_fixture_checksum": self.trade_fixture_checksum,
            "order_book_snapshot_checksum": self.order_book_snapshot_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class TimestampedTradeV1:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    trade_id: str
    event_time: str
    receive_time: str
    price: Decimal
    quantity: Decimal
    source_side: str

    def __post_init__(self) -> None:
        for field, value in (
            ("source_id", self.source_id),
            ("venue", self.venue),
            ("instrument_id", self.instrument_id),
            ("trade_id", self.trade_id),
        ):
            require_text(value, field)
        require(self.market_type == "SPOT", "Lot 44 reference trade must be SPOT")
        validate_causal_times(self.event_time, self.receive_time, self.receive_time)
        require(
            self.price.is_finite() and self.price > 0,
            "trade price must be positive finite Decimal",
        )
        require(
            self.quantity.is_finite() and self.quantity > 0,
            "trade quantity must be positive finite Decimal",
        )
        require(
            self.source_side == "UNKNOWN",
            "Lot 44 source trade side must remain UNKNOWN",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "timestamped-trade-v1",
            "source_id": self.source_id,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "market_type": self.market_type,
            "trade_id": self.trade_id,
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "price": decimal_text(self.price),
            "quantity": decimal_text(self.quantity),
            "source_side": self.source_side,
        }


def _validate_classification_tuple(
    classification: str,
    method: str,
    confidence: Decimal,
) -> None:
    allowed = {
        "NONE": ({"UNKNOWN"}, Decimal("0")),
        "QUOTE_TEST": ({"BUY_AGGRESSOR", "SELL_AGGRESSOR"}, Decimal("1")),
        "TICK_RULE": ({"BUY_AGGRESSOR", "SELL_AGGRESSOR"}, Decimal("0.5")),
    }
    allowed_classifications, expected_confidence = allowed[method]
    require(
        classification in allowed_classifications and confidence == expected_confidence,
        "classification method/class/confidence tuple invalid",
    )


@dataclass(frozen=True, slots=True)
class ClassifiedTradeV1:
    trade: TimestampedTradeV1
    aggressor_classification: str
    classification_method: str
    confidence: Decimal
    confidence_version: str
    quote_snapshot_checksum: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        require(
            self.aggressor_classification in CLASSIFICATIONS,
            "unknown aggressor classification",
        )
        require(
            self.classification_method in METHODS,
            "unknown classification method",
        )
        require(
            self.confidence.is_finite()
            and Decimal(0) <= self.confidence <= Decimal(1),
            "confidence outside [0,1]",
        )
        require_text(self.confidence_version, "confidence_version")
        require_sha256(self.quote_snapshot_checksum, "quote_snapshot_checksum")
        require_reason_codes(self.reason_codes)
        _validate_classification_tuple(
            self.aggressor_classification,
            self.classification_method,
            self.confidence,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "classified-trade-v1",
            "trade": self.trade.to_dict(),
            "aggressor_classification": self.aggressor_classification,
            "classification_method": self.classification_method,
            "confidence": decimal_text(self.confidence),
            "confidence_version": self.confidence_version,
            "quote_snapshot_checksum": self.quote_snapshot_checksum,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True, slots=True)
class AggressorConfidenceStateV1:
    policy_version: str
    semantics: str
    quote_test_confidence: Decimal
    tick_rule_confidence: Decimal
    unknown_confidence: Decimal
    confidence_checksum: str

    def __post_init__(self) -> None:
        require_text(self.policy_version, "policy_version")
        require(
            self.semantics == CONFIDENCE_SEMANTICS,
            "confidence semantics changed",
        )
        for field, value in (
            ("quote_test_confidence", self.quote_test_confidence),
            ("tick_rule_confidence", self.tick_rule_confidence),
            ("unknown_confidence", self.unknown_confidence),
        ):
            require(
                value.is_finite() and Decimal(0) <= value <= Decimal(1),
                f"{field} outside [0,1]",
            )
        require(
            (
                self.quote_test_confidence,
                self.tick_rule_confidence,
                self.unknown_confidence,
            )
            == (Decimal("1"), Decimal("0.5"), Decimal("0")),
            "Lot 44 v1 confidence constants changed",
        )
        require_sha256(self.confidence_checksum, "confidence_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("confidence_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "aggressor-confidence-state-v1",
            "policy_version": self.policy_version,
            "semantics": self.semantics,
            "quote_test_confidence": decimal_text(self.quote_test_confidence),
            "tick_rule_confidence": decimal_text(self.tick_rule_confidence),
            "unknown_confidence": decimal_text(self.unknown_confidence),
            "confidence_checksum": self.confidence_checksum,
        }


@dataclass(frozen=True, slots=True)
class Lot44MetricsV1:
    trades_total: int
    buy_trades_total: int
    sell_trades_total: int
    unknown_trades_total: int
    total_volume: Decimal
    buy_volume: Decimal
    sell_volume: Decimal
    unknown_volume: Decimal
    unknown_volume_ratio: Decimal

    def __post_init__(self) -> None:
        for field, value in (
            ("trades_total", self.trades_total),
            ("buy_trades_total", self.buy_trades_total),
            ("sell_trades_total", self.sell_trades_total),
            ("unknown_trades_total", self.unknown_trades_total),
        ):
            require_integer(value, field)
        require(
            self.trades_total
            == self.buy_trades_total
            + self.sell_trades_total
            + self.unknown_trades_total,
            "trade count conservation failed",
        )
        require(
            self.total_volume == self.buy_volume + self.sell_volume + self.unknown_volume,
            "volume conservation failed",
        )
        require(self.total_volume > 0, "total volume must be positive")
        require(
            self.unknown_volume_ratio == self.unknown_volume / self.total_volume,
            "unknown volume ratio mismatch",
        )
        require(
            Decimal(0) <= self.unknown_volume_ratio <= Decimal(1),
            "unknown volume ratio outside [0,1]",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot44-metrics-v1",
            "lot_44_trades_total": self.trades_total,
            "lot_44_buy_trades_total": self.buy_trades_total,
            "lot_44_sell_trades_total": self.sell_trades_total,
            "lot_44_unknown_trades_total": self.unknown_trades_total,
            "total_volume": decimal_text(self.total_volume),
            "buy_volume": decimal_text(self.buy_volume),
            "sell_volume": decimal_text(self.sell_volume),
            "unknown_volume": decimal_text(self.unknown_volume),
            "unknown_volume_ratio": decimal_text(self.unknown_volume_ratio),
        }


def _metrics_from_classified_trades(
    classified_trades: tuple[ClassifiedTradeV1, ...],
) -> Lot44MetricsV1:
    buy = tuple(
        item
        for item in classified_trades
        if item.aggressor_classification == "BUY_AGGRESSOR"
    )
    sell = tuple(
        item
        for item in classified_trades
        if item.aggressor_classification == "SELL_AGGRESSOR"
    )
    unknown = tuple(
        item for item in classified_trades if item.aggressor_classification == "UNKNOWN"
    )
    total_volume = sum(
        (item.trade.quantity for item in classified_trades), Decimal("0")
    )
    buy_volume = sum((item.trade.quantity for item in buy), Decimal("0"))
    sell_volume = sum((item.trade.quantity for item in sell), Decimal("0"))
    unknown_volume = sum((item.trade.quantity for item in unknown), Decimal("0"))
    return Lot44MetricsV1(
        trades_total=len(classified_trades),
        buy_trades_total=len(buy),
        sell_trades_total=len(sell),
        unknown_trades_total=len(unknown),
        total_volume=total_volume,
        buy_volume=buy_volume,
        sell_volume=sell_volume,
        unknown_volume=unknown_volume,
        unknown_volume_ratio=unknown_volume / total_volume,
    )


@dataclass(frozen=True, slots=True)
class TradesAggressorClassificationSchemaStateV1:
    run_context: Lot44RunContextV1
    lineage: Lot44LineageEnvelopeV1
    event_time: str
    receive_time: str
    generated_at: str
    validation_state: str
    classified_trades: tuple[ClassifiedTradeV1, ...]
    confidence_state: AggressorConfidenceStateV1
    metrics: Lot44MetricsV1
    reason_codes: tuple[str, ...]
    safety: Mapping[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        validate_causal_times(self.event_time, self.receive_time, self.generated_at)
        require(
            self.validation_state == "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY",
            "unknown Lot 44 validation state",
        )
        require(bool(self.classified_trades), "classified trades cannot be empty")
        require(
            len({item.trade.trade_id for item in self.classified_trades})
            == len(self.classified_trades),
            "trade ids must be unique",
        )
        require(
            self.metrics == _metrics_from_classified_trades(self.classified_trades),
            "metrics do not match classified trades",
        )
        require_reason_codes(self.reason_codes)
        validate_safety(self.safety)
        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "trades-aggressor-classification-schema-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "receive_time": self.receive_time,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "classified_trades": [item.to_dict() for item in self.classified_trades],
            "confidence_state": self.confidence_state.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class TradesAggressorClassificationSchemaAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    entry_gate_checksum: str
    trade_fixture_checksum: str
    order_book_snapshot_checksum: str
    validation_state: str
    safety: Mapping[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit, "code_commit")
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("entry_gate_checksum", self.entry_gate_checksum),
            ("trade_fixture_checksum", self.trade_fixture_checksum),
            ("order_book_snapshot_checksum", self.order_book_snapshot_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        require(
            self.validation_state == "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY",
            "audit validation state changed",
        )
        validate_safety(self.safety)
        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "trades-aggressor-classification-schema-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "entry_gate_checksum": self.entry_gate_checksum,
            "trade_fixture_checksum": self.trade_fixture_checksum,
            "order_book_snapshot_checksum": self.order_book_snapshot_checksum,
            "validation_state": self.validation_state,
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
