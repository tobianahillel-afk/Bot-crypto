from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

import crypto_quant_bot.microstructure.microstructure_scope_and_offline_data_contracts as lot37
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)
from crypto_quant_bot.microstructure.microstructure_scope_and_offline_data_contracts_models import (
    CapabilityMatrixEntryV1,
    ContractRegistryEntryV1,
    Lot37MetricsV1,
    MicrostructureScopeOfflineDataContractsCapabilityMatrixV1,
    MicrostructureScopeOfflineDataContractsContractRegistryV1,
    PublicApiEntryV1,
)
from crypto_quant_bot.microstructure.microstructure_scope_and_offline_data_contracts_validation import (
    MicrostructureScopeValidationError,
    parse_utc_timestamp,
    validate_reason_codes,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_COMMIT = "2" * 40


def _copy_root(tmp_path: Path) -> Path:
    paths = [
        lot37.CONFIG_PATH,
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
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return tmp_path


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mutated_gate(root: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object) -> dict[str, object]:
    path = root / "data/audit/lot37_v4_entry_gate.json"
    gate = _load(path)
    gate[field] = value
    gate.pop("output_checksum", None)
    checksum = canonical_checksum(gate)
    gate["output_checksum"] = checksum
    _write(path, gate)
    monkeypatch.setattr(lot37, "EXPECTED_GATE_CHECKSUM", checksum)
    return gate


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("owner", "OtherDomain", "does not authorize"),
        ("required_outputs", ["WrongOutputV1"], "required output contract set changed"),
        ("safety", {}, "gate safety boundary changed"),
    ],
)
def test_gate_semantic_drift_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    root = _copy_root(tmp_path)
    _mutated_gate(root, monkeypatch, field, value)
    config = _load(root / lot37.CONFIG_PATH)
    with pytest.raises(MicrostructureScopeValidationError, match=message):
        lot37._verify_gate(root, config)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda overlay: overlay.__setitem__("latest_implemented_lot", 35), "latest lot 36"),
        (lambda overlay: overlay.__setitem__("lots", []), "lot map missing"),
        (lambda overlay: overlay["lots"]["36"].__setitem__("status", "WRONG"), "lifecycle status changed"),
        (lambda overlay: overlay["lots"].__setitem__("37", {"implementation_started": True, "status": "ACTIVE"}), "historical lock changed"),
    ],
)
def test_lifecycle_drift_is_rejected(tmp_path: Path, mutator, message: str) -> None:  # type: ignore[no-untyped-def]
    root = _copy_root(tmp_path)
    path = root / "data/audit/roadmap_lifecycle_overlay_lot36.json"
    overlay = _load(path)
    mutator(overlay)
    _write(path, overlay)
    config = _load(root / lot37.CONFIG_PATH)
    with pytest.raises(MicrostructureScopeValidationError, match=message):
        lot37._verify_lifecycle(root, config)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", "wrong", "config schema changed"),
        ("config_version", "wrong", "config version changed"),
        ("input_reference_time", "2026-08-06T19:18:40.500000Z", "reference time"),
        ("max_input_age_us", 0, "integer >= 1"),
    ],
)
def test_config_semantic_drift_is_rejected(field: str, value: object, message: str) -> None:
    config = _load(ROOT / lot37.CONFIG_PATH)
    config[field] = value
    with pytest.raises(MicrostructureScopeValidationError, match=message):
        lot37._validate_config(config)


