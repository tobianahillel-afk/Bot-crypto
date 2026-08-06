from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

import pytest

from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization import (
    build_lot32_artifacts,
)
from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization_models import (
    InstrumentNormalizationError,
    VenueInstrumentAliasV1,
)
from scripts.validate_lot32_no_connectivity import validate as validate_no_connectivity

ROOT = Path(__file__).resolve().parents[1]
VALID_SHA = "b" * 40
INPUT_PATHS = (
    "config/data_governance/instrument_symbol_contract_normalization_v1.json",
    "data/audit/lot32_v3_entry_gate.json",
    "data/audit/source_registry_lot31.json",
    "data/audit/market_data_governance_scope_and_source_registry_lot31.json",
    "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json",
)


def isolated_root(tmp_path: Path) -> Path:
    for relative in INPUT_PATHS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return tmp_path


def mutate(
    root: Path,
    relative: str,
    callback: Callable[[dict[str, Any]], None],
) -> None:
    path = root / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    callback(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("callback", "message"),
    [
        (lambda value: value.pop("contract_size"), "explicitly present"),
        (lambda value: value.__setitem__("contract_size", 1), "string or null"),
        (lambda value: value.__setitem__("canonical_symbol", "BTC-EUR"), "canonical_symbol"),
        (lambda value: value.__setitem__("market_type", "UNKNOWN"), "market_type"),
        (lambda value: value.__setitem__("settlement_asset", "USD"), "settlement"),
        (lambda value: value.__setitem__("instrument_id", "BTC EUR"), "instrument_id"),
    ],
)
def test_instrument_identity_and_nullable_fields_fail_closed(
    tmp_path: Path,
    callback: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    root = isolated_root(tmp_path)
    mutate(root, INPUT_PATHS[0], lambda payload: callback(payload["instruments"][0]))
    with pytest.raises(InstrumentNormalizationError, match=message):
        build_lot32_artifacts(root, VALID_SHA)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("venue", "kraken", "uppercase"),
        ("source_revision", True, "integer"),
        ("tick_size", 0.1, "string"),
        ("tick_size", "0.10", "canonical"),
        ("lot_size", "0", "positive"),
        ("price_precision", -1, "negative"),
        ("quantity_precision", -1, "negative"),
        ("validation_state", "CONNECTED", "metadata-only"),
    ],
)
def test_alias_type_and_decimal_boundaries_fail_closed(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    root = isolated_root(tmp_path)

    def change(payload: dict[str, Any]) -> None:
        payload["instruments"][0]["aliases"][2][field] = value

    mutate(root, INPUT_PATHS[0], change)
    with pytest.raises(InstrumentNormalizationError, match=message):
        build_lot32_artifacts(root, VALID_SHA)


def test_duplicate_venue_and_exchange_aliases_are_rejected(tmp_path: Path) -> None:
    root = isolated_root(tmp_path)

    def duplicate_venue(payload: dict[str, Any]) -> None:
        aliases = payload["instruments"][0]["aliases"]
        aliases[1]["venue"] = aliases[0]["venue"]
        aliases[1]["source_id"] = aliases[0]["source_id"]

    mutate(root, INPUT_PATHS[0], duplicate_venue)
    with pytest.raises(InstrumentNormalizationError, match="unique and ordered"):
        build_lot32_artifacts(root, VALID_SHA)


def test_source_venue_and_approval_are_strict(tmp_path: Path) -> None:
    root = isolated_root(tmp_path)

    def venue_mismatch(payload: dict[str, Any]) -> None:
        payload["instruments"][0]["aliases"][0]["venue"] = "KRAKEN"

    mutate(root, INPUT_PATHS[0], venue_mismatch)
    with pytest.raises(InstrumentNormalizationError, match="differs from source venue"):
        build_lot32_artifacts(root, VALID_SHA)

    root = isolated_root(tmp_path)

    def unapprove(payload: dict[str, Any]) -> None:
        payload["sources"][0]["approved"] = False

    mutate(root, INPUT_PATHS[2], unapprove)
    with pytest.raises(InstrumentNormalizationError, match="approved"):
        build_lot32_artifacts(root, VALID_SHA)


def test_gate_safety_and_checksum_are_both_required(tmp_path: Path) -> None:
    root = isolated_root(tmp_path)

    def unsafe_gate(payload: dict[str, Any]) -> None:
        payload["safety"]["trade_allowed"] = True

    mutate(root, INPUT_PATHS[1], unsafe_gate)
    with pytest.raises(InstrumentNormalizationError, match="checksum"):
        build_lot32_artifacts(root, VALID_SHA)


def test_alias_dataclass_rejects_non_explicit_policy_values() -> None:
    base = {
        "venue": "KRAKEN",
        "exchange_symbol": "XBTEUR",
        "source_id": "kraken-public-spot-metadata",
        "source_revision": 1,
        "tick_size": "0.1",
        "lot_size": "0.00000001",
        "min_qty": "0.0001",
        "min_notional": "5",
        "price_precision": 1,
        "quantity_precision": 8,
        "fee_tier": "REFERENCE_METADATA_ONLY",
        "margin_mode": None,
        "leverage_policy": "FORBIDDEN",
        "validation_state": "VALIDATED_METADATA_ONLY",
    }
    with pytest.raises(InstrumentNormalizationError, match="trimmed"):
        VenueInstrumentAliasV1(**{**base, "exchange_symbol": " XBTEUR"})
    with pytest.raises(InstrumentNormalizationError, match="positive"):
        VenueInstrumentAliasV1(**{**base, "source_revision": 0})


def test_no_connectivity_validator_remains_green() -> None:
    result = validate_no_connectivity()
    assert result["status"] == "PASS"
    assert result["active_connection_count"] == 0
    assert result["authenticated_source_count"] == 0
    assert result["forbidden_import_count"] == 0
    assert result["forbidden_config_key_count"] == 0
