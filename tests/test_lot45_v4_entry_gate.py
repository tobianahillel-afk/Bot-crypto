from __future__ import annotations

import copy

import pytest

from scripts.validate_lot45_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_OUTPUTS,
    GATE_PATH,
    LOT45_FORBIDDEN_BEFORE_GATE,
    LOT46_FORBIDDEN,
    Lot45EntryGateError,
    load,
    validate,
    validate_gate_payload,
)


def test_lot45_entry_gate_passes() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert result["verdict"] == "GO_LOT45_IMPLEMENTATION_ENTRY"
    assert result["post_merge_verdict"] == "GO_LOT44_POST_MERGE"
    assert result["target_lot"] == 45
    assert result["lot46_status"] == "PLANNED_LOCKED"
    assert result["gate_checksum"] == EXPECTED_GATE_CHECKSUM


def test_lot45_contract_is_exact_and_fail_closed() -> None:
    gate = load(GATE_PATH)
    assert set(gate["output_contracts"]) == EXPECTED_OUTPUTS
    assert gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert gate["safety"]["analysis_only"] is True
    assert gate["safety"]["trade_allowed"] is False
    assert gate["safety"]["execution_allowed"] is False
    assert gate["safety"]["approved_size"] == 0
    assert gate["safety"]["signal_generation_allowed"] is False
    assert gate["safety"]["risk_approval_allowed"] is False
    assert gate["safety"]["order_routing_allowed"] is False


def test_gate_checksum_rejects_tampering() -> None:
    gate = load(GATE_PATH)
    tampered = copy.deepcopy(gate)
    tampered["next_lot_status"] = "IMPLEMENTED"
    with pytest.raises(Lot45EntryGateError, match="checksum"):
        validate_gate_payload(tampered)


def test_lot45_and_lot46_implementation_are_absent_before_gate() -> None:
    root = GATE_PATH.parents[2]
    for path in LOT45_FORBIDDEN_BEFORE_GATE | LOT46_FORBIDDEN:
        assert not (root / path).exists(), path
