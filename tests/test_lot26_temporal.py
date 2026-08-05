from __future__ import annotations

from dataclasses import replace

import pytest

from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError
from crypto_quant_bot.market_analysis.alignment_temporal import select_asof_backward
from tests.lot26_fixtures import load_config, make_availability, make_state


def _base_inputs():
    local = make_state("5m")
    higher = make_state("15m")
    availability = [make_availability(local), make_availability(higher)]
    return local, higher, availability


def test_asof_backward_selects_latest_eligible_state() -> None:
    local = make_state("5m")
    earlier = make_state(
        "15m",
        state_id="earlier",
        open_time="2026-05-25T02:30:00Z",
        close_time="2026-05-25T02:45:00Z",
        available_at="2026-05-25T02:45:00Z",
        sequence_id=0,
    )
    latest = make_state("15m", state_id="latest", sequence_id=1)
    availability = [make_availability(local), make_availability(earlier), make_availability(latest)]
    selected = select_asof_backward(local, [earlier, latest], availability, load_config())
    assert selected.higher.state_id == "latest"
    assert selected.join_lag_seconds == 0.0
    assert selected.local_age_seconds == 0.0
    assert selected.higher_age_seconds == 0.0


def test_asof_backward_uses_revision_and_sequence_tie_breaks() -> None:
    local = make_state("5m")
    first = make_state("15m", state_id="first", revision_id=0, sequence_id=0)
    revised = make_state("15m", state_id="revised", revision_id=1, sequence_id=0)
    selected = select_asof_backward(
        local,
        [first, revised],
        [make_availability(local), make_availability(first), make_availability(revised)],
        load_config(),
    )
    assert selected.higher.state_id == "revised"


def test_future_and_open_higher_states_are_ignored() -> None:
    local, higher, availability = _base_inputs()
    future = make_state(
        "15m",
        state_id="future",
        open_time="2026-05-25T03:00:00Z",
        close_time="2026-05-25T03:15:00Z",
        available_at="2026-05-25T03:15:00Z",
        decision_time="2026-05-25T03:15:00Z",
        sequence_id=2,
    )
    open_state = make_state("15m", state_id="open", sequence_id=1)
    items = [*availability, make_availability(open_state, is_closed=False), make_availability(future)]
    selected = select_asof_backward(local, [higher, open_state, future], items, load_config())
    assert selected.higher.state_id == higher.state_id


def test_equal_available_at_and_decision_time_is_accepted() -> None:
    local, higher, availability = _base_inputs()
    assert higher.available_at == local.decision_time
    assert select_asof_backward(local, [higher], availability, load_config()).higher == higher


def test_no_eligible_higher_state_fails_closed() -> None:
    local = make_state("5m")
    stale = make_state(
        "15m",
        open_time="2026-05-25T02:15:00Z",
        close_time="2026-05-25T02:30:00Z",
        available_at="2026-05-25T02:30:00Z",
    )
    config = load_config()
    config["time_policy"]["higher_max_staleness_seconds"] = 100
    with pytest.raises(Lot26ValidationError, match="MTF_HIGHER_STATE_MISSING"):
        select_asof_backward(local, [stale], [make_availability(local), make_availability(stale)], config)


def test_out_of_order_and_ambiguous_duplicates_are_rejected() -> None:
    local = make_state("5m")
    earlier = make_state("15m", state_id="earlier", open_time="2026-05-25T02:30:00Z", close_time="2026-05-25T02:45:00Z", available_at="2026-05-25T02:45:00Z")
    latest = make_state("15m", state_id="latest", sequence_id=1)
    items = [make_availability(local), make_availability(earlier), make_availability(latest)]
    with pytest.raises(Lot26ValidationError, match="out-of-order"):
        select_asof_backward(local, [latest, earlier], items, load_config())
    duplicate = replace(latest, state_id="duplicate", source_bar_id="other", lineage_id="other")
    with pytest.raises(Lot26ValidationError, match="ambiguous duplicate"):
        select_asof_backward(local, [latest, duplicate], [*items, make_availability(duplicate)], load_config())


def test_missing_duplicate_and_mismatched_availability_are_rejected() -> None:
    local, higher, availability = _base_inputs()
    with pytest.raises(Lot26ValidationError, match="missing availability"):
        select_asof_backward(local, [higher], [availability[0]], load_config())
    with pytest.raises(Lot26ValidationError, match="duplicate availability"):
        select_asof_backward(local, [higher], [*availability, availability[1]], load_config())
    mismatch = replace(availability[1], source_bar_id="different")
    with pytest.raises(Lot26ValidationError, match="availability mismatch"):
        select_asof_backward(local, [higher], [availability[0], mismatch], load_config())


def test_local_open_future_stale_invalid_and_missing_fail_closed() -> None:
    local, higher, availability = _base_inputs()
    cases = [
        ([make_availability(local, is_closed=False), availability[1]], "MTF_OPEN_BAR_REJECTED"),
        ([replace(availability[0], available_at="2026-05-25T03:01:00Z", decision_time="2026-05-25T03:01:00Z"), availability[1]], "availability mismatch"),
    ]
    for items, message in cases:
        with pytest.raises(Lot26ValidationError, match=message):
            select_asof_backward(local, [higher], items, load_config())
    stale_local = make_state("5m", open_time="2026-05-25T02:45:00Z", close_time="2026-05-25T02:50:00Z", available_at="2026-05-25T02:50:00Z")
    config = load_config()
    config["time_policy"]["local_max_staleness_seconds"] = 100
    with pytest.raises(Lot26ValidationError, match="MTF_STALE_LOCAL_STATE"):
        select_asof_backward(stale_local, [higher], [make_availability(stale_local), availability[1]], config)
    invalid = replace(local, validation_state="INVALID")
    with pytest.raises(Lot26ValidationError, match="MTF_LOCAL_STATE_MISSING"):
        select_asof_backward(invalid, [higher], [make_availability(invalid), availability[1]], load_config())
    with pytest.raises(Lot26ValidationError, match="MTF_LOCAL_STATE_MISSING"):
        select_asof_backward(local, [higher], [availability[1]], load_config())


def test_different_instrument_and_scale_are_not_candidates() -> None:
    local, higher, availability = _base_inputs()
    other = replace(higher, instrument_id="ETH/EUR")
    other_item = replace(make_availability(other), instrument_id="ETH/EUR")
    with pytest.raises(Lot26ValidationError, match="MTF_HIGHER_STATE_MISSING"):
        select_asof_backward(local, [other], [availability[0], other_item], load_config())
