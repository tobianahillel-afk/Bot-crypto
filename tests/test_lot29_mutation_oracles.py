from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import (
    MAX_VALIDATOR_STDOUT_BYTES,
    _chain_checksum,
    _parse_artifact_evidence,
    _parse_closure,
    _parse_persisted_state,
    _parse_validator_evidence,
    _validate_artifact_snapshot,
    _validate_audit_and_closure,
    _validate_config,
    _validate_state_checksum,
    _validate_validator_snapshot,
    build_replay_state,
    canonical_checksum,
    file_checksum,
    run_validator,
    run_validators,
    validate_persisted_state,
)
from crypto_quant_bot.market_analysis.v2_replay_audit_models import (
    ArtifactEvidenceV1,
    ReplayValidationError,
    V2DeterministicReplayAuditStateV1,
    ValidatorEvidenceV1,
    _require_git_sha,
    _require_lot_order,
    _require_safety_state,
    _require_sha256,
)
from scripts.run_lot29_v2_deterministic_replay_and_audit import run

CODE_COMMIT = "1" * 40
SHA_A = "a" * 64
SHA_B = "b" * 64


@pytest.fixture()
def oracle_root(tmp_path: Path) -> Path:
    artifacts: list[dict[str, object]] = []
    for lot in range(21, 29):
        relative = f"data/audit/lot_{lot}.json"
        artifacts.append(
            {
                "lot": lot,
                "path": relative,
                "validator": f"scripts/validate_lot{lot}.py",
            }
        )
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "lot": lot,
                    "analysis_only": True,
                    "used_for_decision": False,
                    "trade_allowed": False,
                    "execution_allowed": False,
                    "approved_size": 0,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    config = {
        "schema_version": "v2-deterministic-replay-audit-config-v1",
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "artifacts": artifacts,
        "safety": {
            "analysis_only": True,
            "used_for_decision": False,
            "trade_allowed": False,
            "execution_allowed": False,
            "approved_size": 0,
        },
    }
    config_path = tmp_path / "config/replay/v2_deterministic_replay_audit_v1.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


def _config(root: Path) -> dict[str, Any]:
    return json.loads(
        (root / "config/replay/v2_deterministic_replay_audit_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _documents(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = run(root, CODE_COMMIT, execute_validators=False)
    return (
        copy.deepcopy(result["state"]),
        copy.deepcopy(result["audit"]),
        copy.deepcopy(result["closure"]),
    )


def _rechecksum(state: dict[str, Any]) -> None:
    payload = dict(state)
    payload.pop("output_checksum", None)
    state["output_checksum"] = canonical_checksum(payload)


def test_canonical_checksum_matches_independent_utf8_canonical_json() -> None:
    payload = {"é": "☃", "z": [3, 2, 1], "a": {"false": False, "none": None}}
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    expected = hashlib.sha256(encoded).hexdigest()
    assert canonical_checksum(payload) == expected
    assert canonical_checksum(payload) != hashlib.sha256(repr(payload).encode()).hexdigest()


def test_file_checksum_matches_independent_binary_digest_across_chunks(tmp_path: Path) -> None:
    data = bytes(range(256)) * 700
    path = tmp_path / "binary-evidence.bin"
    path.write_bytes(data)
    assert len(data) > 2 * 65_536
    assert file_checksum(path) == hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize(
    "value",
    ["0" * 63, "0" * 65, "G" + "0" * 63, "A" * 64, "-" * 64],
)
def test_sha256_contract_rejects_every_noncanonical_boundary(value: str) -> None:
    with pytest.raises(ReplayValidationError, match="lowercase sha256"):
        _require_sha256(value, "digest")


def test_sha256_contract_accepts_all_lowercase_hex_digits() -> None:
    _require_sha256("0123456789abcdef" * 4, "digest")


@pytest.mark.parametrize(
    "value",
    ["0" * 39, "0" * 41, "A" * 40, "g" * 40, "-" * 40],
)
def test_git_sha_contract_rejects_every_noncanonical_boundary(value: str) -> None:
    with pytest.raises(ReplayValidationError, match="40-character git sha"):
        _require_git_sha(value)


def test_git_sha_contract_accepts_lowercase_hex() -> None:
    _require_git_sha("0123456789abcdef0123456789abcdef01234567")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"analysis_only": False},
        {"used_for_decision": True},
        {"trade_allowed": True},
        {"execution_allowed": True},
        {"approved_size": -1},
        {"approved_size": 1},
    ],
)
def test_safety_contract_rejects_each_permission_or_size_change(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    values.update(kwargs)
    with pytest.raises(ReplayValidationError):
        _require_safety_state(**values)


def test_lot_order_contract_rejects_duplicates_and_reversal() -> None:
    ordered = tuple(SimpleNamespace(lot=lot) for lot in range(21, 29))
    _require_lot_order(ordered, "evidence")
    with pytest.raises(ReplayValidationError, match="ordered 21..28"):
        _require_lot_order(tuple(reversed(ordered)), "evidence")
    duplicate = list(ordered)
    duplicate[-1] = SimpleNamespace(lot=27)
    with pytest.raises(ReplayValidationError, match="ordered 21..28"):
        _require_lot_order(tuple(duplicate), "evidence")


def test_config_validation_returns_exact_ordered_specs(oracle_root: Path) -> None:
    config = _config(oracle_root)
    specs = _validate_config(config)
    assert isinstance(specs, tuple)
    assert [spec["lot"] for spec in specs] == list(range(21, 29))
    assert [spec["path"] for spec in specs] == [
        f"data/audit/lot_{lot}.json" for lot in range(21, 29)
    ]
    assert [spec["validator"] for spec in specs] == [
        f"scripts/validate_lot{lot}.py" for lot in range(21, 29)
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda cfg: cfg.__setitem__("artifacts", tuple(cfg["artifacts"])),
        lambda cfg: cfg["artifacts"].__setitem__(0, None),
        lambda cfg: cfg["artifacts"][0].__setitem__("lot", 20),
        lambda cfg: cfg["artifacts"][0].__setitem__("lot", "21"),
        lambda cfg: cfg["artifacts"][0].__setitem__("path", "data/auditx/lot21.json"),
        lambda cfg: cfg["artifacts"][0].__setitem__("path", ""),
        lambda cfg: cfg["artifacts"][0].__setitem__("validator", ""),
        lambda cfg: cfg.__setitem__("safety", {**cfg["safety"], "extra": False}),
        lambda cfg: cfg.__setitem__("safety", {"analysis_only": True}),
    ],
)
def test_config_validation_rejects_structural_near_misses(
    oracle_root: Path,
    mutation: object,
) -> None:
    config = _config(oracle_root)
    mutation(config)
    with pytest.raises(ReplayValidationError):
        _validate_config(config)


