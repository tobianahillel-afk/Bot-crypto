from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from .market_data_governance_scope_and_source_registry_models import (
    CapabilityMatrixEntryV1,
    ContractRegistryEntryV1,
    LineageEnvelopeV1,
    Lot31MetricsV1,
    MarketDataGovernanceScopeSourceRegistryAuditV1,
    MarketDataGovernanceScopeSourceRegistryStateV1,
    RunContextV1,
    SourceRegistryEntryV1,
    SourceRegistryV1,
    SourceRegistryValidationError,
    fail_closed_safety,
)


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SourceRegistryValidationError(f"expected JSON object: {path}")
    return payload


def atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _build_source(raw: dict[str, Any]) -> SourceRegistryEntryV1:
    return SourceRegistryEntryV1(
        source_id=str(raw["source_id"]),
        provider=str(raw["provider"]),
        venue=str(raw["venue"]),
        endpoint_type=str(raw["endpoint_type"]),
        endpoint_descriptor=str(raw["endpoint_descriptor"]),
        fields=tuple(str(value) for value in raw["fields"]),
        cadence=int(raw["cadence"]),
        timezone=str(raw["timezone"]),
        license=str(raw["license"]),
        auth_mode=str(raw["auth_mode"]),
        retention=int(raw["retention"]),
        criticality=str(raw["criticality"]),
        source_of_truth=raw["source_of_truth"] is True,
        backup_sources=tuple(str(value) for value in raw["backup_sources"]),
        source_schema_version=str(raw["source_schema_version"]),
        revision=int(raw["revision"]),
        revision_policy=str(raw["revision_policy"]),
        approved=raw["approved"] is True,
        enabled=raw["enabled"] is True,
        connection_status=str(raw["connection_status"]),
    )


def _build_capability(raw: dict[str, Any]) -> CapabilityMatrixEntryV1:
    return CapabilityMatrixEntryV1(
        capability=str(raw["capability"]),
        status=str(raw["status"]),
        owner=str(raw["owner"]),
        contract=str(raw["contract"]),
        gate=str(raw["gate"]),
    )


def _build_contract(raw: dict[str, Any]) -> ContractRegistryEntryV1:
    return ContractRegistryEntryV1(
        contract_name=str(raw["contract_name"]),
        owner=str(raw["owner"]),
        schema_path=str(raw["schema_path"]),
        producer=str(raw["producer"]),
        status=str(raw["status"]),
    )


