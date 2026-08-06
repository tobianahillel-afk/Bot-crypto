from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ClosureValidationError(ValueError):
    """Fail-closed validation error for the V2 market-analysis closure."""


def require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ClosureValidationError(f"{field} must be a lowercase sha256")


def require_git_sha(value: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ClosureValidationError("code_commit must be a lowercase 40-character git sha")


def require_fail_closed_safety(values: dict[str, object]) -> None:
    if values.get("analysis_only") is not True:
        raise ClosureValidationError("analysis_only must remain true")
    forbidden_fields = (
        "used_for_decision",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    )
    if any(values.get(field) is not False for field in forbidden_fields):
        raise ClosureValidationError("decision, trading and execution permissions must remain false")
    if values.get("approved_size") != 0:
        raise ClosureValidationError("approved_size must remain zero")


@dataclass(frozen=True, slots=True)
class UpstreamArtifactEvidenceV1:
    lot: int
    artifact_path: str
    artifact_checksum: str
    embedded_output_checksum: str | None
    byte_size: int

    def __post_init__(self) -> None:
        if self.lot not in range(21, 29):
            raise ClosureValidationError("upstream artifact lot must be in 21..28")
        if not self.artifact_path.startswith("data/audit/"):
            raise ClosureValidationError("upstream artifact must remain inside data/audit")
        require_sha256(self.artifact_checksum, "artifact_checksum")
        if self.embedded_output_checksum is not None:
            require_sha256(self.embedded_output_checksum, "embedded_output_checksum")
        if self.byte_size <= 0:
            raise ClosureValidationError("artifact byte_size must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v2-closure-upstream-artifact-evidence-v1",
            "lot": self.lot,
            "artifact_path": self.artifact_path,
            "artifact_checksum": self.artifact_checksum,
            "embedded_output_checksum": self.embedded_output_checksum,
            "byte_size": self.byte_size,
        }


@dataclass(frozen=True, slots=True)
class ValidatorReplayEvidenceV1:
    run_index: int
    command: tuple[str, ...]
    return_code: int
    status: str
    stdout_checksum: str

    def __post_init__(self) -> None:
        if self.run_index not in (1, 2):
            raise ClosureValidationError("validator replay run_index must be 1 or 2")
        if self.command != ("python", "scripts/validate_lot29.py"):
            raise ClosureValidationError("Lot 30 must use the canonical Lot 29 validator")
        if self.return_code != 0 or self.status != "PASS":
            raise ClosureValidationError("validator replay evidence must be PASS")
        require_sha256(self.stdout_checksum, "stdout_checksum")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v2-closure-validator-replay-evidence-v1",
            "run_index": self.run_index,
            "command": list(self.command),
            "return_code": self.return_code,
            "status": self.status,
            "stdout_checksum": self.stdout_checksum,
        }


@dataclass(frozen=True, slots=True)
class NegativeControlEvidenceV1:
    name: str
    status: str
    reason_code: str

    def __post_init__(self) -> None:
        if not self.name or not self.reason_code:
            raise ClosureValidationError("negative control identity must be explicit")
        if self.status != "PASS":
            raise ClosureValidationError("negative control must be PASS")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v2-closure-negative-control-evidence-v1",
            "name": self.name,
            "status": self.status,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True, slots=True)
class V2FinalClosureManifestV1:
    covered_lot_sequence: tuple[int, ...]
    upstream_lot_sequence: tuple[int, ...]
    direct_validated_lot: int
    closure_lot: int
    upstream_artifact_checksums: tuple[str, ...]
    lot29_state_checksum: str
    lot29_audit_checksum: str
    lot29_closure_checksum: str
    validator_stdout_checksum: str
    negative_control_count: int
    final_chain_checksum: str
    closure_status: str

    def __post_init__(self) -> None:
        if self.covered_lot_sequence != tuple(range(21, 31)):
            raise ClosureValidationError("covered_lot_sequence must be 21..30")
        if self.upstream_lot_sequence != tuple(range(21, 29)):
            raise ClosureValidationError("upstream_lot_sequence must be 21..28")
        if self.direct_validated_lot != 29 or self.closure_lot != 30:
            raise ClosureValidationError("Lot 29 must be direct input and Lot 30 the closure")
        if len(self.upstream_artifact_checksums) != 8:
            raise ClosureValidationError("eight upstream artifact checksums are required")
        self._validate_checksums()
        if self.negative_control_count != 5:
            raise ClosureValidationError("five negative controls are required")
        if self.closure_status != "V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY":
            raise ClosureValidationError("unexpected V2 closure status")

    def _validate_checksums(self) -> None:
        checksums = (
            *self.upstream_artifact_checksums,
            self.lot29_state_checksum,
            self.lot29_audit_checksum,
            self.lot29_closure_checksum,
            self.validator_stdout_checksum,
            self.final_chain_checksum,
        )
        for checksum in checksums:
            require_sha256(checksum, "closure checksum")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v2-final-closure-manifest-v1",
            "covered_lot_sequence": list(self.covered_lot_sequence),
            "upstream_lot_sequence": list(self.upstream_lot_sequence),
            "direct_validated_lot": self.direct_validated_lot,
            "closure_lot": self.closure_lot,
            "upstream_artifact_checksums": list(self.upstream_artifact_checksums),
            "lot29_state_checksum": self.lot29_state_checksum,
            "lot29_audit_checksum": self.lot29_audit_checksum,
            "lot29_closure_checksum": self.lot29_closure_checksum,
            "validator_stdout_checksum": self.validator_stdout_checksum,
            "negative_control_count": self.negative_control_count,
            "final_chain_checksum": self.final_chain_checksum,
            "closure_status": self.closure_status,
        }


