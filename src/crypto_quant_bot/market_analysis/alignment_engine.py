from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from crypto_quant_bot.contracts.timeframe_alignment import (
    COMPONENTS,
    ClosedBarAvailabilityV1,
    MultiTimeframeAlignmentStateV1,
    TimeframeMarketContextStateV1,
)
from crypto_quant_bot.market_analysis.alignment_common import checksum
from crypto_quant_bot.market_analysis.alignment_config import (
    config_checksum,
    validate_decision_clock,
    validate_scale_registry,
)
from crypto_quant_bot.market_analysis.alignment_math import (
    classify_alignment,
    component_compatibility,
    compute_weighted_agreement,
    uncertainty_from_coverage,
)
from crypto_quant_bot.market_analysis.alignment_temporal import TemporalSelectionV1, select_asof_backward


def _stable_id(kind: str, payload: object) -> str:
    return str(uuid5(NAMESPACE_URL, f"lot26:{kind}:{checksum(payload)}"))


def _component_states(state: TimeframeMarketContextStateV1) -> dict[str, str]:
    return {component: str(getattr(state, f"{component}_state")) for component in COMPONENTS}


def _component_scores(
    local: TimeframeMarketContextStateV1,
    higher: TimeframeMarketContextStateV1,
    config: Mapping[str, Any],
) -> dict[str, float | None]:
    local_states = _component_states(local)
    higher_states = _component_states(higher)
    return {
        component: component_compatibility(
            component,
            local_states[component],
            higher_states[component],
            config,
        )
        for component in COMPONENTS
    }


def _alignment_identity(
    selection: TemporalSelectionV1,
    config_hash: str,
) -> dict[str, str]:
    return {
        "local_state_id": selection.local.state_id,
        "higher_state_id": selection.higher.state_id,
        "decision_time": selection.local.decision_time,
        "config_checksum": config_hash,
    }


def _state_payload(
    *,
    selection: TemporalSelectionV1,
    scores: dict[str, float | None],
    count: int,
    coverage: float,
    score: float | None,
    classification: tuple[str, str, str, str, tuple[str, ...], tuple[str, ...]],
    versions: tuple[str, str, str, str],
) -> dict[str, Any]:
    local, higher = selection.local, selection.higher
    alignment, divergence, coherence, context, hard, reasons = classification
    registry_version, clock_version, config_version, config_hash = versions
    identity = _alignment_identity(selection, config_hash)
    return {
        "alignment_id": _stable_id("alignment", identity),
        "instrument_id": local.instrument_id,
        "local_scale_id": local.scale_id,
        "higher_scale_id": higher.scale_id,
        "local_timeframe": local.timeframe,
        "higher_timeframe": higher.timeframe,
        "decision_trigger": "CLOSED_LOCAL_BAR",
        "decision_time": local.decision_time,
        "local_state_id": local.state_id,
        "higher_state_id": higher.state_id,
        "local_bar_close_time": local.bar_close_time,
        "higher_bar_close_time": higher.bar_close_time,
        "join_method": "ASOF_BACKWARD",
        "component_alignment_scores": scores,
        "available_component_count": count,
        "weighted_coverage_ratio": coverage,
        "overall_agreement_score": score,
        "alignment_state": alignment,
        "divergence_state": divergence,
        "coherence_state": coherence,
        "combined_context_state": context,
        "hard_mismatch_components": hard,
        "reason_codes": reasons,
        "uncertainty_state": uncertainty_from_coverage(coverage, count),
        "lineage_id": _stable_id("alignment-lineage", identity),
        "scale_registry_version": registry_version,
        "decision_clock_policy_version": clock_version,
        "config_version": config_version,
        "config_checksum": config_hash,
    }


def build_alignment_state(
    local: TimeframeMarketContextStateV1,
    states: Sequence[TimeframeMarketContextStateV1],
    availability: Sequence[ClosedBarAvailabilityV1],
    config: Mapping[str, Any],
    scale_registry: Mapping[str, Any],
    decision_clock: Mapping[str, Any],
    code_commit: str,
) -> MultiTimeframeAlignmentStateV1:
    validate_scale_registry(scale_registry)
    validate_decision_clock(decision_clock)
    config_hash = config_checksum(config)
    selection = select_asof_backward(local, states, availability, config)
    scores = _component_scores(selection.local, selection.higher, config)
    count, coverage, score = compute_weighted_agreement(scores, config)
    classification = classify_alignment(score, scores, config)
    versions = (
        str(scale_registry["schema_version"]),
        str(decision_clock["schema_version"]),
        str(config["config_id"]),
        config_hash,
    )
    payload = _state_payload(
        selection=selection,
        scores=scores,
        count=count,
        coverage=coverage,
        score=score,
        classification=classification,
        versions=versions,
    )
    state = MultiTimeframeAlignmentStateV1(
        **payload,
        code_commit=code_commit,
        output_checksum="0" * 64,
    )
    output_hash = checksum(
        {key: value for key, value in state.to_dict().items() if key != "output_checksum"}
    )
    return replace(state, output_checksum=output_hash)
