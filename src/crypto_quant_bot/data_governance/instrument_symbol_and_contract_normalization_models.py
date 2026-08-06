from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .source_registry_validation import fail_closed_safety

MARKET_TYPES = ("SPOT", "PERPETUAL", "DATED_FUTURE", "OPTION")
OPTION_TYPES = ("CALL", "PUT")
DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
INSTRUMENT_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOKEN_PATTERN = re.compile(r"^[A-Z0-9]+$")


class InstrumentNormalizationError(ValueError):
    """Fail-closed error for Lot 32 instrument normalization."""


def require_text(value: str, field: str) -> None:
    if not value or value != value.strip():
        raise InstrumentNormalizationError(f"{field} must be explicit and trimmed")


def require_utc(value: str, field: str) -> None:
    require_text(value, field)
    if "T" not in value or not value.endswith("Z"):
        raise InstrumentNormalizationError(f"{field} must be an explicit UTC timestamp")


def require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise InstrumentNormalizationError(f"{field} must be a lowercase sha256")


def require_git_sha(value: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise InstrumentNormalizationError("code_commit must be a lowercase 40-character git sha")


def decimal_value(value: str, field: str) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_PATTERN.fullmatch(value):
        raise InstrumentNormalizationError(f"{field} must be a canonical decimal string")
    parsed = Decimal(value)
    if not parsed.is_finite() or parsed <= 0:
        raise InstrumentNormalizationError(f"{field} must be finite and positive")
    normalized = format(parsed.normalize(), "f")
    if value != normalized:
        raise InstrumentNormalizationError(f"{field} must use canonical decimal form")
    return parsed


def decimal_places(value: str, field: str) -> int:
    exponent = decimal_value(value, field).as_tuple().exponent
    return max(0, -int(exponent))


def optional_decimal(value: str | None, field: str) -> Decimal | None:
    return None if value is None else decimal_value(value, field)


def validate_lot32_safety(values: dict[str, object]) -> None:
    if values != fail_closed_safety():
        raise InstrumentNormalizationError("Lot 32 safety boundary must remain exactly fail-closed")


@dataclass(frozen=True, slots=True)
class Lot32RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        for field, value in (
            ("run_id", self.run_id),
            ("config_version", self.config_version),
            ("correlation_id", self.correlation_id),
        ):
            require_text(value, field)
        if self.runtime_mode != "DATA_GOVERNANCE_ONLY":
            raise InstrumentNormalizationError("Lot 32 runtime must be DATA_GOVERNANCE_ONLY")
        require_git_sha(self.code_commit)

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot32LineageEnvelopeV1:
    lineage_id: str
    source_registry_path: str
    source_registry_checksum: str
    lot31_state_checksum: str
    lot31_audit_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        if self.source_registry_path != "data/audit/source_registry_lot31.json":
            raise InstrumentNormalizationError("Lot 32 lineage must use SourceRegistryV1")
        for field, value in (
            ("source_registry_checksum", self.source_registry_checksum),
            ("lot31_state_checksum", self.lot31_state_checksum),
            ("lot31_audit_checksum", self.lot31_audit_checksum),
        ):
            require_sha256(value, field)
        require_utc(self.available_at, "available_at")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot32-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "source_registry_path": self.source_registry_path,
            "source_registry_checksum": self.source_registry_checksum,
            "lot31_state_checksum": self.lot31_state_checksum,
            "lot31_audit_checksum": self.lot31_audit_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class VenueInstrumentAliasV1:
    venue: str
    exchange_symbol: str
    source_id: str
    source_revision: int
    tick_size: str
    lot_size: str
    min_qty: str
    min_notional: str
    price_precision: int
    quantity_precision: int
    fee_tier: str
    margin_mode: str | None
    leverage_policy: str
    validation_state: str

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_decimal_contract()
        self._validate_policy()

    def _validate_identity(self) -> None:
        if not TOKEN_PATTERN.fullmatch(self.venue):
            raise InstrumentNormalizationError("venue must be an uppercase canonical token")
        for field, value in (
            ("exchange_symbol", self.exchange_symbol),
            ("source_id", self.source_id),
            ("fee_tier", self.fee_tier),
            ("leverage_policy", self.leverage_policy),
        ):
            require_text(value, field)
        if self.source_revision < 1:
            raise InstrumentNormalizationError("source_revision must be positive")

    def _validate_decimal_contract(self) -> None:
        for field, value in (
            ("tick_size", self.tick_size),
            ("lot_size", self.lot_size),
            ("min_qty", self.min_qty),
            ("min_notional", self.min_notional),
        ):
            decimal_value(value, field)
        if self.price_precision < 0 or self.quantity_precision < 0:
            raise InstrumentNormalizationError("instrument precision cannot be negative")
        if decimal_places(self.tick_size, "tick_size") != self.price_precision:
            raise InstrumentNormalizationError("price_precision differs from tick_size")
        if decimal_places(self.lot_size, "lot_size") != self.quantity_precision:
            raise InstrumentNormalizationError("quantity_precision differs from lot_size")

    def _validate_policy(self) -> None:
        if self.margin_mode is not None:
            require_text(self.margin_mode, "margin_mode")
        if self.validation_state != "VALIDATED_METADATA_ONLY":
            raise InstrumentNormalizationError("venue alias must remain metadata-only")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "venue-instrument-alias-v1",
            "venue": self.venue,
            "exchange_symbol": self.exchange_symbol,
            "source_id": self.source_id,
            "source_revision": self.source_revision,
            "tick_size": self.tick_size,
            "lot_size": self.lot_size,
            "min_qty": self.min_qty,
            "min_notional": self.min_notional,
            "price_precision": self.price_precision,
            "quantity_precision": self.quantity_precision,
            "fee_tier": self.fee_tier,
            "margin_mode": self.margin_mode,
            "leverage_policy": self.leverage_policy,
            "validation_state": self.validation_state,
        }