def test_fixture_checksum_canonical_and_causal_guards(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    path = root / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json"
    with pytest.raises(MicrostructureScopeValidationError, match="checksum changed"):
        lot37._verify_fixture(root, str(path.relative_to(root)), "0" * 64, "2026-08-06T19:18:41.000000Z", 1_000_000)

    fixture = _load(path)
    fixture["canonical_contract"] = True
    _write(path, fixture)
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(MicrostructureScopeValidationError, match="cannot be canonical"):
        lot37._verify_fixture(root, str(path.relative_to(root)), checksum, "2026-08-06T19:18:41.000000Z", 1_000_000)

    fixture["canonical_contract"] = False
    fixture["event_time"] = "2026-08-06T19:18:41.100000Z"
    _write(path, fixture)
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(MicrostructureScopeValidationError, match="causal availability"):
        lot37._verify_fixture(root, str(path.relative_to(root)), checksum, "2026-08-06T19:18:41.000000Z", 1_000_000)


def test_offline_input_gate_and_shape_guards(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    config = _load(root / lot37.CONFIG_PATH)
    gate = _load(root / "data/audit/lot37_v4_entry_gate.json")

    broken = dict(gate)
    broken["prerequisites"] = None
    with pytest.raises(MicrostructureScopeValidationError, match="prerequisites missing"):
        lot37._verify_offline_inputs(root, config, broken)

    assert isinstance(gate["prerequisites"], dict)
    mismatch = dict(config)
    mismatch["offline_l2_fixture_path"] = "tests/fixtures/lot37/wrong.json"
    with pytest.raises(MicrostructureScopeValidationError, match="path differs"):
        lot37._verify_offline_inputs(root, mismatch, gate)

    l2_path = root / str(config["offline_l2_fixture_path"])
    l2 = _load(l2_path)
    l2["bids"] = None
    _write(l2_path, l2)
    gate_l2 = json.loads(json.dumps(gate))
    gate_l2["prerequisites"]["offline_l2_fixture_sha256"] = hashlib.sha256(l2_path.read_bytes()).hexdigest()
    with pytest.raises(MicrostructureScopeValidationError, match="bid/ask collections"):
        lot37._verify_offline_inputs(root, config, gate_l2)


def test_trade_shape_and_classification_guards(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    config = _load(root / lot37.CONFIG_PATH)
    gate = _load(root / "data/audit/lot37_v4_entry_gate.json")
    assert isinstance(gate["prerequisites"], dict)
    trade_path = root / str(config["offline_trade_fixture_path"])

    trade = _load(trade_path)
    trade["trades"] = []
    _write(trade_path, trade)
    empty_gate = json.loads(json.dumps(gate))
    empty_gate["prerequisites"]["offline_trade_fixture_sha256"] = hashlib.sha256(trade_path.read_bytes()).hexdigest()
    with pytest.raises(MicrostructureScopeValidationError, match="lacks records"):
        lot37._verify_offline_inputs(root, config, empty_gate)

    trade = _load(ROOT / str(config["offline_trade_fixture_path"]))
    assert isinstance(trade["trades"], list)
    trade["trades"][0]["side"] = "BUY_AGGRESSOR"
    _write(trade_path, trade)
    classified_gate = json.loads(json.dumps(gate))
    classified_gate["prerequisites"]["offline_trade_fixture_sha256"] = hashlib.sha256(trade_path.read_bytes()).hexdigest()
    with pytest.raises(MicrostructureScopeValidationError, match="cannot classify"):
        lot37._verify_offline_inputs(root, config, classified_gate)


def test_registry_membership_and_model_enums_fail_closed(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    config = _load(root / lot37.CONFIG_PATH)
    assert isinstance(config["contracts"], list)
    config["contracts"] = config["contracts"][:-1]
    with pytest.raises(MicrostructureScopeValidationError, match="registry set changed"):
        lot37._build_contract_registry(root, config)

    with pytest.raises(MicrostructureScopeValidationError, match="unknown contract kind"):
        ContractRegistryEntryV1("X", "BAD", "MicrostructureDomain", "contracts/schemas/x.schema.json", "P", "C", "ACTIVE_LOT37_CONTRACT", 37)
    with pytest.raises(MicrostructureScopeValidationError, match="unknown contract status"):
        ContractRegistryEntryV1("X", "INPUT", "MicrostructureDomain", "contracts/schemas/x.schema.json", "P", "C", "BAD", 37)
    with pytest.raises(MicrostructureScopeValidationError, match="cannot be empty"):
        MicrostructureScopeOfflineDataContractsContractRegistryV1("r", "1", ())


def test_capability_semantic_branches_fail_closed() -> None:
    config = _load(ROOT / lot37.CONFIG_PATH)
    matrix = lot37._build_capability_matrix(config)
    entries = list(matrix.entries)

    required_index = next(i for i, item in enumerate(entries) if item.classification == "REQUIRED")
    entries[required_index] = replace(entries[required_index], classification="OPTIONAL_RESEARCH")
    with pytest.raises(MicrostructureScopeValidationError, match="required scope capability disabled"):
        lot37._validate_capability_matrix(tuple(entries))

    entries = list(matrix.entries)
    future_index = next(i for i, item in enumerate(entries) if item.classification == "DISABLED")
    entries[future_index] = replace(entries[future_index], classification="OPTIONAL_RESEARCH")
    with pytest.raises(MicrostructureScopeValidationError, match="prematurely activated"):
        lot37._validate_capability_matrix(tuple(entries))

    entries = list(matrix.entries)
    forbidden_index = next(i for i, item in enumerate(entries) if item.classification == "FORBIDDEN")
    entries[forbidden_index] = replace(entries[forbidden_index], classification="OPTIONAL_RESEARCH")
    with pytest.raises(MicrostructureScopeValidationError, match="forbidden capability weakened"):
        lot37._validate_capability_matrix(tuple(entries))


def test_capability_and_api_model_enum_guards() -> None:
    with pytest.raises(MicrostructureScopeValidationError, match="unknown capability classification"):
        CapabilityMatrixEntryV1("X", "x", "BAD", "MicrostructureDomain", 37, "ACTIVE_LOT37_SCOPE", "X", "LOT37")
    with pytest.raises(MicrostructureScopeValidationError, match="required Lot 37"):
        CapabilityMatrixEntryV1("X", "x", "REQUIRED", "MicrostructureDomain", 38, "ACTIVE_LOT37_SCOPE", "X", "LOT37")
    with pytest.raises(MicrostructureScopeValidationError, match="cannot be empty"):
        MicrostructureScopeOfflineDataContractsCapabilityMatrixV1("m", "1", ())
    with pytest.raises(MicrostructureScopeValidationError, match="unknown public API kind"):
        PublicApiEntryV1("x", "crypto_quant_bot.microstructure.x", "BAD", "ACTIVE_LOT37_API")
    with pytest.raises(MicrostructureScopeValidationError, match="unknown public API status"):
        PublicApiEntryV1("x", "crypto_quant_bot.microstructure.x", "FUNCTION", "BAD")


def test_state_audit_metrics_and_reason_guards() -> None:
    state, audit = lot37.build_lot37_artifacts(ROOT, CODE_COMMIT)
    with pytest.raises(MicrostructureScopeValidationError, match="unknown Lot 37 validation state"):
        replace(state, validation_state="UNKNOWN")
    with pytest.raises(MicrostructureScopeValidationError, match="explicit public API"):
        replace(state, public_api=())
    with pytest.raises(MicrostructureScopeValidationError, match="audit validation state"):
        replace(audit, validation_state="UNKNOWN")
    with pytest.raises(MicrostructureScopeValidationError, match="integer >= 0"):
        Lot37MetricsV1(-1, 0, 0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(MicrostructureScopeValidationError):
        validate_reason_codes(("not_canonical",))


def test_invalid_iso_timestamp_is_rejected() -> None:
    with pytest.raises(MicrostructureScopeValidationError, match="not an ISO timestamp"):
        parse_utc_timestamp("not-a-timeZ", "event_time")
