from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import timedelta
from typing import Any

from crypto_quant_bot.contracts.timeframe_alignment import (
    ClosedBarAvailabilityV1,
    TimeframeMarketContextStateV1,
)
from crypto_quant_bot.market_analysis.alignment_common import (
    Lot26ValidationError,
    parse_utc,
    stable_id,
)

_DURATION_SECONDS = {"5m": 300, "15m": 900}
_STATE_FIELDS = {
    "trend": "trend_state",
    "range": "range_state",
    "momentum": "momentum_state",
    "volatility": "volatility_state",
    "regime": "regime_state",
    "confluence": "confluence_state",
}
_SCORE_FIELDS = {
    "trend": "trend_context_score",
    "range": "range_context_score",
    "momentum": "momentum_context_score",
    "volatility": "volatility_context_score",
    "regime": "regime_context_score",
    "confluence": "confluence_context_score",
}


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise Lot26ValidationError(f"MTF_SCHEMA_INCOMPATIBLE:{key}")
    return value


def _context_scores(row: Mapping[str, Any]) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for component, field_name in _SCORE_FIELDS.items():
        value = row.get(field_name)
        if value is None:
            result[component] = None
        elif isinstance(value, bool) or not isinstance(value, int | float):
            raise Lot26ValidationError(f"MTF_SCHEMA_INCOMPATIBLE:{field_name}")
        else:
            result[component] = float(value)
    return result


def _state_values(row: Mapping[str, Any]) -> dict[str, str]:
    return {component: _required_text(row, field) for component, field in _STATE_FIELDS.items()}


def _times(row: Mapping[str, Any], timeframe: str) -> tuple[str, str]:
    opened_text = _required_text(row, "last_timestamp")
    opened = parse_utc(opened_text, "last_timestamp")
    closed = opened + timedelta(seconds=_DURATION_SECONDS[timeframe])
    return opened_text, closed.isoformat().replace("+00:00", "Z")


def _identity(
    row: Mapping[str, Any],
    decision_time: str,
    code_commit: str,
) -> dict[str, object]:
    return {"row": dict(row), "decision_time": decision_time, "code_commit": code_commit}


def _build_context_state(
    row: Mapping[str, Any],
    *,
    timeframe: str,
    opened: str,
    closed: str,
    decision_time: str,
    code_commit: str,
    sequence_id: int,
) -> TimeframeMarketContextStateV1:
    identity = _identity(row, decision_time, code_commit)
    state_id = stable_id("context", identity)
    lineage_id = stable_id("lineage", identity)
    source_bar_id = stable_id("bar", {"timeframe": timeframe, "open": opened, "close": closed})
    return TimeframeMarketContextStateV1(
        state_id=state_id,
        instrument_id="BTC/EUR",
        timeframe=timeframe,
        scale_id=f"timebar-{timeframe}",
        data_resolution=timeframe,
        feature_lookback="lot25-summary-window",
        forecast_horizon=None,
        decision_clock="CLOSED_LOCAL_BAR",
        signal_ttl=None,
        holding_horizon=None,
        bar_open_time=opened,
        bar_close_time=closed,
        event_time=closed,
        available_at=closed,
        decision_time=decision_time,
        generated_at=decision_time,
        source_bar_id=source_bar_id,
        revision_id=0,
        sequence_id=sequence_id,
        lineage_id=lineage_id,
        config_version="lot25-volatility-regime-confluence-v0-adapter-v1",
        code_commit=code_commit,
        validation_state="VALID",
        component_scores=_context_scores(row),
        reason_codes=("LOT25_ADAPTER_CONFIRMED_CLOSED_BAR",),
        **{f"{key}_state": value for key, value in _state_values(row).items()},
    )


def _build_availability(
    state: TimeframeMarketContextStateV1,
    identity: dict[str, object],
) -> ClosedBarAvailabilityV1:
    return ClosedBarAvailabilityV1(
        availability_id=stable_id("availability", identity),
        state_id=state.state_id,
        instrument_id=state.instrument_id,
        timeframe=state.timeframe,
        scale_id=state.scale_id,
        source_bar_id=state.source_bar_id,
        bar_open_time=state.bar_open_time,
        bar_close_time=state.bar_close_time,
        available_at=state.available_at,
        decision_time=state.decision_time,
        is_closed=True,
        is_complete=True,
        quality_state="VALID",
        revision_id=state.revision_id,
        sequence_id=state.sequence_id,
        lineage_id=state.lineage_id,
        reason_codes=("CLOSED_BAR_CONFIRMED",),
    )


def adapt_lot25_summary(
    row: Mapping[str, Any],
    *,
    decision_time: str,
    code_commit: str,
    sequence_id: int,
) -> tuple[TimeframeMarketContextStateV1, ClosedBarAvailabilityV1]:
    timeframe = _required_text(row, "timeframe")
    if timeframe not in _DURATION_SECONDS:
        raise Lot26ValidationError("MTF_SCALE_RELATION_NOT_ALLOWED")
    opened, closed = _times(row, timeframe)
    if parse_utc(closed, "bar_close_time") > parse_utc(decision_time, "decision_time"):
        raise Lot26ValidationError("MTF_FUTURE_STATE_REJECTED")
    identity = _identity(row, decision_time, code_commit)
    state = _build_context_state(
        row,
        timeframe=timeframe,
        opened=opened,
        closed=closed,
        decision_time=decision_time,
        code_commit=code_commit,
        sequence_id=sequence_id,
    )
    return state, _build_availability(state, identity)


def adapt_lot25_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    decision_time: str,
    code_commit: str,
) -> tuple[list[TimeframeMarketContextStateV1], list[ClosedBarAvailabilityV1]]:
    states: list[TimeframeMarketContextStateV1] = []
    availability: list[ClosedBarAvailabilityV1] = []
    for sequence_id, row in enumerate(rows):
        state, item = adapt_lot25_summary(
            row,
            decision_time=decision_time,
            code_commit=code_commit,
            sequence_id=sequence_id,
        )
        states.append(state)
        availability.append(item)
    if {state.timeframe for state in states} != {"5m", "15m"}:
        raise Lot26ValidationError("MTF_SCALE_RELATION_NOT_ALLOWED")
    return states, availability
