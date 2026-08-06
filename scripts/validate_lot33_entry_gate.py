#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot33_v3_entry_gate.json"
LIFECYCLE_PATH = ROOT / "data/audit/roadmap_lifecycle_overlay_lot32.json"
REGISTRY_PATH = ROOT / "data/audit/instrument_registry_lot32.json"
EXPECTED_CHECKSUM = "c6942ad174c4c8a32d54ac48ed9c00e0e443f3495cc657df0c2677a4dd4cb5cc"
EXPECTED_FIELDS = (
    "source_time", "exchange_time", "event_time", "receive_time", "process_time",
    "available_at", "usable_from", "monotonic_time", "sequence_id", "revision_id",
    "source_timezone", "raw_timestamp", "timestamp_precision", "clock_domain",
)


class Lot33EntryGateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot33EntryGateError(message)


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


def validate_prerequisites() -> None:
    lifecycle = load_json(LIFECYCLE_PATH)
    require(lifecycle.get("latest_implemented_lot") == 32, "Lot 32 lifecycle is not current")
    lots = lifecycle.get("lots")
    require(isinstance(lots, dict), "lifecycle lots missing")
    require(
        lots.get("32", {}).get("status") == "IMPLEMENTED_VALIDATED_NORMALIZATION_ONLY",
        "Lot 32 is not audited normalization-only",
    )
    require(
        lots.get("33") == {"implementation_started": False, "status": "PLANNED_LOCKED"},
        "Lot 33 must remain locked before gate merge",
    )
    registry = load_json(REGISTRY_PATH)
    instruments = registry.get("instruments")
    require(isinstance(instruments, list) and len(instruments) == 1, "Lot 32 registry differs")
    require(instruments[0].get("canonical_symbol") == "BTC/EUR:SPOT", "instrument changed")


def validate_safety(safety: object) -> None:
    require(isinstance(safety, dict), "safety object missing")
    require(safety.get("analysis_only") is True, "analysis-only invariant changed")
    for field in (
        "used_for_decision", "external_connectivity_allowed", "network_ingestion_allowed",
        "real_credentials_allowed", "signal_generation_allowed", "risk_approval_allowed",
        "order_routing_allowed", "trade_allowed", "execution_allowed",
    ):
        require(safety.get(field) is False, f"forbidden permission enabled: {field}")
    require(safety.get("approved_size") == 0, "approved size must remain zero")


def validate_gate(gate: dict[str, Any]) -> dict[str, object]:
    checksum_payload = dict(gate)
    checksum = checksum_payload.pop("output_checksum", None)
    require(isinstance(checksum, str), "Lot 33 entry gate checksum missing")
    require(canonical_checksum(checksum_payload) == checksum, "checksum mismatch")
    require(checksum == EXPECTED_CHECKSUM, "Lot 33 entry gate checksum changed")
    expected = {
        "gate_status": "GO_LOT33_IMPLEMENTATION_ENTRY",
        "target_lot": 33,
        "target_version": "V3_MARKET_DATA_GOVERNANCE",
        "owner": "MarketDataGovernanceDomain",
        "package_boundary": "src/crypto_quant_bot/data_governance",
        "runtime_mode": "DATA_GOVERNANCE_ONLY",
        "human_decision": "APPROVED_START_LOT33",
        "implementation_started": False,
        "next_lot_status": "PLANNED_LOCKED",
    }
    for field, value in expected.items():
        require(gate.get(field) == value, f"unexpected gate field: {field}")
    fields = gate.get("required_timestamp_fields")
    require(tuple(fields) == EXPECTED_FIELDS, "timestamp field registry changed")
    invariants = gate.get("required_temporal_invariants")
    require(isinstance(invariants, list) and len(invariants) == 14, "temporal invariants differ")
    require(len(set(invariants)) == len(invariants), "temporal invariants must be unique")
    validate_safety(gate.get("safety"))
    validate_prerequisites()
    return {
        "schema_version": "lot33-entry-gate-validation-v1",
        "status": "PASS",
        "target_lot": 33,
        "gate_status": "GO_LOT33_IMPLEMENTATION_ENTRY",
        "timestamp_field_count": len(EXPECTED_FIELDS),
        "temporal_invariant_count": len(invariants),
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
