from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path
from typing import Any

from .instrument_symbol_and_contract_normalization_models import (
    InstrumentNormalizationError,
    InstrumentRegistryV1,
    InstrumentSpecificationV1,
    InstrumentSymbolContractNormalizationAuditV1,
    InstrumentSymbolContractNormalizationStateV1,
    Lot32LineageEnvelopeV1,
    Lot32MetricsV1,
    Lot32RunContextV1,
    VenueInstrumentAliasV1,
    decimal_value,
    fail_closed_safety,
)
from .market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)
from .source_registry_validation import (
    require_integer,
    require_object_list,
    require_string,
)

EXPECTED_GATE_CHECKSUM = "ca4f531f5a36173b0159aaab308025da7beaf66b21d1f85304c5d46c7f487a55"
CONFIG_FIELDS = frozenset(
    {
        "schema_version",
        "config_version",
        "run_id",
        "correlation_id",
        "lineage_id",
        "registry_id",
        "registry_version",
        "revision_policy",
        "event_time",
        "available_at",
        "generated_at",
        "instruments",
    }
)
INSTRUMENT_FIELDS = frozenset(
    {
        "instrument_id",
        "canonical_symbol",
        "base_asset",
        "quote_asset",
        "market_type",
        "settlement_asset",
        "contract_size",
        "expiry_time",
        "strike_price",
        "option_type",
        "aliases",
    }
)
ALIAS_FIELDS = frozenset(
    {
        "venue",
        "exchange_symbol",
        "source_id",
        "source_revision",
        "tick_size",
        "lot_size",
        "min_qty",
        "min_notional",
        "price_precision",
        "quantity_precision",
        "fee_tier",
        "margin_mode",
        "leverage_policy",
    }
)
REASON_CODES = (
    "LOT32_ENTRY_GATE_VERIFIED",
    "LOT31_SOURCE_REGISTRY_LINEAGE_VERIFIED",
    "INSTRUMENT_METADATA_NORMALIZED",
    "CANONICAL_VENUE_ROUND_TRIP_VERIFIED",
    "DECIMAL_CONSTRAINTS_VALIDATED",
    "EXTERNAL_CONNECTIVITY_DISABLED",
    "LOT33_REMAINS_LOCKED",
)


def _require_exact_fields(
    raw: dict[str, Any],
    expected: frozenset[str],
    label: str,
) -> None:
    actual = set(raw)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise InstrumentNormalizationError(
            f"{label} fields differ: missing={missing}, extra={extra}"
        )


def _explicit_nullable_string(raw: dict[str, Any], field: str) -> str | None:
    if field not in raw:
        raise InstrumentNormalizationError(f"{field} must be explicitly present")
    value = raw[field]
    if value is None:
        return None
    if not isinstance(value, str):
        raise InstrumentNormalizationError(f"{field} must be a string or null")
    if not value or value != value.strip():
        raise InstrumentNormalizationError(f"{field} must be explicit and trimmed")
    return value