def _verify_entry_gate(gate: dict[str, Any]) -> None:
    expected = {
        "gate_status": "GO_LOT31_IMPLEMENTATION_ENTRY",
        "target_lot": 31,
        "target_version": "V3_MARKET_DATA_GOVERNANCE",
        "owner": "MarketDataGovernanceDomain",
        "package_boundary": "src/crypto_quant_bot/data_governance",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "human_decision": "APPROVED_START_LOT31",
        "implementation_started": False,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise SourceRegistryValidationError("Lot 31 entry gate does not authorize this implementation")
    safety = gate.get("safety")
    if not isinstance(safety, dict) or safety != fail_closed_safety():
        raise SourceRegistryValidationError("Lot 31 entry gate safety boundary changed")


def _build_run_context(config: dict[str, Any], code_commit: str) -> RunContextV1:
    return RunContextV1(
        run_id=str(config["run_id"]),
        runtime_mode="DATA_GOVERNANCE_ONLY",
        config_version=str(config["config_version"]),
        code_commit=code_commit,
        correlation_id=str(config["correlation_id"]),
    )


def _build_lineage(config: dict[str, Any], upstream_checksum: str) -> LineageEnvelopeV1:
    return LineageEnvelopeV1(
        lineage_id=str(config["lineage_id"]),
        upstream_lot=30,
        upstream_artifact_path="data/audit/v2_market_analysis_closure_lot30.json",
        upstream_artifact_checksum=upstream_checksum,
        available_at=str(config["available_at"]),
    )


def _build_registry(config: dict[str, Any]) -> SourceRegistryV1:
    sources = tuple(
        sorted(
            (_build_source(raw) for raw in config["sources"]),
            key=lambda item: item.source_id,
        )
    )
    return SourceRegistryV1(
        registry_id=str(config["registry_id"]),
        registry_version=str(config["registry_version"]),
        source_of_truth_id=str(config["source_of_truth_id"]),
        sources=sources,
        revision_policy=str(config["revision_policy"]),
    )


def _build_capabilities(config: dict[str, Any]) -> tuple[CapabilityMatrixEntryV1, ...]:
    return tuple(
        sorted(
            (_build_capability(raw) for raw in config["capability_matrix"]),
            key=lambda item: item.capability,
        )
    )


def _build_contracts(config: dict[str, Any]) -> tuple[ContractRegistryEntryV1, ...]:
    return tuple(
        sorted(
            (_build_contract(raw) for raw in config["contract_registry"]),
            key=lambda item: item.contract_name,
        )
    )


def _build_state(
    config: dict[str, Any],
    code_commit: str,
    upstream_checksum: str,
) -> MarketDataGovernanceScopeSourceRegistryStateV1:
    registry = _build_registry(config)
    state = MarketDataGovernanceScopeSourceRegistryStateV1(
        run_context=_build_run_context(config, code_commit),
        lineage=_build_lineage(config, upstream_checksum),
        event_time=str(config["event_time"]),
        generated_at=str(config["generated_at"]),
        available_at=str(config["available_at"]),
        validation_state="VALIDATED_METADATA_ONLY",
        source_registry=registry,
        capability_matrix=_build_capabilities(config),
        contract_registry=_build_contracts(config),
        metrics=Lot31MetricsV1(len(registry.sources), 0, 0),
        reason_codes=(
            "LOT31_ENTRY_GATE_VERIFIED",
            "SOURCE_REGISTRY_METADATA_VALIDATED",
            "SOURCE_OF_TRUTH_AND_BACKUPS_DECLARED",
            "EXTERNAL_CONNECTIVITY_DISABLED",
            "LOT32_REMAINS_LOCKED",
        ),
        safety=fail_closed_safety(),
        output_checksum="0" * 64,
    )
    return replace(state, output_checksum=canonical_checksum(state.payload_without_checksum()))


def _build_audit(
    state: MarketDataGovernanceScopeSourceRegistryStateV1,
    config_checksum: str,
) -> MarketDataGovernanceScopeSourceRegistryAuditV1:
    sources = state.source_registry.sources
    payload = MarketDataGovernanceScopeSourceRegistryAuditV1(
        code_commit=state.run_context.code_commit,
        state_output_checksum=state.output_checksum,
        config_checksum=config_checksum,
        source_count=len(sources),
        source_of_truth_count=sum(source.source_of_truth for source in sources),
        backup_source_count=sum(not source.source_of_truth for source in sources),
        disabled_connection_count=sum(source.connection_status == "DISABLED" for source in sources),
        capability_count=len(state.capability_matrix),
        contract_count=len(state.contract_registry),
        validation_state=state.validation_state,
        safety=fail_closed_safety(),
        audit_checksum="0" * 64,
    )
    checksum = canonical_checksum(payload.payload_without_checksum())
    return replace(payload, audit_checksum=checksum)


def build_lot31_artifacts(
    root: Path,
    code_commit: str,
) -> tuple[MarketDataGovernanceScopeSourceRegistryStateV1, MarketDataGovernanceScopeSourceRegistryAuditV1]:
    config_path = root / "config/data_governance/market_data_source_registry_v1.json"
    gate_path = root / "data/audit/lot31_v3_entry_gate.json"
    upstream_path = root / "data/audit/v2_market_analysis_closure_lot30.json"
    config = load_json_object(config_path)
    gate = load_json_object(gate_path)
    _verify_entry_gate(gate)
    state = _build_state(config, code_commit, file_checksum(upstream_path))
    audit = _build_audit(state, file_checksum(config_path))
    return state, audit


def persist_lot31_artifacts(
    root: Path,
    state: MarketDataGovernanceScopeSourceRegistryStateV1,
    audit: MarketDataGovernanceScopeSourceRegistryAuditV1,
) -> None:
    atomic_write_json(
        root / "data/audit/market_data_governance_scope_and_source_registry_lot31.json",
        state.to_dict(),
    )
    atomic_write_json(
        root / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json",
        audit.to_dict(),
    )
    atomic_write_json(root / "data/audit/source_registry_lot31.json", state.source_registry.to_dict())
