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

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry_models import (
    SourceRegistryValidationError,
    fail_closed_safety,
)

STATE_PATH = ROOT / "data/audit/market_data_governance_scope_and_source_registry_lot31.json"
AUDIT_PATH = ROOT / "data/audit/market_data_governance_scope_and_source_registry_audit_lot31.json"
REGISTRY_PATH = ROOT / "data/audit/source_registry_lot31.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceRegistryValidationError(message)


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(isinstance(checksum, str), f"{field} missing")
    require(canonical_checksum(content) == checksum, f"{field} mismatch")
    return checksum


def validate() -> dict[str, object]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    registry = load_json_object(REGISTRY_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    audit_checksum = payload_checksum(audit, "audit_checksum")
    require(state["source_registry"] == registry, "persisted SourceRegistryV1 differs from state")
    require(audit["state_output_checksum"] == state_checksum, "audit/state checksum link mismatch")
    require(state["validation_state"] == "VALIDATED_METADATA_ONLY", "state is not validated")
    require(audit["validation_state"] == "VALIDATED_METADATA_ONLY", "audit is not validated")
    sources = registry.get("sources")
    require(isinstance(sources, list) and len(sources) == 3, "three sources are required")
    require(sum(item["source_of_truth"] is True for item in sources) == 1, "truth count differs")
    require(all(item["connection_status"] == "DISABLED" for item in sources), "connection enabled")
    for field, expected in fail_closed_safety().items():
        require(state.get(field) == expected, f"state safety mismatch: {field}")
        require(audit.get(field) == expected, f"audit safety mismatch: {field}")
    capabilities = state.get("capability_matrix")
    require(isinstance(capabilities, list), "capability matrix missing")
    statuses = {item["capability"]: item["status"] for item in capabilities}
    require(statuses["source_registry"] == "REQUIRED", "source registry is not required")
    require(statuses["instrument_normalization"] == "DISABLED", "Lot 32 was unlocked")
    require(statuses["external_connectivity"] == "FORBIDDEN", "connectivity was enabled")
    return {
        "schema_version": "lot31-validation-v1",
        "status": "PASS",
        "source_count": len(sources),
        "source_of_truth_count": 1,
        "disabled_connection_count": len(sources),
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
        print(f"LOT31 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
