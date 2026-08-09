from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .microstructure_scope_and_offline_data_contracts_validation import (
    ALLOWED_API_KINDS,
    ALLOWED_API_STATUSES,
    ALLOWED_CAPABILITY_CLASSIFICATIONS,
    ALLOWED_CONTRACT_KINDS,
    ALLOWED_CONTRACT_STATUSES,
    MicrostructureScopeValidationError,
    require_capability_id,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    require_unique,
    validate_contract_schema_path,
    validate_causal_times,
    validate_lot37_safety,
    validate_reason_codes,
    validate_runtime_mode,
)


@dataclass(frozen=True, slots=True)
class Lot37RunContextV1:
    run_id: str
    runtime_mode: str
    config_version: str
    code_commit: str
    correlation_id: str

    def __post_init__(self) -> None:
        require_text(self.run_id, "run_id")
        validate_runtime_mode(self.runtime_mode)
        require_text(self.config_version, "config_version")
        require_git_sha(self.code_commit, "code_commit")
        require_text(self.correlation_id, "correlation_id")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot37-run-context-v1",
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "config_version": self.config_version,
            "code_commit": self.code_commit,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True, slots=True)
class Lot37LineageEnvelopeV1:
    lineage_id: str
    entry_gate_checksum: str
    v3_post_merge_audit_commit: str
    lot36_state_checksum: str
    lot36_audit_checksum: str
    l2_fixture_checksum: str
    trade_fixture_checksum: str
    available_at: str

    def __post_init__(self) -> None:
        require_text(self.lineage_id, "lineage_id")
        require_sha256(self.entry_gate_checksum, "entry_gate_checksum")
        require_git_sha(self.v3_post_merge_audit_commit, "v3_post_merge_audit_commit")
        require_sha256(self.lot36_state_checksum, "lot36_state_checksum")
        require_sha256(self.lot36_audit_checksum, "lot36_audit_checksum")
        require_sha256(self.l2_fixture_checksum, "l2_fixture_checksum")
        require_sha256(self.trade_fixture_checksum, "trade_fixture_checksum")
        validate_causal_times(self.available_at, self.available_at, self.available_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot37-lineage-envelope-v1",
            "lineage_id": self.lineage_id,
            "entry_gate_checksum": self.entry_gate_checksum,
            "v3_post_merge_audit_commit": self.v3_post_merge_audit_commit,
            "lot36_state_checksum": self.lot36_state_checksum,
            "lot36_audit_checksum": self.lot36_audit_checksum,
            "l2_fixture_checksum": self.l2_fixture_checksum,
            "trade_fixture_checksum": self.trade_fixture_checksum,
            "available_at": self.available_at,
        }


@dataclass(frozen=True, slots=True)
class ContractRegistryEntryV1:
    contract_name: str
    contract_kind: str
    owner: str
    schema_path: str
    producer: str
    consumer: str
    status: str
    enabled_by_lot: int

    def __post_init__(self) -> None:
        for field, value in (
            ("contract_name", self.contract_name),
            ("owner", self.owner),
            ("producer", self.producer),
            ("consumer", self.consumer),
        ):
            require_text(value, field)
        if self.contract_kind not in ALLOWED_CONTRACT_KINDS:
            raise MicrostructureScopeValidationError("unknown contract kind")
        if self.status not in ALLOWED_CONTRACT_STATUSES:
            raise MicrostructureScopeValidationError("unknown contract status")
        if self.owner != "MicrostructureDomain":
            raise MicrostructureScopeValidationError("Lot 37 contracts require MicrostructureDomain")
        validate_contract_schema_path(self.schema_path)
        require_integer(self.enabled_by_lot, "enabled_by_lot", minimum=37)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot37-contract-registry-entry-v1",
            "contract_name": self.contract_name,
            "contract_kind": self.contract_kind,
            "owner": self.owner,
            "schema_path": self.schema_path,
            "producer": self.producer,
            "consumer": self.consumer,
            "status": self.status,
            "enabled_by_lot": self.enabled_by_lot,
        }


