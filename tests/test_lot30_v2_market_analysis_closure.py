from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from crypto_quant_bot.market_analysis.v2_market_analysis_closure import (
    EXPECTED_FUTURE_LOCKS,
    EXPECTED_NEGATIVE_CONTROLS,
    VALIDATOR_COMMAND,
    build_closure_state,
    canonical_checksum,
    file_checksum,
    replay_matches,
    run_lot29_validator,
    run_negative_controls,
    validate_persisted_state,
)
from crypto_quant_bot.market_analysis.v2_market_analysis_closure_models import (
    ClosureValidationError,
    NegativeControlEvidenceV1,
    UpstreamArtifactEvidenceV1,
    V2FinalClosureManifestV1,
    ValidatorReplayEvidenceV1,
)

CODE_COMMIT = "a" * 40
VALIDATOR_CHECKSUM = "b" * 64


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def closure_config() -> dict[str, Any]:
    return {
        "schema_version": "v2-market-analysis-closure-config-v1",
        "version_id": "V2_MARKET_ANALYSIS",
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "future_capabilities_locked": list(EXPECTED_FUTURE_LOCKS),
        "negative_controls": list(EXPECTED_NEGATIVE_CONTROLS),
        "safety": {
            "analysis_only": True,
            "approved_size": 0,
            "execution_allowed": False,
            "order_routing_allowed": False,
            "risk_approval_allowed": False,
            "signal_generation_allowed": False,
            "trade_allowed": False,
            "used_for_decision": False,
        },
        "lot29": {
            "state_path": "data/audit/v2_deterministic_replay_and_audit_lot29.json",
            "audit_path": "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json",
            "closure_path": "data/audit/v2_replay_closure_manifest_lot29.json",
            "lifecycle_path": "data/audit/roadmap_lifecycle_overlay_lot29.json",
            "validator": "scripts/validate_lot29.py",
        },
    }


def validator_replays(checksum: str = VALIDATOR_CHECKSUM) -> tuple[ValidatorReplayEvidenceV1, ...]:
    return (
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", checksum),
        ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", checksum),
    )


