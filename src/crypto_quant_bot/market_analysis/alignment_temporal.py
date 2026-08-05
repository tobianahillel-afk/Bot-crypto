from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from itertools import pairwise
from typing import Any

from crypto_quant_bot.contracts.timeframe_alignment import (
    ClosedBarAvailabilityV1,
    TimeframeMarketContextStateV1,
)
from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError, parse_utc


@dataclass(frozen=True, slots=True)
class TemporalSelectionV1:
    local: TimeframeMarketContextStateV1
    higher: TimeframeMarketContextStateV1
    local_availability: ClosedBarAvailabilityV1
    higher_availability: ClosedBarAvailabilityV1
    join_lag_seconds: float
    local_age_seconds: float
    higher_age_seconds: float


def _temporal_key(state: TimeframeMarketContextStateV1) -> tuple[datetime, datetime, int, int]:
    return (
        parse_utc(state.bar_close_time, "bar_close_time"),
        parse_utc(state.available_at, "available_at"),
        state.revision_id,
        state.sequence_id,
    )


def _availability_by_state(
    items: Iterable[ClosedBarAvailabilityV1],
) -> dict[str, ClosedBarAvailabilityV1]:
    result: dict[str, ClosedBarAvailabilityV1] = {}
    for item in items:
        if item.state_id in result:
            raise Lot26ValidationError("MTF_SCHEMA_INCOMPATIBLE:duplicate availability")
        result[item.state_id] = item
    return result


def _validate_availability_match(
    state: TimeframeMarketContextStateV1,
    availability: ClosedBarAvailabilityV1,
) -> None:
    pairs = (
        (state.state_id, availability.state_id),
        (state.instrument_id, availability.instrument_id),
        (state.timeframe, availability.timeframe),
        (state.scale_id, availability.scale_id),
        (state.source_bar_id, availability.source_bar_id),
        (state.bar_open_time, availability.bar_open_time),
        (state.bar_close_time, availability.bar_close_time),
        (state.available_at, availability.available_at),
        (state.revision_id, availability.revision_id),
        (state.sequence_id, availability.sequence_id),
    )
    if any(left != right for left, right in pairs):
        raise Lot26ValidationError("MTF_SCHEMA_INCOMPATIBLE:availability mismatch")


def _age_seconds(decision_time: datetime, state: TimeframeMarketContextStateV1) -> float:
    return (decision_time - parse_utc(state.bar_close_time, "bar_close_time")).total_seconds()


def _validate_local(
    state: TimeframeMarketContextStateV1,
    availability: ClosedBarAvailabilityV1,
    decision_time: datetime,
    config: Mapping[str, Any],
) -> float:
    _validate_availability_match(state, availability)
    if state.scale_id != "timebar-5m" or state.validation_state != "VALID":
        raise Lot26ValidationError("MTF_LOCAL_STATE_MISSING")
    if not availability.consumable:
        raise Lot26ValidationError("MTF_OPEN_BAR_REJECTED")
    if parse_utc(state.available_at, "available_at") > decision_time:
        raise Lot26ValidationError("MTF_FUTURE_STATE_REJECTED")
    age = _age_seconds(decision_time, state)
    maximum = int(config["time_policy"]["local_max_staleness_seconds"])
    if age < 0:
        raise Lot26ValidationError("MTF_FUTURE_STATE_REJECTED")
    if age > maximum:
        raise Lot26ValidationError("MTF_STALE_LOCAL_STATE")
    return age


def _is_higher_candidate(
    state: TimeframeMarketContextStateV1,
    availability: ClosedBarAvailabilityV1,
    local: TimeframeMarketContextStateV1,
    decision_time: datetime,
    maximum_age: int,
) -> bool:
    _validate_availability_match(state, availability)
    if state.instrument_id != local.instrument_id or state.scale_id != "timebar-15m":
        return False
    if state.validation_state != "VALID" or not availability.consumable:
        return False
    available_at = parse_utc(state.available_at, "available_at")
    close_time = parse_utc(state.bar_close_time, "bar_close_time")
    if close_time > decision_time or available_at > decision_time:
        return False
    age = (decision_time - close_time).total_seconds()
    return 0 <= age <= maximum_age


def _require_canonical_order(states: list[TimeframeMarketContextStateV1]) -> None:
    keys = [_temporal_key(state) for state in states]
    if keys != sorted(keys):
        raise Lot26ValidationError("MTF_TIME_ALIGNMENT_INVALID:out-of-order higher states")
    for previous, current in pairwise(states):
        if _temporal_key(previous) == _temporal_key(current):
            raise Lot26ValidationError("MTF_TIME_ALIGNMENT_INVALID:ambiguous duplicate")


def select_asof_backward(
    local: TimeframeMarketContextStateV1,
    states: Iterable[TimeframeMarketContextStateV1],
    availability_items: Iterable[ClosedBarAvailabilityV1],
    config: Mapping[str, Any],
) -> TemporalSelectionV1:
    decision_time = parse_utc(local.decision_time, "decision_time")
    state_list = list(states)
    _require_canonical_order(state_list)
    availability = _availability_by_state(availability_items)
    local_availability = availability.get(local.state_id)
    if local_availability is None:
        raise Lot26ValidationError("MTF_LOCAL_STATE_MISSING")
    local_age = _validate_local(local, local_availability, decision_time, config)
    maximum_age = int(config["time_policy"]["higher_max_staleness_seconds"])
    candidates: list[tuple[TimeframeMarketContextStateV1, ClosedBarAvailabilityV1]] = []
    for state in state_list:
        item = availability.get(state.state_id)
        if item is None:
            raise Lot26ValidationError("MTF_SCHEMA_INCOMPATIBLE:missing availability")
        if _is_higher_candidate(state, item, local, decision_time, maximum_age):
            candidates.append((state, item))
    if not candidates:
        raise Lot26ValidationError("MTF_HIGHER_STATE_MISSING")
    higher, higher_availability = max(candidates, key=lambda pair: _temporal_key(pair[0]))
    higher_age = _age_seconds(decision_time, higher)
    join_lag = (
        parse_utc(local.bar_close_time, "local.bar_close_time")
        - parse_utc(higher.bar_close_time, "higher.bar_close_time")
    ).total_seconds()
    return TemporalSelectionV1(
        local=local,
        higher=higher,
        local_availability=local_availability,
        higher_availability=higher_availability,
        join_lag_seconds=join_lag,
        local_age_seconds=local_age,
        higher_age_seconds=higher_age,
    )
