from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

import crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance as engine
from crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance import (
    build_lot33_artifacts,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_models import (
    ClockHealthStateV1,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_validation import (
    TimestampGovernanceError,
    parse_aware_timestamp,
    require_text,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_SHA = "d" * 40


def certified_state_and_audit():
    return build_lot33_artifacts(ROOT, VALID_SHA)


def test_nullable_helpers_cover_missing_null_and_value_paths() -> None:
    assert engine._nullable_string({"field": None}, "field") is None
    assert engine._nullable_string({"field": "value"}, "field") == "value"
    with pytest.raises(TimestampGovernanceError, match="explicitly present"):
        engine._nullable_string({}, "field")

    assert engine._nullable_integer({"field": None}, "field") is None
    assert engine._nullable_integer({"field": 7}, "field") == 7
    with pytest.raises(TimestampGovernanceError, match="explicitly present"):
        engine._nullable_integer({}, "field")


def test_health_rejects_empty_envelopes_and_invalid_thresholds() -> None:
    with pytest.raises(TimestampGovernanceError, match="at least one"):
        engine._build_health(
            (),
            {
                "max_clock_drift_us": 1,
                "max_out_of_order_delay_us": 1,
                "max_total_latency_us": 1,
            },
        )

    state, _ = certified_state_and_audit()
    with pytest.raises(TimestampGovernanceError, match="thresholds"):
        engine._build_health(
            state.canonical_envelopes,
            {
                "max_clock_drift_us": -1,
                "max_out_of_order_delay_us": 500000,
                "max_total_latency_us": 500000,
            },
        )


def test_raw_sequence_revision_and_monotonic_values_fail_closed() -> None:
    state, _ = certified_state_and_audit()
    wall_clock = state.canonical_envelopes[0].raw
    process_clock = state.canonical_envelopes[1].raw

    with pytest.raises(TimestampGovernanceError, match="cannot be negative"):
        replace(wall_clock, sequence_id=-1)
    with pytest.raises(TimestampGovernanceError, match="cannot be negative"):
        replace(wall_clock, revision_id=-1)
    with pytest.raises(TimestampGovernanceError, match="PROCESS_MONOTONIC_NS"):
        replace(process_clock, monotonic_time=-1)


def test_canonical_envelope_rejects_negative_latency_and_wrong_state() -> None:
    state, _ = certified_state_and_audit()
    envelope = state.canonical_envelopes[0]
    with pytest.raises(TimestampGovernanceError, match="latency values"):
        replace(envelope, total_latency_us=-1)
    with pytest.raises(TimestampGovernanceError, match="validation_state"):
        replace(envelope, validation_state="UNKNOWN")


def test_clock_health_rejects_negative_observation() -> None:
    with pytest.raises(TimestampGovernanceError, match="cannot be negative"):
        ClockHealthStateV1("HEALTHY", 1, 1, 1, -1, 0, 0, ("NEGATIVE",))


def test_state_rejects_empty_duplicate_wrong_state_and_reason_sequence() -> None:
    state, _ = certified_state_and_audit()
    with pytest.raises(TimestampGovernanceError, match="validation_state"):
        replace(state, validation_state="UNKNOWN")
    with pytest.raises(TimestampGovernanceError, match="unique and ordered"):
        replace(state, canonical_envelopes=())
    with pytest.raises(TimestampGovernanceError, match="unique and ordered"):
        replace(
            state,
            canonical_envelopes=(state.canonical_envelopes[0], state.canonical_envelopes[0]),
        )
    with pytest.raises(TimestampGovernanceError, match="reason code"):
        replace(state, reason_codes=("WRONG",))


def test_audit_rejects_clock_status_observations_and_validation_state() -> None:
    _, audit = certified_state_and_audit()
    with pytest.raises(TimestampGovernanceError, match="clock status"):
        replace(audit, clock_health_status="UNKNOWN")
    with pytest.raises(TimestampGovernanceError, match="observations"):
        replace(audit, max_observed_clock_drift_us=-1)
    with pytest.raises(TimestampGovernanceError, match="validation_state"):
        replace(audit, validation_state="UNKNOWN")


def test_text_and_timestamp_format_guards_are_exercised() -> None:
    with pytest.raises(TimestampGovernanceError, match="trimmed"):
        require_text(" value ", "field")
    with pytest.raises(TimestampGovernanceError, match="timezone"):
        parse_aware_timestamp("not-a-timestamp", "event_time")
