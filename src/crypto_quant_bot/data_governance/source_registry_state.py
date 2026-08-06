from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .source_registry_models import (
    CapabilityMatrixEntryV1,
    ContractRegistryEntryV1,
    LineageEnvelopeV1,
    RunContextV1,
    SourceRegistryEntryV1,
)
from .source_registry_validation import (
    SourceRegistryValidationError,
    require_git_sha,
    require_non_empty,
    require_sha256,
    require_utc_timestamp,
    validate_fail_closed_safety,
)


@dataclass(frozen=True, slots=True)
class SourceRegistryV1:
    registry_id: str
    registry_version: str
    source_of_truth_id: str
    sources: tuple[SourceRegistryEntryV1, ...]
    revision_policy: str

    def __post_init__(self) -> None:
        require_non_empty(self.registry_id, "registry_id")
        require_non_empty(self.registry_version, "registry_version")
        if self.revision_policy != "IMMUTABLE_VERSIONED_REPLACEMENT":
            raise SourceRegistryValidationError("registry revision policy changed")
        self._validate_sources()
        self._validate_backup_graph()

    def _validate_sources(self) -> None:
        source_ids = tuple(source.source_id for source in self.sources)
        if not source_ids or len(set(source_ids)) != len(source_ids):
            raise SourceRegistryValidationError("registry source ids must be non-empty and unique")
        if tuple(sorted(source_ids)) != source_ids:
            raise SourceRegistryValidationError("registry sources must be canonically ordered")
        entries = {source.source_id: source for source in self.sources}
        truth = entries.get(self.source_of_truth_id)
        if truth is None or truth.source_of_truth is not True:
            raise SourceRegistryValidationError("source_of_truth_id must reference the truth source")
        if sum(source.source_of_truth for source in self.sources) != 1:
            raise SourceRegistryValidationError("exactly one source of truth is required")

    def _validate_backup_graph(self) -> None:
        entries = {source.source_id: source for source in self.sources}
        for source in self.sources:
            if any(backup not in entries for backup in source.backup_sources):
                raise SourceRegistryValidationError("backup source reference is unknown")
        for source_id in entries:
            self._walk_backup_graph(source_id, source_id, entries, set())

    @classmethod
    def _walk_backup_graph(
        cls,
        origin: str,
        current: str,
        entries: dict[str, SourceRegistryEntryV1],
        visited: set[str],
    ) -> None:
        for backup in entries[current].backup_sources:
            if backup == origin or backup in visited:
                raise SourceRegistryValidationError("backup graph must be acyclic")
            cls._walk_backup_graph(origin, backup, entries, {*visited, backup})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "source-registry-v1",
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "source_of_truth_id": self.source_of_truth_id,
            "sources": [source.to_dict() for source in self.sources],
            "revision_policy": self.revision_policy,
        }


@dataclass(frozen=True, slots=True)
class Lot31MetricsV1:
    records_processed_total: int
    validation_failures_total: int
    processing_latency_ms: int

    def __post_init__(self) -> None:
        values = (
            self.records_processed_total,
            self.validation_failures_total,
            self.processing_latency_ms,
        )
        if any(value < 0 for value in values):
            raise SourceRegistryValidationError("Lot 31 metrics cannot be negative")

    def to_dict(self) -> dict[str, int | str]:
        return {
            "schema_version": "lot31-metrics-v1",
            "lot_31_records_processed_total": self.records_processed_total,
            "lot_31_validation_failures_total": self.validation_failures_total,
            "lot_31_processing_latency_ms": self.processing_latency_ms,
        }


