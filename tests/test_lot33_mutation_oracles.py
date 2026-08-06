from __future__ import annotations

from pathlib import Path

import pytest

import crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance as engine
from crypto_quant_bot.data_governance.timestamp_clock_and_timezone_governance import (
    build_lot33_artifacts,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_models import (
    ClockHealthStateV1,
    RawTimestampEnvelopeV1,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_validation import (
    TimestampGovernanceError,
    canonical_utc,
    duration_us,
    signed_duration_us,
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
EXPECTED_REASONS = (
    "LOT33_ENTRY_GATE_VERIFIED",
    "LOT32_INSTRUMENT_LINEAGE_VERIFIED",
    "TIMESTAMPS_CANONICALIZED_TO_UTC",
    "RAW_TIMEZONE_AND_PRECISION_PRESERVED",
    "AVAILABLE_AT_ANTI_LOOKAHEAD_VERIFIED",
    "CLOCK_HEALTH_EVALUATED",
    "EXTERNAL_CONNECTIVITY_DISABLED",
    "LOT34_REMAINS_LOCKED",
)


def test_literal_reference_state_oracle() -> None:
    state, audit = build_lot33_artifacts(ROOT, VALID_SHA)
    assert state.safety == EXPECTED_SAFETY
    assert audit.safety == EXPECTED_SAFETY
    assert state.reason_codes == EXPECTED_REASONS
    assert state.validation_state == "VALIDATED_TEMPORAL_ONLY"
    assert audit.validation_state == "VALIDATED_TEMPORAL_ONLY"
    assert state.metrics.to_dict() == {
        "schema_version": "lot33-metrics-v1",
        "lot_33_records_processed_total": 3,
        "lot_33_validation_failures_total": 0,
        "lot_33_out_of_order_records_total": 1,
        "lot_33_processing_latency_us": 0,
    }
    assert audit.record_count == 3
    assert audit.out_of_order_record_count == 1
    assert audit.clock_health_status == "HEALTHY"
    assert audit.max_observed_clock_drift_us == 1000
    assert audit.max_observed_total_latency_us == 420000


def test_literal_clock_health_oracle() -> None:
    state, _ = build_lot33_artifacts(ROOT, VALID_SHA)
    assert state.clock_health.to_dict() == {
        "schema_version": "clock-health-state-v1",
        "status": "HEALTHY",
        "max_clock_drift_us": 5000,
        "max_out_of_order_delay_us": 500000,
        "max_total_latency_us": 500000,
        "observed_clock_drift_us": 1000,
        "observed_out_of_order_delay_us": 201000,
        "observed_total_latency_us": 420000,
        "reason_codes": ["CLOCK_THRESHOLDS_SATISFIED"],
    }


def test_literal_envelope_order_and_metrics_oracle() -> None:
    state, _ = build_lot33_artifacts(ROOT, VALID_SHA)
    rows = [
        (
            item.raw.record_id,
            item.event_time_utc,
            item.raw.sequence_id,
            item.clock_drift_us,
            item.transport_latency_us,
            item.processing_latency_us,
            item.total_latency_us,
            item.out_of_order_delay_us,
        )
        for item in state.canonical_envelopes
    ]
    assert rows == [
        (
            "kraken-record-3-late",
            "2026-08-06T19:14:59.900000Z",
            1,
            1000,
            400000,
            20000,
            420000,
            201000,
        ),
        (
            "bitstamp-record-1",
            "2026-08-06T19:15:00.101000Z",
            1,
            1000,
            50000,
            20000,
            70000,
            0,
        ),
        (
            "coinbase-record-2",
            "2026-08-06T19:15:00.101000Z",
            2,
            500,
            60000,
            20000,
            80000,
            0,
        ),
    ]


def test_raw_envelope_serialization_oracle() -> None:
    raw = RawTimestampEnvelopeV1(
        "record", "btc-eur-spot", "kraken-public-spot-metadata",
        "2026-08-06T19:15:00.100000Z", "UTC", "MICROSECONDS",
        "2026-08-06T19:15:00.100000Z", None,
        "2026-08-06T19:15:00.101000Z", "2026-08-06T19:15:00.151000Z",
        "2026-08-06T19:15:00.171000Z", "2026-08-06T19:15:00.171000Z",
        "2026-08-06T19:15:00.171000Z", None, "WALL_CLOCK_ONLY", 1, 0,
    )
    assert raw.to_dict() == {
        "schema_version": "raw-timestamp-envelope-v1",
        "record_id": "record",
        "instrument_id": "btc-eur-spot",
        "source_id": "kraken-public-spot-metadata",
        "raw_timestamp": "2026-08-06T19:15:00.100000Z",
        "source_timezone": "UTC",
        "timestamp_precision": "MICROSECONDS",
        "source_time": "2026-08-06T19:15:00.100000Z",
        "exchange_time": None,
        "event_time": "2026-08-06T19:15:00.101000Z",
        "receive_time": "2026-08-06T19:15:00.151000Z",
        "process_time": "2026-08-06T19:15:00.171000Z",
        "available_at": "2026-08-06T19:15:00.171000Z",
        "usable_from": "2026-08-06T19:15:00.171000Z",
        "monotonic_time": None,
        "clock_domain": "WALL_CLOCK_ONLY",
        "sequence_id": 1,
        "revision_id": 0,
    }


def test_canonicalization_and_duration_literals() -> None:
    assert canonical_utc(
        "2026-08-06T21:15:00.100000+02:00", "MICROSECONDS", "source"
    ) == "2026-08-06T19:15:00.100000Z"
    assert duration_us(
        "2026-08-06T19:15:00.101000Z",
        "2026-08-06T19:15:00.171000Z",
        "latency",
    ) == 70000
    assert signed_duration_us(
        "2026-08-06T19:15:00.100500Z",
        "2026-08-06T19:15:00.101000Z",
    ) == 500


def test_health_boundary_uses_strict_greater_than() -> None:
    state, _ = build_lot33_artifacts(ROOT, VALID_SHA)
    exact = ClockHealthStateV1("HEALTHY", 1000, 201000, 420000, 1000, 201000, 420000, ("EXACT",))
    assert exact.status == "HEALTHY"
    health = engine._build_health(
        state.canonical_envelopes,
        {
            "max_clock_drift_us": 1000,
            "max_out_of_order_delay_us": 201000,
            "max_total_latency_us": 420000,
        },
    )
    assert health.status == "HEALTHY"
    degraded = engine._build_health(
        state.canonical_envelopes,
        {
            "max_clock_drift_us": 999,
            "max_out_of_order_delay_us": 201000,
            "max_total_latency_us": 420000,
        },
    )
    assert degraded.status == "DEGRADED"


def test_failure_oracles_are_not_self_referential() -> None:
    with pytest.raises(TimestampGovernanceError, match="negative"):
        duration_us(
            "2026-08-06T19:15:00.101000Z",
            "2026-08-06T19:15:00.100000Z",
            "negative",
        )
    with pytest.raises(TimestampGovernanceError, match="runtime"):
        from crypto_quant_bot.data_governance.timestamp_clock_timezone_models import Lot33RunContextV1

        Lot33RunContextV1("run", "LIVE", "config", VALID_SHA, "correlation")