def _verify_entry_gate(gate: dict[str, Any]) -> None:
    checksum_payload = dict(gate)
    output_checksum = checksum_payload.pop("output_checksum", None)
    if (
        not isinstance(output_checksum, str)
        or canonical_checksum(checksum_payload) != output_checksum
        or output_checksum != EXPECTED_GATE_CHECKSUM
    ):
        raise InstrumentNormalizationError("Lot 32 entry gate checksum changed")
    expected = {
        "gate_status": "GO_LOT32_IMPLEMENTATION_ENTRY",
        "target_lot": 32,
        "target_version": "V3_MARKET_DATA_GOVERNANCE",
        "owner": "MarketDataGovernanceDomain",
        "package_boundary": "src/crypto_quant_bot/data_governance",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "human_decision": "APPROVED_START_LOT32",
        "implementation_started": False,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise InstrumentNormalizationError("Lot 32 entry gate does not authorize implementation")
    if gate.get("safety") != fail_closed_safety():
        raise InstrumentNormalizationError("Lot 32 entry gate safety boundary changed")


def _source_entries(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if registry.get("schema_version") != "source-registry-v1":
        raise InstrumentNormalizationError("Lot 32 requires SourceRegistryV1")
    raw_sources = require_object_list(registry.get("sources"), "sources")
    entries: dict[str, dict[str, Any]] = {}
    for source in raw_sources:
        source_id = require_string(source.get("source_id"), "source_id")
        if source_id in entries:
            raise InstrumentNormalizationError("source registry ids must be unique")
        if source.get("approved") is not True:
            raise InstrumentNormalizationError("instrument source must be approved")
        if source.get("auth_mode") != "NONE":
            raise InstrumentNormalizationError("instrument source authentication is forbidden")
        if source.get("enabled") is not False or source.get("connection_status") != "DISABLED":
            raise InstrumentNormalizationError("instrument source must remain connection-disabled")
        entries[source_id] = source
    return entries


def _build_alias(
    raw: dict[str, Any],
    sources: dict[str, dict[str, Any]],
) -> VenueInstrumentAliasV1:
    _require_exact_fields(raw, ALIAS_FIELDS, "venue alias")
    source_id = require_string(raw.get("source_id"), "source_id")
    source = sources.get(source_id)
    if source is None:
        raise InstrumentNormalizationError("instrument alias references an unknown source")
    venue = require_string(raw.get("venue"), "venue")
    if source.get("venue") != venue:
        raise InstrumentNormalizationError("instrument alias venue differs from source venue")
    source_revision = require_integer(raw.get("source_revision"), "source_revision")
    if source.get("revision") != source_revision:
        raise InstrumentNormalizationError("instrument alias source revision changed")
    return VenueInstrumentAliasV1(
        venue=venue,
        exchange_symbol=require_string(raw.get("exchange_symbol"), "exchange_symbol"),
        source_id=source_id,
        source_revision=source_revision,
        tick_size=require_string(raw.get("tick_size"), "tick_size"),
        lot_size=require_string(raw.get("lot_size"), "lot_size"),
        min_qty=require_string(raw.get("min_qty"), "min_qty"),
        min_notional=require_string(raw.get("min_notional"), "min_notional"),
        price_precision=require_integer(raw.get("price_precision"), "price_precision"),
        quantity_precision=require_integer(raw.get("quantity_precision"), "quantity_precision"),
        fee_tier=require_string(raw.get("fee_tier"), "fee_tier"),
        margin_mode=_explicit_nullable_string(raw, "margin_mode"),
        leverage_policy=require_string(raw.get("leverage_policy"), "leverage_policy"),
        validation_state="VALIDATED_METADATA_ONLY",
    )


def _build_instrument(
    raw: dict[str, Any],
    sources: dict[str, dict[str, Any]],
) -> InstrumentSpecificationV1:
    _require_exact_fields(raw, INSTRUMENT_FIELDS, "instrument")
    aliases = tuple(
        sorted(
            (
                _build_alias(alias, sources)
                for alias in require_object_list(raw.get("aliases"), "aliases")
            ),
            key=lambda item: item.venue,
        )
    )
    return InstrumentSpecificationV1(
        instrument_id=require_string(raw.get("instrument_id"), "instrument_id"),
        canonical_symbol=require_string(raw.get("canonical_symbol"), "canonical_symbol"),
        base_asset=require_string(raw.get("base_asset"), "base_asset"),
        quote_asset=require_string(raw.get("quote_asset"), "quote_asset"),
        market_type=require_string(raw.get("market_type"), "market_type"),
        settlement_asset=require_string(raw.get("settlement_asset"), "settlement_asset"),
        contract_size=_explicit_nullable_string(raw, "contract_size"),
        expiry_time=_explicit_nullable_string(raw, "expiry_time"),
        strike_price=_explicit_nullable_string(raw, "strike_price"),
        option_type=_explicit_nullable_string(raw, "option_type"),
        aliases=aliases,
        validation_state="VALIDATED_NORMALIZATION_ONLY",
    )


def _build_registry(
    config: dict[str, Any],
    source_registry: dict[str, Any],
) -> InstrumentRegistryV1:
    sources = _source_entries(source_registry)
    instruments = tuple(
        sorted(
            (
                _build_instrument(raw, sources)
                for raw in require_object_list(config.get("instruments"), "instruments")
            ),
            key=lambda item: item.instrument_id,
        )
    )
    return InstrumentRegistryV1(
        registry_id=require_string(config.get("registry_id"), "registry_id"),
        registry_version=require_string(config.get("registry_version"), "registry_version"),
        revision_policy=require_string(config.get("revision_policy"), "revision_policy"),
        instruments=instruments,
    )


def _verify_round_trips(registry: InstrumentRegistryV1) -> int:
    checks = 0
    for instrument in registry.instruments:
        for alias in instrument.aliases:
            exchange = registry.exchange_symbol_for(instrument.canonical_symbol, alias.venue)
            if exchange != alias.exchange_symbol:
                raise InstrumentNormalizationError("canonical to venue round-trip failed")
            canonical = registry.canonical_symbol_for(alias.venue, alias.exchange_symbol)
            if canonical != instrument.canonical_symbol:
                raise InstrumentNormalizationError("venue to canonical round-trip failed")
            checks += 2
    return checks


def _decimal_output(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def quantize_to_increment(value: str, increment: str) -> str:
    parsed_value = decimal_value(value, "value")
    parsed_increment = decimal_value(increment, "increment")
    units = (parsed_value / parsed_increment).to_integral_value(rounding=ROUND_FLOOR)
    return _decimal_output(units * parsed_increment)


def normalize_candidate_amounts(
    price: str,
    quantity: str,
    alias: VenueInstrumentAliasV1,
) -> dict[str, str]:
    normalized_price = quantize_to_increment(price, alias.tick_size)
    normalized_quantity = quantize_to_increment(quantity, alias.lot_size)
    price_value = Decimal(normalized_price)
    quantity_value = Decimal(normalized_quantity)
    if price_value <= 0 or quantity_value <= 0:
        raise InstrumentNormalizationError("quantization produced a non-positive value")
    if quantity_value < decimal_value(alias.min_qty, "min_qty"):
        raise InstrumentNormalizationError("quantized quantity violates min_qty")
    notional = price_value * quantity_value
    if notional < decimal_value(alias.min_notional, "min_notional"):
        raise InstrumentNormalizationError("quantized amount violates min_notional")
    return {
        "price": normalized_price,
        "quantity": normalized_quantity,
        "notional": _decimal_output(notional),
    }


def _build_run_context(config: dict[str, Any], code_commit: str) -> Lot32RunContextV1:
    return Lot32RunContextV1(
        run_id=require_string(config.get("run_id"), "run_id"),
        runtime_mode="DATA_GOVERNANCE_ONLY",
        config_version=require_string(config.get("config_version"), "config_version"),
        code_commit=code_commit,
        correlation_id=require_string(config.get("correlation_id"), "correlation_id"),
    )


def _build_lineage(config: dict[str, Any], root: Path) -> Lot32LineageEnvelopeV1:
    return Lot32LineageEnvelopeV1(
        lineage_id=require_string(config.get("lineage_id"), "lineage_id"),
        source_registry_path="data/audit/source_registry_lot31.json",
        source_registry_checksum=file_checksum(root / "data/audit/source_registry_lot31.json"),
        lot31_state_checksum=file_checksum(
            root / "data/audit/market_data_governance_scope_and_source_registry_lot31.json"
        ),
        lot31_audit_checksum=file_checksum(
            root
            / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
        ),
        available_at=require_string(config.get("available_at"), "available_at"),
    )


def _build_state(
    config: dict[str, Any],
    registry: InstrumentRegistryV1,
    root: Path,
    code_commit: str,
) -> InstrumentSymbolContractNormalizationStateV1:
    alias_count = sum(len(item.aliases) for item in registry.instruments)
    state = InstrumentSymbolContractNormalizationStateV1(
        run_context=_build_run_context(config, code_commit),
        lineage=_build_lineage(config, root),
        event_time=require_string(config.get("event_time"), "event_time"),
        available_at=require_string(config.get("available_at"), "available_at"),
        generated_at=require_string(config.get("generated_at"), "generated_at"),
        validation_state="VALIDATED_NORMALIZATION_ONLY",
        instrument_registry=registry,
        metrics=Lot32MetricsV1(len(registry.instruments), alias_count, 0, 0, 0),
        reason_codes=REASON_CODES,
        safety=fail_closed_safety(),
        output_checksum="0" * 64,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    state: InstrumentSymbolContractNormalizationStateV1,
    config_checksum: str,
) -> InstrumentSymbolContractNormalizationAuditV1:
    alias_count = sum(len(item.aliases) for item in state.instrument_registry.instruments)
    audit = InstrumentSymbolContractNormalizationAuditV1(
        code_commit=state.run_context.code_commit,
        state_output_checksum=state.output_checksum,
        config_checksum=config_checksum,
        source_registry_checksum=state.lineage.source_registry_checksum,
        instrument_count=len(state.instrument_registry.instruments),
        venue_alias_count=alias_count,
        round_trip_count=_verify_round_trips(state.instrument_registry),
        frozen_instrument_count=state.metrics.frozen_instruments_total,
        validation_state=state.validation_state,
        safety=fail_closed_safety(),
        audit_checksum="0" * 64,
    )
    return replace(audit, audit_checksum=canonical_checksum(audit.payload_without_checksum()))


def build_lot32_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[
    InstrumentSymbolContractNormalizationStateV1,
    InstrumentSymbolContractNormalizationAuditV1,
]:
    config_path = root / "config/data_governance/instrument_symbol_contract_normalization_v1.json"
    gate_path = root / "data/audit/lot32_v3_entry_gate.json"
    source_registry_path = root / "data/audit/source_registry_lot31.json"
    config = load_json_object(config_path)
    gate = load_json_object(gate_path)
    source_registry = load_json_object(source_registry_path)
    _require_exact_fields(config, CONFIG_FIELDS, "Lot 32 config")
    if config.get("schema_version") != "instrument-symbol-contract-normalization-config-v1":
        raise InstrumentNormalizationError("unexpected Lot 32 config schema_version")
    _verify_entry_gate(gate)
    registry = _build_registry(config, source_registry)
    _verify_round_trips(registry)
    state = _build_state(config, registry, root, code_commit)
    audit = _build_audit(state, file_checksum(config_path))
    return state, audit


def persist_lot32_artifacts(
    root: Path,
    state: InstrumentSymbolContractNormalizationStateV1,
    audit: InstrumentSymbolContractNormalizationAuditV1,
) -> None:
    atomic_write_json(
        root / "data/audit/instrument_symbol_and_contract_normalization_lot32.json",
        state.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json",
        audit.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/instrument_registry_lot32.json",
        state.instrument_registry.to_dict(),
    )


__all__ = [
    "build_lot32_artifacts",
    "normalize_candidate_amounts",
    "persist_lot32_artifacts",
    "quantize_to_increment",
]
