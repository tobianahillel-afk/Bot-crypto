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
