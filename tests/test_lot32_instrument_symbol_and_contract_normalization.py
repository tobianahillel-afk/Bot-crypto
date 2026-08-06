from __future__ import annotations

import copy
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization import (
    build_lot32_artifacts,
    normalize_candidate_amounts,
    persist_lot32_artifacts,
    quantize_to_increment,
)
from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization_models import (
    InstrumentNormalizationError,
    InstrumentRegistryV1,
    InstrumentSpecificationV1,
    InstrumentSymbolContractNormalizationStateV1,
    Lot32LineageEnvelopeV1,
    Lot32MetricsV1,
    Lot32RunContextV1,
    VenueInstrumentAliasV1,
    decimal_value,
    fail_closed_safety,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_SHA = "a" * 40
INPUT_PATHS = (
    "config/data_governance/instrument_symbol_contract_normalization_v1.json",
    "data/audit/lot32_v3_entry_gate.json",
    "data/audit/source_registry_lot31.json",
    "data/audit/market_data_governance_scope_and_source_registry_lot31.json",
    "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json",
)


def make_alias(**overrides: object) -> VenueInstrumentAliasV1:
    values: dict[str, object] = {
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
    values.update(overrides)
    return VenueInstrumentAliasV1(**values)  # type: ignore[arg-type]


def make_instrument(**overrides: object) -> InstrumentSpecificationV1:
    values: dict[str, object] = {
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
        "aliases": (make_alias(),),
        "validation_state": "VALIDATED_NORMALIZATION_ONLY",
    }
    values.update(overrides)
    return InstrumentSpecificationV1(**values)  # type: ignore[arg-type]


def copy_inputs(destination: Path) -> None:
    for relative in INPUT_PATHS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def mutate_json(root: Path, relative: str, mutate: object) -> None:
    path = root / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert callable(mutate)
    mutate(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_lot32_build_is_deterministic_and_fail_closed() -> None:
    first_state, first_audit = build_lot32_artifacts(ROOT, VALID_SHA)
    second_state, second_audit = build_lot32_artifacts(ROOT, VALID_SHA)
    assert first_state.to_dict() == second_state.to_dict()
    assert first_audit.to_dict() == second_audit.to_dict()
    assert first_state.validation_state == "VALIDATED_NORMALIZATION_ONLY"
    assert first_state.safety == fail_closed_safety()
    assert first_audit.safety == fail_closed_safety()
    assert first_audit.instrument_count == 1
    assert first_audit.venue_alias_count == 3
    assert first_audit.round_trip_count == 6
    assert first_audit.frozen_instrument_count == 0


def test_lot32_registry_round_trip_is_exact_for_all_venues() -> None:
    state, _ = build_lot32_artifacts(ROOT, VALID_SHA)
    registry = state.instrument_registry
    expected = {
        "BITSTAMP": "btceur",
        "COINBASE": "BTC-EUR",
        "KRAKEN": "XBTEUR",
    }
    for venue, exchange_symbol in expected.items():
        assert registry.exchange_symbol_for("BTC/EUR:SPOT", venue) == exchange_symbol
        assert registry.canonical_symbol_for(venue, exchange_symbol) == "BTC/EUR:SPOT"
    with pytest.raises(InstrumentNormalizationError, match="unknown"):
        registry.exchange_symbol_for("BTC/EUR:SPOT", "UNKNOWN")
    with pytest.raises(InstrumentNormalizationError, match="unknown"):
        registry.canonical_symbol_for("KRAKEN", "UNKNOWN")


def test_lot32_persistence_writes_three_linked_artifacts(tmp_path: Path) -> None:
    state, audit = build_lot32_artifacts(ROOT, VALID_SHA)
    persist_lot32_artifacts(tmp_path, state, audit)
    state_path = tmp_path / "data/audit/instrument_symbol_and_contract_normalization_lot32.json"
    audit_path = (
        tmp_path / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json"
    )
    registry_path = tmp_path / "data/audit/instrument_registry_lot32.json"
    persisted_state = json.loads(state_path.read_text(encoding="utf-8"))
    persisted_audit = json.loads(audit_path.read_text(encoding="utf-8"))
    persisted_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert persisted_state == state.to_dict()
    assert persisted_audit == audit.to_dict()
    assert persisted_registry == state.instrument_registry.to_dict()
    assert persisted_state["instrument_registry"] == persisted_registry
    assert persisted_audit["state_output_checksum"] == persisted_state["output_checksum"]


def test_decimal_contract_rejects_float_zero_and_noncanonical_forms() -> None:
    assert str(decimal_value("0.00000001", "value")) == "1E-8"
    for invalid in (0.1, 1, "0", "0.10", "01", "-1", "NaN", "Infinity", " 1"):
        with pytest.raises(InstrumentNormalizationError, match="decimal|positive|canonical"):
            decimal_value(invalid, "value")  # type: ignore[arg-type]


def test_quantization_uses_floor_and_preserves_exact_decimal_output() -> None:
    assert quantize_to_increment("50000.19", "0.1") == "50000.1"
    assert quantize_to_increment("0.000200009", "0.00000001") == "0.0002"
    alias = make_alias()
    assert normalize_candidate_amounts("50000.19", "0.0002", alias) == {
        "price": "50000.1",
        "quantity": "0.0002",
        "notional": "10.00002",
    }


def test_quantization_rejects_minimum_quantity_and_notional_breaches() -> None:
    alias = make_alias()
    with pytest.raises(InstrumentNormalizationError, match="min_qty"):
        normalize_candidate_amounts("50000", "0.000099", alias)
    with pytest.raises(InstrumentNormalizationError, match="min_notional"):
        normalize_candidate_amounts("1000", "0.0001", alias)
    with pytest.raises(InstrumentNormalizationError, match="non-positive"):
        normalize_candidate_amounts("0.05", "0.0001", alias)


def test_spot_applicability_requires_explicit_nulls_and_forbids_leverage() -> None:
    assert make_instrument().to_dict()["contract_size"] is None
    with pytest.raises(InstrumentNormalizationError, match="derivative fields"):
        make_instrument(contract_size="1")
    with pytest.raises(InstrumentNormalizationError, match="settlement"):
        make_instrument(settlement_asset="USD")
    with pytest.raises(InstrumentNormalizationError, match="margin or leverage"):
        make_instrument(aliases=(make_alias(margin_mode="CROSS"),))
    with pytest.raises(InstrumentNormalizationError, match="margin or leverage"):
        make_instrument(aliases=(make_alias(leverage_policy="ALLOWED"),))


def derivative_alias() -> VenueInstrumentAliasV1:
    return make_alias(margin_mode="CROSS", leverage_policy="DISABLED_METADATA_ONLY")


def test_perpetual_future_and_option_applicability_rules() -> None:
    perpetual = make_instrument(
        instrument_id="btc-usd-perpetual",
        canonical_symbol="BTC/USD:PERPETUAL",
        quote_asset="USD",
        market_type="PERPETUAL",
        settlement_asset="USD",
        contract_size="1",
        aliases=(derivative_alias(),),
    )
    assert perpetual.market_type == "PERPETUAL"
    future = make_instrument(
        instrument_id="btc-usd-dated-future",
        canonical_symbol="BTC/USD:DATED_FUTURE",
        quote_asset="USD",
        market_type="DATED_FUTURE",
        settlement_asset="USD",
        contract_size="1",
        expiry_time="2027-01-01T00:00:00Z",
        aliases=(derivative_alias(),),
    )
    assert future.expiry_time == "2027-01-01T00:00:00Z"
    option = make_instrument(
        instrument_id="btc-usd-option",
        canonical_symbol="BTC/USD:OPTION",
        quote_asset="USD",
        market_type="OPTION",
        settlement_asset="USD",
        contract_size="1",
        expiry_time="2027-01-01T00:00:00Z",
        strike_price="50000",
        option_type="CALL",
        aliases=(derivative_alias(),),
    )
    assert option.option_type == "CALL"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"market_type": "PERPETUAL", "canonical_symbol": "BTC/EUR:PERPETUAL"}, "perpetual"),
        (
            {
                "market_type": "DATED_FUTURE",
                "canonical_symbol": "BTC/EUR:DATED_FUTURE",
                "contract_size": "1",
            },
            "dated future",
        ),
        (
            {
                "market_type": "OPTION",
                "canonical_symbol": "BTC/EUR:OPTION",
                "contract_size": "1",
                "expiry_time": "2027-01-01T00:00:00Z",
                "strike_price": "50000",
            },
            "option requires",
        ),
    ],
)
def test_derivative_contracts_fail_closed_when_fields_are_incomplete(
    overrides: dict[str, object], message: str
) -> None:
    overrides["aliases"] = (derivative_alias(),)
    with pytest.raises(InstrumentNormalizationError, match=message):
        make_instrument(**overrides)


