from __future__ import annotations

from dataclasses import replace

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
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
    validate_fail_closed_safety,
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


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("run_id", "", "explicit and trimmed"),
        ("runtime_mode", "LOCAL_OFFLINE_ANALYSIS_ONLY", "DATA_GOVERNANCE_ONLY"),
        ("code_commit", "bad", "40-character git sha"),
        ("correlation_id", " corr ", "explicit and trimmed"),
    ],
)
def test_run_context_rejects_invalid_identity(field: str, value: object, message: str) -> None:
    values = {
        "run_id": "run",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "config_version": "config-v1",
        "code_commit": COMMIT,
        "correlation_id": "corr",
    }
    values[field] = value
    with pytest.raises(SourceRegistryValidationError, match=message):
        RunContextV1(**values)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("upstream_lot", 29, "originate from Lot 30"),
        ("upstream_artifact_path", "data/audit/other.json", "certified Lot 30"),
        ("upstream_artifact_checksum", "bad", "lowercase sha256"),
        ("available_at", "2026-08-06", "explicit UTC timestamp"),
    ],
)
def test_lineage_rejects_wrong_predecessor(field: str, value: object, message: str) -> None:
    values = {
        "lineage_id": "lineage",
        "upstream_lot": 30,
        "upstream_artifact_path": "data/audit/v2_market_analysis_closure_lot30.json",
        "upstream_artifact_checksum": SHA,
        "available_at": UTC,
    }
    values[field] = value
    with pytest.raises(SourceRegistryValidationError, match=message):
        LineageEnvelopeV1(**values)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"source_id": "UPPER"}, "lowercase"),
        ({"timezone": "Europe/Paris"}, "UTC"),
        ({"fields": ("symbol", "symbol")}, "unique"),
        ({"fields": ("api_key",)}, "secret material"),
        ({"endpoint_descriptor": "contains-access_token"}, "secret material"),
        ({"cadence": 0}, "positive"),
        ({"retention": -1}, "negative"),
        ({"criticality": "UNKNOWN"}, "criticality"),
        ({"source_of_truth": 1}, "explicit"),
        ({"revision": 0}, "positive"),
        ({"auth_mode": "API_KEY"}, "auth_mode=NONE"),
        ({"revision_policy": "MUTABLE"}, "revision policy"),
        ({"approved": False}, "explicitly approved"),
        ({"enabled": True}, "connection-disabled"),
        ({"connection_status": "CONNECTED"}, "connection-disabled"),
        ({"backup_sources": ("kraken-public-spot-metadata",)}, "back up itself"),
        ({"backup_sources": ("backup", "backup")}, "unique"),
    ],
)
def test_source_contract_is_fail_closed(change: dict[str, object], message: str) -> None:
    with pytest.raises(SourceRegistryValidationError, match=message):
        replace(source(), **change)


def test_capability_and_contract_registry_reject_invalid_entries() -> None:
    with pytest.raises(SourceRegistryValidationError, match="unknown capability status"):
        CapabilityMatrixEntryV1("source_registry", "ON", "owner", "contract", "gate")
    with pytest.raises(SourceRegistryValidationError, match="explicit and trimmed"):
        CapabilityMatrixEntryV1("", "REQUIRED", "owner", "contract", "gate")
    with pytest.raises(SourceRegistryValidationError, match="contracts/schemas"):
        replace(contract("SourceRegistryV1"), schema_path="docs/schema.json")
    with pytest.raises(SourceRegistryValidationError, match="canonical owner"):
        replace(contract("SourceRegistryV1"), owner="MarketAnalysisDomain")


def test_source_registry_rejects_duplicates_order_truth_unknown_and_cycles() -> None:
    truth = source(backups=("backup",))
    backup = source("backup", truth=False)
    valid = SourceRegistryV1(
        "registry",
        "1.0.0",
        truth.source_id,
        (backup, truth),
        "IMMUTABLE_VERSIONED_REPLACEMENT",
    )
    assert valid.source_of_truth_id == truth.source_id

    with pytest.raises(SourceRegistryValidationError, match="canonically ordered"):
        replace(valid, sources=(truth, backup))
    with pytest.raises(SourceRegistryValidationError, match="unique"):
        replace(valid, sources=(backup, backup))
    with pytest.raises(SourceRegistryValidationError, match="truth source"):
        replace(valid, source_of_truth_id="backup")
    with pytest.raises(SourceRegistryValidationError, match="exactly one"):
        replace(valid, sources=(replace(backup, source_of_truth=True), truth))
    with pytest.raises(SourceRegistryValidationError, match="unknown"):
        replace(valid, sources=(backup, replace(truth, backup_sources=("missing",))))
    with pytest.raises(SourceRegistryValidationError, match="acyclic"):
        cyclic_backup = replace(backup, backup_sources=(truth.source_id,))
        replace(valid, sources=(cyclic_backup, truth))
    with pytest.raises(SourceRegistryValidationError, match="revision policy"):
        replace(valid, revision_policy="MUTABLE")


def test_metrics_and_safety_reject_permissive_values() -> None:
    with pytest.raises(SourceRegistryValidationError, match="cannot be negative"):
        Lot31MetricsV1(-1, 0, 0)
    permissive = fail_closed_safety()
    permissive["trade_allowed"] = True
    with pytest.raises(SourceRegistryValidationError, match="exactly fail-closed"):
        validate_fail_closed_safety(permissive)


def test_state_rejects_temporal_registry_and_policy_mutations() -> None:
    valid = state()
    with pytest.raises(SourceRegistryValidationError, match="causal availability"):
        replace(valid, event_time="2026-08-07T00:00:00Z")
    with pytest.raises(SourceRegistryValidationError, match="validation_state"):
        replace(valid, validation_state="UNKNOWN")
    duplicated_capability = valid.capability_matrix * 2
    with pytest.raises(SourceRegistryValidationError, match="unique"):
        replace(valid, capability_matrix=duplicated_capability)
    unknown_capability = replace(valid.capability_matrix[0], contract="UnknownContract")
    with pytest.raises(SourceRegistryValidationError, match="unknown contract"):
        replace(valid, capability_matrix=(unknown_capability,))
    duplicate_contract = valid.contract_registry * 2
    with pytest.raises(SourceRegistryValidationError, match="unique"):
        replace(valid, contract_registry=duplicate_contract)
    with pytest.raises(SourceRegistryValidationError, match="reason code"):
        replace(valid, reason_codes=("PASS",))
    permissive = fail_closed_safety()
    permissive["execution_allowed"] = True
    with pytest.raises(SourceRegistryValidationError, match="fail-closed"):
        replace(valid, safety=permissive)
    with pytest.raises(SourceRegistryValidationError, match="lowercase sha256"):
        replace(valid, output_checksum="bad")


def test_audit_rejects_count_link_and_safety_mutations() -> None:
    valid = MarketDataGovernanceScopeSourceRegistryAuditV1(
        code_commit=COMMIT,
        state_output_checksum=SHA,
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
    mutations = (
        ({"source_count": 2}, "exactly three"),
        ({"source_of_truth_count": 0}, "source roles"),
        ({"backup_source_count": 1}, "source roles"),
        ({"disabled_connection_count": 2}, "remain disabled"),
        ({"capability_count": 4}, "registry counts"),
        ({"contract_count": 4}, "registry counts"),
        ({"validation_state": "UNKNOWN"}, "validation_state"),
        ({"config_checksum": "bad"}, "lowercase sha256"),
    )
    for change, message in mutations:
        with pytest.raises(SourceRegistryValidationError, match=message):
            replace(valid, **change)
