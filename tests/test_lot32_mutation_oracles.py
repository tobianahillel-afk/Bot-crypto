from __future__ import annotations

from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization import (
    build_lot32_artifacts,
    normalize_candidate_amounts,
    quantize_to_increment,
)
from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization_models import (
    InstrumentNormalizationError,
    InstrumentRegistryV1,
    InstrumentSpecificationV1,
    VenueInstrumentAliasV1,
    decimal_value,
    fail_closed_safety,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_SHA = "c" * 40
EXPECTED_SAFETY = {
    "analysis_only": True,
    "used_for_decision": False,
    "external_connectivity_allowed": False,
    "network_ingestion_allowed": False,
    "real_credentials_allowed": False,
    "signal_generation_allowed": False,
    "risk_approval_allowed": False,
    "order_routing_allowed": False,
    "trade_allowed": False,
    "execution_allowed": False,
    "approved_size": 0,
}


def alias() -> VenueInstrumentAliasV1:
    return VenueInstrumentAliasV1(
        venue="KRAKEN",
        exchange_symbol="XBTEUR",
        source_id="kraken-public-spot-metadata",
        source_revision=1,
        tick_size="0.1",
        lot_size="0.00000001",
        min_qty="0.0001",
        min_notional="5",
        price_precision=1,
        quantity_precision=8,
        fee_tier="REFERENCE_METADATA_ONLY",
        margin_mode=None,
        leverage_policy="FORBIDDEN",
        validation_state="VALIDATED_METADATA_ONLY",
    )


def instrument() -> InstrumentSpecificationV1:
    return InstrumentSpecificationV1(
        instrument_id="btc-eur-spot",
        canonical_symbol="BTC/EUR:SPOT",
        base_asset="BTC",
        quote_asset="EUR",
        market_type="SPOT",
        settlement_asset="EUR",
        contract_size=None,
        expiry_time=None,
        strike_price=None,
        option_type=None,
        aliases=(alias(),),
        validation_state="VALIDATED_NORMALIZATION_ONLY",
    )


def test_fail_closed_safety_matches_independent_literal() -> None:
    assert fail_closed_safety() == EXPECTED_SAFETY


def test_canonical_checksum_has_fixed_unicode_oracle() -> None:
    assert canonical_checksum({"a": 1, "b": "é"}) == (
        "09ad9fd2fb648cb2f62141215828ea00a62c299db05d20aa9ade2f527a301cc6"
    )


def test_alias_serialization_matches_exact_contract() -> None:
    assert alias().to_dict() == {
        "schema_version": "venue-instrument-alias-v1",
        "venue": "KRAKEN",
        "exchange_symbol": "XBTEUR",
        "source_id": "kraken-public-spot-metadata",
        "source_revision": 1,
        "tick_size": "0.1",
        "lot_size": "0.00000001",
        "min_qty": "0.0001",
        "min_notional": "5",
        "price_precision": 1,
        "quantity_precision": 8,
        "fee_tier": "REFERENCE_METADATA_ONLY",
        "margin_mode": None,
        "leverage_policy": "FORBIDDEN",
        "validation_state": "VALIDATED_METADATA_ONLY",
    }


def test_instrument_and_registry_serialization_match_exact_contract() -> None:
    expected_instrument = {
        "schema_version": "instrument-specification-v1",
        "instrument_id": "btc-eur-spot",
        "canonical_symbol": "BTC/EUR:SPOT",
        "base_asset": "BTC",
        "quote_asset": "EUR",
        "market_type": "SPOT",
        "settlement_asset": "EUR",
        "contract_size": None,
        "expiry_time": None,
        "strike_price": None,
        "option_type": None,
        "aliases": [alias().to_dict()],
        "validation_state": "VALIDATED_NORMALIZATION_ONLY",
    }
    assert instrument().to_dict() == expected_instrument
    registry = InstrumentRegistryV1(
        registry_id="canonical-instrument-registry",
        registry_version="1.0.0",
        revision_policy="IMMUTABLE_VERSIONED_REPLACEMENT",
        instruments=(instrument(),),
    )
    assert registry.to_dict() == {
        "schema_version": "instrument-registry-v1",
        "registry_id": "canonical-instrument-registry",
        "registry_version": "1.0.0",
        "revision_policy": "IMMUTABLE_VERSIONED_REPLACEMENT",
        "instruments": [expected_instrument],
    }
    assert registry.exchange_symbol_for("BTC/EUR:SPOT", "KRAKEN") == "XBTEUR"
    assert registry.canonical_symbol_for("KRAKEN", "XBTEUR") == "BTC/EUR:SPOT"


def test_decimal_and_quantization_have_literal_outputs() -> None:
    assert decimal_value("1", "value").as_tuple().exponent == 0
    assert decimal_value("0.00000001", "value").as_tuple().exponent == -8
    assert quantize_to_increment("123.456", "0.1") == "123.4"
    assert quantize_to_increment("1.999999999", "0.00000001") == "1.99999999"
    assert normalize_candidate_amounts("50000.19", "0.0002", alias()) == {
        "price": "50000.1",
        "quantity": "0.0002",
        "notional": "10.00002",
    }


@pytest.mark.parametrize("value", ["", "0", "00.1", "1.0", "1e-8", "-0.1"])
def test_decimal_invalid_forms_have_no_implicit_fallback(value: str) -> None:
    with pytest.raises(InstrumentNormalizationError):
        decimal_value(value, "value")


def test_built_state_and_audit_have_exact_public_shape() -> None:
    state, audit = build_lot32_artifacts(ROOT, VALID_SHA)
    state_dict = state.to_dict()
    audit_dict = audit.to_dict()
    assert tuple(state_dict) == (
        "schema_version",
        "run_context",
        "lineage",
        "event_time",
        "available_at",
        "generated_at",
        "validation_state",
        "instrument_registry",
        "metrics",
        "reason_codes",
        "analysis_only",
        "used_for_decision",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "real_credentials_allowed",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
        "approved_size",
        "output_checksum",
    )
    assert state_dict["reason_codes"] == [
        "LOT32_ENTRY_GATE_VERIFIED",
        "LOT31_SOURCE_REGISTRY_LINEAGE_VERIFIED",
        "INSTRUMENT_METADATA_NORMALIZED",
        "CANONICAL_VENUE_ROUND_TRIP_VERIFIED",
        "DECIMAL_CONSTRAINTS_VALIDATED",
        "EXTERNAL_CONNECTIVITY_DISABLED",
        "LOT33_REMAINS_LOCKED",
    ]
    assert state_dict["metrics"] == {
        "schema_version": "lot32-metrics-v1",
        "lot_32_records_processed_total": 1,
        "lot_32_venue_aliases_total": 3,
        "lot_32_frozen_instruments_total": 0,
        "lot_32_validation_failures_total": 0,
        "lot_32_processing_latency_ms": 0,
    }
    assert audit_dict["instrument_count"] == 1
    assert audit_dict["venue_alias_count"] == 3
    assert audit_dict["round_trip_count"] == 6
    assert audit_dict["frozen_instrument_count"] == 0
    assert audit_dict["state_output_checksum"] == state_dict["output_checksum"]
    assert len(state_dict["output_checksum"]) == 64
    assert len(audit_dict["audit_checksum"]) == 64
    for field, expected in EXPECTED_SAFETY.items():
        assert state_dict[field] == expected
        assert audit_dict[field] == expected
