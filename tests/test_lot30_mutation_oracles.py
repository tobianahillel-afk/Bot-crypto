from __future__ import annotations

import pytest

from crypto_quant_bot.market_analysis.v2_market_analysis_closure import VALIDATOR_COMMAND
from crypto_quant_bot.market_analysis.v2_market_analysis_closure_models import (
    ClosureValidationError,
    NegativeControlEvidenceV1,
    UpstreamArtifactEvidenceV1,
    V2FinalClosureManifestV1,
    V2MarketAnalysisClosureStateV1,
    ValidatorReplayEvidenceV1,
)

SHA = "a" * 64


def upstream() -> tuple[UpstreamArtifactEvidenceV1, ...]:
    return tuple(
        UpstreamArtifactEvidenceV1(
            lot=lot,
            artifact_path=f"data/audit/lot_{lot}.json",
            artifact_checksum=f"{lot:064x}",
            embedded_output_checksum=None,
            byte_size=lot,
        )
        for lot in range(21, 29)
    )


def replays() -> tuple[ValidatorReplayEvidenceV1, ...]:
    return (
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", SHA),
        ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", SHA),
    )


def manifest() -> V2FinalClosureManifestV1:
    return V2FinalClosureManifestV1(
        covered_lot_sequence=tuple(range(21, 31)),
        upstream_lot_sequence=tuple(range(21, 29)),
        direct_validated_lot=29,
        closure_lot=30,
        upstream_artifact_checksums=tuple(item.artifact_checksum for item in upstream()),
        lot29_state_checksum="b" * 64,
        lot29_audit_checksum="c" * 64,
        lot29_closure_checksum="d" * 64,
        validator_stdout_checksum=SHA,
        negative_control_count=5,
        final_chain_checksum="e" * 64,
        closure_status="V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
    )


def controls() -> tuple[NegativeControlEvidenceV1, ...]:
    return tuple(
        NegativeControlEvidenceV1(name=f"CONTROL_{index}", status="PASS", reason_code=f"R{index}")
        for index in range(5)
    )


def state(**overrides: object) -> V2MarketAnalysisClosureStateV1:
    values: dict[str, object] = {
        "code_commit": "f" * 40,
        "version_id": "V2_MARKET_ANALYSIS",
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "upstream_artifacts": upstream(),
        "validator_replays": replays(),
        "negative_controls": controls(),
        "closure_manifest": manifest(),
        "reason_codes": (
            "V2_LOTS_21_30_COVERED",
            "V2_REPLAY_CHAIN_MATCH",
            "V2_NEGATIVE_CONTROLS_PASS",
            "V3_CAPABILITIES_LOCKED",
            "V2_OFFLINE_ONLY",
        ),
        "future_capabilities_locked": (
            "ContinuousMarketStateV1",
            "MultiHorizonForecastV1",
            "ParticipantBehaviorScenarioV1",
            "TradeIntent",
            "RiskDecisionV1",
            "RiskReservationV1",
            "OrderIntent",
        ),
        "analysis_only": True,
        "used_for_decision": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        "output_checksum": "9" * 64,
    }
    values.update(overrides)
    return V2MarketAnalysisClosureStateV1(**values)  # type: ignore[arg-type]


def test_valid_state_oracle() -> None:
    result = state()
    assert result.analysis_only is True
    assert result.trade_allowed is False
    assert result.execution_allowed is False
    assert result.approved_size == 0
    assert result.closure_manifest.covered_lot_sequence == tuple(range(21, 31))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("analysis_only", False),
        ("used_for_decision", True),
        ("signal_generation_allowed", True),
        ("risk_approval_allowed", True),
        ("order_routing_allowed", True),
        ("trade_allowed", True),
        ("execution_allowed", True),
        ("approved_size", 1),
        ("runtime_mode", "LIVE"),
        ("version_id", "V3_MARKET_DATA_GOVERNANCE"),
    ],
)
def test_every_permission_and_identity_mutation_is_rejected(field: str, value: object) -> None:
    with pytest.raises(ClosureValidationError):
        state(**{field: value})


def test_validator_replay_checksum_divergence_is_rejected() -> None:
    divergent = (
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", "1" * 64),
        ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", "2" * 64),
    )
    with pytest.raises(ClosureValidationError, match="outputs must match"):
        state(validator_replays=divergent)


def test_reason_code_order_is_not_interchangeable() -> None:
    with pytest.raises(ClosureValidationError, match="reason code"):
        state(
            reason_codes=(
                "V2_REPLAY_CHAIN_MATCH",
                "V2_LOTS_21_30_COVERED",
                "V2_NEGATIVE_CONTROLS_PASS",
                "V3_CAPABILITIES_LOCKED",
                "V2_OFFLINE_ONLY",
            )
        )


def test_future_lock_set_cannot_be_reduced() -> None:
    with pytest.raises(ClosureValidationError, match="lock set"):
        state(future_capabilities_locked=("ContinuousMarketStateV1",))


def test_manifest_requires_all_ten_lots() -> None:
    with pytest.raises(ClosureValidationError, match="21..30"):
        V2FinalClosureManifestV1(
            covered_lot_sequence=tuple(range(21, 30)),
            upstream_lot_sequence=tuple(range(21, 29)),
            direct_validated_lot=29,
            closure_lot=30,
            upstream_artifact_checksums=(SHA,) * 8,
            lot29_state_checksum=SHA,
            lot29_audit_checksum=SHA,
            lot29_closure_checksum=SHA,
            validator_stdout_checksum=SHA,
            negative_control_count=5,
            final_chain_checksum=SHA,
            closure_status="V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
        )


def test_manifest_requires_five_negative_controls() -> None:
    with pytest.raises(ClosureValidationError, match="five negative"):
        V2FinalClosureManifestV1(
            covered_lot_sequence=tuple(range(21, 31)),
            upstream_lot_sequence=tuple(range(21, 29)),
            direct_validated_lot=29,
            closure_lot=30,
            upstream_artifact_checksums=(SHA,) * 8,
            lot29_state_checksum=SHA,
            lot29_audit_checksum=SHA,
            lot29_closure_checksum=SHA,
            validator_stdout_checksum=SHA,
            negative_control_count=4,
            final_chain_checksum=SHA,
            closure_status="V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
        )
