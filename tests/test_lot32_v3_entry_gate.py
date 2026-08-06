from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.validate_lot32_entry_gate import (
    EXPECTED_CHECKSUM,
    EXPECTED_MARKET_TYPES,
    GATE_PATH,
    Lot32EntryGateError,
    canonical_checksum,
    load_json,
    validate_gate,
)

ROOT = Path(__file__).resolve().parents[1]


def load_gate() -> dict[str, object]:
    return load_json(GATE_PATH)


def test_lot32_entry_gate_is_valid_and_fail_closed() -> None:
    result = validate_gate(load_gate())
    assert result == {
        "schema_version": "lot32-entry-gate-validation-v1",
        "status": "PASS",
        "target_lot": 32,
        "gate_status": "GO_LOT32_IMPLEMENTATION_ENTRY",
        "market_type_count": 4,
        "instrument_field_count": 24,
        "normalization_invariant_count": 13,
        "external_connectivity_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        "output_checksum": EXPECTED_CHECKSUM,
    }


def test_lot32_entry_gate_checksum_is_independently_recomputed() -> None:
    gate = load_gate()
    payload = dict(gate)
    output_checksum = payload.pop("output_checksum")
    assert output_checksum == EXPECTED_CHECKSUM
    assert canonical_checksum(payload) == EXPECTED_CHECKSUM


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("gate_status",), "NO_GO", "gate is not GO"),
        (("target_lot",), 33, "target lot"),
        (("target_version",), "V4", "wrong V3 target"),
        (("owner",), "InstrumentDomain", "wrong domain owner"),
        (("runtime_mode",), "LIVE", "wrong runtime ceiling"),
        (("human_decision",), "UNKNOWN", "human GO missing"),
        (("implementation_started",), True, "precede implementation"),
        (("next_lot_status",), "IMPLEMENTATION_STARTED", "Lot 33"),
        (("safety", "external_connectivity_allowed"), True, "external_connectivity"),
        (("safety", "network_ingestion_allowed"), True, "network_ingestion"),
        (("safety", "real_credentials_allowed"), True, "real_credentials"),
        (("safety", "signal_generation_allowed"), True, "signal_generation"),
        (("safety", "trade_allowed"), True, "trade_allowed"),
        (("safety", "execution_allowed"), True, "execution_allowed"),
        (("safety", "approved_size"), 1, "approved size"),
    ],
)
def test_lot32_entry_gate_rejects_permission_or_scope_changes(
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
    with pytest.raises(Lot32EntryGateError, match=message):
        validate_gate(gate)


def test_lot32_entry_gate_rejects_tampering_before_scope_validation() -> None:
    gate = load_gate()
    gate["target_lot"] = 33
    with pytest.raises(Lot32EntryGateError, match="checksum"):
        validate_gate(gate)


def test_lot32_market_types_fields_and_invariants_are_exact() -> None:
    gate = load_gate()
    assert tuple(gate["required_market_types"]) == EXPECTED_MARKET_TYPES
    assert gate["required_instrument_fields"] == [
        "instrument_id",
        "venue",
        "base_asset",
        "quote_asset",
        "market_type",
        "canonical_symbol",
        "exchange_symbol",
        "tick_size",
        "lot_size",
        "min_qty",
        "min_notional",
        "price_precision",
        "quantity_precision",
        "fee_tier",
        "settlement_asset",
        "margin_mode",
        "leverage_policy",
        "contract_size",
        "expiry_time",
        "strike_price",
        "option_type",
        "source_id",
        "source_revision",
        "validation_state",
    ]
    assert "NO_FLOAT_COERCION" in gate["required_normalization_invariants"]
    assert "NON_APPLICABLE_FIELDS_EXPLICIT_NULL" in gate[
        "required_normalization_invariants"
    ]
    assert "AMBIGUOUS_OR_REVISED_INSTRUMENT_FROZEN" in gate[
        "required_normalization_invariants"
    ]


def test_lot32_entry_gate_docs_preserve_boundaries() -> None:
    document = (ROOT / "docs/LOT_32_V3_ENTRY_GATE.md").read_text(encoding="utf-8")
    report = (ROOT / "reports/lot_32_v3_entry_gate_report.md").read_text(encoding="utf-8")
    schema = json.loads(
        (ROOT / "contracts/schemas/lot32_v3_entry_gate_v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert "GO_LOT32_IMPLEMENTATION_ENTRY" in document
    assert "external_connectivity_allowed=false" in document
    assert "Lot 33 remains `PLANNED_LOCKED`" in report
    assert "round-trip" in document
    assert schema["additionalProperties"] is False
    assert schema["properties"]["safety"]["additionalProperties"] is False