def test_chain_checksum_matches_independent_order_sensitive_payload(oracle_root: Path) -> None:
    state = build_replay_state(
        oracle_root,
        _config(oracle_root),
        CODE_COMMIT,
        execute_validators=False,
    )
    payload = [
        {
            "lot": item.lot,
            "path": item.artifact_path,
            "artifact_checksum": item.artifact_checksum,
            "embedded_output_checksum": item.embedded_output_checksum,
        }
        for item in state.artifacts
    ]
    assert _chain_checksum(state.artifacts) == canonical_checksum(payload)
    assert _chain_checksum(tuple(reversed(state.artifacts))) != _chain_checksum(state.artifacts)


def test_artifact_parser_preserves_every_field_exactly() -> None:
    raw = [
        {
            "schema_version": "artifact-replay-evidence-v1",
            "lot": lot,
            "artifact_path": f"data/audit/lot_{lot}.json",
            "artifact_checksum": f"{lot - 21:x}" * 64,
            "byte_size": lot * 17,
            "embedded_output_checksum": None if lot == 21 else f"{lot - 20:x}" * 64,
            "validation_state": "VALIDATED",
        }
        for lot in range(21, 29)
    ]
    parsed = _parse_artifact_evidence(raw)
    assert [item.to_dict() for item in parsed] == raw


def test_validator_parser_preserves_every_field_exactly() -> None:
    raw = [
        {
            "schema_version": "validator-replay-evidence-v1",
            "lot": lot,
            "command": ["python", f"scripts/validate_lot{lot}.py"],
            "return_code": 0,
            "status": "PASS",
            "stdout_checksum": f"{lot - 21:x}" * 64,
        }
        for lot in range(21, 29)
    ]
    parsed = _parse_validator_evidence(raw)
    assert [item.to_dict() for item in parsed] == raw


def test_closure_parser_preserves_every_field_exactly() -> None:
    raw = {
        "schema_version": "v2-closure-manifest-v1",
        "lot_sequence": list(range(21, 29)),
        "artifact_checksums": [f"{index:x}" * 64 for index in range(8)],
        "chain_checksum": "f" * 64,
        "validator_count": 8,
        "artifact_count": 8,
        "closure_status": "V2_REPLAY_VALIDATED_OFFLINE_ONLY",
    }
    assert _parse_closure(raw).to_dict() == raw


