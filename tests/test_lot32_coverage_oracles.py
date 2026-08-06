from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization as engine
from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization import (
    build_lot32_artifacts,
)
from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization_models import (
    InstrumentNormalizationError,
    InstrumentRegistryV1,
    InstrumentSpecificationV1,
    InstrumentSymbolContractNormalizationAuditV1,
    VenueInstrumentAliasV1,
    fail_closed_safety,
    require_git_sha,
    require_sha256,
    require_utc,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_SHA = "d" * 40


def make_alias(**changes: object) -> VenueInstrumentAliasV1:
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
    values.update(changes)
    return VenueInstrumentAliasV1(**values)  # type: ignore[arg-type]


def make_instrument(**changes: object) -> InstrumentSpecificationV1:
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
    values.update(changes)
    return InstrumentSpecificationV1(**values)  # type: ignore[arg-type]


def rewritten_gate(**changes: object) -> dict[str, object]:
    gate = json.loads((ROOT / "data/audit/lot32_v3_entry_gate.json").read_text())
    gate.update(changes)
    body = dict(gate)
    body.pop("output_checksum", None)
    gate["output_checksum"] = canonical_checksum(body)
    return gate


def test_low_level_timestamp_hash_and_commit_guards() -> None:
    with pytest.raises(InstrumentNormalizationError, match="UTC"):
        require_utc("2026-08-06", "event_time")
    with pytest.raises(InstrumentNormalizationError, match="sha256"):
        require_sha256("x" * 64, "checksum")
    with pytest.raises(InstrumentNormalizationError, match="40-character"):
        require_git_sha("a" * 39)


def test_alias_optional_text_and_validation_state_guards() -> None:
    with pytest.raises(InstrumentNormalizationError, match="trimmed"):
        make_alias(margin_mode=" ")
    with pytest.raises(InstrumentNormalizationError, match="metadata-only"):
        make_alias(validation_state="UNKNOWN")
    with pytest.raises(InstrumentNormalizationError, match="quantity_precision"):
        make_alias(quantity_precision=7)


def test_instrument_validation_state_option_and_empty_alias_guards() -> None:
    with pytest.raises(InstrumentNormalizationError, match="validation_state"):
        make_instrument(validation_state="UNKNOWN")
    with pytest.raises(InstrumentNormalizationError, match="CALL or PUT"):
        make_instrument(
            instrument_id="btc-usd-option",
            canonical_symbol="BTC/USD:OPTION",
            quote_asset="USD",
            settlement_asset="USD",
            market_type="OPTION",
            contract_size="1",
            expiry_time="2027-01-01T00:00:00Z",
            strike_price="50000",
            option_type="OTHER",
        )
    with pytest.raises(InstrumentNormalizationError, match="at least one"):
        make_instrument(aliases=())
    with pytest.raises(InstrumentNormalizationError, match="future option fields"):
        make_instrument(
            instrument_id="btc-usd-dated-future",
            canonical_symbol="BTC/USD:DATED_FUTURE",
            quote_asset="USD",
            settlement_asset="USD",
            market_type="DATED_FUTURE",
            contract_size="1",
            expiry_time="2027-01-01T00:00:00Z",
            strike_price="50000",
        )


def test_registry_revision_empty_order_and_unknown_lookup_guards() -> None:
    instrument = make_instrument()
    with pytest.raises(InstrumentNormalizationError, match="revision policy"):
        InstrumentRegistryV1("registry", "1", "MUTABLE", (instrument,))
    with pytest.raises(InstrumentNormalizationError, match="non-empty"):
        InstrumentRegistryV1("registry", "1", "IMMUTABLE_VERSIONED_REPLACEMENT", ())
    earlier = replace(
        instrument,
        instrument_id="aaa-eur-spot",
        canonical_symbol="AAA/EUR:SPOT",
        base_asset="AAA",
        aliases=(make_alias(exchange_symbol="AAAEUR"),),
    )
    with pytest.raises(InstrumentNormalizationError, match="ordered"):
        InstrumentRegistryV1(
            "registry",
            "1",
            "IMMUTABLE_VERSIONED_REPLACEMENT",
            (instrument, earlier),
        )
    registry = InstrumentRegistryV1(
        "registry", "1", "IMMUTABLE_VERSIONED_REPLACEMENT", (instrument,)
    )
    with pytest.raises(InstrumentNormalizationError, match="unknown"):
        registry.exchange_symbol_for("UNKNOWN", "KRAKEN")


def test_gate_semantic_and_safety_guards_after_valid_checksum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    changed_target = rewritten_gate(target_lot=33)
    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", changed_target["output_checksum"])
    with pytest.raises(InstrumentNormalizationError, match="does not authorize"):
        engine._verify_entry_gate(changed_target)

    unsafe = rewritten_gate()
    unsafe["safety"] = {**fail_closed_safety(), "trade_allowed": True}
    body = dict(unsafe)
    body.pop("output_checksum")
    unsafe["output_checksum"] = canonical_checksum(body)
    monkeypatch.setattr(engine, "EXPECTED_GATE_CHECKSUM", unsafe["output_checksum"])
    with pytest.raises(InstrumentNormalizationError, match="safety boundary"):
        engine._verify_entry_gate(unsafe)


def test_source_registry_schema_duplicate_and_auth_guards() -> None:
    registry = json.loads((ROOT / "data/audit/source_registry_lot31.json").read_text())
    with pytest.raises(InstrumentNormalizationError, match="SourceRegistryV1"):
        engine._source_entries({**registry, "schema_version": "wrong"})
    duplicate = {**registry, "sources": [registry["sources"][0], registry["sources"][0]]}
    with pytest.raises(InstrumentNormalizationError, match="unique"):
        engine._source_entries(duplicate)
    authenticated = json.loads(json.dumps(registry))
    authenticated["sources"][0]["auth_mode"] = "API_KEY"
    with pytest.raises(InstrumentNormalizationError, match="authentication"):
        engine._source_entries(authenticated)


def test_exact_fields_blank_nullable_and_config_schema_guards(tmp_path: Path) -> None:
    with pytest.raises(InstrumentNormalizationError, match="fields differ"):
        engine._require_exact_fields({"a": 1}, frozenset({"b"}), "object")
    with pytest.raises(InstrumentNormalizationError, match="trimmed"):
        engine._explicit_nullable_string({"value": " "}, "value")
    for relative in (
        "config/data_governance/instrument_symbol_contract_normalization_v1.json",
        "data/audit/lot32_v3_entry_gate.json",
        "data/audit/source_registry_lot31.json",
        "data/audit/market_data_governance_scope_and_source_registry_lot31.json",
        "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    config_path = tmp_path / "config/data_governance/instrument_symbol_contract_normalization_v1.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "wrong"
    config_path.write_text(json.dumps(config))
    with pytest.raises(InstrumentNormalizationError, match="schema_version"):
        build_lot32_artifacts(tmp_path, VALID_SHA)


def test_round_trip_defensive_mismatch_branches() -> None:
    alias = SimpleNamespace(venue="KRAKEN", exchange_symbol="XBTEUR")
    instrument = SimpleNamespace(canonical_symbol="BTC/EUR:SPOT", aliases=(alias,))
    bad_forward = SimpleNamespace(
        instruments=(instrument,),
        exchange_symbol_for=lambda canonical, venue: "WRONG",
        canonical_symbol_for=lambda venue, symbol: "BTC/EUR:SPOT",
    )
    with pytest.raises(InstrumentNormalizationError, match="canonical to venue"):
        engine._verify_round_trips(bad_forward)
    bad_reverse = SimpleNamespace(
        instruments=(instrument,),
        exchange_symbol_for=lambda canonical, venue: "XBTEUR",
        canonical_symbol_for=lambda venue, symbol: "WRONG",
    )
    with pytest.raises(InstrumentNormalizationError, match="venue to canonical"):
        engine._verify_round_trips(bad_reverse)


def test_state_and_audit_invalid_status_count_and_reason_guards() -> None:
    state, audit = build_lot32_artifacts(ROOT, VALID_SHA)
    with pytest.raises(InstrumentNormalizationError, match="validation_state"):
        replace(state, validation_state="UNKNOWN")
    with pytest.raises(InstrumentNormalizationError, match="reason code"):
        replace(state, reason_codes=("UNKNOWN",))
    with pytest.raises(InstrumentNormalizationError, match="registry counts"):
        replace(audit, instrument_count=0)
    with pytest.raises(InstrumentNormalizationError, match="round-trip"):
        replace(audit, round_trip_count=5)
    with pytest.raises(InstrumentNormalizationError, match="frozen"):
        replace(audit, frozen_instrument_count=1)
    with pytest.raises(InstrumentNormalizationError, match="validation_state"):
        replace(audit, validation_state="UNKNOWN")