def test_registry_rejects_duplicate_canonical_and_venue_aliases() -> None:
    first = make_instrument()
    duplicate_symbol = replace(first, instrument_id="btc-eur-spot-copy")
    with pytest.raises(InstrumentNormalizationError, match="canonical symbols"):
        InstrumentRegistryV1("registry", "1.0.0", "IMMUTABLE_VERSIONED_REPLACEMENT", (first, duplicate_symbol))
    second = make_instrument(
        instrument_id="eth-eur-spot",
        canonical_symbol="ETH/EUR:SPOT",
        base_asset="ETH",
    )
    with pytest.raises(InstrumentNormalizationError, match="venue symbol aliases"):
        InstrumentRegistryV1("registry", "1.0.0", "IMMUTABLE_VERSIONED_REPLACEMENT", (first, second))


def test_build_rejects_unknown_source_and_revision(tmp_path: Path) -> None:
    copy_inputs(tmp_path)

    def unknown_source(payload: dict[str, object]) -> None:
        instruments = payload["instruments"]
        assert isinstance(instruments, list)
        instruments[0]["aliases"][0]["source_id"] = "unknown-source"

    mutate_json(
        tmp_path,
        "config/data_governance/instrument_symbol_contract_normalization_v1.json",
        unknown_source,
    )
    with pytest.raises(InstrumentNormalizationError, match="unknown source"):
        build_lot32_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)

    def wrong_revision(payload: dict[str, object]) -> None:
        instruments = payload["instruments"]
        assert isinstance(instruments, list)
        instruments[0]["aliases"][0]["source_revision"] = 2

    mutate_json(
        tmp_path,
        "config/data_governance/instrument_symbol_contract_normalization_v1.json",
        wrong_revision,
    )
    with pytest.raises(InstrumentNormalizationError, match="revision changed"):
        build_lot32_artifacts(tmp_path, VALID_SHA)


