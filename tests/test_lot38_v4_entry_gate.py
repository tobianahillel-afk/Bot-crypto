from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import scripts.validate_lot38_entry_gate as gate_validator
from scripts.validate_lot38_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_INPUTS,
    EXPECTED_OUTPUTS,
    Lot38EntryGateError,
    canonical_checksum,
    canonical_roadmap_record,
    validate,
    validate_offline_l2_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot38_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot38_v4_entry_gate_v1.schema.json"
MATRIX_PATH = ROOT / "data/audit/microstructure_capability_matrix_lot37.json"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _tampered_gate(tmp_path: Path, payload: dict[str, object]) -> Path:
    body = dict(payload)
    body.pop("output_checksum", None)
    payload["output_checksum"] = canonical_checksum(body)
    path = tmp_path / "gate.json"
    _write_json(path, payload)
    return path


def test_lot38_entry_gate_passes_exact_audited_state() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["gate_status"] == "GO_LOT38_IMPLEMENTATION_ENTRY"
    assert result["base_commit"] == "c7ff8eecafd5f34196e9383013e97548b1a0ba02"
    assert result["output_checksum"] == EXPECTED_GATE_CHECKSUM
    assert result["next_locked_lot"] == 39
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0


def test_gate_checksum_is_canonical_and_tamper_evident() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    body = dict(gate)
    checksum = body.pop("output_checksum")
    assert checksum == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(body) == checksum
    body["implementation_started"] = True
    assert canonical_checksum(body) != checksum


def test_canonical_roadmap_row_is_exact_lot38_contract() -> None:
    record = canonical_roadmap_record()
    assert record["lot_id"] == "Lot 38"
    assert record["lot_number"] == 38
    assert record["title"] == "Order Book L2 Snapshot Engine"
    assert record["responsible_component"] == "MicrostructureDomain"
    assert record["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert set(record["input_contracts"]) == EXPECTED_INPUTS
    assert set(record["output_contracts"]) == EXPECTED_OUTPUTS


def test_gate_schema_is_strict_on_safety_and_identity() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["properties"]["safety"]["additionalProperties"] is False
    assert schema["properties"]["target_lot"]["const"] == 38
    assert schema["properties"]["next_lot"]["const"] == 39
    safety = schema["properties"]["safety"]["properties"]
    assert safety["trade_allowed"]["const"] is False
    assert safety["execution_allowed"]["const"] is False


def test_offline_l2_fixture_remains_noncanonical_and_nondecision() -> None:
    validate_offline_l2_fixture()
    fixture = json.loads(
        (ROOT / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture["fixture_only"] is True
    assert fixture["canonical_contract"] is False
    assert fixture["used_for_decision"] is False


def test_lot39_remains_locked_in_lot37_capability_matrix() -> None:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    lot39 = next(
        item for item in matrix["entries"]
        if item["capability_id"] == "LOT39_ORDER_BOOK_DELTA_SEQUENCE_RECONSTRUCTOR"
    )
    assert lot39["classification"] == "DISABLED"
    assert lot39["implementation_status"] == "PLANNED_LOCKED"


def test_gate_rejects_future_delta_reconstructor_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["forbidden_scope"].remove("ORDER_BOOK_DELTA_SEQUENCE_RECONSTRUCTION")
    path = _tampered_gate(tmp_path, tampered)
    monkeypatch.setattr(gate_validator, "GATE_PATH", path)
    monkeypatch.setattr(gate_validator, "EXPECTED_GATE_CHECKSUM", tampered["output_checksum"])
    with pytest.raises(Lot38EntryGateError, match="forbidden scope"):
        validate()


def test_gate_rejects_trading_permission(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["safety"]["trade_allowed"] = True
    path = _tampered_gate(tmp_path, tampered)
    monkeypatch.setattr(gate_validator, "GATE_PATH", path)
    monkeypatch.setattr(gate_validator, "EXPECTED_GATE_CHECKSUM", tampered["output_checksum"])
    with pytest.raises(Lot38EntryGateError, match="trade_allowed"):
        validate()


def test_gate_rejects_roadmap_binding_tamper(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["canonical_roadmap"]["source_line"] = 40
    path = _tampered_gate(tmp_path, tampered)
    monkeypatch.setattr(gate_validator, "GATE_PATH", path)
    monkeypatch.setattr(gate_validator, "EXPECTED_GATE_CHECKSUM", tampered["output_checksum"])
    with pytest.raises(Lot38EntryGateError, match="roadmap line binding"):
        validate()
