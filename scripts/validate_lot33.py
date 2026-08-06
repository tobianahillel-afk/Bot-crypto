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

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    file_checksum,
    load_json_object,
)
from crypto_quant_bot.data_governance.source_registry_validation import (  # noqa: E402
    fail_closed_safety,
)
from crypto_quant_bot.data_governance.timestamp_clock_timezone_validation import (  # noqa: E402
    TimestampGovernanceError,
    parse_aware_timestamp,
)

STATE_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_lot33.json"
AUDIT_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json"
COLLECTION_PATH = ROOT / "data/audit/canonical_time_envelopes_lot33.json"
REGISTRY_PATH = ROOT / "data/audit/instrument_registry_lot32.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TimestampGovernanceError(message)


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(isinstance(checksum, str), f"{field} missing")
    require(canonical_checksum(content) == checksum, f"{field} mismatch")
    return checksum


def validate_envelopes(state: dict[str, Any], collection: dict[str, Any]) -> tuple[int, int]:
    envelopes = state.get("canonical_envelopes")
    require(isinstance(envelopes, list) and envelopes, "canonical envelopes missing")
    require(collection.get("records") == envelopes, "persisted envelope collection differs")
    keys: list[tuple[str, int, int]] = []
    out_of_order_count = 0
    for item in envelopes:
        raw = item["raw"]
        require(raw["raw_timestamp"] == raw["source_time"], "raw timestamp was not preserved")
        for field in (
            "source_time_utc", "event_time_utc", "receive_time_utc", "process_time_utc",
            "available_at_utc", "usable_from_utc",
        ):
            require(str(item[field]).endswith("Z"), f"{field} is not UTC")
            parse_aware_timestamp(item[field], field)
        require(
            item["event_time_utc"] <= item["receive_time_utc"] <= item["process_time_utc"]
            <= item["available_at_utc"] <= item["usable_from_utc"],
            "canonical envelope violates causal availability",
        )
        for field in (
            "transport_latency_us", "processing_latency_us", "total_latency_us",
            "out_of_order_delay_us",
        ):
            require(item[field] >= 0, f"negative temporal metric: {field}")
        out_of_order_count += int(item["out_of_order_delay_us"] > 0)
        keys.append((item["event_time_utc"], raw["sequence_id"], raw["revision_id"]))
    require(keys == sorted(keys) and len(set(keys)) == len(keys), "canonical ordering differs")
    return len(envelopes), out_of_order_count


def validate() -> dict[str, object]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    collection = load_json_object(COLLECTION_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    audit_checksum = payload_checksum(audit, "audit_checksum")
    require(audit["state_output_checksum"] == state_checksum, "audit/state checksum mismatch")
    require(
        audit["instrument_registry_checksum"] == file_checksum(REGISTRY_PATH),
        "instrument registry lineage mismatch",
    )
    record_count, out_of_order_count = validate_envelopes(state, collection)
    require(audit["record_count"] == record_count, "audit record count mismatch")
    require(audit["out_of_order_record_count"] == out_of_order_count, "audit late count mismatch")
    require(state["clock_health"]["status"] == "HEALTHY", "certified clock is not healthy")
    require(audit["clock_health_status"] == "HEALTHY", "audit clock is not healthy")
    require(state["validation_state"] == "VALIDATED_TEMPORAL_ONLY", "state not validated")
    require(audit["validation_state"] == "VALIDATED_TEMPORAL_ONLY", "audit not validated")
    for field, expected in fail_closed_safety().items():
        require(state.get(field) == expected, f"state safety mismatch: {field}")
        require(audit.get(field) == expected, f"audit safety mismatch: {field}")
    return {
        "schema_version": "lot33-validation-v1",
        "status": "PASS",
        "record_count": record_count,
        "out_of_order_record_count": out_of_order_count,
        "clock_health_status": "HEALTHY",
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
        print(f"LOT33 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