def build_fake_repository(root: Path) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    artifact_checksums: list[str] = []
    for lot in range(21, 29):
        embedded = f"{lot:064x}"
        relative = f"data/audit/lot_{lot}_artifact.json"
        payload = {
            "schema_version": f"lot-{lot}-state-v1",
            "output_checksum": embedded,
            "analysis_only": True,
            "used_for_decision": False,
            "trade_allowed": False,
            "execution_allowed": False,
            "approved_size": 0,
        }
        path = root / relative
        write_json(path, payload)
        checksum = file_checksum(path)
        artifact_checksums.append(checksum)
        artifacts.append(
            {
                "schema_version": "artifact-replay-evidence-v1",
                "lot": lot,
                "artifact_path": relative,
                "artifact_checksum": checksum,
                "byte_size": path.stat().st_size,
                "embedded_output_checksum": embedded,
                "validation_state": "VALIDATED",
            }
        )

    closure = {
        "schema_version": "v2-closure-manifest-v1",
        "lot_sequence": list(range(21, 29)),
        "artifact_checksums": artifact_checksums,
        "chain_checksum": "c" * 64,
        "validator_count": 8,
        "artifact_count": 8,
        "closure_status": "V2_REPLAY_VALIDATED_OFFLINE_ONLY",
    }
    state = {
        "schema_version": "v2-deterministic-replay-audit-state-v1",
        "code_commit": "d" * 40,
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "artifacts": artifacts,
        "validators": [],
        "closure_manifest": closure,
        "replay_status": "MATCH",
        "reason_codes": [
            "V2_ARTIFACT_CHAIN_MATCH",
            "V2_VALIDATORS_PASS",
            "V2_OFFLINE_ONLY",
        ],
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    state["output_checksum"] = canonical_checksum(state)
    audit = {
        "schema_version": "v2-deterministic-replay-audit-audit-v1",
        "output_checksum": state["output_checksum"],
        "chain_checksum": closure["chain_checksum"],
        "replay_status": "MATCH",
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    lifecycle = {
        "schema_version": "roadmap-lifecycle-overlay-v1",
        "latest_implemented_lot": 29,
        "lots": {
            "29": {
                "status": "IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY",
                "trade_allowed": False,
                "execution_allowed": False,
            },
            "30": {"implementation_started": False, "status": "PLANNED_LOCKED"},
        },
    }
    write_json(root / closure_config()["lot29"]["state_path"], state)
    write_json(root / closure_config()["lot29"]["audit_path"], audit)
    write_json(root / closure_config()["lot29"]["closure_path"], closure)
    write_json(root / closure_config()["lot29"]["lifecycle_path"], lifecycle)
    return {"state": state, "audit": audit, "closure": closure, "lifecycle": lifecycle}


def build_valid_state(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    build_fake_repository(root)
    state = build_closure_state(
        root,
        closure_config(),
        CODE_COMMIT,
        execute_validator=False,
        validator_evidence=validator_replays(),
    ).to_dict()
    manifest = state["closure_manifest"]
    audit = {
        "schema_version": "v2-market-analysis-closure-audit-v1",
        "output_checksum": state["output_checksum"],
        "final_chain_checksum": manifest["final_chain_checksum"],
        "closure_status": manifest["closure_status"],
        "covered_lot_count": 10,
        "negative_control_count": 5,
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    return state, audit, manifest


def test_build_closure_state_covers_v2_and_remains_fail_closed(tmp_path: Path) -> None:
    build_fake_repository(tmp_path)
    result = build_closure_state(
        tmp_path,
        closure_config(),
        CODE_COMMIT,
        execute_validator=False,
        validator_evidence=validator_replays(),
    )
    payload = result.to_dict()
    assert payload["closure_manifest"]["covered_lot_sequence"] == list(range(21, 31))
    assert payload["closure_manifest"]["closure_status"] == (
        "V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY"
    )
    assert len(payload["upstream_artifacts"]) == 8
    assert len(payload["negative_controls"]) == 5
    assert payload["trade_allowed"] is False
    assert payload["execution_allowed"] is False
    assert payload["approved_size"] == 0


def test_closure_replay_is_deterministic(tmp_path: Path) -> None:
    build_fake_repository(tmp_path)
    first = build_closure_state(
        tmp_path,
        closure_config(),
        CODE_COMMIT,
        execute_validator=False,
        validator_evidence=validator_replays(),
    )
    second = build_closure_state(
        tmp_path,
        closure_config(),
        CODE_COMMIT,
        execute_validator=False,
        validator_evidence=first.validator_replays,
    )
    assert replay_matches(first, second)


def test_validate_persisted_state_rebuilds_exact_closure(tmp_path: Path) -> None:
    state, audit, manifest = build_valid_state(tmp_path)
    result = validate_persisted_state(tmp_path, closure_config(), state, audit, manifest)
    assert result["status"] == "PASS"
    assert result["covered_lot_count"] == 10
    assert result["validator_replay_count"] == 2
    assert result["trade_allowed"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "unsupported"),
        ("version_id", "V3_MARKET_DATA_GOVERNANCE"),
        ("runtime_mode", "LIVE"),
        ("future_capabilities_locked", []),
        ("negative_controls", []),
    ],
)
def test_invalid_config_is_rejected(tmp_path: Path, field: str, value: object) -> None:
    build_fake_repository(tmp_path)
    config = closure_config()
    config[field] = value
    with pytest.raises(ClosureValidationError):
        build_closure_state(
            tmp_path,
            config,
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_non_fail_closed_config_is_rejected(tmp_path: Path) -> None:
    build_fake_repository(tmp_path)
    config = closure_config()
    config["safety"]["trade_allowed"] = True
    with pytest.raises(ClosureValidationError, match="fail-closed"):
        build_closure_state(
            tmp_path,
            config,
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_noncanonical_lot29_registry_is_rejected(tmp_path: Path) -> None:
    build_fake_repository(tmp_path)
    config = closure_config()
    config["lot29"]["validator"] = "scripts/other.py"
    with pytest.raises(ClosureValidationError, match="source registry"):
        build_closure_state(
            tmp_path,
            config,
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_missing_upstream_artifact_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    path = tmp_path / data["state"]["artifacts"][0]["artifact_path"]
    path.unlink()
    with pytest.raises(ClosureValidationError, match="missing"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_changed_upstream_artifact_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    path = tmp_path / data["state"]["artifacts"][0]["artifact_path"]
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ClosureValidationError, match="checksum changed"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_changed_artifact_size_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    state = data["state"]
    state["artifacts"][0]["byte_size"] += 1
    payload = dict(state)
    payload.pop("output_checksum")
    state["output_checksum"] = canonical_checksum(payload)
    write_json(tmp_path / closure_config()["lot29"]["state_path"], state)
    with pytest.raises(ClosureValidationError, match="byte size"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_embedded_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    state = data["state"]
    state["artifacts"][0]["embedded_output_checksum"] = "f" * 64
    payload = dict(state)
    payload.pop("output_checksum")
    state["output_checksum"] = canonical_checksum(payload)
    write_json(tmp_path / closure_config()["lot29"]["state_path"], state)
    with pytest.raises(ClosureValidationError, match="embedded output"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_upstream_order_mismatch_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    state = data["state"]
    state["artifacts"].reverse()
    payload = dict(state)
    payload.pop("output_checksum")
    state["output_checksum"] = canonical_checksum(payload)
    write_json(tmp_path / closure_config()["lot29"]["state_path"], state)
    with pytest.raises(ClosureValidationError, match="ordered"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update({"latest_implemented_lot": 28}), "latest"),
        (
            lambda value: value["lots"]["29"].update({"status": "PLANNED_LOCKED"}),
            "Lot 29 lifecycle",
        ),
        (
            lambda value: value["lots"].update(
                {"30": {"implementation_started": True, "status": "IMPLEMENTATION_STARTED"}}
            ),
            "entry lifecycle",
        ),
    ],
)
def test_invalid_lifecycle_is_rejected(
    tmp_path: Path,
    mutation: Any,
    message: str,
) -> None:
    data = build_fake_repository(tmp_path)
    lifecycle = data["lifecycle"]
    mutation(lifecycle)
    write_json(tmp_path / closure_config()["lot29"]["lifecycle_path"], lifecycle)
    with pytest.raises(ClosureValidationError, match=message):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_lot29_state_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    data["state"]["output_checksum"] = "0" * 64
    write_json(tmp_path / closure_config()["lot29"]["state_path"], data["state"])
    with pytest.raises(ClosureValidationError, match="state checksum"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_lot29_audit_linkage_mismatch_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    data["audit"]["output_checksum"] = "0" * 64
    write_json(tmp_path / closure_config()["lot29"]["audit_path"], data["audit"])
    with pytest.raises(ClosureValidationError, match="audit output"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_lot29_closure_linkage_mismatch_is_rejected(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    data["closure"]["chain_checksum"] = "e" * 64
    write_json(tmp_path / closure_config()["lot29"]["closure_path"], data["closure"])
    with pytest.raises(ClosureValidationError, match="state and closure"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=validator_replays(),
        )


def test_validator_evidence_is_required_when_execution_disabled(tmp_path: Path) -> None:
    build_fake_repository(tmp_path)
    with pytest.raises(ClosureValidationError, match="required"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
        )


def test_divergent_validator_replays_are_rejected(tmp_path: Path) -> None:
    build_fake_repository(tmp_path)
    divergent = (
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", "1" * 64),
        ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", "2" * 64),
    )
    with pytest.raises(ClosureValidationError, match="diverged"):
        build_closure_state(
            tmp_path,
            closure_config(),
            CODE_COMMIT,
            execute_validator=False,
            validator_evidence=divergent,
        )


def test_negative_controls_are_ordered_and_pass(tmp_path: Path) -> None:
    data = build_fake_repository(tmp_path)
    controls = run_negative_controls(
        closure_config(),
        data["lifecycle"],
        data["state"]["artifacts"][0]["artifact_checksum"],
    )
    assert tuple(item.name for item in controls) == EXPECTED_NEGATIVE_CONTROLS
    assert {item.status for item in controls} == {"PASS"}


def test_persisted_state_checksum_tamper_is_rejected(tmp_path: Path) -> None:
    state, audit, manifest = build_valid_state(tmp_path)
    state["output_checksum"] = "0" * 64
    with pytest.raises(ClosureValidationError, match="persisted Lot 30 state checksum"):
        validate_persisted_state(tmp_path, closure_config(), state, audit, manifest)


def test_persisted_manifest_mismatch_is_rejected(tmp_path: Path) -> None:
    state, audit, manifest = build_valid_state(tmp_path)
    manifest = dict(manifest)
    manifest["closure_status"] = "BROKEN"
    with pytest.raises(ClosureValidationError, match="manifest differs"):
        validate_persisted_state(tmp_path, closure_config(), state, audit, manifest)


def test_persisted_audit_mismatch_is_rejected(tmp_path: Path) -> None:
    state, audit, manifest = build_valid_state(tmp_path)
    audit["covered_lot_count"] = 9
    with pytest.raises(ClosureValidationError, match="covered_lot_count"):
        validate_persisted_state(tmp_path, closure_config(), state, audit, manifest)


def test_run_lot29_validator_hashes_bounded_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_market_analysis_closure.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="PASS", stderr=""),
    )
    evidence = run_lot29_validator(Path("."), 1)
    assert evidence.status == "PASS"
    assert evidence.command == VALIDATOR_COMMAND


def test_run_lot29_validator_rejects_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_market_analysis_closure.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="", stderr="failure"),
    )
    with pytest.raises(ClosureValidationError, match="failed"):
        run_lot29_validator(Path("."), 1)


def test_run_lot29_validator_rejects_unbounded_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_market_analysis_closure.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="x" * 1_000_001,
            stderr="",
        ),
    )
    with pytest.raises(ClosureValidationError, match="exceeds"):
        run_lot29_validator(Path("."), 1)


def test_contract_models_reject_invalid_values() -> None:
    with pytest.raises(ClosureValidationError):
        UpstreamArtifactEvidenceV1(20, "data/audit/x.json", "a" * 64, None, 1)
    with pytest.raises(ClosureValidationError):
        ValidatorReplayEvidenceV1(3, VALIDATOR_COMMAND, 0, "PASS", "a" * 64)
    with pytest.raises(ClosureValidationError):
        NegativeControlEvidenceV1("X", "FAIL", "REJECTED")
    with pytest.raises(ClosureValidationError):
        V2FinalClosureManifestV1(
            covered_lot_sequence=tuple(range(21, 30)),
            upstream_lot_sequence=tuple(range(21, 29)),
            direct_validated_lot=29,
            closure_lot=30,
            upstream_artifact_checksums=("a" * 64,) * 8,
            lot29_state_checksum="b" * 64,
            lot29_audit_checksum="c" * 64,
            lot29_closure_checksum="d" * 64,
            validator_stdout_checksum="e" * 64,
            negative_control_count=5,
            final_chain_checksum="f" * 64,
            closure_status="V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
        )
