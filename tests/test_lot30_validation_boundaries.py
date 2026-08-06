from __future__ import annotations

import pytest

from crypto_quant_bot.market_analysis.v2_market_analysis_closure import (
    VALIDATOR_COMMAND,
    _require_list_of_objects,
    _require_object,
    _validate_historical_artifact_safety,
    _validate_lifecycle,
    _validate_strict_fail_closed_document,
)
from crypto_quant_bot.market_analysis.v2_market_analysis_closure_models import (
    ClosureValidationError,
    NegativeControlEvidenceV1,
    UpstreamArtifactEvidenceV1,
    V2FinalClosureManifestV1,
    V2MarketAnalysisClosureStateV1,
    ValidatorReplayEvidenceV1,
    require_git_sha,
    require_sha256,
)

SHA = "a" * 64
GIT_SHA = "b" * 40


def valid_upstream() -> tuple[UpstreamArtifactEvidenceV1, ...]:
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


def valid_replays() -> tuple[ValidatorReplayEvidenceV1, ...]:
    return (
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", SHA),
        ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", SHA),
    )


def valid_controls() -> tuple[NegativeControlEvidenceV1, ...]:
    return tuple(
        NegativeControlEvidenceV1(f"CONTROL_{index}", "PASS", f"REASON_{index}")
        for index in range(5)
    )


def valid_manifest() -> V2FinalClosureManifestV1:
    return V2FinalClosureManifestV1(
        covered_lot_sequence=tuple(range(21, 31)),
        upstream_lot_sequence=tuple(range(21, 29)),
        direct_validated_lot=29,
        closure_lot=30,
        upstream_artifact_checksums=tuple(item.artifact_checksum for item in valid_upstream()),
        lot29_state_checksum="1" * 64,
        lot29_audit_checksum="2" * 64,
        lot29_closure_checksum="3" * 64,
        validator_stdout_checksum=SHA,
        negative_control_count=5,
        final_chain_checksum="4" * 64,
        closure_status="V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
    )


def valid_state(**overrides: object) -> V2MarketAnalysisClosureStateV1:
    values: dict[str, object] = {
        "code_commit": GIT_SHA,
        "version_id": "V2_MARKET_ANALYSIS",
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "upstream_artifacts": valid_upstream(),
        "validator_replays": valid_replays(),
        "negative_controls": valid_controls(),
        "closure_manifest": valid_manifest(),
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
        "output_checksum": "5" * 64,
    }
    values.update(overrides)
    return V2MarketAnalysisClosureStateV1(**values)  # type: ignore[arg-type]


