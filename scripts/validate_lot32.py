#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.data_governance.instrument_symbol_and_contract_normalization_models import (  # noqa: E402
    InstrumentNormalizationError,
    decimal_value,
    fail_closed_safety,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    file_checksum,
    load_json_object,
)

STATE_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_lot32.json"
AUDIT_PATH = ROOT / "data/audit/instrument_symbol_and_contract_normalization_audit_lot32.json"
REGISTRY_PATH = ROOT / "data/audit/instrument_registry_lot32.json"
SOURCE_REGISTRY_PATH = ROOT / "data/audit/source_registry_lot31.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InstrumentNormalizationError(message)


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(isinstance(checksum, str), f"{field} missing")
    require(canonical_checksum(content) == checksum, f"{field} mismatch")
    return checksum


def decimal_places(value: str, field: str) -> int:
    exponent = decimal_value(value, field).as_tuple().exponent
    return max(0, -int(exponent))


def _validate_aliases(instrument: dict[str, Any]) -> int:
    aliases = instrument.get("aliases")
    require(isinstance(aliases, list) and aliases, "venue aliases missing")
    venues = [item["venue"] for item in aliases]
    require(venues == sorted(venues), "venue aliases are not ordered")
    require(len(set(venues)) == len(venues), "venue aliases are not unique")
    for alias in aliases:
        for field in ("tick_size", "lot_size", "min_qty", "min_notional"):
            decimal_value(alias[field], field)
        require(
            decimal_places(alias["tick_size"], "tick_size") == alias["price_precision"],
            "price_precision differs from tick_size",
        )
        require(
            decimal_places(alias["lot_size"], "lot_size") == alias["quantity_precision"],
            "quantity_precision differs from lot_size",
        )
        require(alias["validation_state"] == "VALIDATED_METADATA_ONLY", "alias not validated")
        require(alias["margin_mode"] is None, "spot alias enabled margin")
        require(alias["leverage_policy"] == "FORBIDDEN", "spot alias enabled leverage")
    return len(aliases)


def _validate_registry(registry: dict[str, Any]) -> tuple[int, int]:
    require(registry.get("schema_version") == "instrument-registry-v1", "wrong registry")
    instruments = registry.get("instruments")
    require(isinstance(instruments, list) and instruments, "instrument registry is empty")
    ids = [item["instrument_id"] for item in instruments]
    symbols = [item["canonical_symbol"] for item in instruments]
    require(ids == sorted(ids) and len(set(ids)) == len(ids), "instrument ids differ")
    require(len(set(symbols)) == len(symbols), "canonical symbols differ")
    alias_count = 0
    reverse: dict[tuple[str, str], str] = {}
    forward: dict[tuple[str, str], str] = {}
    for instrument in instruments:
        require(
            instrument["canonical_symbol"]
            == f"{instrument['base_asset']}/{instrument['quote_asset']}:{instrument['market_type']}",
            "canonical symbol identity mismatch",
        )
        require(instrument["market_type"] == "SPOT", "certified example must remain spot")
        require(
            all(
                instrument[field] is None
                for field in ("contract_size", "expiry_time", "strike_price", "option_type")
            ),
            "spot derivative fields must remain null",
        )
        alias_count += _validate_aliases(instrument)
        for alias in instrument["aliases"]:
            venue_key = (alias["venue"], alias["exchange_symbol"])
            canonical_key = (instrument["canonical_symbol"], alias["venue"])
            require(venue_key not in reverse, "duplicate venue symbol alias")
            require(canonical_key not in forward, "duplicate canonical venue alias")
            reverse[venue_key] = instrument["canonical_symbol"]
            forward[canonical_key] = alias["exchange_symbol"]
            require(reverse[venue_key] == instrument["canonical_symbol"], "reverse round-trip")
            require(forward[canonical_key] == alias["exchange_symbol"], "forward round-trip")
    return len(instruments), alias_count


def validate() -> dict[str, object]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    registry = load_json_object(REGISTRY_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    audit_checksum = payload_checksum(audit, "audit_checksum")
    require(state["instrument_registry"] == registry, "persisted registry differs from state")
    require(audit["state_output_checksum"] == state_checksum, "audit/state checksum mismatch")
    require(
        audit["source_registry_checksum"] == file_checksum(SOURCE_REGISTRY_PATH),
        "source registry lineage checksum mismatch",
    )
    require(
        state["validation_state"] == "VALIDATED_NORMALIZATION_ONLY",
        "state is not validated",
    )
    require(
        audit["validation_state"] == "VALIDATED_NORMALIZATION_ONLY",
        "audit is not validated",
    )
    instrument_count, alias_count = _validate_registry(registry)
    require(audit["instrument_count"] == instrument_count, "audit instrument count mismatch")
    require(audit["venue_alias_count"] == alias_count, "audit alias count mismatch")
    require(audit["round_trip_count"] == alias_count * 2, "audit round-trip count mismatch")
    require(audit["frozen_instrument_count"] == 0, "frozen instruments persisted as valid")
    for field, expected in fail_closed_safety().items():
        require(state.get(field) == expected, f"state safety mismatch: {field}")
        require(audit.get(field) == expected, f"audit safety mismatch: {field}")
    return {
        "schema_version": "lot32-validation-v1",
        "status": "PASS",
        "instrument_count": instrument_count,
        "venue_alias_count": alias_count,
        "round_trip_count": alias_count * 2,
        "frozen_instrument_count": 0,
        "state_output_checksum": state_checksum,
        "audit_checksum": audit_checksum,
        "external_connectivity_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT32 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
