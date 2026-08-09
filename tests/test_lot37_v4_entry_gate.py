from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

import scripts.validate_lot37_entry_gate as gate_validator
from scripts.validate_lot37_entry_gate import (
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_OUTPUTS,
    Lot37EntryGateError,
    canonical_checksum,
    canonical_roadmap_record,
    validate,
    validate_l2_fixture,
    validate_trade_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot37_v4_entry_gate.json"
L2_PATH = ROOT / "tests/fixtures/lot37/offline_l2_availability_fixture_v1.json"
TRADE_PATH = ROOT / "tests/fixtures/lot37/offline_trade_availability_fixture_v1.json"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def test_lot37_entry_gate_passes_exact_certified_state() -> None:
    result = validate()
    assert result == {
        "schema_version": "lot37-entry-gate-validation-v1",
        "status": "PASS",
        "gate_status": "GO_LOT37_IMPLEMENTATION_ENTRY",
        "canonical_title": "Microstructure Scope & Offline Data Contracts",
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "output_checksum": EXPECTED_GATE_CHECKSUM,
        "v3_closed": True,
        "offline_l2_available": True,
        "offline_trades_available": True,
        "next_locked_lot": 38,
        "external_connectivity_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def test_gate_checksum_is_canonical_and_tamper_evident() -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    body = dict(gate)
    checksum = body.pop("output_checksum")
    assert checksum == EXPECTED_GATE_CHECKSUM
    assert canonical_checksum(body) == checksum
    body["implementation_started"] = True
    assert canonical_checksum(body) != checksum


def test_canonical_roadmap_record_is_lot37_and_outputs_are_exact() -> None:
    record = canonical_roadmap_record()
    assert record["lot_id"] == "Lot 37"
    assert record["lot_number"] == 37
    assert record["title"] == "Microstructure Scope & Offline Data Contracts"
    assert record["version_id"] == "V4_MICROSTRUCTURE_LIQUIDITY"
    assert record["responsible_component"] == "MicrostructureDomain"
    assert record["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY"
    assert record["package_boundary"] == "src/crypto_quant_bot/microstructure"
    assert set(record["output_contracts"]) == EXPECTED_OUTPUTS


def test_offline_prerequisite_fixtures_are_explicitly_noncanonical() -> None:
    l2 = json.loads(L2_PATH.read_text(encoding="utf-8"))
    trades = json.loads(TRADE_PATH.read_text(encoding="utf-8"))
    for fixture in (l2, trades):
        assert fixture["fixture_only"] is True
        assert fixture["canonical_contract"] is False
        assert fixture["used_for_decision"] is False
        assert fixture["venue"] == "KRAKEN"
        assert fixture["instrument_id"] == "BTC-EUR-SPOT"
    assert all(item["side"] == "UNKNOWN" for item in trades["trades"])


def test_l2_fixture_rejects_crossed_book(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = json.loads(L2_PATH.read_text(encoding="utf-8"))
    payload["bids"][0]["price"] = "50026.00"
    path = tmp_path / "l2.json"
    _write_json(path, payload)
    monkeypatch.setattr(
        gate_validator,
        "EXPECTED_L2_SHA256",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    with pytest.raises(Lot37EntryGateError, match="crossed or locked"):
        validate_l2_fixture(path)


def test_l2_fixture_rejects_decision_or_canonical_promotion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for field, value, message in (
        ("fixture_only", False, "fixture-only"),
        ("canonical_contract", True, "cannot predefine"),
        ("used_for_decision", True, "cannot be decision"),
    ):
        payload = json.loads(L2_PATH.read_text(encoding="utf-8"))
        payload[field] = value
        path = tmp_path / f"{field}.json"
        _write_json(path, payload)
        monkeypatch.setattr(
            gate_validator,
            "EXPECTED_L2_SHA256",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        with pytest.raises(Lot37EntryGateError, match=message):
            validate_l2_fixture(path)


def test_trade_fixture_rejects_premature_aggressor_classification(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.loads(TRADE_PATH.read_text(encoding="utf-8"))
    payload["trades"][0]["side"] = "BUY"
    path = tmp_path / "trades.json"
    _write_json(path, payload)
    monkeypatch.setattr(
        gate_validator,
        "EXPECTED_TRADE_SHA256",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    with pytest.raises(Lot37EntryGateError, match="must not classify aggressor"):
        validate_trade_fixture(path)


def test_trade_fixture_rejects_duplicate_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.loads(TRADE_PATH.read_text(encoding="utf-8"))
    payload["trades"][1]["trade_id"] = payload["trades"][0]["trade_id"]
    path = tmp_path / "trades.json"
    _write_json(path, payload)
    monkeypatch.setattr(
        gate_validator,
        "EXPECTED_TRADE_SHA256",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    with pytest.raises(Lot37EntryGateError, match="duplicate trade"):
        validate_trade_fixture(path)


def test_gate_fails_closed_if_scope_is_tampered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(gate)
    tampered["forbidden_scope"].remove("TRADING")
    body = dict(tampered)
    body.pop("output_checksum")
    tampered["output_checksum"] = canonical_checksum(body)
    path = tmp_path / "gate.json"
    _write_json(path, tampered)
    monkeypatch.setattr(gate_validator, "GATE_PATH", path)
    monkeypatch.setattr(
        gate_validator, "EXPECTED_GATE_CHECKSUM", tampered["output_checksum"]
    )
    with pytest.raises(Lot37EntryGateError, match="forbidden scope"):
        validate()
