from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot32_v3_entry_gate.json"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot31.json"
SOURCE_REGISTRY_PATH = ROOT / "data/audit/source_registry_lot31.json"
EXPECTED_CHECKSUM = "ca4f531f5a36173b0159aaab308025da7beaf66b21d1f85304c5d46c7f487a55"
EXPECTED_MARKET_TYPES = ("SPOT", "PERPETUAL", "DATED_FUTURE", "OPTION")


class Lot32EntryGateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot32EntryGateError(message)


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON object required: {path}")
    return payload


def validate_lifecycle() -> None:
    lifecycle = load_json(LIFECYCLE_PATH)
    require(lifecycle.get("latest_implemented_lot") == 31, "Lot 31 lifecycle is not current")
    lots = lifecycle.get("lots")
    require(isinstance(lots, dict), "lifecycle lots object missing")
    lot31 = lots.get("31")
    require(isinstance(lot31, dict), "Lot 31 lifecycle entry missing")
    require(
        lot31.get("status") == "IMPLEMENTED_VALIDATED_METADATA_ONLY",
        "Lot 31 is not validated metadata-only",
    )
    require(lot31.get("external_connectivity_allowed") is False, "Lot 31 connectivity changed")
    require(lot31.get("network_ingestion_allowed") is False, "Lot 31 ingestion changed")
    lot32 = lots.get("32")
    require(
        lot32 == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 32 must remain locked before gate merge",
    )


def validate_source_registry() -> None:
    registry = load_json(SOURCE_REGISTRY_PATH)
    require(registry.get("schema_version") == "source-registry-v1", "wrong source registry")
    require(
        registry.get("source_of_truth_id") == "kraken-public-spot-metadata",
        "source of truth changed",
    )
    sources = registry.get("sources")
    require(isinstance(sources, list), "source registry entries missing")
    require(len(sources) == 3, "Lot 31 source registry must contain three sources")
    truth_count = 0
    for source in sources:
        require(isinstance(source, dict), "source registry entry must be an object")
        require(source.get("approved") is True, "unapproved source in certified registry")
        require(source.get("auth_mode") == "NONE", "source authentication became active")
        require(source.get("enabled") is False, "source connector became enabled")
        require(source.get("connection_status") == "DISABLED", "source connection is active")
        truth_count += int(source.get("source_of_truth") is True)
    require(truth_count == 1, "exactly one source of truth is required")


def validate_safety(safety: object) -> None:
    require(isinstance(safety, dict), "safety object missing")
    require(safety.get("analysis_only") is True, "analysis-only invariant changed")
    forbidden_fields = (
        "used_for_decision",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "real_credentials_allowed",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    )
    for field in forbidden_fields:
        require(safety.get(field) is False, f"forbidden permission enabled: {field}")
    require(safety.get("approved_size") == 0, "approved size must remain zero")


def validate_gate(gate: dict[str, Any]) -> dict[str, object]:
    checksum_payload = dict(gate)
    output_checksum = checksum_payload.pop("output_checksum", None)
    require(isinstance(output_checksum, str), "Lot 32 entry gate checksum is missing")
    require(canonical_checksum(checksum_payload) == output_checksum, "checksum mismatch")

    require(gate.get("gate_status") == "GO_LOT32_IMPLEMENTATION_ENTRY", "gate is not GO")
    require(gate.get("target_lot") == 32, "target lot must be 32")
    require(gate.get("target_version") == "V3_MARKET_DATA_GOVERNANCE", "wrong V3 target")
    require(gate.get("owner") == "MarketDataGovernanceDomain", "wrong domain owner")
    require(
        gate.get("package_boundary") == "src/crypto_quant_bot/data_governance",
        "wrong package boundary",
    )
    require(gate.get("runtime_mode") == "DATA_GOVERNANCE_ONLY", "wrong runtime ceiling")
    require(gate.get("human_decision") == "APPROVED_START_LOT32", "human GO missing")
    require(gate.get("implementation_started") is False, "gate must precede implementation")
    require(gate.get("next_lot_status") == "PLANNED_LOCKED", "Lot 33 must remain locked")
    require(
        tuple(gate.get("required_market_types", ())) == EXPECTED_MARKET_TYPES,
        "market type registry changed",
    )

    fields = gate.get("required_instrument_fields")
    require(isinstance(fields, list), "instrument field registry missing")
    require(len(fields) == 24, "instrument field registry must contain 24 fields")
    require(len(set(fields)) == len(fields), "instrument fields must be unique")
    invariants = gate.get("required_normalization_invariants")
    require(isinstance(invariants, list), "normalization invariants missing")
    require(len(invariants) == 13, "normalization invariant count changed")
    require(len(set(invariants)) == len(invariants), "normalization invariants must be unique")
    validate_safety(gate.get("safety"))
    validate_lifecycle()
    validate_source_registry()
    require(output_checksum == EXPECTED_CHECKSUM, "Lot 32 entry gate checksum changed")
    return {
        "schema_version": "lot32-entry-gate-validation-v1",
        "status": "PASS",
        "target_lot": 32,
        "gate_status": "GO_LOT32_IMPLEMENTATION_ENTRY",
        "market_type_count": len(EXPECTED_MARKET_TYPES),
        "instrument_field_count": len(fields),
        "normalization_invariant_count": len(invariants),
        "external_connectivity_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
        "output_checksum": EXPECTED_CHECKSUM,
    }


def main() -> int:
    print(json.dumps(validate_gate(load_json(GATE_PATH)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
