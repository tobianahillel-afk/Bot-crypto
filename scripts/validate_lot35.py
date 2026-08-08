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

from crypto_quant_bot.data_governance.candle_trade_book_reconciliation_validation import (  # noqa: E402
    ReconciliationError,
    lot35_safety,
)
from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    file_checksum,
    load_json_object,
)

STATE_PATH = ROOT / "data/audit/candle_trade_book_reconciliation_lot35.json"
AUDIT_PATH = ROOT / "data/audit/candle_trade_book_reconciliation_audit_lot35.json"
REPORTS_PATH = ROOT / "data/audit/reconciliation_reports_lot35.json"
VETO_PATH = ROOT / "data/audit/reconciliation_veto_lot35.json"
LOT34_STATE_PATH = ROOT / "data/audit/market_data_quality_engine_lot34.json"
LOT34_AUDIT_PATH = ROOT / "data/audit/market_data_quality_engine_audit_lot34.json"
LOT34_QUALITY_PATH = ROOT / "data/audit/data_quality_states_lot34.json"
LOT34_ANOMALY_PATH = ROOT / "data/audit/data_anomalies_lot34.json"
LOT34_VETO_PATH = ROOT / "data/audit/data_quality_veto_lot34.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReconciliationError(message)


def payload_checksum(payload: dict[str, Any], field: str) -> str:
    content = dict(payload)
    checksum = content.pop(field, None)
    require(isinstance(checksum, str), f"{field} missing")
    require(canonical_checksum(content) == checksum, f"{field} mismatch")
    return checksum


def validate_lineage(state: dict[str, Any]) -> None:
    lot34_state = load_json_object(LOT34_STATE_PATH)
    lot34_audit = load_json_object(LOT34_AUDIT_PATH)
    lineage = state["lineage"]
    require(
        lineage["lot34_state_checksum"] == lot34_state["output_checksum"],
        "Lot 34 state lineage mismatch",
    )
    require(
        lineage["lot34_audit_checksum"] == lot34_audit["audit_checksum"],
        "Lot 34 audit lineage mismatch",
    )
    require(
        lineage["quality_state_collection_checksum"] == file_checksum(LOT34_QUALITY_PATH),
        "Lot 34 quality collection lineage mismatch",
    )
    require(
        lineage["anomaly_collection_checksum"] == file_checksum(LOT34_ANOMALY_PATH),
        "Lot 34 anomaly collection lineage mismatch",
    )
    require(
        lineage["quality_veto_checksum"] == file_checksum(LOT34_VETO_PATH),
        "Lot 34 veto lineage mismatch",
    )


def validate_reports(state: dict[str, Any], reports: dict[str, Any]) -> None:
    require(reports["records"] == state["reports"], "reconciliation report collection differs")
    for report in state["reports"]:
        classification = report["classification"]
        require(
            classification in {
                "MATCH",
                "TOLERATED_DIFF",
                "MINOR_DIVERGENCE",
                "CRITICAL_DIVERGENCE",
            },
            "unknown reconciliation classification",
        )
        delta = report["delta"]
        if report["orphan"]:
            require(delta is None, "orphan reconciliation cannot expose exact delta")
        else:
            require(isinstance(delta, dict), "non-orphan reconciliation requires exact delta")
            require(delta["timestamp_us"] >= 0, "negative timestamp delta")


def validate() -> dict[str, object]:
    state = load_json_object(STATE_PATH)
    audit = load_json_object(AUDIT_PATH)
    reports = load_json_object(REPORTS_PATH)
    veto = load_json_object(VETO_PATH)
    state_checksum = payload_checksum(state, "output_checksum")
    audit_checksum = payload_checksum(audit, "audit_checksum")
    require(audit["state_output_checksum"] == state_checksum, "audit/state checksum mismatch")
    validate_lineage(state)
    validate_reports(state, reports)
    require(veto == state["veto"], "reconciliation veto artifact differs")
    for field, expected in lot35_safety().items():
        require(state.get(field) == expected, f"state safety mismatch: {field}")
        require(audit.get(field) == expected, f"audit safety mismatch: {field}")
    require(state["veto"]["reconciliation_known"] is True, "reconciliation must be known")
    require(audit["report_count"] == len(state["reports"]), "report count mismatch")
    count_total = (
        audit["match_count"]
        + audit["tolerated_diff_count"]
        + audit["minor_divergence_count"]
        + audit["critical_divergence_count"]
    )
    require(count_total == audit["report_count"], "classification counts do not reconcile")
    return {
        "schema_version": "lot35-validation-v1",
        "status": "PASS",
        "report_count": audit["report_count"],
        "match_count": audit["match_count"],
        "tolerated_diff_count": audit["tolerated_diff_count"],
        "minor_divergence_count": audit["minor_divergence_count"],
        "critical_divergence_count": audit["critical_divergence_count"],
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
        print(f"LOT35 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
