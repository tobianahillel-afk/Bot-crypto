from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from crypto_quant_bot.contracts.timeframe_alignment import (
    ClosedBarAvailabilityV1,
    MultiTimeframeAlignmentStateV1,
    TimeframeMarketContextStateV1,
)

ROOT = Path(__file__).resolve().parents[1]


def load_config() -> dict[str, Any]:
    return json.loads((ROOT / "config/math/multi_timeframe_alignment_v1.json").read_text())


def load_registry() -> dict[str, Any]:
    return json.loads((ROOT / "config/temporal/temporal_scale_registry_v1.json").read_text())


def load_clock() -> dict[str, Any]:
    return json.loads((ROOT / "config/temporal/decision_clock_policy_v1.json").read_text())


def make_state(
    timeframe: str,
    *,
    state_id: str | None = None,
    open_time: str | None = None,
    close_time: str = "2026-05-25T03:00:00Z",
    available_at: str | None = None,
    decision_time: str = "2026-05-25T03:00:00Z",
    revision_id: int = 0,
    sequence_id: int = 0,
    validation_state: str = "VALID",
    **states: str,
) -> TimeframeMarketContextStateV1:
    opened = open_time or ("2026-05-25T02:55:00Z" if timeframe == "5m" else "2026-05-25T02:45:00Z")
    values = {
        "trend_state": "TREND_CONTEXT_UPWARD",
        "range_state": "RANGE_CONTEXT_BREAKING_STRUCTURE",
        "momentum_state": "MOMENTUM_CONTEXT_ACCELERATING",
        "volatility_state": "VOLATILITY_CONTEXT_LOW",
        "regime_state": "REGIME_CONTEXT_TRENDING",
        "confluence_state": "CONFLUENCE_CONTEXT_PARTIAL",
    }
    values.update(states)
    return TimeframeMarketContextStateV1(
        state_id=state_id or f"state-{timeframe}-{sequence_id}-{revision_id}",
        instrument_id="BTC/EUR",
        timeframe=timeframe,
        scale_id=f"timebar-{timeframe}",
        data_resolution=timeframe,
        feature_lookback="fixture",
        forecast_horizon=None,
        decision_clock="CLOSED_LOCAL_BAR",
        signal_ttl=None,
        holding_horizon=None,
        bar_open_time=opened,
        bar_close_time=close_time,
        event_time=close_time,
        available_at=available_at or close_time,
        decision_time=decision_time,
        generated_at=decision_time,
        source_bar_id=f"bar-{timeframe}-{sequence_id}-{revision_id}",
        revision_id=revision_id,
        sequence_id=sequence_id,
        lineage_id=f"lineage-{timeframe}-{sequence_id}-{revision_id}",
        config_version="fixture-v1",
        code_commit="abcdef1",
        validation_state=validation_state,
        component_scores={key: 0.5 for key in ("trend", "range", "momentum", "volatility", "regime", "confluence")},
        reason_codes=("FIXTURE",),
        **values,
    )


def make_availability(
    state: TimeframeMarketContextStateV1,
    *,
    is_closed: bool = True,
    is_complete: bool = True,
    quality_state: str = "VALID",
) -> ClosedBarAvailabilityV1:
    return ClosedBarAvailabilityV1(
        availability_id=f"availability-{state.state_id}",
        state_id=state.state_id,
        instrument_id=state.instrument_id,
        timeframe=state.timeframe,
        scale_id=state.scale_id,
        source_bar_id=state.source_bar_id,
        bar_open_time=state.bar_open_time,
        bar_close_time=state.bar_close_time,
        available_at=state.available_at,
        decision_time=state.decision_time,
        is_closed=is_closed,
        is_complete=is_complete,
        quality_state=quality_state,
        revision_id=state.revision_id,
        sequence_id=state.sequence_id,
        lineage_id=state.lineage_id,
        reason_codes=("FIXTURE",),
    )


def make_alignment(**changes: Any) -> MultiTimeframeAlignmentStateV1:
    values: dict[str, Any] = {
        "alignment_id": "alignment-1",
        "instrument_id": "BTC/EUR",
        "local_scale_id": "timebar-5m",
        "higher_scale_id": "timebar-15m",
        "local_timeframe": "5m",
        "higher_timeframe": "15m",
        "decision_trigger": "CLOSED_LOCAL_BAR",
        "decision_time": "2026-05-25T03:00:00Z",
        "local_state_id": "local",
        "higher_state_id": "higher",
        "local_bar_close_time": "2026-05-25T03:00:00Z",
        "higher_bar_close_time": "2026-05-25T03:00:00Z",
        "join_method": "ASOF_BACKWARD",
        "component_alignment_scores": {key: 1.0 for key in ("trend", "range", "momentum", "volatility", "regime", "confluence")},
        "available_component_count": 6,
        "weighted_coverage_ratio": 1.0,
        "overall_agreement_score": 1.0,
        "alignment_state": "MTF_ALIGNED",
        "divergence_state": "MTF_NO_HARD_DIVERGENCE",
        "coherence_state": "MTF_COHERENT",
        "combined_context_state": "MTF_CONTEXT_ALIGNED",
        "hard_mismatch_components": (),
        "reason_codes": ("MTF_ALIGNED",),
        "uncertainty_state": "LOW",
        "lineage_id": "lineage",
        "scale_registry_version": "temporal-scale-registry-v1",
        "decision_clock_policy_version": "decision-clock-policy-v1",
        "config_version": "lot26-mtf-alignment-v1",
        "config_checksum": "a" * 64,
        "code_commit": "abcdef1",
        "output_checksum": "b" * 64,
    }
    values.update(changes)
    return MultiTimeframeAlignmentStateV1(**values)


def replace_state(state: TimeframeMarketContextStateV1, **changes: Any) -> TimeframeMarketContextStateV1:
    return replace(state, **changes)
