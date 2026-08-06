from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .source_registry_validation import (
    ALLOWED_CAPABILITY_STATES,
    ALLOWED_CRITICALITY,
    SourceRegistryValidationError,
    require_git_sha,
    require_non_empty,
    require_secret_free,
    require_sha256,
    require_utc_timestamp,
)


@dataclass(frozen=True, slots=True)
class RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        for field, value in (
            ("run_id", self.run_id),
            ("config_version", self.config_version),
            ("correlation_id", self.correlation_id),
        ):
            require_non_empty(value, field)
        if self.runtime_mode != "DATA_GOVERNANCE_ONLY":
            raise SourceRegistryValidationError("Lot 31 runtime_mode must be DATA_GOVERNANCE_ONLY")
        require_git_sha(self.code_commit)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class LineageEnvelopeV1:
    lineage_id: str
    upstream_lot: int
    upstream_artifact_path: str
    upstream_artifact_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_non_empty(self.lineage_id, "lineage_id")
        if self.upstream_lot != 30:
            raise SourceRegistryValidationError("Lot 31 lineage must originate from Lot 30")
        if self.upstream_artifact_path != "data/audit/v2_market_analysis_closure_lot30.json":
            raise SourceRegistryValidationError("Lot 31 lineage must use the certified Lot 30 state")
        require_sha256(self.upstream_artifact_checksum, "upstream_artifact_checksum")
        require_utc_timestamp(self.available_at, "available_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "upstream_lot": self.upstream_lot,
            "upstream_artifact_path": self.upstream_artifact_path,
            "upstream_artifact_checksum": self.upstream_artifact_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class SourceRegistryEntryV1:
    source_id: str
    provider: str
    venue: str
    endpoint_type: str
    endpoint_descriptor: str
    fields: tuple[str, ...]
    cadence: int
    timezone: str
    license: str
    auth_mode: str
    retention: int
    criticality: str
    source_of_truth: bool
    backup_sources: tuple[str, ...]
    source_schema_version: str
    revision: int
    revision_policy: str
    approved: bool
    enabled: bool
    connection_status: str

    def __post_init__(self) -> None:
        self._validate_identity()
        self._validate_metadata()
        self._validate_policy()

    def _validate_identity(self) -> None:
        for field, value in (
            ("source_id", self.source_id),
            ("provider", self.provider),
            ("venue", self.venue),
            ("endpoint_type", self.endpoint_type),
            ("endpoint_descriptor", self.endpoint_descriptor),
            ("source_schema_version", self.source_schema_version),
        ):
            require_non_empty(value, field)
        if self.source_id.lower() != self.source_id:
            raise SourceRegistryValidationError("source_id must use canonical lowercase form")
        if self.timezone != "UTC":
            raise SourceRegistryValidationError("source timezone must be UTC")

    def _validate_metadata(self) -> None:
        if not self.fields or len(set(self.fields)) != len(self.fields):
            raise SourceRegistryValidationError("source fields must be non-empty and unique")
        require_secret_free((*self.fields, self.endpoint_descriptor), "source metadata")
        if self.cadence <= 0:
            raise SourceRegistryValidationError("cadence must be positive")
        if self.retention < 0:
            raise SourceRegistryValidationError("retention cannot be negative")
        if self.criticality not in ALLOWED_CRITICALITY:
            raise SourceRegistryValidationError("unknown source criticality")
        if not isinstance(self.source_of_truth, bool):
            raise SourceRegistryValidationError("source_of_truth must be explicit")
        if self.revision < 1:
            raise SourceRegistryValidationError("source revision must be positive")

    def _validate_policy(self) -> None:
        if self.auth_mode != "NONE":
            raise SourceRegistryValidationError("Lot 31 only permits auth_mode=NONE")
        if self.revision_policy != "IMMUTABLE_VERSIONED_REPLACEMENT":
            raise SourceRegistryValidationError("unexpected revision policy")
        if self.approved is not True:
            raise SourceRegistryValidationError("registered source must be explicitly approved")
        if self.enabled is not False or self.connection_status != "DISABLED":
            raise SourceRegistryValidationError("Lot 31 sources must remain connection-disabled")
        if self.source_id in self.backup_sources:
            raise SourceRegistryValidationError("source cannot back up itself")
        if len(set(self.backup_sources)) != len(self.backup_sources):
            raise SourceRegistryValidationError("backup source ids must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "source-registry-entry-v1",
            "source_id": self.source_id,
            "provider": self.provider,
            "venue": self.venue,
            "endpoint_type": self.endpoint_type,
            "endpoint_descriptor": self.endpoint_descriptor,
            "fields": list(self.fields),
            "cadence": self.cadence,
            "timezone": self.timezone,
            "license": self.license,
            "auth_mode": self.auth_mode,
            "retention": self.retention,
            "criticality": self.criticality,
            "source_of_truth": self.source_of_truth,
            "backup_sources": list(self.backup_sources),
            "source_schema_version": self.source_schema_version,
            "revision": self.revision,
            "revision_policy": self.revision_policy,
            "approved": self.approved,
            "enabled": self.enabled,
            "connection_status": self.connection_status,
        }


@dataclass(frozen=True, slots=True)
class CapabilityMatrixEntryV1:
    capability: str
    status: str
    owner: str
    contract: str
    gate: str

    def __post_init__(self) -> None:
        for field, value in (
            ("capability", self.capability),
            ("owner", self.owner),
            ("contract", self.contract),
            ("gate", self.gate),
        ):
            require_non_empty(value, field)
        if self.status not in ALLOWED_CAPABILITY_STATES:
            raise SourceRegistryValidationError("unknown capability status")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot31-capability-matrix-entry-v1",
            "capability": self.capability,
            "status": self.status,
            "owner": self.owner,
            "contract": self.contract,
            "gate": self.gate,
        }


@dataclass(frozen=True, slots=True)
class ContractRegistryEntryV1:
    contract_name: str
    owner: str
    schema_path: str
    producer: str
    status: str

    def __post_init__(self) -> None:
        for field, value in (
            ("contract_name", self.contract_name),
            ("owner", self.owner),
            ("schema_path", self.schema_path),
            ("producer", self.producer),
            ("status", self.status),
        ):
            require_non_empty(value, field)
        if not self.schema_path.startswith("contracts/schemas/"):
            raise SourceRegistryValidationError("contract schema must remain in contracts/schemas")
        if self.owner != "MarketDataGovernanceDomain":
            raise SourceRegistryValidationError("Lot 31 contracts require the V3 canonical owner")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot31-contract-registry-entry-v1",
            "contract_name": self.contract_name,
            "owner": self.owner,
            "schema_path": self.schema_path,
            "producer": self.producer,
            "status": self.status,
        }