def test_object_boundaries_reject_non_objects() -> None:
    with pytest.raises(ClosureValidationError, match="must be an object"):
        _require_object([], "value")
    with pytest.raises(ClosureValidationError, match="list of objects"):
        _require_list_of_objects({}, "items")
    with pytest.raises(ClosureValidationError, match="list of objects"):
        _require_list_of_objects([{} , "bad"], "items")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("analysis_only", False),
        ("used_for_decision", True),
        ("trade_allowed", True),
        ("execution_allowed", True),
        ("approved_size", 1),
    ],
)
def test_strict_documents_reject_safety_changes(field: str, value: object) -> None:
    document: dict[str, object] = {
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    document[field] = value
    with pytest.raises(ClosureValidationError, match="safety mismatch"):
        _validate_strict_fail_closed_document(document, "state")


@pytest.mark.parametrize(
    "field",
    ["signal_generation_allowed", "risk_approval_allowed", "order_routing_allowed"],
)
def test_strict_documents_reject_present_forbidden_permissions(field: str) -> None:
    document = {
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        field: True,
    }
    with pytest.raises(ClosureValidationError, match="enables forbidden"):
        _validate_strict_fail_closed_document(document, "state")


@pytest.mark.parametrize(
    "field",
    [
        "used_for_decision",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    ],
)
def test_historical_artifacts_reject_explicit_permissions(field: str) -> None:
    with pytest.raises(ClosureValidationError, match="enables forbidden"):
        _validate_historical_artifact_safety({field: True}, 21)


def test_historical_artifacts_reject_nonzero_size_and_nonanalysis() -> None:
    with pytest.raises(ClosureValidationError, match="approved_size"):
        _validate_historical_artifact_safety({"approved_size": 1}, 21)
    with pytest.raises(ClosureValidationError, match="analysis_only"):
        _validate_historical_artifact_safety({"analysis_only": False}, 21)
    _validate_historical_artifact_safety({}, 21)


def test_lifecycle_rejects_lot29_permission() -> None:
    lifecycle = {
        "latest_implemented_lot": 29,
        "lots": {
            "29": {
                "status": "IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY",
                "trade_allowed": True,
                "execution_allowed": False,
            },
            "30": {"implementation_started": False, "status": "PLANNED_LOCKED"},
        },
    }
    with pytest.raises(ClosureValidationError, match="enables trading"):
        _validate_lifecycle(lifecycle)


@pytest.mark.parametrize("value", ["a" * 63, "A" * 64, "g" * 64])
def test_sha256_contract_is_strict(value: str) -> None:
    with pytest.raises(ClosureValidationError, match="sha256"):
        require_sha256(value, "checksum")


@pytest.mark.parametrize("value", ["b" * 39, "B" * 40, "z" * 40])
def test_git_sha_contract_is_strict(value: str) -> None:
    with pytest.raises(ClosureValidationError, match="git sha"):
        require_git_sha(value)


def test_upstream_contract_rejects_path_checksum_and_size() -> None:
    with pytest.raises(ClosureValidationError, match="data/audit"):
        UpstreamArtifactEvidenceV1(21, "tmp/a.json", SHA, None, 1)
    with pytest.raises(ClosureValidationError, match="sha256"):
        UpstreamArtifactEvidenceV1(21, "data/audit/a.json", "bad", None, 1)
    with pytest.raises(ClosureValidationError, match="embedded_output_checksum"):
        UpstreamArtifactEvidenceV1(21, "data/audit/a.json", SHA, "bad", 1)
    with pytest.raises(ClosureValidationError, match="positive"):
        UpstreamArtifactEvidenceV1(21, "data/audit/a.json", SHA, None, 0)


def test_validator_contract_rejects_command_result_and_checksum() -> None:
    with pytest.raises(ClosureValidationError, match="canonical"):
        ValidatorReplayEvidenceV1(1, ("python", "other.py"), 0, "PASS", SHA)
    with pytest.raises(ClosureValidationError, match="must be PASS"):
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 1, "FAIL", SHA)
    with pytest.raises(ClosureValidationError, match="sha256"):
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", "bad")


def test_negative_control_identity_is_required() -> None:
    with pytest.raises(ClosureValidationError, match="identity"):
        NegativeControlEvidenceV1("", "PASS", "REASON")
    with pytest.raises(ClosureValidationError, match="identity"):
        NegativeControlEvidenceV1("CONTROL", "PASS", "")


def test_manifest_rejects_sequence_owner_count_checksum_and_status() -> None:
    base = valid_manifest()
    values = base.to_dict()
    values.pop("schema_version")

    with pytest.raises(ClosureValidationError, match="21..28"):
        V2FinalClosureManifestV1(**{**values, "upstream_lot_sequence": (21,)})
    with pytest.raises(ClosureValidationError, match="direct input"):
        V2FinalClosureManifestV1(**{**values, "direct_validated_lot": 28})
    with pytest.raises(ClosureValidationError, match="eight upstream"):
        V2FinalClosureManifestV1(**{**values, "upstream_artifact_checksums": (SHA,)})
    with pytest.raises(ClosureValidationError, match="sha256"):
        V2FinalClosureManifestV1(**{**values, "final_chain_checksum": "bad"})
    with pytest.raises(ClosureValidationError, match="unexpected V2"):
        V2FinalClosureManifestV1(**{**values, "closure_status": "OPEN"})


def test_state_rejects_upstream_order_validator_order_and_control_count() -> None:
    reversed_upstream = tuple(reversed(valid_upstream()))
    with pytest.raises(ClosureValidationError, match="upstream artifacts"):
        valid_state(upstream_artifacts=reversed_upstream)
    reversed_replays = tuple(reversed(valid_replays()))
    with pytest.raises(ClosureValidationError, match="ordered validator"):
        valid_state(validator_replays=reversed_replays)
    with pytest.raises(ClosureValidationError, match="all five"):
        valid_state(negative_controls=valid_controls()[:4])


def test_state_payload_serialization_preserves_fail_closed_values() -> None:
    state = valid_state()
    payload = state.payload_without_checksum()
    assert payload["analysis_only"] is True
    assert payload["trade_allowed"] is False
    assert payload["execution_allowed"] is False
    assert payload["approved_size"] == 0
    assert state.to_dict()["output_checksum"] == "5" * 64
