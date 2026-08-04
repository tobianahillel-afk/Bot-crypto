from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from types import MappingProxyType

_HEX64 = re.compile(r"^[A-Fa-f0-9]{64}$")
_COMMIT = re.compile(r"^[A-Fa-f0-9]{7,64}$")
_DECISION_STATES = {
    "APPROVE",
    "WAIT",
    "BLOCK_TRADING",
    "PAUSE",
    "KILL_SWITCH",
    "UNKNOWN",
    "NOT_APPLICABLE",
}
_BLOCKING_STATES = {"BLOCK_TRADING", "PAUSE", "KILL_SWITCH"}


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_optional_text(value: str | None, field: str) -> None:
    if value is not None:
        _require_text(value, field)


def _require_utc_timestamp(value: str, field: str) -> None:
    _require_text(value, field)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{field} must be timezone-aware UTC")


def _require_checksum(value: str, field: str) -> None:
    if not _HEX64.fullmatch(value):
        raise ValueError(f"{field} must be a 64-character hexadecimal checksum")


def _freeze_codes(values: Sequence[str], field: str) -> tuple[str, ...]:
    result = tuple(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise ValueError(f"{field} must contain non-empty strings")
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicates")
    return result


def _freeze_mapping(values: Mapping[str, str], field: str) -> Mapping[str, str]:
    result = dict(values)
    for key, value in result.items():
        _require_text(key, f"{field}.key")
        _require_text(value, f"{field}.{key}")
    return MappingProxyType(result)


@dataclass(frozen=True, slots=True)
class EvidenceReferenceV1:
    evidence_id: str
    evidence_type: str
    checksum: str
    available_at: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.evidence_type, "evidence_type")
        _require_checksum(self.checksum, "checksum")
        if self.available_at is not None:
            _require_utc_timestamp(self.available_at, "available_at")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "checksum": self.checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class UncertaintyEnvelopeV1:
    data: float | None
    model: float | None
    calibration: float | None
    execution: float | None

    def __post_init__(self) -> None:
        for field in ("data", "model", "calibration", "execution"):
            value = getattr(self, field)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"uncertainty.{field} must be within [0, 1]")

    def to_dict(self) -> dict[str, float | None]:
        return {
            "data": self.data,
            "model": self.model,
            "calibration": self.calibration,
            "execution": self.execution,
        }


