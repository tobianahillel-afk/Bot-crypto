#!/usr/bin/env python3
"""Validate the mandatory decision traceability contract and its governance links."""
from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.contracts import DecisionEvidenceEnvelopeV1  # noqa: E402

SCHEMA_PATH = ROOT / "contracts" / "schemas" / "decision_evidence_envelope_v1.schema.json"
REQUIRED_DOCS = (
    ROOT / "docs" / "DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md",
    ROOT / "docs" / "LOT_SPECIFICATION_STANDARD.md",
    ROOT / "docs" / "LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
    ROOT / "docs" / "LOT26_REQUIREMENT_TEST_MATRIX.md",
)


def main() -> int:
    violations: list[str] = []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_fields = set(map(str, schema.get("required", [])))
    model_fields = {field.name for field in fields(DecisionEvidenceEnvelopeV1)}

    if schema.get("title") != "DecisionEvidenceEnvelopeV1":
        violations.append("schema title must be DecisionEvidenceEnvelopeV1")
    if schema.get("additionalProperties") is not False:
        violations.append("schema must be closed with additionalProperties=false")
    if schema_fields != model_fields:
        missing_schema = sorted(model_fields - schema_fields)
        missing_model = sorted(schema_fields - model_fields)
        violations.append(
            f"schema/model field mismatch missing_schema={missing_schema} missing_model={missing_model}"
        )

    for path in REQUIRED_DOCS:
        if not path.is_file():
            violations.append(f"missing governance document: {path.relative_to(ROOT)}")
            continue
        content = path.read_text(encoding="utf-8")
        if "DecisionEvidenceEnvelopeV1" not in content:
            violations.append(f"{path.relative_to(ROOT)} does not require DecisionEvidenceEnvelopeV1")

    if violations:
        print("TRACEABILITY_CONTRACT: FAIL")
        print("\n".join(violations))
        return 1
    print("TRACEABILITY_CONTRACT: PASS")
    print(f"required_fields={len(schema_fields)} governance_documents={len(REQUIRED_DOCS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
