from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    build_lot31_artifacts,
    canonical_checksum,
    load_json_object,
    persist_lot31_artifacts,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry_models import (
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

COMMIT = "0123456789abcdef0123456789abcdef01234567"
SHA = "a" * 64
UTC = "2026-08-06T00:00:00Z"


def source(
    source_id: str = "kraken-public-spot-metadata",
    *,
    truth: bool = True,
    backups: tuple[str, ...] = (),
) -> SourceRegistryEntryV1:
    return SourceRegistryEntryV1(
        source_id=source_id,
        provider="Provider",
        venue="VENUE",
        endpoint_type="PUBLIC_REFERENCE_METADATA",
        endpoint_descriptor="metadata-contract-only-no-network-call",
        fields=("exchange_symbol", "market_status"),
        cadence=86400,
        timezone="UTC",
        license="PUBLIC_EXCHANGE_TERMS_REVIEW_REQUIRED",
        auth_mode="NONE",
        retention=3650,
        criticality="PRIMARY" if truth else "SECONDARY",
        source_of_truth=truth,
        backup_sources=backups,
        source_schema_version=f"{source_id}-v1",
        revision=1,
        revision_policy="IMMUTABLE_VERSIONED_REPLACEMENT",
        approved=True,
        enabled=False,
        connection_status="DISABLED",
    )


def contract(name: str) -> ContractRegistryEntryV1:
    return ContractRegistryEntryV1(
        contract_name=name,
        owner="MarketDataGovernanceDomain",
        schema_path="contracts/schemas/source_registry_v1.schema.json",
        producer="Lot31",
        status="IMPLEMENTED_METADATA_ONLY",
    )


def capability(name: str, contract_name: str = "SourceRegistryV1") -> CapabilityMatrixEntryV1:
    return CapabilityMatrixEntryV1(
        capability=name,
        status="REQUIRED",
        owner="MarketDataGovernanceDomain",
        contract=contract_name,
        gate="LOT31_ENTRY_GATE",
    )


def state() -> MarketDataGovernanceScopeSourceRegistryStateV1:
    registry = SourceRegistryV1(
        registry_id="registry",
        registry_version="1.0.0",
        source_of_truth_id="kraken-public-spot-metadata",
        sources=(source(),),
        revision_policy="IMMUTABLE_VERSIONED_REPLACEMENT",
    )
    initial = MarketDataGovernanceScopeSourceRegistryStateV1(
        run_context=RunContextV1("run", "DATA_GOVERNANCE_ONLY", "config-v1", COMMIT, "corr"),
        lineage=LineageEnvelopeV1(
            "lineage",
            30,
            "data/audit/v2_market_analysis_closure_lot30.json",
            SHA,
            UTC,
        ),
        event_time=UTC,
        generated_at=UTC,
        available_at=UTC,
        validation_state="VALIDATED_METADATA_ONLY",
        source_registry=registry,
        capability_matrix=(capability("source_registry"),),
        contract_registry=(contract("SourceRegistryV1"),),
        metrics=Lot31MetricsV1(1, 0, 0),
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
    return replace(initial, output_checksum=canonical_checksum(initial.payload_without_checksum()))


def write_fixture_root(root: Path) -> None:
    config = json.loads(
        Path("config/data_governance/market_data_source_registry_v1.json").read_text(
            encoding="utf-8"
        )
    )
    atomic_write_json(root / "config/data_governance/market_data_source_registry_v1.json", config)
    atomic_write_json(
        root / "data/audit/lot31_v3_entry_gate.json",
        {
            "gate_status": "GO_LOT31_IMPLEMENTATION_ENTRY",
            "target_lot": 31,
            "target_version": "V3_MARKET_DATA_GOVERNANCE",
            "owner": "MarketDataGovernanceDomain",
            "package_boundary": "src/crypto_quant_bot/data_governance",
            "runtime_mode": "DATA_GOVERNANCE_ONLY",
            "human_decision": "APPROVED_START_LOT31",
            "implementation_started": False,
            "next_lot_status": "PLANNED_LOCKED",
            "safety": fail_closed_safety(),
        },
    )
    atomic_write_json(
        root / "data/audit/v2_market_analysis_closure_lot30.json",
        {"output_checksum": SHA},
    )


def test_build_is_deterministic_and_metadata_only(tmp_path: Path) -> None:
    write_fixture_root(tmp_path)
    first_state, first_audit = build_lot31_artifacts(tmp_path, COMMIT)
    second_state, second_audit = build_lot31_artifacts(tmp_path, COMMIT)

    assert first_state.to_dict() == second_state.to_dict()
    assert first_audit.to_dict() == second_audit.to_dict()
    assert first_state.output_checksum == canonical_checksum(first_state.payload_without_checksum())
    assert first_audit.audit_checksum == canonical_checksum(first_audit.payload_without_checksum())
    assert first_state.validation_state == "VALIDATED_METADATA_ONLY"
    assert first_state.run_context.runtime_mode == "DATA_GOVERNANCE_ONLY"
    assert first_state.safety == fail_closed_safety()
    assert first_audit.safety == fail_closed_safety()

    sources = first_state.source_registry.sources
    assert tuple(item.source_id for item in sources) == tuple(
        sorted(item.source_id for item in sources)
    )
    assert len(sources) == 3
    assert sum(item.source_of_truth for item in sources) == 1
    assert all(item.auth_mode == "NONE" for item in sources)
    assert all(item.enabled is False for item in sources)
    assert all(item.connection_status == "DISABLED" for item in sources)


def test_persisted_artifacts_are_linked_and_closed(tmp_path: Path) -> None:
    write_fixture_root(tmp_path)
    built_state, built_audit = build_lot31_artifacts(tmp_path, COMMIT)
    persist_lot31_artifacts(tmp_path, built_state, built_audit)

    persisted_state = load_json_object(
        tmp_path / "data/audit/market_data_governance_scope_and_source_registry_lot31.json"
    )
    persisted_audit = load_json_object(
        tmp_path / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
    )
    persisted_registry = load_json_object(tmp_path / "data/audit/source_registry_lot31.json")

    assert persisted_state == built_state.to_dict()
    assert persisted_audit == built_audit.to_dict()
    assert persisted_registry == built_state.source_registry.to_dict()
    assert persisted_audit["state_output_checksum"] == persisted_state["output_checksum"]
    assert persisted_state["source_registry"] == persisted_registry
    statuses = {item["capability"]: item["status"] for item in persisted_state["capability_matrix"]}
    assert statuses["instrument_normalization"] == "DISABLED"


def test_atomic_write_replaces_complete_json(tmp_path: Path) -> None:
    target = tmp_path / "nested/artifact.json"
    atomic_write_json(target, {"value": 1})
    atomic_write_json(target, {"value": 2, "status": "PASS"})
    assert target.read_text(encoding="utf-8") == '{\n  "status": "PASS",\n  "value": 2\n}\n'
    assert not list(target.parent.glob(f".{target.name}.*"))


def test_load_json_object_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(SourceRegistryValidationError, match="expected JSON object"):
        load_json_object(path)


def test_serialization_contains_gate_required_source_fields() -> None:
    payload = source().to_dict()
    required = {
        "source_id",
        "provider",
        "venue",
        "endpoint_type",
        "fields",
        "cadence",
        "timezone",
        "license",
        "auth_mode",
        "retention",
        "criticality",
        "source_of_truth",
        "backup_sources",
        "revision_policy",
    }
    assert required <= payload.keys()
    assert payload["schema_version"] == "source-registry-entry-v1"


def test_state_and_audit_serialization_are_exactly_linked() -> None:
    built_state = state()
    audit = MarketDataGovernanceScopeSourceRegistryAuditV1(
        code_commit=COMMIT,
        state_output_checksum=built_state.output_checksum,
        config_checksum="b" * 64,
        source_count=3,
        source_of_truth_count=1,
        backup_source_count=2,
        disabled_connection_count=3,
        capability_count=9,
        contract_count=5,
        validation_state="VALIDATED_METADATA_ONLY",
        safety=fail_closed_safety(),
        audit_checksum="c" * 64,
    )
    assert built_state.to_dict()["output_checksum"] == built_state.output_checksum
    assert audit.to_dict()["state_output_checksum"] == built_state.output_checksum
    assert audit.to_dict()["approved_size"] == 0
