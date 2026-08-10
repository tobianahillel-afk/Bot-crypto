from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import scripts.validate_lot40_entry_gate as gate_validator
from scripts.validate_lot40_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_INPUTS,
    EXPECTED_OUTPUTS,
    Lot40EntryGateError,
    canonical_checksum,
    canonical_roadmap_record,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot40_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot40_v4_entry_gate_v1.schema.json"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _install_tampered_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    body = dict(payload)
    body.pop("output_checksum", None)
    payload["output_checksum"] = canonical_checksum(body)
    path = tmp_path / "gate.json"
    _write_json(path, payload)
    monkeypatch.setattr(gate_validator, "GATE_PATH", path)
    monkeypatch.setattr(gate_validator, "EXPECTED_GATE_CHECKSUM", payload["output_checksum"])


def test_lot40_entry_gate_passes_exact_audited_state() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["gate_status"] == "GO_LOT40_IMPLEMENTATION_ENTRY"
    assert result["base_commit"] == "5381a773a9d69036b38c57904b2f4a66ffb2f595"
    assert result["current_version"] == "0.39.0"
    assert result["output_checksum"] == EXPECTED_GATE_CHECKSUM
    assert result["target_lot"] == 40
    assert result["next_locked_lot"] == 41
    assert result["next_lot_status"] == "PLANNED_LOCKED"
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0


def test_lot40_gate_checksum_is_canonical_and_tamper_evident() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    body = dict(gate)
    checksum = body.pop("output_checksum")
    assert checksum == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(body) == checksum
    body["implementation_started"] = True
    assert canonical_checksum(body) != checksum


def test_lot40_canonical_roadmap_row_is_exact() -> None:
    record = canonical_roadmap_record()
    assert record["lot_id"] == "Lot 40"
    assert record["lot_number"] == 40
    assert record["title"] == "Book Integrity / Desynchronization Detector"
    assert record["responsible_component"] == "MicrostructureDomain"
    assert record["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert set(record["input_contracts"]) == EXPECTED_INPUTS
    assert set(record["output_contracts"]) == EXPECTED_OUTPUTS


def test_lot40_gate_schema_is_strict_on_identity_safety_and_lot41_lock() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["properties"]["target_lot"]["const"] == 40
    assert schema["properties"]["base_commit"]["const"] == (
        "5381a773a9d69036b38c57904b2f4a66ffb2f595"
    )
    assert schema["properties"]["current_version"]["const"] == "0.39.0"
    assert schema["properties"]["next_lot"]["const"] == 41
    assert schema["properties"]["next_lot_status"]["const"] == "PLANNED_LOCKED"
    safety = schema["properties"]["safety"]
    assert safety["additionalProperties"] is False
    assert safety["properties"]["trade_allowed"]["const"] is False
    assert safety["properties"]["execution_allowed"]["const"] is False
    assert safety["properties"]["approved_size"]["const"] == 0


def test_lot40_preimplementation_boundary_and_lot41_lock() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert gate["implementation_started"] is False
    assert gate["gate_status"] == "GO_LOT40_IMPLEMENTATION_ENTRY"
    assert gate["next_lot"] == 41
    assert gate["next_lot_status"] == "PLANNED_LOCKED"
    for path in gate_validator.LOT40_FORBIDDEN_IMPLEMENTATION_PATHS:
        assert not path.exists()
    for path in gate_validator.LOT41_FORBIDDEN_IMPLEMENTATION_PATHS:
        assert not path.exists()


def test_lot40_gate_rejects_lot41_scope_unlock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["forbidden_scope"].remove("SPREAD_DEPTH_IMBALANCE_ENGINE")
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot40EntryGateError, match="forbidden scope"):
        validate()


def test_lot40_gate_rejects_trading_permission(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["safety"]["trade_allowed"] = True
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot40EntryGateError, match="trade_allowed"):
        validate()


def test_lot40_gate_rejects_roadmap_binding_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["canonical_roadmap"]["source_line"] = 40
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot40EntryGateError, match="roadmap line binding"):
        validate()


def test_lot40_gate_rejects_prerequisite_evidence_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["prerequisites"]["mutation_score_percent"] = 99.99
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot40EntryGateError, match="prerequisite evidence"):
        validate()


def test_lot40_gate_rejects_required_output_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["required_outputs"].remove("BookHealthVetoV1")
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot40EntryGateError, match="gate outputs"):
        validate()
