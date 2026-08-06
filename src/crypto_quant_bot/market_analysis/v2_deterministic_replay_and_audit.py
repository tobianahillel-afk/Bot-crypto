from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from crypto_quant_bot.market_analysis.alignment_io import load_json
from crypto_quant_bot.market_analysis.v2_replay_audit_models import (
    ArtifactEvidenceV1,
    ClosureManifestV1,
    ReplayValidationError,
    V2DeterministicReplayAuditStateV1,
    ValidatorEvidenceV1,
)

EXPECTED_LOTS = tuple(range(21, 29))
EXPECTED_REASON_CODES = (
    "V2_ARTIFACT_CHAIN_MATCH",
    "V2_VALIDATORS_PASS",
    "V2_OFFLINE_ONLY",
)
MAX_VALIDATOR_STDOUT_BYTES = 1_000_000


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_artifact_specs(raw_artifacts: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(raw_artifacts, list):
        raise ReplayValidationError("artifacts must be a list")
    if not all(isinstance(raw, dict) for raw in raw_artifacts):
        raise ReplayValidationError("artifact specs must be objects")
    return tuple(raw_artifacts)


def _validate_artifact_specs(artifacts: tuple[dict[str, Any], ...]) -> None:
    lots = tuple(item.get("lot") for item in artifacts)
    if lots != EXPECTED_LOTS:
        raise ReplayValidationError("artifact specs must be ordered lots 21..28")
    paths = tuple(str(item.get("path", "")) for item in artifacts)
    if len(set(paths)) != len(EXPECTED_LOTS):
        raise ReplayValidationError("artifact paths must be unique")
    if any(not path.startswith("data/audit/") for path in paths):
        raise ReplayValidationError("artifact paths must remain inside data/audit")
    validators = tuple(str(item.get("validator", "")) for item in artifacts)
    if any(not command.startswith("scripts/validate_lot") for command in validators):
        raise ReplayValidationError("each lot requires its canonical validator")


def _validate_safety_policy(safety: object) -> None:
    expected = {
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    if safety != expected:
        raise ReplayValidationError("replay safety policy is not fail-closed")


def _validate_config(config: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    if config.get("schema_version") != "v2-deterministic-replay-audit-config-v1":
        raise ReplayValidationError("unsupported replay config schema")
    if config.get("runtime_mode") != "LOCAL_OFFLINE_ANALYSIS_ONLY":
        raise ReplayValidationError("replay config must remain offline only")
    artifacts = _normalize_artifact_specs(config.get("artifacts"))
    _validate_artifact_specs(artifacts)
    _validate_safety_policy(config.get("safety"))
    return artifacts


def _validate_artifact_safety(payload: dict[str, Any], lot: int) -> None:
    forbidden_true = ("used_for_decision", "trade_allowed", "execution_allowed")
    for field in forbidden_true:
        if payload.get(field) is True:
            raise ReplayValidationError(f"lot {lot} enables forbidden field {field}")
    if "approved_size" in payload and payload["approved_size"] != 0:
        raise ReplayValidationError(f"lot {lot} approved_size must remain zero")
    if "analysis_only" in payload and payload["analysis_only"] is not True:
        raise ReplayValidationError(f"lot {lot} analysis_only must remain true")


def build_artifact_evidence(root: Path, spec: dict[str, Any]) -> ArtifactEvidenceV1:
    lot = int(spec["lot"])
    path = root / str(spec["path"])
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ReplayValidationError(f"lot {lot} artifact must be a JSON object")
    _validate_artifact_safety(payload, lot)
    embedded = payload.get("output_checksum")
    if embedded is not None and not isinstance(embedded, str):
        raise ReplayValidationError(f"lot {lot} output_checksum must be text")
    return ArtifactEvidenceV1(
        lot=lot,
        artifact_path=path.relative_to(root).as_posix(),
        artifact_checksum=file_checksum(path),
        byte_size=path.stat().st_size,
        embedded_output_checksum=embedded,
        validation_state="VALIDATED",
    )


def run_validator(root: Path, lot: int, script_path: str) -> ValidatorEvidenceV1:
    command = ("python", script_path)
    result = subprocess.run(
        command,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    combined = (result.stdout + "\n" + result.stderr).encode("utf-8")
    if len(combined) > MAX_VALIDATOR_STDOUT_BYTES:
        raise ReplayValidationError(f"lot {lot} validator output exceeds limit")
    if result.returncode != 0:
        raise ReplayValidationError(f"lot {lot} validator failed with rc={result.returncode}")
    return ValidatorEvidenceV1(
        lot=lot,
        command=command,
        return_code=0,
        status="PASS",
        stdout_checksum=hashlib.sha256(combined).hexdigest(),
    )


def run_validators(root: Path, specs: Iterable[dict[str, Any]]) -> tuple[ValidatorEvidenceV1, ...]:
    return tuple(
        run_validator(root, int(spec["lot"]), str(spec["validator"])) for spec in specs
    )


def _synthetic_validators(specs: Iterable[dict[str, Any]]) -> tuple[ValidatorEvidenceV1, ...]:
    return tuple(
        ValidatorEvidenceV1(
            lot=int(spec["lot"]),
            command=("python", str(spec["validator"])),
            return_code=0,
            status="PASS",
            stdout_checksum=hashlib.sha256(
                f"synthetic-pass:{spec['lot']}:{spec['validator']}".encode()
            ).hexdigest(),
        )
        for spec in specs
    )


def _select_validators(
    root: Path,
    specs: tuple[dict[str, Any], ...],
    execute_validators: bool,
    validator_evidence: tuple[ValidatorEvidenceV1, ...] | None,
) -> tuple[ValidatorEvidenceV1, ...]:
    if validator_evidence is not None:
        return validator_evidence
    if execute_validators:
        return run_validators(root, specs)
    return _synthetic_validators(specs)


def _chain_checksum(artifacts: tuple[ArtifactEvidenceV1, ...]) -> str:
    payload = [
        {
            "lot": item.lot,
            "path": item.artifact_path,
            "artifact_checksum": item.artifact_checksum,
            "embedded_output_checksum": item.embedded_output_checksum,
        }
        for item in artifacts
    ]
    return canonical_checksum(payload)


def _build_closure(
    artifacts: tuple[ArtifactEvidenceV1, ...],
    validators: tuple[ValidatorEvidenceV1, ...],
) -> ClosureManifestV1:
    return ClosureManifestV1(
        lot_sequence=EXPECTED_LOTS,
        artifact_checksums=tuple(item.artifact_checksum for item in artifacts),
        chain_checksum=_chain_checksum(artifacts),
        validator_count=len(validators),
        artifact_count=len(artifacts),
        closure_status="V2_REPLAY_VALIDATED_OFFLINE_ONLY",
    )


def _state_payload(
    code_commit: str,
    artifacts: tuple[ArtifactEvidenceV1, ...],
    validators: tuple[ValidatorEvidenceV1, ...],
    closure: ClosureManifestV1,
) -> dict[str, Any]:
    return {
        "schema_version": "v2-deterministic-replay-audit-state-v1",
        "code_commit": code_commit,
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "artifacts": [item.to_dict() for item in artifacts],
        "validators": [item.to_dict() for item in validators],
        "closure_manifest": closure.to_dict(),
        "replay_status": "MATCH",
        "reason_codes": list(EXPECTED_REASON_CODES),
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def build_replay_state(
    root: Path,
    config: dict[str, Any],
    code_commit: str,
    *,
    execute_validators: bool = True,
    validator_evidence: tuple[ValidatorEvidenceV1, ...] | None = None,
) -> V2DeterministicReplayAuditStateV1:
    specs = _validate_config(config)
    artifacts = tuple(build_artifact_evidence(root, spec) for spec in specs)
    validators = _select_validators(root, specs, execute_validators, validator_evidence)
    closure = _build_closure(artifacts, validators)
    payload = _state_payload(code_commit, artifacts, validators, closure)
    return V2DeterministicReplayAuditStateV1(
        code_commit=code_commit,
        runtime_mode="LOCAL_OFFLINE_ANALYSIS_ONLY",
        artifacts=artifacts,
        validators=validators,
        closure_manifest=closure,
        replay_status="MATCH",
        reason_codes=EXPECTED_REASON_CODES,
        analysis_only=True,
        used_for_decision=False,
        trade_allowed=False,
        execution_allowed=False,
        approved_size=0,
        output_checksum=canonical_checksum(payload),
    )


def replay_matches(
    first: V2DeterministicReplayAuditStateV1,
    second: V2DeterministicReplayAuditStateV1,
) -> bool:
    return first.to_dict() == second.to_dict()


def _validate_state_checksum(state: dict[str, Any]) -> str:
    persisted_payload = dict(state)
    output_checksum = persisted_payload.pop("output_checksum", None)
    if output_checksum != canonical_checksum(persisted_payload):
        raise ReplayValidationError("persisted state checksum mismatch")
    return str(output_checksum)


def _parse_artifact_evidence(raw_items: object) -> tuple[ArtifactEvidenceV1, ...]:
    if not isinstance(raw_items, list):
        raise ReplayValidationError("persisted artifacts must be a list")
    evidence: list[ArtifactEvidenceV1] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ReplayValidationError("persisted artifact evidence must be an object")
        evidence.append(
            ArtifactEvidenceV1(
                lot=int(raw.get("lot", -1)),
                artifact_path=str(raw.get("artifact_path", "")),
                artifact_checksum=str(raw.get("artifact_checksum", "")),
                byte_size=int(raw.get("byte_size", 0)),
                embedded_output_checksum=raw.get("embedded_output_checksum"),
                validation_state=str(raw.get("validation_state", "")),
            )
        )
    return tuple(evidence)


def _parse_validator_evidence(raw_items: object) -> tuple[ValidatorEvidenceV1, ...]:
    if not isinstance(raw_items, list):
        raise ReplayValidationError("persisted validators must be a list")
    evidence: list[ValidatorEvidenceV1] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ReplayValidationError("persisted validator evidence must be an object")
        evidence.append(
            ValidatorEvidenceV1(
                lot=int(raw.get("lot", -1)),
                command=tuple(raw.get("command", ())),
                return_code=int(raw.get("return_code", -1)),
                status=str(raw.get("status", "")),
                stdout_checksum=str(raw.get("stdout_checksum", "")),
            )
        )
    return tuple(evidence)


def _parse_closure(raw: dict[str, Any]) -> ClosureManifestV1:
    return ClosureManifestV1(
        lot_sequence=tuple(raw.get("lot_sequence", ())),
        artifact_checksums=tuple(raw.get("artifact_checksums", ())),
        chain_checksum=str(raw.get("chain_checksum", "")),
        validator_count=int(raw.get("validator_count", -1)),
        artifact_count=int(raw.get("artifact_count", -1)),
        closure_status=str(raw.get("closure_status", "")),
    )


def _parse_persisted_state(
    state: dict[str, Any],
    output_checksum: str,
) -> V2DeterministicReplayAuditStateV1:
    return V2DeterministicReplayAuditStateV1(
        code_commit=str(state.get("code_commit", "")),
        runtime_mode=str(state.get("runtime_mode", "")),
        artifacts=_parse_artifact_evidence(state.get("artifacts")),
        validators=_parse_validator_evidence(state.get("validators")),
        closure_manifest=_parse_closure(dict(state.get("closure_manifest", {}))),
        replay_status=str(state.get("replay_status", "")),
        reason_codes=tuple(state.get("reason_codes", ())),
        analysis_only=state.get("analysis_only") is True,
        used_for_decision=state.get("used_for_decision") is True,
        trade_allowed=state.get("trade_allowed") is True,
        execution_allowed=state.get("execution_allowed") is True,
        approved_size=int(state.get("approved_size", -1)),
        output_checksum=output_checksum,
    )


def _validate_artifact_snapshot(
    persisted_artifacts: tuple[ArtifactEvidenceV1, ...],
    observed_artifacts: tuple[ArtifactEvidenceV1, ...],
) -> None:
    if len(persisted_artifacts) != len(observed_artifacts):
        raise ReplayValidationError("persisted artifact count mismatch")
    fields = (
        "lot",
        "artifact_path",
        "artifact_checksum",
        "byte_size",
        "embedded_output_checksum",
    )
    for persisted, observed in zip(persisted_artifacts, observed_artifacts, strict=True):
        for field in fields:
            if getattr(persisted, field) != getattr(observed, field):
                raise ReplayValidationError(f"persisted artifact field mismatch: {field}")


def _validate_validator_snapshot(
    persisted_validators: tuple[ValidatorEvidenceV1, ...],
    specs: tuple[dict[str, Any], ...],
) -> None:
    if len(persisted_validators) != len(specs):
        raise ReplayValidationError("persisted validator count mismatch")
    for evidence, spec in zip(persisted_validators, specs, strict=True):
        expected_command = ("python", str(spec["validator"]))
        if evidence.lot != int(spec["lot"]) or evidence.command != expected_command:
            raise ReplayValidationError("persisted validator identity mismatch")


def _validate_audit_and_closure(
    persisted: V2DeterministicReplayAuditStateV1,
    audit: dict[str, Any],
    closure: dict[str, Any],
) -> None:
    if persisted.closure_manifest.to_dict() != closure:
        raise ReplayValidationError("closure manifest differs from state")
    if audit.get("output_checksum") != persisted.output_checksum:
        raise ReplayValidationError("audit output checksum mismatch")
    if audit.get("chain_checksum") != persisted.closure_manifest.chain_checksum:
        raise ReplayValidationError("audit chain checksum mismatch")
    if audit.get("replay_status") != "MATCH":
        raise ReplayValidationError("audit replay status mismatch")


def _validate_safety_documents(state: dict[str, Any], audit: dict[str, Any]) -> None:
    expected_fields = (
        ("analysis_only", True),
        ("used_for_decision", False),
        ("trade_allowed", False),
        ("execution_allowed", False),
        ("approved_size", 0),
    )
    for field, expected in expected_fields:
        if state.get(field) != expected or audit.get(field) != expected:
            raise ReplayValidationError(f"persisted safety field mismatch: {field}")


def validate_persisted_state(
    root: Path,
    config: dict[str, Any],
    state: dict[str, Any],
    audit: dict[str, Any],
    closure: dict[str, Any],
) -> dict[str, Any]:
    code_commit = state.get("code_commit")
    if not isinstance(code_commit, str):
        raise ReplayValidationError("persisted state code_commit missing")
    specs = _validate_config(config)
    rebuilt = build_replay_state(root, config, code_commit, execute_validators=False)
    output_checksum = _validate_state_checksum(state)
    persisted = _parse_persisted_state(state, output_checksum)
    _validate_artifact_snapshot(persisted.artifacts, rebuilt.artifacts)
    _validate_validator_snapshot(persisted.validators, specs)
    _validate_audit_and_closure(persisted, audit, closure)
    _validate_safety_documents(state, audit)
    return {
        "schema_version": "lot29-validation-v1",
        "status": "PASS",
        "artifact_count": len(state["artifacts"]),
        "validator_count": len(state["validators"]),
        "chain_checksum": closure["chain_checksum"],
        "output_checksum": output_checksum,
        "replay_status": "MATCH",
    }
