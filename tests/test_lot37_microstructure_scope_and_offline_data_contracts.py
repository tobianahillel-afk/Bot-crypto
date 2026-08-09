from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.microstructure_scope_and_offline_data_contracts import (
    CONFIG_PATH,
    EXPECTED_FORBIDDEN_CAPABILITIES,
    EXPECTED_FUTURE_LOTS,
    _build_capability_matrix,
    _build_contract_registry,
    _build_public_api,
    _objects,
    _validate_config,
    _verify_fixture,
    build_lot37_artifacts,
    write_lot37_artifacts,
)
from crypto_quant_bot.microstructure.microstructure_scope_and_offline_data_contracts_models import (
    CapabilityMatrixEntryV1,
    ContractRegistryEntryV1,
    MicrostructureScopeOfflineDataContractsCapabilityMatrixV1,
    PublicApiEntryV1,
)
from crypto_quant_bot.microstructure.microstructure_scope_and_offline_data_contracts_validation import (
    MicrostructureScopeValidationError,
    duration_us,
    lot37_safety,
    parse_utc_timestamp,
    require_capability_id,
    require_git_sha,
    require_integer,
    require_sha256,
    require_text,
    require_unique,
    validate_causal_times,
    validate_contract_schema_path,
    validate_lot37_safety,
    validate_reason_codes,
    validate_runtime_mode,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "1" * 40


def _copy_reference_root(tmp_path: Path) -> Path:
    paths = [
        CONFIG_PATH,
        Path("data/audit/lot37_v4_entry_gate.json"),
        Path("data/audit/roadmap_lifecycle_overlay_lot36.json"),
        Path("tests/fixtures/lot37/offline_l2_availability_fixture_v1.json"),
        Path("tests/fixtures/lot37/offline_trade_availability_fixture_v1.json"),
        Path("contracts/schemas/microstructure_offline_l2_input_v1.schema.json"),
        Path("contracts/schemas/microstructure_offline_trade_input_v1.schema.json"),
        Path("contracts/schemas/microstructure_scope_offline_data_contracts_state_v1.schema.json"),
        Path("contracts/schemas/microstructure_scope_offline_data_contracts_audit_v1.schema.json"),
        Path("contracts/schemas/microstructure_scope_offline_data_contracts_contract_registry_v1.schema.json"),
        Path("contracts/schemas/microstructure_scope_offline_data_contracts_capability_matrix_v1.schema.json"),
    ]
    for relative in paths:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    return tmp_path


def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _refresh_gate(root: Path) -> dict[str, object]:
    path = root / "data/audit/lot37_v4_entry_gate.json"
    gate = _load(path)
    gate.pop("output_checksum", None)
    gate["output_checksum"] = canonical_checksum(gate)
    _write(path, gate)
    return gate


def test_lot37_reference_build_is_deterministic() -> None:
    state_a, audit_a = build_lot37_artifacts(ROOT, CODE_COMMIT)
    state_b, audit_b = build_lot37_artifacts(ROOT, CODE_COMMIT)
    assert state_a.to_dict() == state_b.to_dict()
    assert audit_a.to_dict() == audit_b.to_dict()
    assert state_a.validation_state == "VALIDATED_OFFLINE_CONTRACT_SCOPE"
    assert state_a.metrics.contracts_total == 6
    assert state_a.metrics.capabilities_total == 27
    assert state_a.metrics.required_capabilities_total == 4
    assert state_a.metrics.disabled_capabilities_total == 15
    assert state_a.metrics.forbidden_capabilities_total == 8
    assert state_a.metrics.processing_latency_us == 950_000
    assert audit_a.state_output_checksum == state_a.output_checksum
    assert canonical_checksum(state_a.payload_without_checksum()) == state_a.output_checksum
    assert canonical_checksum(audit_a.payload_without_checksum()) == audit_a.audit_checksum


def test_lot37_future_and_forbidden_capabilities_remain_locked() -> None:
    state, _ = build_lot37_artifacts(ROOT, CODE_COMMIT)
    by_id = {entry.capability_id: entry for entry in state.capability_matrix.entries}
    for capability, lot in EXPECTED_FUTURE_LOTS.items():
        assert by_id[capability].classification == "DISABLED"
        assert by_id[capability].enabled_by_lot == lot
        assert by_id[capability].implementation_status == "PLANNED_LOCKED"
    for capability in EXPECTED_FORBIDDEN_CAPABILITIES:
        assert by_id[capability].classification == "FORBIDDEN"
        assert by_id[capability].enabled_by_lot == 0
    assert state.safety == lot37_safety()


def test_lot37_write_persists_four_consistent_outputs(tmp_path: Path) -> None:
    root = _copy_reference_root(tmp_path)
    paths = write_lot37_artifacts(root, CODE_COMMIT)
    assert set(paths) == {"state", "audit", "contract_registry", "capability_matrix"}
    state = _load(root / paths["state"])
    audit = _load(root / paths["audit"])
    registry = _load(root / paths["contract_registry"])
    matrix = _load(root / paths["capability_matrix"])
    assert state["contract_registry"] == registry
    assert state["capability_matrix"] == matrix
    assert audit["state_output_checksum"] == state["output_checksum"]


def test_gate_tamper_is_fail_closed(tmp_path: Path) -> None:
    root = _copy_reference_root(tmp_path)
    gate_path = root / "data/audit/lot37_v4_entry_gate.json"
    gate = _load(gate_path)
    gate["gate_status"] = "NO_GO"
    _write(gate_path, gate)
    with pytest.raises(MicrostructureScopeValidationError, match="entry gate checksum changed"):
        build_lot37_artifacts(root, CODE_COMMIT)


def test_v3_closure_tamper_is_fail_closed(tmp_path: Path) -> None:
    root = _copy_reference_root(tmp_path)
    overlay_path = root / "data/audit/roadmap_lifecycle_overlay_lot36.json"
    overlay = _load(overlay_path)
    assert isinstance(overlay["lots"], dict)
    overlay["lots"]["36"]["v3_closed"] = False
    _write(overlay_path, overlay)
    with pytest.raises(MicrostructureScopeValidationError, match="V3 post-merge closure"):
        build_lot37_artifacts(root, CODE_COMMIT)


def test_classified_trade_fixture_is_rejected(tmp_path: Path) -> None:
    root = _copy_reference_root(tmp_path)
    fixture_path = root / "tests/fixtures/lot37/offline_trade_availability_fixture_v1.json"
    fixture = _load(fixture_path)
    assert isinstance(fixture["trades"], list)
    fixture["trades"][0]["side"] = "BUY_AGGRESSOR"
    _write(fixture_path, fixture)
    gate = _load(root / "data/audit/lot37_v4_entry_gate.json")
    assert isinstance(gate["prerequisites"], dict)
    gate["prerequisites"]["offline_trade_fixture_sha256"] = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    _write(root / "data/audit/lot37_v4_entry_gate.json", gate)
    _refresh_gate(root)
    with pytest.raises(MicrostructureScopeValidationError):
        build_lot37_artifacts(root, CODE_COMMIT)


def test_fixture_semantics_reject_decision_and_stale_data(tmp_path: Path) -> None:
    root = _copy_reference_root(tmp_path)
    fixture_path = root / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json"
    fixture = _load(fixture_path)
    fixture["used_for_decision"] = True
    _write(fixture_path, fixture)
    digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    with pytest.raises(MicrostructureScopeValidationError, match="cannot be decision data"):
        _verify_fixture(root, str(fixture_path.relative_to(root)), digest, "2026-08-06T19:18:41.000000Z", 1_000_000)
    fixture["used_for_decision"] = False
    fixture["available_at"] = "2026-08-06T19:18:39.000000Z"
    fixture["event_time"] = "2026-08-06T19:18:38.000000Z"
    _write(fixture_path, fixture)
    digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    with pytest.raises(MicrostructureScopeValidationError, match="freshness"):
        _verify_fixture(root, str(fixture_path.relative_to(root)), digest, "2026-08-06T19:18:41.000000Z", 1_000_000)


def test_config_and_registry_fail_closed(tmp_path: Path) -> None:
    config = _load(ROOT / CONFIG_PATH)
    config["unexpected"] = True
    with pytest.raises(MicrostructureScopeValidationError, match="config fields"):
        _validate_config(config)
    root = _copy_reference_root(tmp_path)
    config = _load(root / CONFIG_PATH)
    schema = root / "contracts/schemas/microstructure_offline_l2_input_v1.schema.json"
    schema.unlink()
    with pytest.raises(MicrostructureScopeValidationError, match="schema missing"):
        _build_contract_registry(root, config)


def test_public_api_membership_is_exact() -> None:
    config = _load(ROOT / CONFIG_PATH)
    assert isinstance(config["public_api"], list)
    config["public_api"][0]["symbol"] = "unexpected_symbol"
    with pytest.raises(MicrostructureScopeValidationError, match="public API set changed"):
        _build_public_api(config)


def test_model_activation_boundaries_are_fail_closed() -> None:
    with pytest.raises(MicrostructureScopeValidationError, match="planned locked"):
        CapabilityMatrixEntryV1("LOT38_TEST", "test", "DISABLED", "MicrostructureDomain", 37, "PLANNED_LOCKED", "X", "LOT38")
    with pytest.raises(MicrostructureScopeValidationError, match="enabling lot"):
        CapabilityMatrixEntryV1("TRADING", "trading", "FORBIDDEN", "LiveGovernanceDomain", 37, "FORBIDDEN_BY_LOT37", "NONE", "NO_GATE")
    with pytest.raises(MicrostructureScopeValidationError, match="MicrostructureDomain"):
        ContractRegistryEntryV1("X", "INPUT", "OtherDomain", "contracts/schemas/x.schema.json", "P", "C", "ACTIVE_LOT37_CONTRACT", 37)
    with pytest.raises(MicrostructureScopeValidationError, match="MicrostructureDomain"):
        PublicApiEntryV1("x", "crypto_quant_bot.execution.x", "FUNCTION", "ACTIVE_LOT37_API")


def test_capability_matrix_rejects_duplicate_ids() -> None:
    entry = CapabilityMatrixEntryV1("V4_SCOPE_BOUNDARY", "scope", "REQUIRED", "MicrostructureDomain", 37, "ACTIVE_LOT37_SCOPE", "StateV1", "LOT37")
    with pytest.raises(MicrostructureScopeValidationError, match="unique"):
        MicrostructureScopeOfflineDataContractsCapabilityMatrixV1("matrix", "1", (entry, entry))


def test_low_level_validation_boundaries() -> None:
    assert require_text("x", "field") == "x"
    assert require_integer(0, "field") == 0
    with pytest.raises(MicrostructureScopeValidationError):
        require_text("", "field")
    with pytest.raises(MicrostructureScopeValidationError):
        require_integer(True, "field")
    with pytest.raises(MicrostructureScopeValidationError):
        require_git_sha("ABC", "sha")
    with pytest.raises(MicrostructureScopeValidationError):
        require_sha256("abc", "checksum")
    with pytest.raises(MicrostructureScopeValidationError):
        require_capability_id("lowercase")
    with pytest.raises(MicrostructureScopeValidationError):
        validate_runtime_mode("LIVE")
    with pytest.raises(MicrostructureScopeValidationError):
        validate_contract_schema_path("outside.json")
    with pytest.raises(MicrostructureScopeValidationError):
        require_unique(("x", "x"), "items")
    with pytest.raises(MicrostructureScopeValidationError):
        validate_reason_codes(())
    with pytest.raises(MicrostructureScopeValidationError):
        validate_lot37_safety({})


def test_temporal_validation_is_integer_microsecond_and_causal() -> None:
    start = parse_utc_timestamp("2026-08-06T19:18:40.050000Z", "start")
    end = parse_utc_timestamp("2026-08-06T19:18:41.000000Z", "end")
    assert duration_us(start, end) == 950_000
    validate_causal_times("2026-08-06T19:18:40.000000Z", "2026-08-06T19:18:40.050000Z", "2026-08-06T19:18:41.000000Z")
    with pytest.raises(MicrostructureScopeValidationError):
        parse_utc_timestamp("2026-08-06T19:18:40+00:00", "time")
    with pytest.raises(MicrostructureScopeValidationError):
        validate_causal_times("2026-08-06T19:18:42.000000Z", "2026-08-06T19:18:40.050000Z", "2026-08-06T19:18:41.000000Z")
    with pytest.raises(MicrostructureScopeValidationError):
        duration_us(end, start)


def test_object_collection_helper_rejects_ambiguous_inputs() -> None:
    with pytest.raises(MicrostructureScopeValidationError, match="object list"):
        _objects([], "items")
    with pytest.raises(MicrostructureScopeValidationError, match="object list"):
        _objects(["not-an-object"], "items")


def test_build_capability_matrix_matches_config() -> None:
    config = _load(ROOT / CONFIG_PATH)
    matrix = _build_capability_matrix(config)
    assert len(matrix.entries) == 27
    changed = dict(config)
    changed["capability_matrix"] = [dict(item) for item in config["capability_matrix"]]
    changed["capability_matrix"][0]["capability_id"] = "UNEXPECTED"
    with pytest.raises(MicrostructureScopeValidationError, match="membership changed"):
        _build_capability_matrix(changed)
