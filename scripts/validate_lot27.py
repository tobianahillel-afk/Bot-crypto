from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.market_analysis.alignment_io import load_json  # noqa: E402
from crypto_quant_bot.market_analysis.global_market_context_aggregator import checksum  # noqa: E402

OUTPUT_PATH = "data/audit/global_market_context_aggregator_lot27.json"
AUDIT_PATH = "data/audit/global_market_context_aggregator_audit_lot27.json"
REPORT_PATH = "reports/lot_27_global_market_context_aggregator_report.md"
SCHEMA_PATH = "contracts/schemas/global_market_context_aggregator_state_v1.schema.json"


def _validate_closed_schema(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    if schema.get("additionalProperties") is not False:
        raise ValueError("Lot 27 schema must be closed")
    properties = set(schema.get("properties", {}))
    required = set(schema.get("required", []))
    if set(payload) != properties or not required.issubset(payload):
        raise ValueError("Lot 27 payload/schema fields diverge")
    contribution_schema = schema["properties"]["contributions"]["items"]
    expected = set(contribution_schema["properties"])
    for contribution in payload["contributions"]:
        if set(contribution) != expected:
            raise ValueError("Lot 27 contribution/schema fields diverge")


def _validate_safety(payload: dict[str, Any]) -> None:
    false_fields = (
        "used_for_decision",
        "forecast_generation_allowed",
        "probability_claims_allowed",
        "signal_generation_allowed",
        "order_routing_allowed",
        "execution_allowed",
        "trade_allowed",
    )
    if payload.get("analysis_only") is not True:
        raise ValueError("analysis_only must remain true")
    if any(payload.get(field) is not False for field in false_fields):
        raise ValueError("Lot 27 executable permissions are invalid")
    if payload.get("approved_size") != 0:
        raise ValueError("approved_size must remain zero")


def validate(root: Path) -> dict[str, Any]:
    required = (OUTPUT_PATH, AUDIT_PATH, REPORT_PATH, SCHEMA_PATH)
    missing = [path for path in required if not (root / path).is_file()]
    if missing:
        raise ValueError("missing Lot 27 evidence: " + ", ".join(missing))
    state = load_json(root / OUTPUT_PATH)
    audit = load_json(root / AUDIT_PATH)
    schema = load_json(root / SCHEMA_PATH)
    _validate_closed_schema(state, schema)
    _validate_safety(state)
    expected_checksum = checksum({key: value for key, value in state.items() if key != "output_checksum"})
    if state.get("output_checksum") != expected_checksum:
        raise ValueError("Lot 27 output checksum mismatch")
    if audit.get("output_checksum") != state["output_checksum"]:
        raise ValueError("Lot 27 audit does not reference the output")
    if audit.get("replay_status") != "MATCH":
        raise ValueError("Lot 27 replay evidence is invalid")
    if state.get("dominant_state") != "GLOBAL_CONTEXT_MIXED":
        raise ValueError("Lot 27 deterministic context oracle mismatch")
    if state.get("aggregate_evidence_score") != 0.5646:
        raise ValueError("Lot 27 aggregate score oracle mismatch")
    if state.get("weighted_coverage_ratio") != 1.0 or state.get("available_source_count") != 5:
        raise ValueError("Lot 27 source coverage oracle mismatch")
    if state.get("conflict_states") != ["MTF_DIVERGENT"]:
        raise ValueError("Lot 27 conflict oracle mismatch")
    result = {
        "schema_version": "lot27-validation-v1",
        "status": "PASS",
        "dominant_state": state["dominant_state"],
        "aggregate_evidence_score": state["aggregate_evidence_score"],
        "weighted_coverage_ratio": state["weighted_coverage_ratio"],
        "output_checksum": state["output_checksum"],
    }
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Lot 27 evidence")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    args = parser.parse_args()
    validate(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