def test_build_rejects_enabled_source_or_modified_gate(tmp_path: Path) -> None:
    copy_inputs(tmp_path)

    def enable_source(payload: dict[str, object]) -> None:
        sources = payload["sources"]
        assert isinstance(sources, list)
        sources[0]["enabled"] = True
        sources[0]["connection_status"] = "CONNECTED"

    mutate_json(tmp_path, "data/audit/source_registry_lot31.json", enable_source)
    with pytest.raises(InstrumentNormalizationError, match="connection-disabled"):
        build_lot32_artifacts(tmp_path, VALID_SHA)

    copy_inputs(tmp_path)

    def modify_gate(payload: dict[str, object]) -> None:
        payload["human_decision"] = "UNKNOWN"

    mutate_json(tmp_path, "data/audit/lot32_v3_entry_gate.json", modify_gate)
    with pytest.raises(InstrumentNormalizationError, match="does not authorize"):
        build_lot32_artifacts(tmp_path, VALID_SHA)


def test_state_rejects_future_availability_and_permission_changes() -> None:
    state, _ = build_lot32_artifacts(ROOT, VALID_SHA)
    with pytest.raises(InstrumentNormalizationError, match="causal availability"):
        InstrumentSymbolContractNormalizationStateV1(
            state.run_context,
            state.lineage,
            "2026-08-06T19:16:00Z",
            "2026-08-06T19:15:00Z",
            "2026-08-06T19:15:00Z",
            state.validation_state,
            state.instrument_registry,
            state.metrics,
            state.reason_codes,
            state.safety,
            state.output_checksum,
        )
    unsafe = dict(state.safety)
    unsafe["trade_allowed"] = True
    with pytest.raises(ValueError, match="fail-closed"):
        replace(state, safety=unsafe)


def test_lineage_and_metrics_are_strict() -> None:
    with pytest.raises(InstrumentNormalizationError, match="SourceRegistryV1"):
        Lot32LineageEnvelopeV1(
            "lineage",
            "wrong.json",
            "a" * 64,
            "b" * 64,
            "c" * 64,
            "2026-08-06T19:15:00Z",
        )
    with pytest.raises(InstrumentNormalizationError, match="negative"):
        Lot32MetricsV1(1, 3, 0, -1, 0)
    with pytest.raises(InstrumentNormalizationError, match="runtime"):
        Lot32RunContextV1("run", "LIVE", "v1", VALID_SHA, "correlation")


def test_lot32_schemas_are_strict_and_reference_the_registry() -> None:
    paths = (
        "instrument_specification_v1.schema.json",
        "instrument_registry_v1.schema.json",
        "instrument_symbol_contract_normalization_state_v1.schema.json",
        "instrument_symbol_contract_normalization_audit_v1.schema.json",
    )
    schemas = {
        path: json.loads((ROOT / "contracts/schemas" / path).read_text(encoding="utf-8"))
        for path in paths
    }
    assert all(schema["additionalProperties"] is False for schema in schemas.values())
    state = schemas["instrument_symbol_contract_normalization_state_v1.schema.json"]
    assert state["properties"]["instrument_registry"]["$ref"] == (
        "instrument_registry_v1.schema.json"
    )
    audit = schemas["instrument_symbol_contract_normalization_audit_v1.schema.json"]
    assert audit["properties"]["trade_allowed"]["const"] is False
    assert audit["properties"]["approved_size"]["const"] == 0