@dataclass(frozen=True, slots=True)
class MicrostructureScopeOfflineDataContractsContractRegistryV1:
    registry_id: str
    registry_version: str
    entries: tuple[ContractRegistryEntryV1, ...]

    def __post_init__(self) -> None:
        require_text(self.registry_id, "registry_id")
        require_text(self.registry_version, "registry_version")
        if not self.entries:
            raise MicrostructureScopeValidationError("contract registry cannot be empty")
        require_unique(tuple(item.contract_name for item in self.entries), "contract registry")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "microstructure-scope-offline-data-contracts-contract-registry-v1",
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "entries": [item.to_dict() for item in self.entries],
        }


@dataclass(frozen=True, slots=True)
class CapabilityMatrixEntryV1:
    capability_id: str
    title: str
    classification: str
    owner: str
    enabled_by_lot: int
    implementation_status: str
    contract_ref: str
    gate_ref: str

    def __post_init__(self) -> None:
        require_capability_id(self.capability_id)
        for field, value in (
            ("title", self.title),
            ("owner", self.owner),
            ("implementation_status", self.implementation_status),
            ("contract_ref", self.contract_ref),
            ("gate_ref", self.gate_ref),
        ):
            require_text(value, field)
        if self.classification not in ALLOWED_CAPABILITY_CLASSIFICATIONS:
            raise MicrostructureScopeValidationError("unknown capability classification")
        require_integer(self.enabled_by_lot, "enabled_by_lot")
        self._validate_activation_boundary()

    def _validate_activation_boundary(self) -> None:
        if self.classification == "REQUIRED":
            if self.enabled_by_lot != 37 or self.implementation_status != "ACTIVE_LOT37_SCOPE":
                raise MicrostructureScopeValidationError("required Lot 37 capability is not active scope")
        elif self.classification == "DISABLED":
            if not 38 <= self.enabled_by_lot <= 52 or self.implementation_status != "PLANNED_LOCKED":
                raise MicrostructureScopeValidationError("future V4 capability must remain planned locked")
        elif self.classification == "FORBIDDEN":
            if self.enabled_by_lot != 0 or not self.implementation_status.startswith("FORBIDDEN_"):
                raise MicrostructureScopeValidationError("forbidden capability cannot have an enabling lot")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot37-capability-matrix-entry-v1",
            "capability_id": self.capability_id,
            "title": self.title,
            "classification": self.classification,
            "owner": self.owner,
            "enabled_by_lot": self.enabled_by_lot,
            "implementation_status": self.implementation_status,
            "contract_ref": self.contract_ref,
            "gate_ref": self.gate_ref,
        }


@dataclass(frozen=True, slots=True)
class MicrostructureScopeOfflineDataContractsCapabilityMatrixV1:
    matrix_id: str
    matrix_version: str
    entries: tuple[CapabilityMatrixEntryV1, ...]

    def __post_init__(self) -> None:
        require_text(self.matrix_id, "matrix_id")
        require_text(self.matrix_version, "matrix_version")
        if not self.entries:
            raise MicrostructureScopeValidationError("capability matrix cannot be empty")
        require_unique(tuple(item.capability_id for item in self.entries), "capability matrix")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "microstructure-scope-offline-data-contracts-capability-matrix-v1",
            "matrix_id": self.matrix_id,
            "matrix_version": self.matrix_version,
            "entries": [item.to_dict() for item in self.entries],
        }


@dataclass(frozen=True, slots=True)
class PublicApiEntryV1:
    symbol: str
    module: str
    kind: str
    status: str

    def __post_init__(self) -> None:
        require_text(self.symbol, "symbol")
        require_text(self.module, "module")
        if not self.module.startswith("crypto_quant_bot.microstructure"):
            raise MicrostructureScopeValidationError("public API must stay in MicrostructureDomain")
        if self.kind not in ALLOWED_API_KINDS:
            raise MicrostructureScopeValidationError("unknown public API kind")
        if self.status not in ALLOWED_API_STATUSES:
            raise MicrostructureScopeValidationError("unknown public API status")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "lot37-public-api-entry-v1",
            "symbol": self.symbol,
            "module": self.module,
            "kind": self.kind,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class Lot37MetricsV1:
    contracts_total: int
    capabilities_total: int
    required_capabilities_total: int
    disabled_capabilities_total: int
    forbidden_capabilities_total: int
    public_api_symbols_total: int
    offline_fixture_total: int
    validation_failures_total: int
    processing_latency_us: int

    def __post_init__(self) -> None:
        for field, value in self.to_dict().items():
            if field != "schema_version":
                require_integer(value, field)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "lot37-metrics-v1",
            "lot_37_contracts_total": self.contracts_total,
            "lot_37_capabilities_total": self.capabilities_total,
            "lot_37_required_capabilities_total": self.required_capabilities_total,
            "lot_37_disabled_capabilities_total": self.disabled_capabilities_total,
            "lot_37_forbidden_capabilities_total": self.forbidden_capabilities_total,
            "lot_37_public_api_symbols_total": self.public_api_symbols_total,
            "lot_37_offline_fixture_total": self.offline_fixture_total,
            "lot_37_validation_failures_total": self.validation_failures_total,
            "lot_37_processing_latency_us": self.processing_latency_us,
        }


