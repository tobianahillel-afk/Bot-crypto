from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from crypto_quant_bot.contracts.decision_evidence import (
    DecisionEvidenceEnvelopeV1,
    EvidenceReferenceV1,
    UncertaintyEnvelopeV1,
)
from crypto_quant_bot.contracts.timeframe_alignment import (
    MultiTimeframeAlignmentStateV1,
    TimeframeMarketContextStateV1,
)
from crypto_quant_bot.market_analysis.alignment_common import Lot26ValidationError, checksum

_FORBIDDEN_KEYS = {
    "forecast",
    "forecast_horizon",
    "probability",
    "expected_return",
    "signal",
    "side",
    "quantity",
    "order",
    "position",
    "stop_loss",
    "take_profit",
}


def assert_no_forbidden_capabilities(payload: object) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise Lot26ValidationError(f"MTF_FORECAST_FIELD_FORBIDDEN:{key}")
            assert_no_forbidden_capabilities(value)
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        for value in payload:
            assert_no_forbidden_capabilities(value)


def _evidence_reference(state: TimeframeMarketContextStateV1) -> EvidenceReferenceV1:
    return EvidenceReferenceV1(
        evidence_id=state.state_id,
        evidence_type=state.schema_version,
        checksum=checksum(state.to_dict()),
        available_at=state.available_at,
    )


def _uncertainty(state: str) -> UncertaintyEnvelopeV1:
    value = {"LOW": 0.0, "MODERATE": 0.5, "HIGH": 1.0, "UNKNOWN": None}[state]
    return UncertaintyEnvelopeV1(data=value, model=None, calibration=None, execution=None)


def _identity_fields(
    alignment: MultiTimeframeAlignmentStateV1,
    local: TimeframeMarketContextStateV1,
    run_id: str,
    replay_id: str | None,
) -> dict[str, Any]:
    identity = checksum({"alignment": alignment.to_dict(), "run_id": run_id, "replay_id": replay_id})
    return {
        "decision_id": str(uuid5(NAMESPACE_URL, f"lot26:evidence:{identity}")),
        "parent_decision_ids": (),
        "run_id": run_id,
        "correlation_id": alignment.alignment_id,
        "replay_id": replay_id,
        "event_time": local.bar_close_time,
        "decision_time": alignment.decision_time,
        "generated_at": alignment.decision_time,
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "instrument_id": alignment.instrument_id,
    }


def _traceability_fields(
    alignment: MultiTimeframeAlignmentStateV1,
    local: TimeframeMarketContextStateV1,
    higher: TimeframeMarketContextStateV1,
) -> dict[str, Any]:
    return {
        "venue_id": None,
        "data_snapshot_id": alignment.lineage_id,
        "data_quality_state_id": local.validation_state,
        "feature_set_id": None,
        "market_context_id": alignment.alignment_id,
        "scenario_set_id": None,
        "strategy_id": None,
        "strategy_version": None,
        "model_versions": {},
        "calibration_version": None,
        "risk_state_id": None,
        "risk_decision_id": None,
        "config_version": alignment.config_version,
        "code_commit": alignment.code_commit,
        "input_checksums": {
            "local_state": checksum(local.to_dict()),
            "higher_state": checksum(higher.to_dict()),
            "alignment_config": alignment.config_checksum,
        },
        "output_checksum": alignment.output_checksum,
    }


def _explanation_fields(
    alignment: MultiTimeframeAlignmentStateV1,
    local: TimeframeMarketContextStateV1,
    higher: TimeframeMarketContextStateV1,
) -> dict[str, Any]:
    features = tuple(
        f"{component}={score}"
        for component, score in sorted(alignment.component_alignment_scores.items())
    )
    return {
        "decision_state": "NOT_APPLICABLE",
        "reason_codes": alignment.reason_codes,
        "veto_codes": (),
        "uncertainty": _uncertainty(alignment.uncertainty_state),
        "human_approval_id": None,
        "facts_observed": (
            f"local_state={local.state_id}",
            f"higher_state={higher.state_id}",
            "join_method=ASOF_BACKWARD",
            f"weighted_coverage_ratio={alignment.weighted_coverage_ratio}",
        ),
        "features_computed": features,
        "inferences": (
            f"alignment_state={alignment.alignment_state}",
            f"divergence_state={alignment.divergence_state}",
            f"coherence_state={alignment.coherence_state}",
        ),
        "assumptions": ("agreement_score_is_descriptive_not_predictive",),
        "supporting_evidence": (_evidence_reference(local), _evidence_reference(higher)),
        "contradicting_evidence": (),
        "rules_triggered": ("LOT26_CLOSED_BAR_ASOF_BACKWARD", "LOT26_WEIGHTED_ALIGNMENT_V1"),
        "final_consequence": "DESCRIPTIVE_ALIGNMENT_ONLY_NO_TRADING",
    }


def build_alignment_evidence(
    alignment: MultiTimeframeAlignmentStateV1,
    local: TimeframeMarketContextStateV1,
    higher: TimeframeMarketContextStateV1,
    *,
    run_id: str,
    replay_id: str | None = None,
) -> DecisionEvidenceEnvelopeV1:
    assert_no_forbidden_capabilities(alignment.to_dict())
    fields = _identity_fields(alignment, local, run_id, replay_id)
    fields.update(_traceability_fields(alignment, local, higher))
    fields.update(_explanation_fields(alignment, local, higher))
    return DecisionEvidenceEnvelopeV1(**fields)


def replay_matches(
    first: MultiTimeframeAlignmentStateV1,
    second: MultiTimeframeAlignmentStateV1,
) -> bool:
    return first.to_dict() == second.to_dict() and first.output_checksum == second.output_checksum
