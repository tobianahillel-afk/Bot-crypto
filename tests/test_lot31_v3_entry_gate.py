from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.validate_lot31_entry_gate import (
    EXPECTED_CHECKSUM,
    Lot31EntryGateError,
    canonical_checksum,
    load_gate,
    validate_gate,
)

ROOT = Path(__file__).resolve().parents[1]


def test_lot31_entry_gate_is_valid_and_fail_closed() -> None:
    gate = load_gate()
    result = validate_gate(gate)
    assert result == {
        "schema_version": "lot31-entry-gate-validation-v1",
        "status": "PASS",
        "target_lot": 31,
        "gate_status": "GO_LOT31_IMPLEMENTATION_ENTRY",
        "external_connectivity_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        "output_checksum": EXPECTED_CHECKSUM,
    }


def test_lot31_entry_gate_checksum_is_independently_recomputed() -> None:
    gate = load_gate()
    payload = dict(gate)
    output_checksum = payload.pop("output_checksum")
    assert output_checksum == EXPECTED_CHECKSUM
    assert canonical_checksum(payload) == EXPECTED_CHECKSUM


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("gate_status",), "NO_GO", "gate is not GO"),
        (("target_lot",), 32, "target lot"),
        (("target_version",), "V4", "wrong V3 target"),
        (("owner",), "MarketDataDomain", "wrong domain owner"),
        (("runtime_mode",), "LIVE", "wrong runtime ceiling"),
        (("human_decision",), "UNKNOWN", "human GO missing"),
        (("implementation_started",), True, "precede implementation"),
        (("next_lot_status",), "IMPLEMENTATION_STARTED", "Lot 32"),
        (("safety", "external_connectivity_allowed"), True, "external_connectivity"),
        (("safety", "network_ingestion_allowed"), True, "network_ingestion"),
        (("safety", "real_credentials_allowed"), True, "real_credentials"),
        (("safety", "trade_allowed"), True, "trade_allowed"),
        (("safety", "execution_allowed"), True, "execution_allowed"),
        (("safety", "approved_size"), 1, "approved size"),
    ],
)
def test_lot31_entry_gate_rejects_permission_or_scope_changes(
    path: tuple[str, ...], value: object, message: str
) -> None:
    gate = copy.deepcopy(load_gate())
    target = gate
    for key in path[:-1]:
        nested = target[key]
        assert isinstance(nested, dict)
        target = nested
    target[path[-1]] = value
    payload = dict(gate)
    payload.pop("output_checksum")
    gate["output_checksum"] = canonical_checksum(payload)
    with pytest.raises(Lot31EntryGateError, match=message):
        validate_gate(gate)


def test_lot31_entry_gate_rejects_tampering_before_scope_validation() -> None:
    gate = load_gate()
    gate["target_lot"] = 32
    with pytest.raises(Lot31EntryGateError, match="checksum"):
        validate_gate(gate)


def test_lot31_entry_gate_source_fields_are_exact_and_unique() -> None:
    gate = load_gate()
    assert gate["required_source_fields"] == [
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
    ]


def test_lot31_entry_gate_docs_preserve_no_connectivity_boundary() -> None:
    document = (ROOT / "docs/LOT_31_V3_ENTRY_GATE.md").read_text(encoding="utf-8")
    report = (ROOT / "reports/lot_31_v3_entry_gate_report.md").read_text(encoding="utf-8")
    schema = json.loads(
        (ROOT / "contracts/schemas/lot31_v3_entry_gate_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert "GO_LOT31_IMPLEMENTATION_ENTRY" in document
    assert "external_connectivity_allowed=false" in document
    assert "Lot 32 remains `PLANNED_LOCKED`" in report
    assert schema["additionalProperties"] is False
    assert schema["properties"]["safety"]["additionalProperties"] is False