@dataclass(frozen=True, slots=True)
class InstrumentSpecificationV1:
    instrument_id: str
    canonical_symbol: str
    base_asset: str
    quote_asset: str
    market_type: str
    settlement_asset: str
    contract_size: str | None
    expiry_time: str | None
    strike_price: str | None
    option_type: str | None
    aliases: tuple[VenueInstrumentAliasV1, ...]
    validation_state: str

    def __post_init__(self) -> None:
        if not INSTRUMENT_ID_PATTERN.fullmatch(self.instrument_id):
            raise InstrumentNormalizationError("instrument_id must be canonical lowercase")
        for field, value in (
            ("base_asset", self.base_asset),
            ("quote_asset", self.quote_asset),
            ("settlement_asset", self.settlement_asset),
        ):
            if not TOKEN_PATTERN.fullmatch(value):
                raise InstrumentNormalizationError(f"{field} must be an uppercase token")
        if self.market_type not in MARKET_TYPES:
            raise InstrumentNormalizationError("unknown market_type")
        expected_symbol = f"{self.base_asset}/{self.quote_asset}:{self.market_type}"
        if self.canonical_symbol != expected_symbol:
            raise InstrumentNormalizationError("canonical_symbol does not match instrument identity")
        if self.validation_state != "VALIDATED_NORMALIZATION_ONLY":
            raise InstrumentNormalizationError("unexpected instrument validation_state")
        self._validate_applicability()
        self._validate_aliases()

    def _validate_applicability(self) -> None:
        contract = optional_decimal(self.contract_size, "contract_size")
        strike = optional_decimal(self.strike_price, "strike_price")
        if self.expiry_time is not None:
            require_utc(self.expiry_time, "expiry_time")
        if self.option_type is not None and self.option_type not in OPTION_TYPES:
            raise InstrumentNormalizationError("option_type must be CALL or PUT")
        validators = {
            "SPOT": self._validate_spot,
            "PERPETUAL": self._validate_perpetual,
            "DATED_FUTURE": self._validate_dated_future,
            "OPTION": self._validate_option,
        }
        validators[self.market_type](contract, strike)

    def _validate_spot(self, contract: Decimal | None, strike: Decimal | None) -> None:
        values = (contract, self.expiry_time, strike, self.option_type)
        if any(value is not None for value in values):
            raise InstrumentNormalizationError("spot derivative fields must be null")
        if self.settlement_asset != self.quote_asset:
            raise InstrumentNormalizationError("spot settlement must equal quote asset")

    def _validate_perpetual(self, contract: Decimal | None, strike: Decimal | None) -> None:
        invalid_optional = (self.expiry_time, strike, self.option_type)
        if contract is None or any(value is not None for value in invalid_optional):
            raise InstrumentNormalizationError("perpetual applicability fields are invalid")

    def _validate_dated_future(self, contract: Decimal | None, strike: Decimal | None) -> None:
        if contract is None or self.expiry_time is None:
            raise InstrumentNormalizationError("dated future requires contract size and expiry")
        if strike is not None or self.option_type is not None:
            raise InstrumentNormalizationError("future option fields must be null")

    def _validate_option(self, contract: Decimal | None, strike: Decimal | None) -> None:
        required = (contract, self.expiry_time, strike, self.option_type)
        if any(value is None for value in required):
            raise InstrumentNormalizationError("option requires contract, expiry, strike and type")

    def _validate_aliases(self) -> None:
        if not self.aliases:
            raise InstrumentNormalizationError("instrument requires at least one venue alias")
        venues = tuple(alias.venue for alias in self.aliases)
        if tuple(sorted(venues)) != venues or len(set(venues)) != len(venues):
            raise InstrumentNormalizationError("venue aliases must be unique and ordered")
        if self.market_type == "SPOT" and any(
            alias.margin_mode is not None or alias.leverage_policy != "FORBIDDEN"
            for alias in self.aliases
        ):
            raise InstrumentNormalizationError("spot aliases cannot enable margin or leverage")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "instrument-specification-v1",
            "instrument_id": self.instrument_id,
            "canonical_symbol": self.canonical_symbol,
            "base_asset": self.base_asset,
            "quote_asset": self.quote_asset,
            "market_type": self.market_type,
            "settlement_asset": self.settlement_asset,
            "contract_size": self.contract_size,
            "expiry_time": self.expiry_time,
            "strike_price": self.strike_price,
            "option_type": self.option_type,
            "aliases": [alias.to_dict() for alias in self.aliases],
            "validation_state": self.validation_state,
        }


