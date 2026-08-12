from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import scripts.validate_lot43_entry_gate as gate_validator
from scripts.validate_lot43_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_INPUTS,
    EXPECTED_OUTPUTS,
    Lot43EntryGateError,
    canonical_checksum,
    roadmap_record,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot43_v4_entry_gate.json"
SCHEMA_PATH = ROOT / "contracts/schemas/lot43_v4_entry_gate_v1.schema.json"


@pytest.fixture(autouse=True)
def _isolate_historical_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replay immutable gate facts without requiring Lot 43 absence after gate merge."""
    monkeypatch.setattr(
        gate_validator,
        "validate_lot42_post_merge",
        lambda: {
            "status": "PASS",
            "verdict": "GO_LOT42_POST_MERGE",
            "project_version": "0.42.0",
            "latest_implemented_lot": 42,
            "next_lot": 43,
            "next_lot_status": "PLANNED_LOCKED",
        },
    )
    monkeypatch.setattr(gate_validator, "LOT43_FORBIDDEN_IMPLEMENTATION_PATHS", ())


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


def test_lot43_entry_gate_passes_exact_audited_state() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["gate_status"] == "GO_LOT43_IMPLEMENTATION_ENTRY"
    assert result["base_commit"] == "2438622734e597cdcbada6b926e3c05d9e4cf8bc"
    assert result["current_version"] == "0.42.0"
    assert result["output_checksum"] == EXPECTED_GATE_CHECKSUM
    assert result["target_lot"] == 43
    assert result["next_locked_lot"] == 44
    assert result["next_lot_status"] == "PLANNED_LOCKED"
    assert result["trade_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["approved_size"] == 0


def test_lot43_gate_checksum_is_canonical_and_tamper_evident() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    body = dict(gate)
    actual = body.pop("output_checksum")
    assert actual == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(body) == actual
    body["implementation_started"] = True
    assert canonical_checksum(body) != actual


def test_lot43_and_lot44_canonical_roadmap_rows_are_exact() -> None:
    lot43 = roadmap_record(44)
    lot44 = roadmap_record(45)
    assert lot43["lot_id"] == "Lot 43"
    assert lot43["lot_number"] == 43
    assert lot43["title"] == "Book Resilience & Replenishment Engine"
    assert lot43["responsible_component"] == "MicrostructureDomain"
    assert lot43["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert set(lot43["input_contracts"]) == EXPECTED_INPUTS
    assert set(lot43["output_contracts"]) == EXPECTED_OUTPUTS
    assert lot44["lot_id"] == "Lot 44"
    assert lot44["title"] == "Trades & Aggressor Classification Schema"
    assert lot44["status"] == "PLANNED_LOCKED"


def test_lot43_gate_schema_is_closed_and_lot44_locked() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    props = schema["properties"]
    assert props["target_lot"]["const"] == 43
    assert props["base_commit"]["const"] == "2438622734e597cdcbada6b926e3c05d9e4cf8bc"
    assert props["current_version"]["const"] == "0.42.0"
    assert props["next_lot"]["const"] == 44
    assert props["next_lot_status"]["const"] == "PLANNED_LOCKED"
    assert props["prerequisites"]["additionalProperties"] is False
    safety = props["safety"]
    assert safety["additionalProperties"] is False
    assert safety["properties"]["trade_allowed"]["const"] is False
    assert safety["properties"]["execution_allowed"]["const"] is False
    assert safety["properties"]["approved_size"]["const"] == 0


def test_lot43_historical_gate_keeps_lot44_implementation_absent() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    assert gate["implementation_started"] is False
    assert gate["next_lot"] == 44
    assert gate["next_lot_status"] == "PLANNED_LOCKED"
    for path in gate_validator.LOT44_FORBIDDEN_IMPLEMENTATION_PATHS:
        assert not path.exists()


def test_lot43_gate_rejects_future_scope_unlock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["forbidden_scope"].remove("TRADE_AGGRESSOR_CLASSIFICATION")
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot43EntryGateError, match="forbidden scope"):
        validate()


def test_lot43_gate_rejects_trading_permission(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["safety"]["trade_allowed"] = True
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot43EntryGateError, match="safety boundary"):
        validate()


def test_lot43_gate_rejects_roadmap_binding_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["canonical_roadmap"]["source_line"] = 43
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot43EntryGateError, match="roadmap line binding"):
        validate()


def test_lot43_gate_rejects_lot42_prerequisite_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["prerequisites"]["mutation_score_percent"] = 99.99
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot43EntryGateError, match="prerequisite evidence"):
        validate()


def test_lot43_gate_rejects_required_output_tamper(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["required_outputs"].remove("BookResilienceStateV1")
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot43EntryGateError, match="gate outputs"):
        validate()


def test_lot43_gate_rejects_participant_intent_as_fact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["forbidden_scope"].remove("PARTICIPANT_INTENT_AS_FACT")
    _install_tampered_gate(monkeypatch, tmp_path, tampered)
    with pytest.raises(Lot43EntryGateError, match="forbidden scope"):
        validate()