def test_persisted_state_parser_round_trips_every_field(oracle_root: Path) -> None:
    state, _, _ = _documents(oracle_root)
    parsed = _parse_persisted_state(state, state["output_checksum"])
    assert parsed.to_dict() == state


def test_state_checksum_validation_returns_exact_checksum_and_rejects_missing(
    oracle_root: Path,
) -> None:
    state, _, _ = _documents(oracle_root)
    assert _validate_state_checksum(state) == state["output_checksum"]
    state.pop("output_checksum")
    with pytest.raises(ReplayValidationError, match="checksum mismatch"):
        _validate_state_checksum(state)


@pytest.mark.parametrize(
    "field,replacement",
    [
        ("lot", 22),
        ("artifact_path", "data/audit/other.json"),
        ("artifact_checksum", SHA_B),
        ("byte_size", 999_999),
        ("embedded_output_checksum", SHA_A),
    ],
)
def test_artifact_snapshot_checks_each_observed_field(
    field: str,
    replacement: object,
) -> None:
    persisted = ArtifactEvidenceV1(21, "data/audit/a.json", SHA_A, 10, None, "VALIDATED")
    values = {
        "lot": 21,
        "artifact_path": "data/audit/a.json",
        "artifact_checksum": SHA_A,
        "byte_size": 10,
        "embedded_output_checksum": None,
        "validation_state": "VALIDATED",
    }
    values[field] = replacement
    observed = ArtifactEvidenceV1(**values)
    with pytest.raises(ReplayValidationError, match=field):
        _validate_artifact_snapshot((persisted,), (observed,))


def test_artifact_snapshot_rejects_count_difference() -> None:
    item = ArtifactEvidenceV1(21, "data/audit/a.json", SHA_A, 10, None, "VALIDATED")
    with pytest.raises(ReplayValidationError, match="count mismatch"):
        _validate_artifact_snapshot((item,), ())


@pytest.mark.parametrize(
    "evidence",
    [
        ValidatorEvidenceV1(22, ("python", "scripts/validate_lot21.py"), 0, "PASS", SHA_A),
        ValidatorEvidenceV1(21, ("python", "scripts/validate_lot22.py"), 0, "PASS", SHA_A),
    ],
)
def test_validator_snapshot_rejects_lot_or_command_identity(
    evidence: ValidatorEvidenceV1,
) -> None:
    spec = ({"lot": 21, "validator": "scripts/validate_lot21.py"},)
    with pytest.raises(ReplayValidationError, match="identity mismatch"):
        _validate_validator_snapshot((evidence,), spec)


def test_validator_snapshot_rejects_count_difference() -> None:
    spec = ({"lot": 21, "validator": "scripts/validate_lot21.py"},)
    with pytest.raises(ReplayValidationError, match="count mismatch"):
        _validate_validator_snapshot((), spec)


def test_run_validator_uses_exact_bounded_subprocess_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: tuple[str, str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="OUT", stderr="ERR")

    monkeypatch.setattr("subprocess.run", fake_run)
    evidence = run_validator(tmp_path, 24, "scripts/validate_lot24.py")
    assert captured == {
        "command": ("python", "scripts/validate_lot24.py"),
        "cwd": tmp_path,
        "check": False,
        "capture_output": True,
        "text": True,
        "timeout": 180,
    }
    expected_output = hashlib.sha256(b"OUT\nERR").hexdigest()
    assert evidence.to_dict() == {
        "schema_version": "validator-replay-evidence-v1",
        "lot": 24,
        "command": ["python", "scripts/validate_lot24.py"],
        "return_code": 0,
        "status": "PASS",
        "stdout_checksum": expected_output,
    }


def test_run_validator_accepts_exact_output_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stdout = "x" * (MAX_VALIDATOR_STDOUT_BYTES - 1)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout, stderr=""),
    )
    assert run_validator(tmp_path, 21, "scripts/validate_lot21.py").status == "PASS"


def test_run_validators_preserves_spec_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[int, str]] = []

    def fake(root: Path, lot: int, script: str) -> ValidatorEvidenceV1:
        assert root == tmp_path
        calls.append((lot, script))
        return ValidatorEvidenceV1(lot, ("python", script), 0, "PASS", SHA_A)

    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit.run_validator",
        fake,
    )
    specs = tuple(
        {"lot": lot, "validator": f"scripts/validate_lot{lot}.py"}
        for lot in range(21, 29)
    )
    evidence = run_validators(tmp_path, specs)
    expected = [(lot, f"scripts/validate_lot{lot}.py") for lot in range(21, 29)]
    assert calls == expected
    assert [item.lot for item in evidence] == list(range(21, 29))