@dataclass(frozen=True, slots=True)
class InstrumentRegistryV1:
    registry_id: str
    registry_version: str
    revision_policy: str
    instruments: tuple[InstrumentSpecificationV1, ...]

    def __post_init__(self) -> None:
        require_text(self.registry_id, "registry_id")
        require_text(self.registry_version, "registry_version")
        if self.revision_policy != "IMMUTABLE_VERSIONED_REPLACEMENT":
            raise InstrumentNormalizationError("instrument registry revision policy changed")
        ids = tuple(item.instrument_id for item in self.instruments)
        symbols = tuple(item.canonical_symbol for item in self.instruments)
        if not ids or tuple(sorted(ids)) != ids or len(set(ids)) != len(ids):
            raise InstrumentNormalizationError("instrument ids must be non-empty, unique and ordered")
        if len(set(symbols)) != len(symbols):
            raise InstrumentNormalizationError("canonical symbols must be unique")
        aliases = [
            (alias.venue, alias.exchange_symbol)
            for instrument in self.instruments
            for alias in instrument.aliases
        ]
        if len(set(aliases)) != len(aliases):
            raise InstrumentNormalizationError("venue symbol aliases must be unique")

    def exchange_symbol_for(self, canonical_symbol: str, venue: str) -> str:
        for instrument in self.instruments:
            if instrument.canonical_symbol == canonical_symbol:
                for alias in instrument.aliases:
                    if alias.venue == venue:
                        return alias.exchange_symbol
        raise InstrumentNormalizationError("canonical symbol or venue alias is unknown")

    def canonical_symbol_for(self, venue: str, exchange_symbol: str) -> str:
        for instrument in self.instruments:
            for alias in instrument.aliases:
                if alias.venue == venue and alias.exchange_symbol == exchange_symbol:
                    return instrument.canonical_symbol
        raise InstrumentNormalizationError("venue symbol alias is unknown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "instrument-registry-v1",
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "revision_policy": self.revision_policy,
            "instruments": [instrument.to_dict() for instrument in self.instruments],
        }


