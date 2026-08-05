from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest
from lot26_fixtures import make_alignment, make_availability, make_state

from crypto_quant_bot.contracts.timeframe_alignment import (
    ClosedBarAvailabilityV1,
    MultiTimeframeAlignmentStateV1,
    TimeframeMarketContextStateV1,
    parse_utc,
)


def test_context_contract_round_trip_and_dimensions() -> None:
    state = make_state("5m")
    payload = state.to_dict()
    assert payload["scale_id"] == "timebar-5m"
    assert payload["forecast_horizon"] is None
    assert payload["signal_ttl"] is None
    assert payload["holding_horizon"] is None
    assert payload["execution_allowed"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("timeframe", "1m"),
        ("scale_id", "timebar-15m"),
        ("data_resolution", "15m"),
        ("decision_clock", "MARKET_EVENT"),
        ("forecast_horizon", "5m"),
        ("signal_ttl", "5m"),
        ("holding_horizon", "5m"),
        ("revision_id", -1),
        ("sequence_id", -1),
        ("validation_state", "STALE"),
        ("analysis_only", False),
        ("used_for_decision", True),
        ("execution_allowed", True),
    ],
)
def test_context_contract_rejects_invalid_dimensions(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        replace(make_state("5m"), **{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("bar_open_time", "2026-05-25T03:00:00Z"),
        ("event_time", "2026-05-25T03:00:01Z"),
        ("available_at", "2026-05-25T02:59:59Z"),
        ("decision_time", "2026-05-25T02:59:59Z"),
        ("generated_at", "2026-05-25T03:00:00"),
    ],
)
def test_context_contract_rejects_invalid_time_order(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        replace(make_state("5m"), **{field: value})


def test_context_contract_rejects_unknown_and_nonfinite_scores() -> None:
    with pytest.raises(ValueError, match="unknown component"):
        replace(make_state("5m"), component_scores={"unknown": 0.5})
    with pytest.raises(ValueError, match="finite"):
        replace(make_state("5m"), component_scores={"trend": float("nan")})
    with pytest.raises(ValueError, match="numeric"):
        replace(make_state("5m"), component_scores={"trend": True})


def test_context_contract_rejects_duplicate_reason_codes() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        replace(make_state("5m"), reason_codes=("A", "A"))


def test_parse_utc_rejects_naive_and_invalid_timestamps() -> None:
    with pytest.raises(ValueError):
        parse_utc("2026-05-25T03:00:00", "time")
    with pytest.raises(ValueError):
        parse_utc("not-a-timeZ", "time")


def test_availability_consumability_is_fail_closed() -> None:
    state = make_state("5m")
    assert make_availability(state).consumable is True
    assert make_availability(state, is_closed=False).consumable is False
    assert make_availability(state, is_complete=False).consumable is False
    assert make_availability(state, quality_state="STALE").consumable is False


@pytest.mark.parametrize("field", ["revision_id", "sequence_id"])
def test_availability_rejects_negative_sequence_fields(field: str) -> None:
    item = make_availability(make_state("5m"))
    with pytest.raises(ValueError):
        replace(item, **{field: -1})


def test_availability_rejects_invalid_schema_scale_time_and_quality() -> None:
    item = make_availability(make_state("5m"))
    for changes in (
        {"schema_version": "v2"},
        {"scale_id": "timebar-15m"},
        {"quality_state": "BLOCKED"},
        {"bar_close_time": item.bar_open_time},
        {"reason_codes": ("A", "A")},
    ):
        with pytest.raises(ValueError):
            replace(item, **changes)


def test_alignment_contract_round_trip_and_safety() -> None:
    payload = make_alignment().to_dict()
    assert payload["analysis_only"] is True
    assert payload["forecast_generation_allowed"] is False
    assert payload["probability_claims_allowed"] is False
    assert payload["trade_allowed"] is False
    assert payload["approved_size"] == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("local_scale_id", "timebar-1m"),
        ("decision_trigger", "FORECAST_UPDATE"),
        ("join_method", "INNER"),
        ("available_component_count", 7),
        ("weighted_coverage_ratio", 1.1),
        ("overall_agreement_score", -0.1),
        ("alignment_state", "BUY"),
        ("divergence_state", "OTHER"),
        ("coherence_state", "OTHER"),
        ("combined_context_state", "OTHER"),
        ("uncertainty_state", "OTHER"),
        ("hard_mismatch_components", ("unknown",)),
        ("used_for_decision", True),
        ("forecast_generation_allowed", True),
        ("probability_claims_allowed", True),
        ("signal_generation_allowed", True),
        ("order_routing_allowed", True),
        ("execution_allowed", True),
        ("trade_allowed", True),
        ("approved_size", 1),
    ],
)
def test_alignment_contract_rejects_invalid_or_executable_fields(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        replace(make_alignment(), **{field: value})


def test_alignment_contract_rejects_incomplete_scores_and_duplicate_codes() -> None:
    with pytest.raises(ValueError, match="six components"):
        replace(make_alignment(), component_alignment_scores={"trend": 1.0})
    with pytest.raises(ValueError, match="duplicates"):
        replace(make_alignment(), reason_codes=("A", "A"))
    with pytest.raises(ValueError, match="duplicates"):
        replace(make_alignment(), hard_mismatch_components=("trend", "trend"))


def test_closed_contract_types_are_immutable() -> None:
    state = make_state("5m")
    with pytest.raises(FrozenInstanceError):
        state.timeframe = "15m"  # type: ignore[misc]
    assert isinstance(make_availability(state), ClosedBarAvailabilityV1)
    assert isinstance(make_alignment(), MultiTimeframeAlignmentStateV1)
    assert isinstance(state, TimeframeMarketContextStateV1)