@dataclass(frozen=True, slots=True)
class V2MarketAnalysisClosureStateV1:
    code_commit: str
    version_id: str
    runtime_mode: str
    upstream_artifacts: tuple[UpstreamArtifactEvidenceV1, ...]
    validator_replays: tuple[ValidatorReplayEvidenceV1, ...]
    negative_controls: tuple[NegativeControlEvidenceV1, ...]
    closure_manifest: V2FinalClosureManifestV1
    reason_codes: tuple[str, ...]
    future_capabilities_locked: tuple[str, ...]
    analysis_only: bool
    used_for_decision: bool
    signal_generation_allowed: bool
    risk_approval_allowed: bool
    order_routing_allowed: bool
    trade_allowed: bool
    execution_allowed: bool
    approved_size: int
    output_checksum: str

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_evidence()
        self._validate_policy()
        require_sha256(self.output_checksum, "output_checksum")

    def _validate_identity(self) -> None:
        require_git_sha(self.code_commit)
        if self.version_id != "V2_MARKET_ANALYSIS":
            raise ClosureValidationError("unexpected version_id")
        if self.runtime_mode != "LOCAL_OFFLINE_ANALYSIS_ONLY":
            raise ClosureValidationError("unexpected runtime mode")

    def _validate_evidence(self) -> None:
        if tuple(item.lot for item in self.upstream_artifacts) != tuple(range(21, 29)):
            raise ClosureValidationError("upstream artifacts must be ordered 21..28")
        if tuple(item.run_index for item in self.validator_replays) != (1, 2):
            raise ClosureValidationError("two ordered validator replays are required")
        if self.validator_replays[0].stdout_checksum != self.validator_replays[1].stdout_checksum:
            raise ClosureValidationError("Lot 29 validator replay outputs must match")
        if len(self.negative_controls) != 5:
            raise ClosureValidationError("all five negative controls must pass")
        if any(item.status != "PASS" for item in self.negative_controls):
            raise ClosureValidationError("all five negative controls must pass")

    def _validate_policy(self) -> None:
        expected_reasons = (
            "V2_LOTS_21_30_COVERED",
            "V2_REPLAY_CHAIN_MATCH",
            "V2_NEGATIVE_CONTROLS_PASS",
            "V3_CAPABILITIES_LOCKED",
            "V2_OFFLINE_ONLY",
        )
        if self.reason_codes != expected_reasons:
            raise ClosureValidationError("unexpected closure reason code sequence")
        expected_locks = (
            "ContinuousMarketStateV1",
            "MultiHorizonForecastV1",
            "ParticipantBehaviorScenarioV1",
            "TradeIntent",
            "RiskDecisionV1",
            "RiskReservationV1",
            "OrderIntent",
        )
        if self.future_capabilities_locked != expected_locks:
            raise ClosureValidationError("future capability lock set differs")
        require_fail_closed_safety(self._safety_values())

    def _safety_values(self) -> dict[str, object]:
        return {
            "analysis_only": self.analysis_only,
            "used_for_decision": self.used_for_decision,
            "signal_generation_allowed": self.signal_generation_allowed,
            "risk_approval_allowed": self.risk_approval_allowed,
            "order_routing_allowed": self.order_routing_allowed,
            "trade_allowed": self.trade_allowed,
            "execution_allowed": self.execution_allowed,
            "approved_size": self.approved_size,
        }

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "v2-market-analysis-closure-state-v1",
            "code_commit": self.code_commit,
            "version_id": self.version_id,
            "runtime_mode": self.runtime_mode,
            "upstream_artifacts": [item.to_dict() for item in self.upstream_artifacts],
            "validator_replays": [item.to_dict() for item in self.validator_replays],
            "negative_controls": [item.to_dict() for item in self.negative_controls],
            "closure_manifest": self.closure_manifest.to_dict(),
            "reason_codes": list(self.reason_codes),
            "future_capabilities_locked": list(self.future_capabilities_locked),
            **self._safety_values(),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["output_checksum"] = self.output_checksum
        return payload