@dataclass(frozen=True, slots=True)
class MicrostructureScopeOfflineDataContractsStateV1:
    run_context: Lot37RunContextV1
    lineage: Lot37LineageEnvelopeV1
    event_time: str
    available_at: str
    generated_at: str
    validation_state: str
    contract_registry: MicrostructureScopeOfflineDataContractsContractRegistryV1
    capability_matrix: MicrostructureScopeOfflineDataContractsCapabilityMatrixV1
    public_api: tuple[PublicApiEntryV1, ...]
    metrics: Lot37MetricsV1
    reason_codes: tuple[str, ...]
    safety: dict[str, object]
    output_checksum: str

    def __post_init__(self) -> None:
        validate_causal_times(self.event_time, self.available_at, self.generated_at)
        if self.validation_state != "VALIDATED_OFFLINE_CONTRACT_SCOPE":
            raise MicrostructureScopeValidationError("unknown Lot 37 validation state")
        if not self.public_api:
            raise MicrostructureScopeValidationError("Lot 37 requires an explicit public API")
        require_unique(tuple(item.symbol for item in self.public_api), "public API")
        validate_reason_codes(self.reason_codes)
        validate_lot37_safety(self.safety)
        require_sha256(self.output_checksum, "output_checksum")

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("output_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "microstructure-scope-offline-data-contracts-state-v1",
            "run_context": self.run_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "event_time": self.event_time,
            "available_at": self.available_at,
            "generated_at": self.generated_at,
            "validation_state": self.validation_state,
            "contract_registry": self.contract_registry.to_dict(),
            "capability_matrix": self.capability_matrix.to_dict(),
            "public_api": [item.to_dict() for item in self.public_api],
            "metrics": self.metrics.to_dict(),
            "reason_codes": list(self.reason_codes),
            "safety": dict(self.safety),
            "output_checksum": self.output_checksum,
        }


@dataclass(frozen=True, slots=True)
class MicrostructureScopeOfflineDataContractsAuditV1:
    code_commit: str
    state_output_checksum: str
    config_checksum: str
    entry_gate_checksum: str
    contract_registry_checksum: str
    capability_matrix_checksum: str
    validation_state: str
    safety: dict[str, object]
    audit_checksum: str

    def __post_init__(self) -> None:
        require_git_sha(self.code_commit, "code_commit")
        for field, value in (
            ("state_output_checksum", self.state_output_checksum),
            ("config_checksum", self.config_checksum),
            ("entry_gate_checksum", self.entry_gate_checksum),
            ("contract_registry_checksum", self.contract_registry_checksum),
            ("capability_matrix_checksum", self.capability_matrix_checksum),
            ("audit_checksum", self.audit_checksum),
        ):
            require_sha256(value, field)
        if self.validation_state != "VALIDATED_OFFLINE_CONTRACT_SCOPE":
            raise MicrostructureScopeValidationError("unknown Lot 37 audit validation state")
        validate_lot37_safety(self.safety)

    def payload_without_checksum(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("audit_checksum")
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "microstructure-scope-offline-data-contracts-audit-v1",
            "code_commit": self.code_commit,
            "state_output_checksum": self.state_output_checksum,
            "config_checksum": self.config_checksum,
            "entry_gate_checksum": self.entry_gate_checksum,
            "contract_registry_checksum": self.contract_registry_checksum,
            "capability_matrix_checksum": self.capability_matrix_checksum,
            "validation_state": self.validation_state,
            "safety": dict(self.safety),
            "audit_checksum": self.audit_checksum,
        }
