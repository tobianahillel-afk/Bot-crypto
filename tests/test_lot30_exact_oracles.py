from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_quant_bot.market_analysis.v2_market_analysis_closure import (
    EXPECTED_FUTURE_LOCKS,
    EXPECTED_NEGATIVE_CONTROLS,
    EXPECTED_REASON_CODES,
    VALIDATOR_COMMAND,
    _build_manifest,
    _build_state,
    _divergent_replays,
    _final_chain_checksum,
    _invalid_control_inputs,
    _parse_validator_evidence,
    _persisted_output_checksum,
    _reject_tampered_checksum,
    _resolve_validator_evidence,
    _validate_persisted_manifest,
    _validation_summary,
    canonical_checksum,
    run_lot29_validator,
    run_negative_controls,
)
from crypto_quant_bot.market_analysis.v2_market_analysis_closure_models import (
    ClosureValidationError,
    NegativeControlEvidenceV1,
    UpstreamArtifactEvidenceV1,
    ValidatorReplayEvidenceV1,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
GIT_SHA = "d" * 40


def independent_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def upstream_evidence() -> tuple[UpstreamArtifactEvidenceV1, ...]:
    return tuple(
        UpstreamArtifactEvidenceV1(
            lot=lot,
            artifact_path=f"data/audit/lot_{lot}.json",
            artifact_checksum=f"{lot:064x}",
            embedded_output_checksum=f"{lot + 100:064x}",
            byte_size=lot * 10,
        )
        for lot in range(21, 29)
    )


def validator_evidence() -> tuple[ValidatorReplayEvidenceV1, ...]:
    return (
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", SHA_A),
        ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", SHA_A),
    )


def closure_config() -> dict[str, object]:
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


def lifecycle() -> dict[str, object]:
    return {
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


def test_canonical_checksum_has_independent_exact_oracle() -> None:
    payload = {"z": [3, 2, 1], "a": {"é": True}, "n": None}
    assert canonical_checksum(payload) == independent_checksum(payload)
    assert canonical_checksum(payload) == "f7a39d0a85aa69f0276b1d0d35bafe65463e12b71df60b78253f61437971c62c"


def test_invalid_control_inputs_are_exact_and_do_not_mutate_sources() -> None:
    config = closure_config()
    current_lifecycle = lifecycle()
    config_before = json.loads(json.dumps(config))
    lifecycle_before = json.loads(json.dumps(current_lifecycle))

    wrong_schema, forbidden, unlocked = _invalid_control_inputs(config, current_lifecycle)

    assert wrong_schema == {**config_before, "schema_version": "unsupported"}
    assert forbidden["schema_version"] == "v2-market-analysis-closure-config-v1"
    safety_before = config_before["safety"]
    assert isinstance(safety_before, dict)
    assert forbidden["safety"] == {**safety_before, "trade_allowed": True}
    unlocked_lots = unlocked["lots"]
    lifecycle_lots = lifecycle_before["lots"]
    assert isinstance(unlocked_lots, dict)
    assert isinstance(lifecycle_lots, dict)
    assert unlocked["latest_implemented_lot"] == 29
    assert unlocked_lots["29"] == lifecycle_lots["29"]
    assert unlocked_lots["30"] == {
        "implementation_started": True,
        "status": "IMPLEMENTATION_STARTED",
    }
    assert config == config_before
    assert current_lifecycle == lifecycle_before


def test_divergent_replays_have_exact_canonical_shape() -> None:
    replays = _divergent_replays()
    assert [item.to_dict() for item in replays] == [
        {
            "schema_version": "v2-closure-validator-replay-evidence-v1",
            "run_index": 1,
            "command": ["python", "scripts/validate_lot29.py"],
            "return_code": 0,
            "status": "PASS",
            "stdout_checksum": "1" * 64,
        },
        {
            "schema_version": "v2-closure-validator-replay-evidence-v1",
            "run_index": 2,
            "command": ["python", "scripts/validate_lot29.py"],
            "return_code": 0,
            "status": "PASS",
            "stdout_checksum": "2" * 64,
        },
    ]


def test_tampered_checksum_control_has_exact_boundary() -> None:
    _reject_tampered_checksum("0" * 64)
    for value in ("1" * 64, "0" * 63, ""):
        with pytest.raises(ClosureValidationError, match="tampered checksum rejected"):
            _reject_tampered_checksum(value)


def test_negative_controls_have_exact_order_and_reason_codes() -> None:
    controls = run_negative_controls(closure_config(), lifecycle(), SHA_A)
    assert [item.to_dict() for item in controls] == [
        {
            "schema_version": "v2-closure-negative-control-evidence-v1",
            "name": "SCHEMA_MISMATCH_REJECTED",
            "status": "PASS",
            "reason_code": "UNSUPPORTED_SCHEMA_BLOCKED",
        },
        {
            "schema_version": "v2-closure-negative-control-evidence-v1",
            "name": "UPSTREAM_CHECKSUM_TAMPER_REJECTED",
            "status": "PASS",
            "reason_code": "UPSTREAM_CHECKSUM_MISMATCH_BLOCKED",
        },
        {
            "schema_version": "v2-closure-negative-control-evidence-v1",
            "name": "FORBIDDEN_CAPABILITY_REJECTED",
            "status": "PASS",
            "reason_code": "FORBIDDEN_CAPABILITY_BLOCKED",
        },
        {
            "schema_version": "v2-closure-negative-control-evidence-v1",
            "name": "VALIDATOR_DIVERGENCE_REJECTED",
            "status": "PASS",
            "reason_code": "NON_DETERMINISTIC_VALIDATOR_BLOCKED",
        },
        {
            "schema_version": "v2-closure-negative-control-evidence-v1",
            "name": "LIFECYCLE_UNLOCK_REJECTED",
            "status": "PASS",
            "reason_code": "UNAUTHORIZED_LIFECYCLE_ADVANCE_BLOCKED",
        },
    ]


def test_final_chain_checksum_has_independent_exact_oracle() -> None:
    upstream = upstream_evidence()
    checksums = (SHA_A, SHA_B, SHA_C)
    expected_payload = {
        "upstream": [item.artifact_checksum for item in upstream],
        "lot29_state": SHA_A,
        "lot29_audit": SHA_B,
        "lot29_closure": SHA_C,
        "validator_stdout": "e" * 64,
        "covered_lots": list(range(21, 31)),
    }
    assert _final_chain_checksum(upstream, checksums, "e" * 64) == independent_checksum(
        expected_payload
    )


def test_build_manifest_serializes_every_binding_exactly() -> None:
    upstream = upstream_evidence()
    checksums = (SHA_A, SHA_B, SHA_C)
    manifest = _build_manifest(upstream, checksums, "e" * 64, 5)
    expected_chain = _final_chain_checksum(upstream, checksums, "e" * 64)
    assert manifest.to_dict() == {
        "schema_version": "v2-final-closure-manifest-v1",
        "covered_lot_sequence": list(range(21, 31)),
        "upstream_lot_sequence": list(range(21, 29)),
        "direct_validated_lot": 29,
        "closure_lot": 30,
        "upstream_artifact_checksums": [item.artifact_checksum for item in upstream],
        "lot29_state_checksum": SHA_A,
        "lot29_audit_checksum": SHA_B,
        "lot29_closure_checksum": SHA_C,
        "validator_stdout_checksum": "e" * 64,
        "negative_control_count": 5,
        "final_chain_checksum": expected_chain,
        "closure_status": "V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
    }


def test_build_state_has_exact_policy_and_independent_checksum() -> None:
    upstream = upstream_evidence()
    validators = validator_evidence()
    controls = tuple(
        NegativeControlEvidenceV1(name, "PASS", f"REASON_{index}")
        for index, name in enumerate(EXPECTED_NEGATIVE_CONTROLS)
    )
    manifest = _build_manifest(upstream, (SHA_A, SHA_B, SHA_C), "e" * 64, 5)
    state = _build_state(GIT_SHA, upstream, validators, controls, manifest)
    payload = state.payload_without_checksum()

    assert payload["code_commit"] == GIT_SHA
    assert payload["version_id"] == "V2_MARKET_ANALYSIS"
    assert payload["runtime_mode"] == "LOCAL_OFFLINE_ANALYSIS_ONLY"
    assert payload["reason_codes"] == list(EXPECTED_REASON_CODES)
    assert payload["future_capabilities_locked"] == list(EXPECTED_FUTURE_LOCKS)
    assert payload["analysis_only"] is True
    assert payload["used_for_decision"] is False
    assert payload["signal_generation_allowed"] is False
    assert payload["risk_approval_allowed"] is False
    assert payload["order_routing_allowed"] is False
    assert payload["trade_allowed"] is False
    assert payload["execution_allowed"] is False
    assert payload["approved_size"] == 0
    assert state.output_checksum == independent_checksum(payload)
    assert state.to_dict() == {**payload, "output_checksum": state.output_checksum}


def test_parse_validator_evidence_preserves_all_fields_and_types() -> None:
    raw = [
        {
            "run_index": "1",
            "command": ["python", "scripts/validate_lot29.py"],
            "return_code": "0",
            "status": "PASS",
            "stdout_checksum": SHA_A,
        },
        {
            "run_index": 2,
            "command": ("python", "scripts/validate_lot29.py"),
            "return_code": 0,
            "status": "PASS",
            "stdout_checksum": SHA_A,
        },
    ]
    parsed = _parse_validator_evidence(raw)
    assert parsed == validator_evidence()
    assert [item.to_dict() for item in parsed] == [item.to_dict() for item in validator_evidence()]


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {},
        ["bad"],
        [{"run_index": 1}],
        [
            {
                "run_index": 1,
                "command": ["python", "other.py"],
                "return_code": 0,
                "status": "PASS",
                "stdout_checksum": SHA_A,
            }
        ],
    ],
)
def test_parse_validator_evidence_rejects_every_malformed_shape(raw: object) -> None:
    with pytest.raises((ClosureValidationError, TypeError, ValueError)):
        _parse_validator_evidence(raw)


