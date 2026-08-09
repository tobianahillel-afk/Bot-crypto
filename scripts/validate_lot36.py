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

from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure import (  # noqa: E402
    CONFIG_PATH,
    EXPECTED_GATE_CHECKSUM,
    EXPECTED_LOT34_AUDIT_CHECKSUM,
    EXPECTED_LOT34_STATE_CHECKSUM,
    EXPECTED_LOT35_AUDIT_CHECKSUM,
    EXPECTED_LOT35_STATE_CHECKSUM,
    EXPECTED_ROADMAP_BLOB,
)
from crypto_quant_bot.data_governance.freshness_gap_outage_audit_and_v3_closure_validation import (  # noqa: E402
    V3ClosureError,
    lot36_safety,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    file_checksum,
    load_json_object,
)

STATE_PATH = ROOT / "data/audit/freshness_gap_outage_audit_and_v3_closure_lot36.json"
AUDIT_PATH = ROOT / "data/audit/freshness_gap_outage_audit_and_v3_closure_audit_lot36.json"
QUALITY_PATH = ROOT / "data/audit/data_quality_states_lot36.json"
ANOMALY_PATH = ROOT / "data/audit/data_anomalies_lot36.json"
VETO_PATH = ROOT / "data/audit/data_quality_veto_lot36.json"
REPLAY_PATH = ROOT / "data/audit/replay_evidence_lot36.json"
MANIFEST_PATH = ROOT / "data/audit/closure_manifest_lot36.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise V3ClosureError(message)


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    body = dict(payload)
    checksum = body.pop(field, None)
    require(isinstance(checksum, str), f"{field} missing")
    require(canonical_checksum(body) == checksum, f"{field} mismatch")
    return checksum


def validate_lineage(state: dict[str, Any]) -> None:
    lineage = state.get("lineage")
    require(isinstance(lineage, dict), "Lot 36 lineage missing")
    expected = {
        "entry_gate_checksum": EXPECTED_GATE_CHECKSUM,
        "canonical_roadmap_blob_sha": EXPECTED_ROADMAP_BLOB,
        "lot34_state_checksum": EXPECTED_LOT34_STATE_CHECKSUM,
        "lot34_audit_checksum": EXPECTED_LOT34_AUDIT_CHECKSUM,
        "lot35_state_checksum": EXPECTED_LOT35_STATE_CHECKSUM,
        "lot35_audit_checksum": EXPECTED_LOT35_AUDIT_CHECKSUM,
    }
    for field, value in expected.items():
        require(lineage.get(field) == value, f"Lot 36 lineage changed: {field}")


def validate_collections(state: dict[str, Any]) -> None:
    quality = load_json_object(QUALITY_PATH)
    anomalies = load_json_object(ANOMALY_PATH)
    veto = load_json_object(VETO_PATH)
    require(quality.get("records") == state.get("quality_states"), "quality collection differs")
    require(anomalies.get("records") == state.get("anomalies"), "anomaly collection differs")
    require(veto == state.get("data_quality_veto"), "data quality veto artifact differs")


def validate_manifest(state: dict[str, Any], audit: dict[str, Any]) -> str:
    manifest = load_json_object(MANIFEST_PATH)
    manifest_checksum = payload_checksum(manifest, "manifest_checksum")
    require(manifest == state.get("closure_manifest"), "closure manifest differs from state")
    require(audit.get("closure_manifest_checksum") == manifest_checksum, "audit/manifest mismatch")
    require(manifest.get("version_id") == "V3_MARKET_DATA_GOVERNANCE", "manifest version changed")
    require(manifest.get("lots_included") == list(range(31, 37)), "manifest lot chain changed")
    require(manifest.get("v3_closed") is False, "implementation cannot finalize V3")
    require(manifest.get("post_merge_audit_required") is True, "post-merge audit requirement missing")
    require(manifest.get("human_review_required") is True, "human review requirement missing")
    require(manifest.get("next_lot") == 37, "manifest next lot changed")
    require(manifest.get("next_lot_status") == "PLANNED_LOCKED", "Lot 37 must remain locked")
    return manifest_checksum


def validate_replay(state_checksum: str) -> str:
    replay = load_json_object(REPLAY_PATH)
    replay_checksum = payload_checksum(replay, "replay_checksum")
    require(replay.get("run1_checksum") == state_checksum, "replay run1 differs from state")
    require(replay.get("run2_checksum") == state_checksum, "replay run2 differs from state")
    require(replay.get("replay_status") == "REPLAY_MATCH", "Lot 36 replay did not match")
    require(replay.get("match") is True, "Lot 36 replay match flag false")
    return replay_checksum


def validate_reference_state(state: dict[str, Any], audit: dict[str, Any]) -> None:
    require(
        state.get("validation_state") == "VALIDATED_V3_CLOSURE_CANDIDATE",
        "reference Lot 36 state is not a validated closure candidate",
    )
    freshness = state.get("freshness_audits")
    require(isinstance(freshness, list) and len(freshness) == 1, "reference freshness audit changed")
    evidence = freshness[0]
    require(isinstance(evidence, dict), "freshness evidence must be an object")
    expected_counts = {
        "record_count": 3,
        "expected_interval_count": 3,
        "observed_interval_count": 3,
        "missing_interval_count": 0,
        "gap_count": 0,
        "outage_count": 0,
        "stale_record_count": 0,
        "freshness_bps": 10000,
        "status": "PASS",
    }
    for field, value in expected_counts.items():
        require(evidence.get(field) == value, f"reference freshness evidence changed: {field}")
    require(state.get("anomalies") == [], "reference closure contains anomalies")
    require(state["data_quality_veto"]["action"] == "ALLOW_ANALYSIS", "quality veto changed")
    require(state["reconciliation_veto"]["action"] == "ALLOW_ANALYSIS", "reconciliation veto changed")
    require(audit.get("anomaly_count") == 0, "audit anomaly count changed")


def validate_safety(state: dict[str, Any], audit: dict[str, Any]) -> None:
    for field, expected in lot36_safety().items():
        require(state.get(field) == expected, f"state safety mismatch: {field}")
        require(audit.get(field) == expected, f"audit safety mismatch: {field}")


def validate() -> dict[str, object]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    audit_checksum = payload_checksum(audit, "audit_checksum")
    require(audit.get("state_output_checksum") == state_checksum, "audit/state checksum mismatch")
    require(audit.get("config_checksum") == file_checksum(ROOT / CONFIG_PATH), "config checksum mismatch")
    validate_lineage(state)
    validate_collections(state)
    manifest_checksum = validate_manifest(state, audit)
    replay_checksum = validate_replay(state_checksum)
    validate_reference_state(state, audit)
    validate_safety(state, audit)
    return {
        "schema_version": "lot36-validation-v1",
        "status": "PASS",
        "validation_state": state["validation_state"],
        "closure_status": state["closure_manifest"]["closure_status"],
        "v3_closed": False,
        "next_lot": 37,
        "next_lot_status": "PLANNED_LOCKED",
        "state_output_checksum": state_checksum,
        "audit_checksum": audit_checksum,
        "closure_manifest_checksum": manifest_checksum,
        "replay_checksum": replay_checksum,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True))
    except (OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOT36 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
