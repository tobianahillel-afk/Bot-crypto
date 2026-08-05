from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.market_analysis.alignment_io import load_json  # noqa: E402
from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer import (  # noqa: E402
    checksum,
    validate_config,
)
from crypto_quant_bot.market_analysis.explanation_core_validation import (  # noqa: E402
    mapping,
    validate_reason_set,
    validate_safety,
    validate_statements,
)

CONFIG_PATH = "config/explanations/explanation_core_why_not_trade_v1.json"
OUTPUT_PATH = "data/audit/explanation_core_and_why_not_trade_layer_lot28.json"
AUDIT_PATH = "data/audit/explanation_core_and_why_not_trade_layer_audit_lot28.json"
REPORT_PATH = "reports/lot_28_explanation_core_and_why_not_trade_layer_report.md"
SCHEMA_PATH = "contracts/schemas/explanation_core_why_not_trade_layer_state_v1.schema.json"


def _field_sets(schema: Mapping[str, Any]) -> dict[str, set[str]]:
    bundle = mapping(schema["properties"]["bundle"], "schema.bundle")
    statement = mapping(schema["$defs"]["statement"], "schema.statement")
    evidence = mapping(schema["$defs"]["evidence_reference"], "schema.evidence")
    reason = mapping(schema["$defs"]["why_reason"], "schema.reason")
    reason_set = mapping(bundle["properties"]["why_not_trade"], "schema.reason_set")
    return {
        "state": set(schema["properties"]),
        "bundle": set(bundle["properties"]),
        "statement": set(statement["properties"]),
        "evidence": set(evidence["properties"]),
        "reason": set(reason["properties"]),
        "reason_set": set(reason_set["properties"]),
    }


def _validate_evidence_fields(refs: object, expected: set[str]) -> None:
    if not isinstance(refs, list) or not refs:
        raise ValueError("evidence reference list is empty or invalid")
    for reference in refs:
        if set(mapping(reference, "evidence")) != expected:
            raise ValueError("evidence/schema fields diverge")


def _validate_closed_fields(state: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    expected = _field_sets(schema)
    if schema.get("additionalProperties") is not False or set(state) != expected["state"]:
        raise ValueError("state/schema fields diverge")
    bundle = mapping(state["bundle"], "bundle")
    if set(bundle) != expected["bundle"]:
        raise ValueError("bundle/schema fields diverge")
    for section, values in bundle.items():
        if section in {"schema_version", "why_not_trade"}:
            continue
        if not isinstance(values, list):
            raise ValueError(f"invalid bundle section: {section}")
        for statement_value in values:
            statement = mapping(statement_value, "statement")
            if set(statement) != expected["statement"]:
                raise ValueError("statement/schema fields diverge")
            _validate_evidence_fields(statement["evidence_refs"], expected["evidence"])
    reason_set = mapping(bundle["why_not_trade"], "reason_set")
    if set(reason_set) != expected["reason_set"]:
        raise ValueError("reason-set/schema fields diverge")
    reasons = reason_set["reasons"]
    if not isinstance(reasons, list):
        raise ValueError("reason list is invalid")
    for reason_value in reasons:
        reason = mapping(reason_value, "reason")
        if set(reason) != expected["reason"]:
            raise ValueError("reason/schema fields diverge")
        _validate_evidence_fields(reason["evidence_refs"], expected["evidence"])


def _load_sources(root: Path, config: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = mapping(config["input_artifacts"], "input_artifacts")
    return {str(path): load_json(root / str(path)) for path in artifacts.values()}


def _validate_checksums(state: Mapping[str, Any], audit: Mapping[str, Any]) -> str:
    payload = dict(state)
    stored = str(payload.pop("output_checksum"))
    if stored != checksum(payload):
        raise ValueError("Lot 28 output checksum mismatch")
    if audit.get("output_checksum") != stored or audit.get("replay_status") != "MATCH":
        raise ValueError("Lot 28 audit linkage or replay status is invalid")
    return stored


def validate(root: Path) -> dict[str, Any]:
    required = (CONFIG_PATH, OUTPUT_PATH, AUDIT_PATH, REPORT_PATH, SCHEMA_PATH)
    missing = [path for path in required if not (root / path).is_file()]
    if missing:
        raise ValueError("missing Lot 28 evidence: " + ", ".join(missing))
    config = load_json(root / CONFIG_PATH)
    state = load_json(root / OUTPUT_PATH)
    audit = load_json(root / AUDIT_PATH)
    schema = load_json(root / SCHEMA_PATH)
    validate_config(config)
    _validate_closed_fields(state, schema)
    bundle = mapping(state["bundle"], "bundle")
    sources = _load_sources(root, config)
    statement_codes = validate_statements(bundle, config, sources)
    reason_codes = validate_reason_set(bundle, config, sources)
    expected_codes = statement_codes + reason_codes
    if tuple(state["reason_codes"]) != expected_codes or len(expected_codes) != len(set(expected_codes)):
        raise ValueError("state reason-code sequence mismatch")
    validate_safety(state, config)
    stored_checksum = _validate_checksums(state, audit)
    if audit.get("dominant_reason_code") != "WNT_PERMISSIONS_DISABLED":
        raise ValueError("audit dominant reason mismatch")
    if audit.get("statement_count") != 14 or audit.get("why_not_reason_count") != 3:
        raise ValueError("deterministic explanation count mismatch")
    result = {
        "schema_version": "lot28-validation-v1",
        "status": "PASS",
        "statement_count": audit["statement_count"],
        "why_not_reason_count": audit["why_not_reason_count"],
        "dominant_reason_code": audit["dominant_reason_code"],
        "output_checksum": stored_checksum,
    }
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Lot 28 explanation evidence")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    args = parser.parse_args()
    validate(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
