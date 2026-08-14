from __future__ import annotations

import copy

import pytest

from scripts.validate_lot45_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_OUTPUTS,
    EXPECTED_QUALITY,
    EXPECTED_SAFETY,
    GATE_PATH,
    LOT45_FORBIDDEN_BEFORE_GATE,
    LOT46_FORBIDDEN,
    SCHEMA_PATH,
    Lot45EntryGateError,
    git,
    load,
    locate_gate_commit,
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
    assert result["gate_commit"] == locate_gate_commit()


def test_lot45_contract_is_exact_and_fail_closed() -> None:
    gate = load(GATE_PATH)
    assert set(gate["output_contracts"]) == EXPECTED_OUTPUTS
    assert gate["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert gate["safety"] == EXPECTED_SAFETY
    assert gate["quality"] == EXPECTED_QUALITY


def test_gate_checksum_rejects_tampering() -> None:
    gate = load(GATE_PATH)
    tampered = copy.deepcopy(gate)
    tampered["next_lot_status"] = "IMPLEMENTED"
    with pytest.raises(Lot45EntryGateError, match="checksum"):
        validate_gate_payload(tampered)


def test_published_schema_encodes_exact_contracts_and_fail_closed_values() -> None:
    gate = load(GATE_PATH)
    schema = load(SCHEMA_PATH)
    properties = schema["properties"]

    assert properties["input_contracts"]["const"] == gate["input_contracts"]
    assert properties["output_contracts"]["const"] == gate["output_contracts"]

    safety_schema = properties["safety"]
    assert safety_schema["additionalProperties"] is False
    assert set(safety_schema["required"]) == set(EXPECTED_SAFETY)
    for key, expected in EXPECTED_SAFETY.items():
        assert safety_schema["properties"][key]["const"] == expected

    quality_schema = properties["quality"]
    assert quality_schema["additionalProperties"] is False
    assert set(quality_schema["required"]) == set(EXPECTED_QUALITY)
    for key, expected in EXPECTED_QUALITY.items():
        assert quality_schema["properties"][key]["const"] == expected


def test_lot45_and_lot46_were_absent_at_frozen_gate_snapshot() -> None:
    gate_commit = locate_gate_commit()
    gate_tree = set(git("ls-tree", "-r", "--name-only", gate_commit).splitlines())
    for path in LOT45_FORBIDDEN_BEFORE_GATE | LOT46_FORBIDDEN:
        assert path not in gate_tree, path


def test_predecessor_lot44_entry_gate_is_archived() -> None:
    root = GATE_PATH.parents[2]
    workflow = (root / ".github/workflows/lot44-entry-gate.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
