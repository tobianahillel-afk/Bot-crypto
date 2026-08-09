from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_quant_bot.microstructure.microstructure_scope_and_offline_data_contracts_validation import (
    MicrostructureScopeValidationError,
    duration_us,
    lot37_safety,
    parse_utc_timestamp,
    require_capability_id,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    require_unique,
    validate_causal_times,
    validate_contract_schema_path,
    validate_lot37_safety,
    validate_reason_codes,
    validate_runtime_mode,
)


def test_lot37_safety_contract_is_exact_and_fail_closed() -> None:
    expected = {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "market_event_publication_allowed": False,
        "network_ingestion_allowed": False,
        "order_routing_allowed": False,
        "participant_behavior_inference_explicitly_labeled": True,
        "raw_data_mutation_allowed": False,
        "real_credentials_allowed": False,
        "risk_approval_allowed": False,
        "scenario_score_is_signal": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }
    assert lot37_safety() == expected
    validate_lot37_safety(expected)

    for field, original in expected.items():
        changed = dict(expected)
        changed[field] = 1 if field == "approved_size" else not original
        with pytest.raises(MicrostructureScopeValidationError, match="safety boundary changed"):
            validate_lot37_safety(changed)


def test_scalar_contract_validators_have_exact_boundaries() -> None:
    assert require_text(" value ", "field") == " value "
    with pytest.raises(MicrostructureScopeValidationError, match="non-empty text"):
        require_text("   ", "field")

    assert require_integer(7, "count", minimum=7) == 7
    for invalid in (True, 6, 7.0, "7"):
        with pytest.raises(MicrostructureScopeValidationError, match="integer >= 7"):
            require_integer(invalid, "count", minimum=7)

    require_git_sha("a" * 40, "commit")
    for invalid in ("A" * 40, "a" * 39, "g" * 40):
        with pytest.raises(MicrostructureScopeValidationError, match="lowercase git SHA"):
            require_git_sha(invalid, "commit")

    require_sha256("b" * 64, "checksum")
    for invalid in ("B" * 64, "b" * 63, "z" * 64):
        with pytest.raises(MicrostructureScopeValidationError, match="lowercase sha256"):
            require_sha256(invalid, "checksum")

    require_capability_id("LOT37_SCOPE_BOUNDARY")
    for invalid in ("lot37_scope_boundary", "LOT37-SCOPE", ""):
        with pytest.raises(MicrostructureScopeValidationError, match="canonical uppercase"):
            require_capability_id(invalid)


def test_timestamp_and_duration_oracles_are_exact() -> None:
    parsed = parse_utc_timestamp("2026-08-06T19:18:40.123456Z", "event_time")
    assert parsed == datetime(2026, 8, 6, 19, 18, 40, 123456, tzinfo=UTC)

    with pytest.raises(MicrostructureScopeValidationError, match="UTC Z notation"):
        parse_utc_timestamp("2026-08-06T19:18:40+00:00", "event_time")

    start = datetime(2026, 8, 6, 0, 0, 0, 999999, tzinfo=UTC)
    end = datetime(2026, 8, 7, 0, 0, 3, 2, tzinfo=UTC)
    assert duration_us(start, end) == 86_402_000_003
    assert duration_us(start, start) == 0
    with pytest.raises(MicrostructureScopeValidationError, match="cannot run backwards"):
        duration_us(end, start)


def test_causal_time_contract_rejects_each_ordering_violation() -> None:
    validate_causal_times(
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:40.500000Z",
        "2026-08-06T19:18:41.000000Z",
    )
    with pytest.raises(MicrostructureScopeValidationError, match="causal availability"):
        validate_causal_times(
            "2026-08-06T19:18:40.600000Z",
            "2026-08-06T19:18:40.500000Z",
            "2026-08-06T19:18:41.000000Z",
        )
    with pytest.raises(MicrostructureScopeValidationError, match="causal availability"):
        validate_causal_times(
            "2026-08-06T19:18:40.000000Z",
            "2026-08-06T19:18:41.100000Z",
            "2026-08-06T19:18:41.000000Z",
        )


def test_runtime_schema_reason_and_uniqueness_boundaries() -> None:
    validate_runtime_mode("OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY")
    with pytest.raises(MicrostructureScopeValidationError, match="runtime must be"):
        validate_runtime_mode("LIVE")

    validate_contract_schema_path("contracts/schemas/example.schema.json")
    for invalid in (
        "schemas/example.schema.json",
        "contracts/schemas/example.json",
        "contracts/schemas/../example.schema.json",
    ):
        with pytest.raises(MicrostructureScopeValidationError):
            validate_contract_schema_path(invalid)

    validate_reason_codes(("LOT37_SCOPE_BOUNDARY", "OFFLINE_DATA_CONTRACT_REGISTRY"))
    with pytest.raises(MicrostructureScopeValidationError, match="requires reason codes"):
        validate_reason_codes(())

    require_unique(("a", "b"), "values")
    with pytest.raises(MicrostructureScopeValidationError, match="must be unique"):
        require_unique(("a", "a"), "values")
