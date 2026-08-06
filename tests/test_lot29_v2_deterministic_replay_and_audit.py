from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import (
    build_replay_state,
    canonical_checksum,
    file_checksum,
    _parse_artifact_evidence,
    _parse_validator_evidence,
    _validate_artifact_snapshot,
    _validate_safety_documents,
    _validate_validator_snapshot,
    replay_matches,
    run_validator,
    validate_persisted_state,
)
from crypto_quant_bot.market_analysis.v2_replay_audit_models import (
    ArtifactEvidenceV1,
    ClosureManifestV1,
    ReplayValidationError,
    ValidatorEvidenceV1,
)
from scripts.run_lot29_v2_deterministic_replay_and_audit import run

CODE_COMMIT = "a" * 40


@pytest.fixture()
def replay_root(tmp_path: Path) -> Path:
    config = {
        "schema_version": "v2-deterministic-replay-audit-config-v1",
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "artifacts": [],
        "safety": {
            "analysis_only": True,
            "used_for_decision": False,
            "trade_allowed": False,
            "execution_allowed": False,
            "approved_size": 0,
        },
    }
    for lot in range(21, 29):
        path = f"data/audit/lot_{lot}.json"
        config["artifacts"].append(
            {
                "lot": lot,
                "path": path,
                "validator": f"scripts/validate_lot{lot}.py",
            }
        )
        target = tmp_path / path
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
    config_path = tmp_path / "config/replay/v2_deterministic_replay_audit_v1.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


def load_config(root: Path) -> dict[str, object]:
    return json.loads(
        (root / "config/replay/v2_deterministic_replay_audit_v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_canonical_checksum_is_order_independent() -> None:
    assert canonical_checksum({"a": 1, "b": 2}) == canonical_checksum({"b": 2, "a": 1})


def test_file_checksum_changes_with_content(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text("one", encoding="utf-8")
    first = file_checksum(path)
    path.write_text("two", encoding="utf-8")
    assert file_checksum(path) != first


def test_build_replay_state_is_deterministic(replay_root: Path) -> None:
    config = load_config(replay_root)
    first = build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)
    second = build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)
    assert replay_matches(first, second)
    assert first.closure_manifest.lot_sequence == tuple(range(21, 29))
    assert first.replay_status == "MATCH"
    assert first.trade_allowed is False
    assert first.execution_allowed is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("used_for_decision", True),
        ("trade_allowed", True),
        ("execution_allowed", True),
        ("approved_size", 1),
        ("analysis_only", False),
    ],
)
def test_artifact_safety_violations_fail_closed(
    replay_root: Path,
    field: str,
    value: object,
) -> None:
    config = load_config(replay_root)
    target = replay_root / "data/audit/lot_24.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload[field] = value
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ReplayValidationError, match="lot 24"):
        build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda cfg: cfg.__setitem__("schema_version", "bad"),
        lambda cfg: cfg.__setitem__("runtime_mode", "LIVE"),
        lambda cfg: cfg.__setitem__("artifacts", "bad"),
        lambda cfg: cfg["artifacts"].reverse(),
        lambda cfg: cfg["artifacts"][1].__setitem__("path", cfg["artifacts"][0]["path"]),
        lambda cfg: cfg["artifacts"][0].__setitem__("path", "outside.json"),
        lambda cfg: cfg["artifacts"][0].__setitem__("validator", "scripts/not_canonical.py"),
        lambda cfg: cfg["safety"].__setitem__("trade_allowed", True),
    ],
)
def test_invalid_config_is_rejected(replay_root: Path, mutation: object) -> None:
    config = load_config(replay_root)
    mutation(config)
    with pytest.raises(ReplayValidationError):
        build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)


def test_non_object_artifact_is_rejected(replay_root: Path) -> None:
    config = load_config(replay_root)
    (replay_root / "data/audit/lot_21.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ReplayValidationError, match="JSON object"):
        build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)


