from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine import (
    build_lot43_artifacts,
)
from crypto_quant_bot.microstructure.book_resilience_and_replenishment_engine_validation import (
    Lot43ValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "e" * 40


def _reference_resilience():
    state, _, _ = build_lot43_artifacts(ROOT, CODE_COMMIT)
    return state.book_resilience


def test_state_rejects_slice_outcomes_that_disagree_with_published_events() -> None:
    resilience = _reference_resilience()
    first_slice = resilience.resilience_slices[0]
    contradictory = replace(
        first_slice,
        recovered_events_total=1,
        expired_events_total=0,
        mean_recovered_fraction=Decimal("1"),
        mean_replenishment_time_us=Decimal("10000"),
        resilience_status="RESILIENT",
    )
    with pytest.raises(Lot43ValidationError, match="slice aggregation must match published events"):
        replace(
            resilience,
            resilience_slices=(contradictory, *resilience.resilience_slices[1:]),
        )


def test_state_rejects_slice_means_that_disagree_with_published_events() -> None:
    resilience = _reference_resilience()
    first_slice = resilience.resilience_slices[0]
    contradictory = replace(first_slice, mean_recovered_fraction=Decimal("0.5"))
    with pytest.raises(Lot43ValidationError, match="slice aggregation must match published events"):
        replace(
            resilience,
            resilience_slices=(contradictory, *resilience.resilience_slices[1:]),
        )


def test_state_requires_non_empty_complete_side_by_horizon_matrix() -> None:
    resilience = _reference_resilience()
    with pytest.raises(Lot43ValidationError, match="slice matrix must be non-empty"):
        replace(resilience, resilience_slices=())

    bid_only = tuple(item for item in resilience.resilience_slices if item.side == "BID")
    with pytest.raises(Lot43ValidationError, match="complete BID/ASK slice matrix"):
        replace(resilience, resilience_slices=bid_only)


def test_state_requires_every_configured_horizon_even_when_both_sides_are_omitted() -> None:
    resilience = _reference_resilience()
    assert resilience.resilience_horizons_us == (10_000, 25_000)
    assert resilience.to_dict()["resilience_horizons_us"] == [10_000, 25_000]
    first_horizon_only = tuple(
        item for item in resilience.resilience_slices if item.horizon_us == 10_000
    )
    with pytest.raises(Lot43ValidationError, match="complete BID/ASK slice matrix"):
        replace(resilience, resilience_slices=first_horizon_only)
    with pytest.raises(Lot43ValidationError, match="horizons cannot be empty"):
        replace(resilience, resilience_horizons_us=())


def test_state_rejects_duplicate_side_horizon_slice_keys() -> None:
    resilience = _reference_resilience()
    duplicated = (*resilience.resilience_slices, resilience.resilience_slices[0])
    with pytest.raises(Lot43ValidationError, match="slice keys must be unique"):
        replace(resilience, resilience_slices=duplicated)


def test_state_rejects_slice_regime_or_threshold_divergence() -> None:
    resilience = _reference_resilience()
    first_slice = resilience.resilience_slices[0]

    wrong_regime = replace(first_slice, volatility_regime="NORMAL")
    with pytest.raises(Lot43ValidationError, match="slice volatility regime"):
        replace(
            resilience,
            resilience_slices=(wrong_regime, *resilience.resilience_slices[1:]),
        )

    wrong_threshold = replace(first_slice, replenishment_min_recovery_ratio=Decimal("0.5"))
    with pytest.raises(Lot43ValidationError, match="recovery threshold must be consistent"):
        replace(
            resilience,
            resilience_slices=(wrong_threshold, *resilience.resilience_slices[1:]),
        )


def test_state_rejects_replenishment_evidence_after_decision_time() -> None:
    resilience = _reference_resilience()
    event = resilience.depletion_events[0]
    future_evidence = replace(
        event,
        replenishment_kind="SAME_PRICE",
        replenishment_sequence_id=1004,
        replenishment_time_us=40_000,
        replenished_quantity=Decimal("1.25"),
        recovered_fraction=Decimal("1"),
        max_window_status="REPLENISHED",
    )
    with pytest.raises(Lot43ValidationError, match="evidence cannot exceed decision_time"):
        replace(
            resilience,
            sequence_id=1004,
            history_sequence_ids=(*resilience.history_sequence_ids, 1004),
            depletion_events=(future_evidence,),
        )


def test_state_binds_event_sequences_to_published_history() -> None:
    resilience = _reference_resilience()
    event = resilience.depletion_events[0]
    with pytest.raises(Lot43ValidationError, match="depletion sequence must belong"):
        replace(resilience, depletion_events=(replace(event, depletion_sequence_id=999),))
    recovery = replace(
        event, replenishment_kind="SAME_PRICE", replenishment_sequence_id=1004,
        replenishment_time_us=10_000, replenished_quantity=Decimal("1.25"),
        recovered_fraction=Decimal("1"), max_window_status="REPLENISHED",
    )
    with pytest.raises(Lot43ValidationError, match="replenishment sequence must belong"):
        replace(resilience, depletion_events=(recovery,))


def test_state_rejects_outcome_beyond_declared_maximum_horizon() -> None:
    resilience = _reference_resilience()
    event = replace(
        resilience.depletion_events[0], replenishment_kind="SAME_PRICE",
        replenishment_sequence_id=1004, replenishment_time_us=25_001,
        replenished_quantity=Decimal("1.25"), recovered_fraction=Decimal("1"),
        max_window_status="REPLENISHED",
    )
    with pytest.raises(Lot43ValidationError, match="max window status must match"):
        replace(
            resilience, sequence_id=1004,
            history_sequence_ids=(*resilience.history_sequence_ids, 1004),
            depletion_events=(event,),
        )


def test_state_rejects_direct_recovery_below_published_threshold() -> None:
    resilience = _reference_resilience()
    event = replace(
        resilience.depletion_events[0], replenishment_kind="SAME_PRICE",
        replenishment_sequence_id=1004, replenishment_time_us=10_000,
        replenished_quantity=Decimal("0.2"), recovered_fraction=Decimal("0.16"),
        max_window_status="REPLENISHED",
    )
    with pytest.raises(Lot43ValidationError, match="below published recovery threshold"):
        replace(
            resilience, sequence_id=1004,
            history_sequence_ids=(*resilience.history_sequence_ids, 1004),
            depletion_events=(event,),
        )
