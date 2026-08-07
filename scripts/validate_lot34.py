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
    load_json_object,
)
from crypto_quant_bot.data_governance.market_data_quality_engine_validation import (  # noqa: E402
    MarketDataQualityError,
    lot34_safety,
)

STATE_PATH = ROOT / "data/audit/market_data_quality_engine_lot34.json"
AUDIT_PATH = ROOT / "data/audit/market_data_quality_engine_audit_lot34.json"
QUALITY_PATH = ROOT / "data/audit/data_quality_states_lot34.json"
ANOMALY_PATH = ROOT / "data/audit/data_anomalies_lot34.json"
VETO_PATH = ROOT / "data/audit/data_quality_veto_lot34.json"
LOT33_STATE_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_lot33.json"
LOT33_AUDIT_PATH = ROOT / "data/audit/timestamp_clock_and_timezone_governance_audit_lot33.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MarketDataQualityError(message)


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(isinstance(checksum, str), f"{field} missing")
    require(canonical_checksum(content) == checksum, f"{field} mismatch")
    return checksum


def validate() -> dict[str, object]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    quality = load_json_object(QUALITY_PATH)
    anomalies = load_json_object(ANOMALY_PATH)
    veto = load_json_object(VETO_PATH)
    lot33_state = load_json_object(LOT33_STATE_PATH)
    lot33_audit = load_json_object(LOT33_AUDIT_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    audit_checksum = payload_checksum(audit, "audit_checksum")
    require(audit["state_output_checksum"] == state_checksum, "audit/state checksum mismatch")
    require(
        state["lineage"]["lot33_state_checksum"] == lot33_state["output_checksum"],
        "Lot 33 state lineage mismatch",
    )
    require(
        state["lineage"]["lot33_audit_checksum"] == lot33_audit["audit_checksum"],
        "Lot 33 audit lineage mismatch",
    )
    require(quality["records"] == state["quality_states"], "quality-state collection differs")
    require(anomalies["records"] == state["anomalies"], "anomaly collection differs")
    require(veto == state["veto"], "quality veto artifact differs")
    quarantine = sorted(
        {
            record_id
            for anomaly in state["anomalies"]
            for record_id in anomaly["record_ids"]
        }
    )
    require(quarantine == state["quarantine_record_ids"], "quarantine references differ")
    require(
        all(not anomaly["correction_permitted"] for anomaly in state["anomalies"]),
        "destructive correction allowed",
    )
    require(
        all(anomaly["quarantined"] for anomaly in state["anomalies"]),
        "anomaly escaped quarantine",
    )
    for field, expected in lot34_safety().items():
        require(state.get(field) == expected, f"state safety mismatch: {field}")
        require(audit.get(field) == expected, f"audit safety mismatch: {field}")
    require(state["veto"]["quality_known"] is True, "quality must be known in certified artifact")
    return {
        "schema_version": "lot34-validation-v1",
        "status": "PASS",
        "record_count": audit["record_count"],
        "anomaly_count": audit["anomaly_count"],
        "veto_action": audit["veto_action"],
        "state_output_checksum": state_checksum,
        "audit_checksum": audit_checksum,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT34 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