def test_missing_artifact_is_rejected(replay_root: Path) -> None:
    config = load_config(replay_root)
    (replay_root / "data/audit/lot_28.json").unlink()
    with pytest.raises(FileNotFoundError):
        build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)


def test_embedded_checksum_must_be_text(replay_root: Path) -> None:
    config = load_config(replay_root)
    target = replay_root / "data/audit/lot_25.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["output_checksum"] = 123
    target.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ReplayValidationError, match="output_checksum"):
        build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)


def test_run_validator_captures_pass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="PASS", stderr=""),
    )
    evidence = run_validator(tmp_path, 21, "scripts/validate_lot21.py")
    assert evidence.status == "PASS"
    assert evidence.return_code == 0


def test_run_validator_rejects_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="", stderr="failed"),
    )
    with pytest.raises(ReplayValidationError, match="rc=2"):
        run_validator(tmp_path, 21, "scripts/validate_lot21.py")


def test_run_validator_rejects_oversized_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="x" * 1_000_001,
            stderr="",
        ),
    )
    with pytest.raises(ReplayValidationError, match="exceeds limit"):
        run_validator(tmp_path, 21, "scripts/validate_lot21.py")


def test_runner_writes_replay_evidence(replay_root: Path) -> None:
    result = run(replay_root, CODE_COMMIT, execute_validators=False)
    assert result["state"]["replay_status"] == "MATCH"
    assert result["audit"]["artifact_count"] == 8
    assert result["closure"]["closure_status"] == "V2_REPLAY_VALIDATED_OFFLINE_ONLY"
    assert (replay_root / "reports/lot_29_v2_deterministic_replay_and_audit_report.md").is_file()


def test_validate_persisted_state_passes(replay_root: Path) -> None:
    result = run(replay_root, CODE_COMMIT, execute_validators=False)
    validation = validate_persisted_state(
        replay_root,
        load_config(replay_root),
        result["state"],
        result["audit"],
        result["closure"],
    )
    assert validation["status"] == "PASS"
    assert validation["artifact_count"] == 8


@pytest.mark.parametrize(
    "tamper",
    [
        lambda state, audit, closure: state.__setitem__("trade_allowed", True),
        lambda state, audit, closure: audit.__setitem__("output_checksum", "0" * 64),
        lambda state, audit, closure: audit.__setitem__("chain_checksum", "0" * 64),
        lambda state, audit, closure: audit.__setitem__("replay_status", "MISMATCH"),
        lambda state, audit, closure: closure.__setitem__("chain_checksum", "0" * 64),
        lambda state, audit, closure: state["artifacts"][0].__setitem__(
            "artifact_checksum", "0" * 64
        ),
    ],
)
def test_persisted_tampering_is_rejected(
    replay_root: Path,
    tamper: object,
) -> None:
    result = run(replay_root, CODE_COMMIT, execute_validators=False)
    state = copy.deepcopy(result["state"])
    audit = copy.deepcopy(result["audit"])
    closure = copy.deepcopy(result["closure"])
    tamper(state, audit, closure)
    if state != result["state"]:
        payload = dict(state)
        payload.pop("output_checksum", None)
        state["output_checksum"] = canonical_checksum(payload)
    with pytest.raises(ReplayValidationError):
        validate_persisted_state(
            replay_root,
            load_config(replay_root),
            state,
            audit,
            closure,
        )


def test_artifact_evidence_contract_rejects_bad_checksum() -> None:
    with pytest.raises(ReplayValidationError, match="sha256"):
        ArtifactEvidenceV1(21, "data/audit/a.json", "bad", 1, None, "VALIDATED")


def test_validator_evidence_contract_rejects_failure() -> None:
    with pytest.raises(ReplayValidationError, match="PASS"):
        ValidatorEvidenceV1(21, ("python", "x.py"), 1, "FAIL", "0" * 64)


def test_closure_contract_rejects_wrong_sequence() -> None:
    with pytest.raises(ReplayValidationError, match="21..28"):
        ClosureManifestV1(
            lot_sequence=(21,),
            artifact_checksums=("0" * 64,),
            chain_checksum="0" * 64,
            validator_count=8,
            artifact_count=8,
            closure_status="V2_REPLAY_VALIDATED_OFFLINE_ONLY",
        )