@dataclass(frozen=True, slots=True)
class Lot32MetricsV1:
    records_processed_total: int
    venue_aliases_total: int
    frozen_instruments_total: int
    validation_failures_total: int
    processing_latency_ms: int

    def __post_init__(self) -> None:
        values = (
            self.records_processed_total,
            self.venue_aliases_total,
            self.frozen_instruments_total,
            self.validation_failures_total,
            self.processing_latency_ms,
        )
        if any(value < 0 for value in values):
            raise InstrumentNormalizationError("Lot 32 metrics cannot be negative")

    def to_dict(self) -> dict[str, int | str]:
        return {
            "schema_version": "lot32-metrics-v1",
            "lot_32_records_processed_total": self.records_processed_total,
            "lot_32_venue_aliases_total": self.venue_aliases_total,
            "lot_32_frozen_instruments_total": self.frozen_instruments_total,
            "lot_32_validation_failures_total": self.validation_failures_total,
            "lot_32_processing_latency_ms": self.processing_latency_ms,
        }


@dataclass(frozen=True, slots=True)
class InstrumentSymbolContractNormalizationStateV1:
    run_context: Lot32RunContextV1
    lineage: Lot32LineageEnvelopeV1
    event_time: str
    available_at: str
    generated_at: str
    validation_state: str
    instrument_registry: InstrumentRegistryV1
    metrics: Lot32MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        for field, value in (
            ("event_time", self.event_time),
            ("available_at", self.available_at),
            ("generated_at", self.generated_at),
        ):
            require_utc(value, field)
        if not self.event_time <= self.available_at <= self.generated_at:
            raise InstrumentNormalizationError("Lot 32 timestamps violate causal availability")
        if self.validation_state != "VALIDATED_NORMALIZATION_ONLY":
            raise InstrumentNormalizationError("unexpected Lot 32 validation_state")
        expected_reasons = (
            "LOT32_ENTRY_GATE_VERIFIED",
            "LOT31_SOURCE_REGISTRY_LINEAGE_VERIFIED",
            "INSTRUMENT_METADATA_NORMALIZED",
            "CANONICAL_VENUE_ROUND_TRIP_VERIFIED",
            "DECIMAL_CONSTRAINTS_VALIDATED",
            "EXTERNAL_CONNECTIVITY_DISABLED",
            "LOT33_REMAINS_LOCKED",
        )
        if self.reason_codes != expected_reasons:
            raise InstrumentNormalizationError("unexpected Lot 32 reason code sequence")
        validate_lot32_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "instrument-symbol-contract-normalization-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "available_at": self.available_at,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "instrument_registry": self.instrument_registry.to_dict(),
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["output_checksum"] = self.output_checksum
        return payload


@dataclass(frozen=True, slots=True)
class InstrumentSymbolContractNormalizationAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    source_registry_checksum: str
    instrument_count: int
    venue_alias_count: int
    round_trip_count: int
    frozen_instrument_count: int
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit)
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("source_registry_checksum", self.source_registry_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        if self.instrument_count < 1 or self.venue_alias_count < self.instrument_count:
            raise InstrumentNormalizationError("Lot 32 audit registry counts are invalid")
        if self.round_trip_count != self.venue_alias_count * 2:
            raise InstrumentNormalizationError("every venue alias requires two round-trip checks")
        if self.frozen_instrument_count != 0:
            raise InstrumentNormalizationError("certified Lot 32 output cannot contain frozen records")
        if self.validation_state != "VALIDATED_NORMALIZATION_ONLY":
            raise InstrumentNormalizationError("unexpected Lot 32 audit validation_state")
        validate_lot32_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "instrument-symbol-contract-normalization-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "source_registry_checksum": self.source_registry_checksum,
            "instrument_count": self.instrument_count,
            "venue_alias_count": self.venue_alias_count,
            "round_trip_count": self.round_trip_count,
            "frozen_instrument_count": self.frozen_instrument_count,
            "validation_state": self.validation_state,
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["audit_checksum"] = self.audit_checksum
        return payload


__all__ = [
    "InstrumentNormalizationError",
    "InstrumentRegistryV1",
    "InstrumentSpecificationV1",
    "InstrumentSymbolContractNormalizationAuditV1",
    "InstrumentSymbolContractNormalizationStateV1",
    "Lot32LineageEnvelopeV1",
    "Lot32MetricsV1",
    "Lot32RunContextV1",
    "MARKET_TYPES",
    "VenueInstrumentAliasV1",
    "decimal_places",
    "decimal_value",
    "fail_closed_safety",
]
