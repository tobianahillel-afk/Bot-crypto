from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from crypto_quant_bot.market_analysis.alignment_audit import assert_no_forbidden_capabilities
from crypto_quant_bot.market_analysis.alignment_common import checksum
from crypto_quant_bot.market_analysis.alignment_io import load_json, load_jsonl

REQUIRED = {
    "contexts": "data/audit/timeframe_market_context_states_lot26.jsonl",
    "availability": "data/audit/closed_bar_availability_lot26.jsonl",
    "alignment": "data/audit/multi_timeframe_alignment_engine_lot26.json",
    "evidence": "data/audit/multi_timeframe_alignment_evidence_lot26.json",
    "replay": "data/audit/multi_timeframe_alignment_replay_lot26.json",
    "report": "reports/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_FINAL_REPORT.md",
}
SCHEMAS = {
    "contexts": "contracts/schemas/timeframe_market_context_state_v1.schema.json",
    "availability": "contracts/schemas/closed_bar_availability_v1.schema.json",
    "alignment": "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json",
}


def _validate_closed_schema(payload: dict[str, Any], schema: dict[str, Any], name: str) -> None:
    if schema.get("additionalProperties") is not False:
        raise ValueError(f"{name} schema is not closed")
    required = set(schema.get("required", []))
    properties = set(schema.get("properties", {}))
    if set(payload) != properties or not required.issubset(payload):
        raise ValueError(f"{name} payload/schema fields diverge")


def _validate_safety(alignment: dict[str, Any]) -> None:
    false_fields = (
        "used_for_decision",
        "forecast_generation_allowed",
        "probability_claims_allowed",
        "signal_generation_allowed",
        "order_routing_allowed",
        "execution_allowed",
        "trade_allowed",
    )
    if alignment.get("analysis_only") is not True:
        raise ValueError("analysis_only must be true")
    if any(alignment.get(field) is not False for field in false_fields):
        raise ValueError("Lot26 safety permissions are invalid")
    if alignment.get("approved_size") != 0:
        raise ValueError("approved_size must remain zero")


def validate(root: Path) -> dict[str, Any]:
    missing = [path for path in REQUIRED.values() if not (root / path).is_file()]
    if missing:
        raise ValueError("missing Lot26 evidence: " + ", ".join(missing))
    contexts = load_jsonl(root / REQUIRED["contexts"])
    availability = load_jsonl(root / REQUIRED["availability"])
    alignment = load_json(root / REQUIRED["alignment"])
    evidence = load_json(root / REQUIRED["evidence"])
    replay = load_json(root / REQUIRED["replay"])
    if len(contexts) != 2 or {row["timeframe"] for row in contexts} != {"5m", "15m"}:
        raise ValueError("Lot26 contexts must contain exactly 5m and 15m")
    if len(availability) != 2 or not all(row["is_closed"] and row["is_complete"] for row in availability):
        raise ValueError("Lot26 availability evidence is incomplete")
    for name, payloads in (("contexts", contexts), ("availability", availability)):
        schema = load_json(root / SCHEMAS[name])
        for payload in payloads:
            _validate_closed_schema(payload, schema, name)
    _validate_closed_schema(alignment, load_json(root / SCHEMAS["alignment"]), "alignment")
    assert_no_forbidden_capabilities(alignment)
    _validate_safety(alignment)
    expected_hash = checksum({key: value for key, value in alignment.items() if key != "output_checksum"})
    if alignment.get("output_checksum") != expected_hash:
        raise ValueError("Lot26 output checksum mismatch")
    if evidence.get("output_checksum") != alignment["output_checksum"]:
        raise ValueError("decision evidence does not reference alignment output")
    if replay.get("status") != "MATCH" or replay.get("run_1_checksum") != alignment["output_checksum"]:
        raise ValueError("Lot26 replay evidence is invalid")
    if alignment.get("overall_agreement_score") != 0.65:
        raise ValueError("Lot25→Lot26 integration oracle mismatch")
    if alignment.get("alignment_state") != "MTF_DIVERGENT":
        raise ValueError("expected multi-component divergence")
    result = {
        "schema_version": "lot26-validation-v1",
        "status": "PASS",
        "contexts": len(contexts),
        "agreement_score": alignment["overall_agreement_score"],
        "alignment_state": alignment["alignment_state"],
        "output_checksum": alignment["output_checksum"],
    }
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Lot 26 evidence")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    validate(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