def test_config_rejects_non_object_artifact_spec(replay_root: Path) -> None:
    config = load_config(replay_root)
    config["artifacts"][0] = "bad"
    with pytest.raises(ReplayValidationError, match="objects"):
        build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)


def test_run_validators_path_is_used(
    replay_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_config(replay_root)

    def fake_run_validator(root: Path, lot: int, script_path: str) -> ValidatorEvidenceV1:
        return ValidatorEvidenceV1(
            lot=lot,
            command=("python", script_path),
            return_code=0,
            status="PASS",
            stdout_checksum="1" * 64,
        )

    monkeypatch.setattr(
        "crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit.run_validator",
        fake_run_validator,
    )
    state = build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=True)
    assert len(state.validators) == 8


@pytest.mark.parametrize(
    "kwargs",
    [
        {"lot": 20},
        {"artifact_path": "outside.json"},
        {"byte_size": 0},
        {"embedded_output_checksum": "bad"},
        {"validation_state": "FAIL"},
    ],
)
def test_artifact_evidence_contract_rejects_invalid_fields(kwargs: dict[str, object]) -> None:
    values = {
        "lot": 21,
        "artifact_path": "data/audit/a.json",
        "artifact_checksum": "0" * 64,
        "byte_size": 1,
        "embedded_output_checksum": None,
        "validation_state": "VALIDATED",
    }
    values.update(kwargs)
    with pytest.raises(ReplayValidationError):
        ArtifactEvidenceV1(**values)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"lot": 29},
        {"command": ()},
        {"stdout_checksum": "bad"},
    ],
)
def test_validator_evidence_contract_rejects_invalid_fields(
    kwargs: dict[str, object],
) -> None:
    values = {
        "lot": 21,
        "command": ("python", "x.py"),
        "return_code": 0,
        "status": "PASS",
        "stdout_checksum": "0" * 64,
    }
    values.update(kwargs)
    with pytest.raises(ReplayValidationError):
        ValidatorEvidenceV1(**values)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"artifact_checksums": ("0" * 64,)},
        {"artifact_checksums": tuple(["bad"] + ["0" * 64] * 7)},
        {"chain_checksum": "bad"},
        {"validator_count": 7},
        {"closure_status": "BAD"},
    ],
)
def test_closure_contract_rejects_invalid_fields(kwargs: dict[str, object]) -> None:
    values = {
        "lot_sequence": tuple(range(21, 29)),
        "artifact_checksums": tuple("0" * 64 for _ in range(8)),
        "chain_checksum": "0" * 64,
        "validator_count": 8,
        "artifact_count": 8,
        "closure_status": "V2_REPLAY_VALIDATED_OFFLINE_ONLY",
    }
    values.update(kwargs)
    with pytest.raises(ReplayValidationError):
        ClosureManifestV1(**values)


@pytest.mark.parametrize(
    "field,value",
    [
        ("code_commit", "bad"),
        ("runtime_mode", "LIVE"),
        ("artifacts", ()),
        ("validators", ()),
        ("replay_status", "MISMATCH"),
        ("reason_codes", ("BAD",)),
        ("analysis_only", False),
        ("used_for_decision", True),
        ("approved_size", 1),
        ("output_checksum", "bad"),
    ],
)
def test_state_contract_rejects_invalid_fields(
    replay_root: Path,
    field: str,
    value: object,
) -> None:
    state = build_replay_state(
        replay_root,
        load_config(replay_root),
        CODE_COMMIT,
        execute_validators=False,
    )
    values = {
        "code_commit": state.code_commit,
        "runtime_mode": state.runtime_mode,
        "artifacts": state.artifacts,
        "validators": state.validators,
        "closure_manifest": state.closure_manifest,
        "replay_status": state.replay_status,
        "reason_codes": state.reason_codes,
        "analysis_only": state.analysis_only,
        "used_for_decision": state.used_for_decision,
        "trade_allowed": state.trade_allowed,
        "execution_allowed": state.execution_allowed,
        "approved_size": state.approved_size,
        "output_checksum": state.output_checksum,
    }
    values[field] = value
    with pytest.raises(ReplayValidationError):
        type(state)(**values)