@dataclass(frozen=True, slots=True)
class MarketDataGovernanceScopeSourceRegistryStateV1:
    run_context: RunContextV1
    lineage: LineageEnvelopeV1
    event_time: str
    generated_at: str
    available_at: str
    validation_state: str
    source_registry: SourceRegistryV1
    capability_matrix: tuple[CapabilityMatrixEntryV1, ...]
    contract_registry: tuple[ContractRegistryEntryV1, ...]
    metrics: Lot31MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        for field, value in (
            ("event_time", self.event_time),
            ("generated_at", self.generated_at),
            ("available_at", self.available_at),
        ):
            require_utc_timestamp(value, field)
        if not self.event_time <= self.available_at <= self.generated_at:
            raise SourceRegistryValidationError("Lot 31 timestamps violate causal availability")
        if self.validation_state != "VALIDATED_METADATA_ONLY":
            raise SourceRegistryValidationError("unexpected Lot 31 validation_state")
        self._validate_registries()
        self._validate_policy()
        require_sha256(self.output_checksum, "output_checksum")

    def _validate_registries(self) -> None:
        capability_names = tuple(item.capability for item in self.capability_matrix)
        if tuple(sorted(capability_names)) != capability_names:
            raise SourceRegistryValidationError("capabilities must be canonically ordered")
        if len(set(capability_names)) != len(capability_names):
            raise SourceRegistryValidationError("capability names must be unique")
        contract_names = tuple(item.contract_name for item in self.contract_registry)
        if tuple(sorted(contract_names)) != contract_names:
            raise SourceRegistryValidationError("contracts must be canonically ordered")
        if len(set(contract_names)) != len(contract_names):
            raise SourceRegistryValidationError("contract names must be unique")
        contracts = set(contract_names)
        if any(item.contract not in contracts for item in self.capability_matrix):
            raise SourceRegistryValidationError("capability references an unknown contract")

    def _validate_policy(self) -> None:
        expected_reasons = (
            "LOT31_ENTRY_GATE_VERIFIED",
            "SOURCE_REGISTRY_METADATA_VALIDATED",
            "SOURCE_OF_TRUTH_AND_BACKUPS_DECLARED",
            "EXTERNAL_CONNECTIVITY_DISABLED",
            "LOT32_REMAINS_LOCKED",
        )
        if self.reason_codes != expected_reasons:
            raise SourceRegistryValidationError("unexpected Lot 31 reason code sequence")
        validate_fail_closed_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "market-data-governance-scope-source-registry-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "generated_at": self.generated_at,
            "available_at": self.available_at,
            "validation_state": self.validation_state,
            "source_registry": self.source_registry.to_dict(),
            "capability_matrix": [item.to_dict() for item in self.capability_matrix],
            "contract_registry": [item.to_dict() for item in self.contract_registry],
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["output_checksum"] = self.output_checksum
        return payload


@dataclass(frozen=True, slots=True)
class MarketDataGovernanceScopeSourceRegistryAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    source_count: int
    source_of_truth_count: int
    backup_source_count: int
    disabled_connection_count: int
    capability_count: int
    contract_count: int
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit)
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        if self.source_count != 3:
            raise SourceRegistryValidationError("Lot 31 audit expects exactly three sources")
        if self.source_of_truth_count != 1 or self.backup_source_count != 2:
            raise SourceRegistryValidationError("Lot 31 audit source roles differ")
        if self.disabled_connection_count != self.source_count:
            raise SourceRegistryValidationError("every Lot 31 source must remain disabled")
        if self.capability_count < 5 or self.contract_count != 5:
            raise SourceRegistryValidationError("Lot 31 audit registry counts differ")
        if self.validation_state != "VALIDATED_METADATA_ONLY":
            raise SourceRegistryValidationError("unexpected audit validation_state")
        validate_fail_closed_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        return {
            "schema_version": "market-data-governance-scope-source-registry-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "source_count": self.source_count,
            "source_of_truth_count": self.source_of_truth_count,
            "backup_source_count": self.backup_source_count,
            "disabled_connection_count": self.disabled_connection_count,
            "capability_count": self.capability_count,
            "contract_count": self.contract_count,
            "validation_state": self.validation_state,
            **self.safety,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload_without_checksum()
        payload["audit_checksum"] = self.audit_checksum
        return payload
