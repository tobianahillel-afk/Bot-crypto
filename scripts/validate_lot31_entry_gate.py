from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/audit/lot31_v3_entry_gate.json"
EXPECTED_CHECKSUM = "36595331f161a32b69afdd84e3f26353f01bdc27720ae276ea37618af794d526"


class Lot31EntryGateError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot31EntryGateError(message)


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_gate() -> dict[str, Any]:
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "Lot 31 entry gate must be a JSON object")
    return payload


def validate_gate(gate: dict[str, Any]) -> dict[str, object]:
    checksum_payload = dict(gate)
    output_checksum = checksum_payload.pop("output_checksum", None)
    require(isinstance(output_checksum, str), "Lot 31 entry gate checksum is missing")
    require(canonical_checksum(checksum_payload) == output_checksum, "checksum mismatch")

    require(gate.get("gate_status") == "GO_LOT31_IMPLEMENTATION_ENTRY", "gate is not GO")
    require(gate.get("target_lot") == 31, "target lot must be 31")
    require(gate.get("target_version") == "V3_MARKET_DATA_GOVERNANCE", "wrong V3 target")
    require(gate.get("owner") == "MarketDataGovernanceDomain", "wrong domain owner")
    require(
        gate.get("package_boundary") == "src/crypto_quant_bot/data_governance",
        "wrong package boundary",
    )
    require(gate.get("runtime_mode") == "DATA_GOVERNANCE_ONLY", "wrong runtime ceiling")
    require(gate.get("human_decision") == "APPROVED_START_LOT31", "human GO missing")
    require(gate.get("implementation_started") is False, "gate must precede implementation")
    require(gate.get("next_lot_status") == "PLANNED_LOCKED", "Lot 32 must remain locked")
    safety = gate.get("safety")
    require(isinstance(safety, dict), "safety object missing")
    require(safety.get("analysis_only") is True, "analysis-only invariant changed")
    for field in (
        "used_for_decision",
        "external_connectivity_allowed",
        "network_ingestion_allowed",
        "real_credentials_allowed",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    ):
        require(safety.get(field) is False, f"forbidden permission enabled: {field}")
    require(safety.get("approved_size") == 0, "approved size must remain zero")
    required_fields = gate.get("required_source_fields")
    require(isinstance(required_fields, list), "source-field registry missing")
    require(len(required_fields) == 14, "source-field registry must contain 14 fields")
    require(len(set(required_fields)) == len(required_fields), "source fields must be unique")
    require(output_checksum == EXPECTED_CHECKSUM, "Lot 31 entry gate checksum changed")
    return {
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


def main() -> int:
    print(json.dumps(validate_gate(load_gate()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
