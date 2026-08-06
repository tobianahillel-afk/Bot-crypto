from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance import market_data_governance_scope_and_source_registry as engine
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry_models import (
    SourceRegistryValidationError,
    fail_closed_safety,
)
from test_lot31_market_data_governance_scope_and_source_registry import (
    COMMIT,
    write_fixture_root,
)


def test_canonical_checksum_has_a_fixed_oracle() -> None:
    assert engine.canonical_checksum({"b": 2, "a": [1, True, None]}) == (
        "d5138eba6545bfd591d7ac0cd424287d99ea070d60c623eabee2fc82697500bd"
    )


def test_file_checksum_has_a_fixed_oracle(tmp_path: Path) -> None:
    path = tmp_path / "bytes.txt"
    path.write_bytes(b"lot31\n")
    assert engine.file_checksum(path) == (
        "1561943c3097faa621d82e5991ef728e5c9350af6f8a6e5781e47a032c2721f6"
    )


def test_entry_gate_requires_every_identity_and_safety_field() -> None:
    gate = {
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
    }
    engine._verify_entry_gate(gate)
    for field in tuple(gate):
        mutated = dict(gate)
        mutated[field] = "MUTATED"
        with pytest.raises(SourceRegistryValidationError):
            engine._verify_entry_gate(mutated)


def test_build_artifacts_binds_config_and_upstream_checksums(tmp_path: Path) -> None:
    write_fixture_root(tmp_path)
    state, audit = engine.build_lot31_artifacts(tmp_path, COMMIT)
    config_path = tmp_path / "config/data_governance/market_data_source_registry_v1.json"
    upstream_path = tmp_path / "data/audit/v2_market_analysis_closure_lot30.json"
    assert state.lineage.upstream_artifact_checksum == engine.file_checksum(upstream_path)
    assert audit.config_checksum == engine.file_checksum(config_path)
    assert audit.state_output_checksum == state.output_checksum
    assert audit.source_count == 3
    assert audit.source_of_truth_count == 1
    assert audit.backup_source_count == 2
    assert audit.disabled_connection_count == 3
    assert audit.capability_count == 9
    assert audit.contract_count == 5


def test_source_builder_preserves_every_configured_field(tmp_path: Path) -> None:
    write_fixture_root(tmp_path)
    config = engine.load_json_object(
        tmp_path / "config/data_governance/market_data_source_registry_v1.json"
    )
    raw = config["sources"][0]
    built = engine._build_source(raw)
    payload = built.to_dict()
    for field in (
        "source_id",
        "provider",
        "venue",
        "endpoint_type",
        "endpoint_descriptor",
        "fields",
        "cadence",
        "timezone",
        "license",
        "auth_mode",
        "retention",
        "criticality",
        "source_of_truth",
        "backup_sources",
        "source_schema_version",
        "revision",
        "revision_policy",
        "approved",
        "enabled",
        "connection_status",
    ):
        assert payload[field] == raw[field]


def test_capability_and_contract_builders_preserve_fields(tmp_path: Path) -> None:
    write_fixture_root(tmp_path)
    config = engine.load_json_object(
        tmp_path / "config/data_governance/market_data_source_registry_v1.json"
    )
    capability = engine._build_capability(config["capability_matrix"][0]).to_dict()
    contract = engine._build_contract(config["contract_registry"][0]).to_dict()
    for field, value in config["capability_matrix"][0].items():
        assert capability[field] == value
    for field, value in config["contract_registry"][0].items():
        assert contract[field] == value


def test_unknown_source_and_active_connection_fail_before_publication(tmp_path: Path) -> None:
    write_fixture_root(tmp_path)
    config_path = tmp_path / "config/data_governance/market_data_source_registry_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["sources"][2]["backup_sources"].append("unknown-source")
    engine.atomic_write_json(config_path, config)
    with pytest.raises(SourceRegistryValidationError, match="unknown"):
        engine.build_lot31_artifacts(tmp_path, COMMIT)

    write_fixture_root(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["sources"][0]["enabled"] = True
    config["sources"][0]["connection_status"] = "CONNECTED"
    engine.atomic_write_json(config_path, config)
    with pytest.raises(SourceRegistryValidationError, match="connection-disabled"):
        engine.build_lot31_artifacts(tmp_path, COMMIT)


def test_persist_writes_three_distinct_artifacts(tmp_path: Path) -> None:
    write_fixture_root(tmp_path)
    state, audit = engine.build_lot31_artifacts(tmp_path, COMMIT)
    engine.persist_lot31_artifacts(tmp_path, state, audit)
    paths = (
        tmp_path / "data/audit/market_data_governance_scope_and_source_registry_lot31.json",
        tmp_path / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json",
        tmp_path / "data/audit/source_registry_lot31.json",
    )
    assert all(path.is_file() for path in paths)
    assert len({path.read_text(encoding="utf-8") for path in paths}) == 3