@pytest.mark.parametrize(
    "tamper",
    [
        lambda audit, closure: audit.__setitem__("output_checksum", SHA_A),
        lambda audit, closure: audit.__setitem__("chain_checksum", SHA_A),
        lambda audit, closure: audit.__setitem__("replay_status", "MISMATCH"),
        lambda audit, closure: closure.__setitem__("validator_count", 7),
        lambda audit, closure: closure.__setitem__("artifact_count", 7),
        lambda audit, closure: closure.__setitem__("chain_checksum", SHA_A),
    ],
)
def test_audit_and_closure_linkage_rejects_each_mismatch(
    oracle_root: Path,
    tamper: object,
) -> None:
    state, audit, closure = _documents(oracle_root)
    persisted = _parse_persisted_state(state, state["output_checksum"])
    tamper(audit, closure)
    with pytest.raises(ReplayValidationError):
        _validate_audit_and_closure(persisted, audit, closure)


@pytest.mark.parametrize(
    "tamper",
    [
        lambda state, audit, closure: state.__setitem__("runtime_mode", "LIVE"),
        lambda state, audit, closure: state.__setitem__("replay_status", "MISMATCH"),
        lambda state, audit, closure: state.__setitem__("reason_codes", ["BAD"]),
        lambda state, audit, closure: state.__setitem__("analysis_only", False),
        lambda state, audit, closure: state.__setitem__("used_for_decision", True),
        lambda state, audit, closure: state.__setitem__("trade_allowed", True),
        lambda state, audit, closure: state.__setitem__("execution_allowed", True),
        lambda state, audit, closure: state.__setitem__("approved_size", 1),
        lambda state, audit, closure: audit.__setitem__("analysis_only", False),
        lambda state, audit, closure: audit.__setitem__("used_for_decision", True),
        lambda state, audit, closure: audit.__setitem__("trade_allowed", True),
        lambda state, audit, closure: audit.__setitem__("execution_allowed", True),
        lambda state, audit, closure: audit.__setitem__("approved_size", 1),
        lambda state, audit, closure: state["validators"][0].__setitem__("lot", 22),
        lambda state, audit, closure: state["validators"][0].__setitem__(
            "command", ["python", "scripts/validate_lot22.py"]
        ),
        lambda state, audit, closure: state["artifacts"][0].__setitem__("byte_size", 1),
        lambda state, audit, closure: state["artifacts"][0].__setitem__(
            "artifact_path", "data/audit/other.json"
        ),
    ],
)
def test_full_persisted_validation_rejects_each_semantic_tamper(
    oracle_root: Path,
    tamper: object,
) -> None:
    state, audit, closure = _documents(oracle_root)
    tamper(state, audit, closure)
    _rechecksum(state)
    with pytest.raises(ReplayValidationError):
        validate_persisted_state(
            oracle_root,
            _config(oracle_root),
            state,
            audit,
            closure,
        )


def test_full_persisted_validation_returns_exact_summary(oracle_root: Path) -> None:
    state, audit, closure = _documents(oracle_root)
    result = validate_persisted_state(
        oracle_root,
        _config(oracle_root),
        state,
        audit,
        closure,
    )
    assert result == {
        "schema_version": "lot29-validation-v1",
        "status": "PASS",
        "artifact_count": 8,
        "validator_count": 8,
        "chain_checksum": state["closure_manifest"]["chain_checksum"],
        "output_checksum": state["output_checksum"],
        "replay_status": "MATCH",
    }


def test_state_contract_payload_and_checksum_are_exact(oracle_root: Path) -> None:
    state = build_replay_state(
        oracle_root,
        _config(oracle_root),
        CODE_COMMIT,
        execute_validators=False,
    )
    payload = state.payload_without_checksum()
    assert state.output_checksum == canonical_checksum(payload)
    assert state.to_dict() == {**payload, "output_checksum": state.output_checksum}
    reconstructed = V2DeterministicReplayAuditStateV1(
        code_commit=state.code_commit,
        runtime_mode=state.runtime_mode,
        artifacts=state.artifacts,
        validators=state.validators,
        closure_manifest=state.closure_manifest,
        replay_status=state.replay_status,
        reason_codes=state.reason_codes,
        analysis_only=state.analysis_only,
        used_for_decision=state.used_for_decision,
        trade_allowed=state.trade_allowed,
        execution_allowed=state.execution_allowed,
        approved_size=state.approved_size,
        output_checksum=state.output_checksum,
    )
    assert reconstructed == state