def test_resolve_validator_evidence_uses_provided_evidence_without_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_market_analysis_closure.run_lot29_validator",
        lambda *_args, **_kwargs: pytest.fail("validator execution must not occur"),
    )
    provided = validator_evidence()
    assert _resolve_validator_evidence(Path("."), True, provided) is provided


def test_resolve_validator_evidence_executes_exactly_two_ordered_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, int]] = []

    def fake(root: Path, run_index: int) -> ValidatorReplayEvidenceV1:
        calls.append((root, run_index))
        return ValidatorReplayEvidenceV1(run_index, VALIDATOR_COMMAND, 0, "PASS", SHA_A)

    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_market_analysis_closure.run_lot29_validator",
        fake,
    )
    root = Path("/tmp/exact-root")
    resolved = _resolve_validator_evidence(root, True, None)
    assert calls == [(root, 1), (root, 2)]
    assert resolved == validator_evidence()


def test_run_lot29_validator_uses_exact_subprocess_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}

    def fake_run(command: tuple[str, ...], **kwargs: object) -> SimpleNamespace:
        observed["command"] = command
        observed.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="PASS", stderr="")

    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_market_analysis_closure.subprocess.run",
        fake_run,
    )
    root = Path("/tmp/repository")
    evidence = run_lot29_validator(root, 2)
    expected_stdout = hashlib.sha256(b"PASS\n").hexdigest()

    assert observed == {
        "command": VALIDATOR_COMMAND,
        "cwd": root,
        "check": False,
        "capture_output": True,
        "text": True,
        "timeout": 240,
    }
    assert evidence.to_dict() == {
        "schema_version": "v2-closure-validator-replay-evidence-v1",
        "run_index": 2,
        "command": ["python", "scripts/validate_lot29.py"],
        "return_code": 0,
        "status": "PASS",
        "stdout_checksum": expected_stdout,
    }