def test_validate_rejects_missing_code_commit(replay_root: Path) -> None:
    result = run(replay_root, CODE_COMMIT, execute_validators=False)
    state = copy.deepcopy(result["state"])
    state.pop("code_commit")
    with pytest.raises(ReplayValidationError, match="code_commit"):
        validate_persisted_state(
            replay_root,
            load_config(replay_root),
            state,
            result["audit"],
            result["closure"],
        )


def test_validate_rejects_bad_state_checksum(replay_root: Path) -> None:
    result = run(replay_root, CODE_COMMIT, execute_validators=False)
    state = copy.deepcopy(result["state"])
    state["output_checksum"] = "0" * 64
    with pytest.raises(ReplayValidationError, match="state checksum"):
        validate_persisted_state(
            replay_root,
            load_config(replay_root),
            state,
            result["audit"],
            result["closure"],
        )


def test_validate_rejects_safety_mismatch(replay_root: Path) -> None:
    result = run(replay_root, CODE_COMMIT, execute_validators=False)
    state = copy.deepcopy(result["state"])
    audit = copy.deepcopy(result["audit"])
    audit["analysis_only"] = False
    with pytest.raises(ReplayValidationError, match="safety"):
        validate_persisted_state(
            replay_root,
            load_config(replay_root),
            state,
            audit,
            result["closure"],
        )


@pytest.mark.parametrize("raw", [None, {}, "bad"])
def test_parse_artifact_evidence_requires_list(raw: object) -> None:
    with pytest.raises(ReplayValidationError, match="artifacts must be a list"):
        _parse_artifact_evidence(raw)


def test_parse_artifact_evidence_requires_objects() -> None:
    with pytest.raises(ReplayValidationError, match="artifact evidence must be an object"):
        _parse_artifact_evidence(["bad"])


@pytest.mark.parametrize("raw", [None, {}, "bad"])
def test_parse_validator_evidence_requires_list(raw: object) -> None:
    with pytest.raises(ReplayValidationError, match="validators must be a list"):
        _parse_validator_evidence(raw)


def test_parse_validator_evidence_requires_objects() -> None:
    with pytest.raises(ReplayValidationError, match="validator evidence must be an object"):
        _parse_validator_evidence(["bad"])


def test_artifact_snapshot_rejects_count_mismatch(replay_root: Path) -> None:
    state = build_replay_state(
        replay_root, load_config(replay_root), CODE_COMMIT, execute_validators=False
    )
    with pytest.raises(ReplayValidationError, match="artifact count"):
        _validate_artifact_snapshot(state.artifacts[:-1], state.artifacts)


def test_validator_snapshot_rejects_count_and_identity(replay_root: Path) -> None:
    config = load_config(replay_root)
    state = build_replay_state(replay_root, config, CODE_COMMIT, execute_validators=False)
    specs = tuple(config["artifacts"])
    with pytest.raises(ReplayValidationError, match="validator count"):
        _validate_validator_snapshot(state.validators[:-1], specs)
    wrong = list(state.validators)
    wrong[0] = ValidatorEvidenceV1(
        lot=21,
        command=("python", "scripts/validate_lot22.py"),
        return_code=0,
        status="PASS",
        stdout_checksum="1" * 64,
    )
    with pytest.raises(ReplayValidationError, match="validator identity"):
        _validate_validator_snapshot(tuple(wrong), specs)


def test_safety_documents_reject_audit_only_mismatch() -> None:
    state = {
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    audit = dict(state)
    audit["execution_allowed"] = True
    with pytest.raises(ReplayValidationError, match="safety"):
        _validate_safety_documents(state, audit)