@dataclass(frozen=True, slots=True)
class DecisionEvidenceEnvelopeV1:
    decision_id: str
    parent_decision_ids: Sequence[str]
    run_id: str
    correlation_id: str
    replay_id: str | None
    event_time: str
    decision_time: str
    generated_at: str
    runtime_mode: str
    instrument_id: str | None
    venue_id: str | None
    data_snapshot_id: str | None
    data_quality_state_id: str | None
    feature_set_id: str | None
    market_context_id: str | None
    scenario_set_id: str | None
    strategy_id: str | None
    strategy_version: str | None
    model_versions: Mapping[str, str]
    calibration_version: str | None
    risk_state_id: str | None
    risk_decision_id: str | None
    config_version: str
    code_commit: str
    input_checksums: Mapping[str, str]
    output_checksum: str
    decision_state: str
    reason_codes: Sequence[str]
    veto_codes: Sequence[str]
    uncertainty: UncertaintyEnvelopeV1
    human_approval_id: str | None
    facts_observed: Sequence[str]
    features_computed: Sequence[str]
    inferences: Sequence[str]
    assumptions: Sequence[str]
    supporting_evidence: Sequence[EvidenceReferenceV1]
    contradicting_evidence: Sequence[EvidenceReferenceV1]
    rules_triggered: Sequence[str]
    final_consequence: str
    schema_version: str = "decision-evidence-envelope-v1"

    def __post_init__(self) -> None:
        self._validate_identifiers()
        self._validate_time_and_integrity()
        self._freeze_collections()
        self._validate_decision_semantics()

    def _validate_identifiers(self) -> None:
        for field in ("decision_id", "run_id", "correlation_id", "runtime_mode", "config_version"):
            _require_text(getattr(self, field), field)
        optional = (
            "replay_id",
            "instrument_id",
            "venue_id",
            "data_snapshot_id",
            "data_quality_state_id",
            "feature_set_id",
            "market_context_id",
            "scenario_set_id",
            "strategy_id",
            "strategy_version",
            "calibration_version",
            "risk_state_id",
            "risk_decision_id",
            "human_approval_id",
        )
        for field in optional:
            _require_optional_text(getattr(self, field), field)

    def _validate_time_and_integrity(self) -> None:
        if self.schema_version != "decision-evidence-envelope-v1":
            raise ValueError("unsupported decision evidence schema_version")
        for field in ("event_time", "decision_time", "generated_at"):
            _require_utc_timestamp(getattr(self, field), field)
        if not _COMMIT.fullmatch(self.code_commit):
            raise ValueError("code_commit must be a 7-64 character hexadecimal commit")
        _require_checksum(self.output_checksum, "output_checksum")
        for key, checksum in self.input_checksums.items():
            _require_checksum(checksum, f"input_checksums.{key}")
        if not self.input_checksums:
            raise ValueError("input_checksums must not be empty")

    def _freeze_collections(self) -> None:
        object.__setattr__(
            self,
            "parent_decision_ids",
            _freeze_codes(self.parent_decision_ids, "parent_decision_ids"),
        )
        object.__setattr__(self, "reason_codes", _freeze_codes(self.reason_codes, "reason_codes"))
        object.__setattr__(self, "veto_codes", _freeze_codes(self.veto_codes, "veto_codes"))
        object.__setattr__(
            self,
            "rules_triggered",
            _freeze_codes(self.rules_triggered, "rules_triggered"),
        )
        for field in ("facts_observed", "features_computed", "inferences", "assumptions"):
            object.__setattr__(self, field, _freeze_codes(getattr(self, field), field))
        object.__setattr__(self, "supporting_evidence", tuple(self.supporting_evidence))
        object.__setattr__(self, "contradicting_evidence", tuple(self.contradicting_evidence))
        object.__setattr__(
            self,
            "model_versions",
            _freeze_mapping(self.model_versions, "model_versions"),
        )
        object.__setattr__(
            self,
            "input_checksums",
            _freeze_mapping(self.input_checksums, "input_checksums"),
        )

    def _validate_decision_semantics(self) -> None:
        if self.decision_state not in _DECISION_STATES:
            raise ValueError(f"unknown decision_state: {self.decision_state}")
        if self.decision_state == "APPROVE" and not self.risk_decision_id:
            raise ValueError("APPROVE requires risk_decision_id")
        if self.decision_state == "APPROVE" and not self.reason_codes:
            raise ValueError("APPROVE requires at least one reason code")
        if self.decision_state in _BLOCKING_STATES and not self.veto_codes:
            raise ValueError(f"{self.decision_state} requires at least one veto code")
        _require_text(self.final_consequence, "final_consequence")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "parent_decision_ids": list(self.parent_decision_ids),
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "replay_id": self.replay_id,
            "event_time": self.event_time,
            "decision_time": self.decision_time,
            "generated_at": self.generated_at,
            "runtime_mode": self.runtime_mode,
            "instrument_id": self.instrument_id,
            "venue_id": self.venue_id,
            "data_snapshot_id": self.data_snapshot_id,
            "data_quality_state_id": self.data_quality_state_id,
            "feature_set_id": self.feature_set_id,
            "market_context_id": self.market_context_id,
            "scenario_set_id": self.scenario_set_id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "model_versions": dict(self.model_versions),
            "calibration_version": self.calibration_version,
            "risk_state_id": self.risk_state_id,
            "risk_decision_id": self.risk_decision_id,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "input_checksums": dict(self.input_checksums),
            "output_checksum": self.output_checksum,
            "decision_state": self.decision_state,
            "reason_codes": list(self.reason_codes),
            "veto_codes": list(self.veto_codes),
            "uncertainty": self.uncertainty.to_dict(),
            "human_approval_id": self.human_approval_id,
            "facts_observed": list(self.facts_observed),
            "features_computed": list(self.features_computed),
            "inferences": list(self.inferences),
            "assumptions": list(self.assumptions),
            "supporting_evidence": [item.to_dict() for item in self.supporting_evidence],
            "contradicting_evidence": [item.to_dict() for item in self.contradicting_evidence],
            "rules_triggered": list(self.rules_triggered),
            "final_consequence": self.final_consequence,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    def envelope_checksum(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()
