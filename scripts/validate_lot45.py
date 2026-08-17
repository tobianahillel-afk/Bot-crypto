#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    atomic_write_json,
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (  # noqa: E402
    EXPECTED_GATE_MERGE,
    build_lot45_artifacts,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (  # noqa: E402
    Lot45ValidationError,
    require_git_sha,
)

SCHEMAS = {
    "state": ROOT / "contracts/schemas/order_flow_delta_cvd_engine_state_v1.schema.json",
    "audit": ROOT / "contracts/schemas/order_flow_delta_cvd_engine_audit_v1.schema.json",
    "order_flow": ROOT / "contracts/schemas/order_flow_state_v1.schema.json",
    "cvd": ROOT / "contracts/schemas/cvd_series_v1.schema.json",
}
LOT46_FORBIDDEN = {
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine.py",
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine_models.py",
    "scripts/run_lot46_trade_classification_confidence_engine.py",
    "scripts/validate_lot46.py",
    "tests/test_lot46_trade_classification_confidence_engine.py",
    "data/audit/trade_classification_confidence_engine_lot46.json",
    "reports/lot_46_trade_classification_confidence_engine_report.md",
    "docs/LOT_46_TRADE_CLASSIFICATION_CONFIDENCE_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_46.md",
}


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _validate_git_boundary(code_commit: str) -> None:
    require_git_sha(code_commit, "code_commit")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_GATE_MERGE, code_commit],
        cwd=ROOT,
        check=True,
    )
    tree = set(_git("ls-tree", "-r", "--name-only", code_commit).splitlines())
    for path in LOT46_FORBIDDEN:
        if path in tree:
            raise Lot45ValidationError(f"Lot46 implementation started during Lot45: {path}")


def _load_schema_documents() -> dict[str, dict[str, Any]]:
    return {label: load_json_object(path) for label, path in SCHEMAS.items()}


def _validate_schema_files(schemas: dict[str, dict[str, Any]]) -> None:
    expected = {
        "state": ("order-flow-delta-cvd-engine-state-v1", "output_checksum"),
        "audit": ("order-flow-delta-cvd-engine-audit-v1", "audit_checksum"),
        "order_flow": ("order-flow-state-v1", "order_flow_checksum"),
        "cvd": ("cvd-series-v1", "cvd_checksum"),
    }
    for label, schema in schemas.items():
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise Lot45ValidationError(f"Lot45 {label} schema draft changed")
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            raise Lot45ValidationError(f"Lot45 {label} schema must be a closed object")
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            raise Lot45ValidationError(f"Lot45 {label} schema properties missing")
        schema_version, checksum_field = expected[label]
        if properties.get("schema_version", {}).get("const") != schema_version:
            raise Lot45ValidationError(f"Lot45 {label} schema version changed")
        required = schema.get("required")
        if not isinstance(required, list) or checksum_field not in required:
            raise Lot45ValidationError(f"Lot45 {label} checksum field not required")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise Lot45ValidationError(f"Lot45 {label} schema is invalid") from exc


def _schema_registry(schemas: dict[str, dict[str, Any]]) -> Registry:
    registry = Registry()
    for label, schema in schemas.items():
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise Lot45ValidationError(f"Lot45 {label} schema id missing")
        registry = registry.with_resource(schema_id, Resource.from_contents(schema))
    return registry


def _validate_generated_payloads(
    schemas: dict[str, dict[str, Any]],
    state: dict[str, Any],
    audit: dict[str, Any],
    order_flow: dict[str, Any],
    cvd: dict[str, Any],
) -> None:
    payloads = {
        "state": state,
        "audit": audit,
        "order_flow": order_flow,
        "cvd": cvd,
    }
    registry = _schema_registry(schemas)
    format_checker = FormatChecker()
    for label, payload in payloads.items():
        validator = Draft202012Validator(
            schemas[label],
            registry=registry,
            format_checker=format_checker,
        )
        errors = sorted(
            validator.iter_errors(payload),
            key=lambda error: (
                tuple(str(item) for item in error.absolute_path),
                error.message,
            ),
        )
        if errors:
            error = errors[0]
            location = ".".join(str(item) for item in error.absolute_path) or "$"
            raise Lot45ValidationError(
                f"Lot45 {label} payload violates schema at {location}: {error.message}"
            ) from error


def _write_validation_artifacts(
    output_dir: Path,
    state: dict[str, Any],
    audit: dict[str, Any],
    order_flow: dict[str, Any],
    cvd: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / "order_flow_delta_cvd_engine_lot45.json", state)
    atomic_write_json(output_dir / "order_flow_delta_cvd_engine_audit_lot45.json", audit)
    atomic_write_json(output_dir / "order_flow_state_lot45.json", order_flow)
    atomic_write_json(output_dir / "cvd_series_lot45.json", cvd)


def validate(code_commit: str, output_dir: Path | None = None) -> dict[str, Any]:
    _validate_git_boundary(code_commit)
    schemas = _load_schema_documents()
    _validate_schema_files(schemas)
    first = build_lot45_artifacts(ROOT, code_commit)
    second = build_lot45_artifacts(ROOT, code_commit)
    if first != second:
        raise Lot45ValidationError("Lot45 deterministic replay diverged")
    state, audit, order_flow, cvd = first
    _validate_generated_payloads(schemas, state, audit, order_flow, cvd)
    if canonical_checksum({k: v for k, v in state.items() if k != "output_checksum"}) != state["output_checksum"]:
        raise Lot45ValidationError("Lot45 state checksum replay mismatch")
    if canonical_checksum({k: v for k, v in audit.items() if k != "audit_checksum"}) != audit["audit_checksum"]:
        raise Lot45ValidationError("Lot45 audit checksum replay mismatch")
    if canonical_checksum({k: v for k, v in order_flow.items() if k != "order_flow_checksum"}) != order_flow["order_flow_checksum"]:
        raise Lot45ValidationError("Lot45 order-flow checksum replay mismatch")
    if canonical_checksum({k: v for k, v in cvd.items() if k != "cvd_checksum"}) != cvd["cvd_checksum"]:
        raise Lot45ValidationError("Lot45 CVD checksum replay mismatch")
    if output_dir is not None:
        _write_validation_artifacts(output_dir, state, audit, order_flow, cvd)
    return {
        "schema_version": "lot45-validation-result-v1",
        "status": "PASS",
        "verdict": "PASS_LOT45_ORDER_FLOW_DELTA_CVD_SOURCE",
        "code_commit": code_commit,
        "state_output_checksum": state["output_checksum"],
        "audit_checksum": audit["audit_checksum"],
        "order_flow_checksum": order_flow["order_flow_checksum"],
        "cvd_checksum": cvd["cvd_checksum"],
        "trades_total": order_flow["trades_total"],
        "total_volume": order_flow["total_volume"],
        "unknown_volume": order_flow["unknown_volume"],
        "signed_delta": order_flow["signed_delta"],
        "classification_coverage": order_flow["classification_coverage"],
        "confidence_weighted_coverage": order_flow["confidence_weighted_coverage"],
        "lot46_status": "PLANNED_LOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic Lot45 source")
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--output-dir", type=Path)
    arguments = parser.parse_args()
    try:
        result = validate(arguments.code_commit, arguments.output_dir)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"LOT45 VALIDATION: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
