from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ReplayValidationError(ValueError):
    """Fail-closed validation error for the Lot 29 replay closure."""


def _require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ReplayValidationError(f"{field} must be a lowercase sha256")


def _require_git_sha(value: str) -> None:
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise ReplayValidationError("code_commit must be a lowercase 40-character git sha")


def _require_lot_order(items: tuple[object, ...], field: str) -> None:
    lots = tuple(getattr(item, "lot", None) for item in items)
    if lots != tuple(range(21, 29)):
        raise ReplayValidationError(f"{field} must be ordered 21..28")


def _require_safety_state(
    analysis_only: bool,
    used_for_decision: bool,
    trade_allowed: bool,
    execution_allowed: bool,
    approved_size: int,
) -> None:
    if not analysis_only:
        raise ReplayValidationError("analysis_only must remain true")
    if used_for_decision or trade_allowed or execution_allowed:
        raise ReplayValidationError("decision and execution permissions must remain false")
    if approved_size != 0:
        raise ReplayValidationError("approved_size must remain zero")


@dataclass(frozen=True, slots=True)
class ArtifactEvidenceV1:
    lot: int
    artifact_path: str
    artifact_checksum: str
    byte_size: int
    embedded_output_checksum: str | None
    validation_state: str

    def __post_init__(self) -> None:
        if self.lot < 21 or self.lot > 28:
            raise ReplayValidationError("artifact lot outside V2 replay range")
        if not self.artifact_path.startswith("data/audit/"):
            raise ReplayValidationError("artifact path outside audit tree")
        _require_sha256(self.artifact_checksum, "artifact_checksum")
        if self.byte_size <= 0:
            raise ReplayValidationError("artifact byte_size must be positive")
        if self.embedded_output_checksum is not None:
            _require_sha256(self.embedded_output_checksum, "embedded_output_checksum")
        if self.validation_state != "VALIDATED":
            raise ReplayValidationError("artifact validation_state must be VALIDATED")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "artifact-replay-evidence-v1",
            "lot": self.lot,
            "artifact_path": self.artifact_path,
            "artifact_checksum": self.artifact_checksum,
            "byte_size": self.byte_size,
            "embedded_output_checksum": self.embedded_output_checksum,
            "validation_state": self.validation_state,
        }


@dataclass(frozen=True, slots=True)
class ValidatorEvidenceV1:
    lot: int
    command: tuple[str, ...]
    return_code: int
    status: str
    stdout_checksum: str

    def __post_init__(self) -> None:
        if self.lot < 21 or self.lot > 28:
            raise ReplayValidationError("validator lot outside V2 replay range")
        if not self.command:
            raise ReplayValidationError("validator command must not be empty")
        if self.return_code != 0 or self.status != "PASS":
            raise ReplayValidationError("validator evidence must be PASS")
        _require_sha256(self.stdout_checksum, "stdout_checksum")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "validator-replay-evidence-v1",
            "lot": self.lot,
            "command": list(self.command),
            "return_code": self.return_code,
            "status": self.status,
            "stdout_checksum": self.stdout_checksum,
        }


@dataclass(frozen=True, slots=True)
class ClosureManifestV1:
    lot_sequence: tuple[int, ...]
    artifact_checksums: tuple[str, ...]
    chain_checksum: str
    validator_count: int
    artifact_count: int
    closure_status: str

    def __post_init__(self) -> None:
        if self.lot_sequence != tuple(range(21, 29)):
            raise ReplayValidationError("closure lot sequence must be 21..28")
        if len(self.artifact_checksums) != len(self.lot_sequence):
            raise ReplayValidationError("one artifact checksum is required per lot")
        for checksum in self.artifact_checksums:
            _require_sha256(checksum, "artifact_checksum")
        _require_sha256(self.chain_checksum, "chain_checksum")
        if self.validator_count != 8 or self.artifact_count != 8:
            raise ReplayValidationError("closure requires eight artifacts and validators")
        if self.closure_status != "V2_REPLAY_VALIDATED_OFFLINE_ONLY":
            raise ReplayValidationError("unexpected closure status")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v2-closure-manifest-v1",
            "lot_sequence": list(self.lot_sequence),
            "artifact_checksums": list(self.artifact_checksums),
            "chain_checksum": self.chain_checksum,
            "validator_count": self.validator_count,
            "artifact_count": self.artifact_count,
            "closure_status": self.closure_status,
        }


@dataclass(frozen=True, slots=True)
class V2DeterministicReplayAuditStateV1:
    code_commit: str
    runtime_mode: str
    artifacts: tuple[ArtifactEvidenceV1, ...]
    validators: tuple[ValidatorEvidenceV1, ...]
    closure_manifest: ClosureManifestV1
    replay_status: str
    reason_codes: tuple[str, ...]
    analysis_only: bool
    used_for_decision: bool
    trade_allowed: bool
    execution_allowed: bool
    approved_size: int
    output_checksum: str

    def __post_init__(self) -> None:
        _require_git_sha(self.code_commit)
        if self.runtime_mode != "LOCAL_OFFLINE_ANALYSIS_ONLY":
            raise ReplayValidationError("unexpected runtime mode")
        _require_lot_order(self.artifacts, "artifact evidence")
        _require_lot_order(self.validators, "validator evidence")
        if self.replay_status != "MATCH":
            raise ReplayValidationError("replay_status must be MATCH")
        expected = ("V2_ARTIFACT_CHAIN_MATCH", "V2_VALIDATORS_PASS", "V2_OFFLINE_ONLY")
        if self.reason_codes != expected:
            raise ReplayValidationError("unexpected reason code sequence")
        _require_safety_state(
            self.analysis_only,
            self.used_for_decision,
            self.trade_allowed,
            self.execution_allowed,
            self.approved_size,
        )
        _require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "v2-deterministic-replay-audit-state-v1",
            "code_commit": self.code_commit,
            "runtime_mode": self.runtime_mode,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "validators": [item.to_dict() for item in self.validators],
            "closure_manifest": self.closure_manifest.to_dict(),
            "replay_status": self.replay_status,
            "reason_codes": list(self.reason_codes),
            "analysis_only": self.analysis_only,
            "used_for_decision": self.used_for_decision,
            "trade_allowed": self.trade_allowed,
            "execution_allowed": self.execution_allowed,
            "approved_size": self.approved_size,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["output_checksum"] = self.output_checksum
        return payload