def test_persisted_output_checksum_returns_exact_checksum() -> None:
    payload = {"schema_version": "state-v1", "value": [1, 2, 3]}
    checksum = independent_checksum(payload)
    assert _persisted_output_checksum({**payload, "output_checksum": checksum}) == checksum
    with pytest.raises(ClosureValidationError, match="persisted Lot 30 state checksum mismatch"):
        _persisted_output_checksum(payload)


def test_persisted_manifest_requires_complete_equality() -> None:
    manifest = {"closure_status": "V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY", "count": 10}
    _validate_persisted_manifest({"closure_manifest": manifest}, dict(manifest))
    for changed in (
        {"closure_status": "BROKEN", "count": 10},
        {"closure_status": "V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY"},
        {**manifest, "extra": True},
    ):
        with pytest.raises(ClosureValidationError, match="manifest differs"):
            _validate_persisted_manifest({"closure_manifest": manifest}, changed)


def test_validation_summary_is_exact_and_fail_closed() -> None:
    manifest = {
        "closure_status": "V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
        "final_chain_checksum": SHA_C,
    }
    assert _validation_summary(manifest, SHA_A) == {
        "schema_version": "lot30-validation-v1",
        "status": "PASS",
        "closure_status": "V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
        "covered_lot_count": 10,
        "upstream_artifact_count": 8,
        "validator_replay_count": 2,
        "negative_control_count": 5,
        "final_chain_checksum": SHA_C,
        "output_checksum": SHA_A,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
