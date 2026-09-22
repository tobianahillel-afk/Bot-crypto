#!/usr/bin/env python3
"""Validate the permanent project-state V1 schema and ENG-00-derived reference fixture."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "config" / "governance" / "project_state_v1.schema.json"
FIXTURE_PATH = ROOT / "engineering" / "fixtures" / "project_state_v1.example.json"
BASELINE_PATH = ROOT / "engineering" / "CANONICAL_BASELINE.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class ProjectStateSchemaError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectStateSchemaError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectStateSchemaError(f"{path} must contain an object")
    return value


def _require_closed_object(schema: dict[str, Any], key: str) -> None:
    section = schema.get("properties", {}).get(key)
    if not isinstance(section, dict):
        raise ProjectStateSchemaError(f"schema missing section: {key}")
    if section.get("additionalProperties") is not False and "$ref" not in section:
        raise ProjectStateSchemaError(f"schema section {key} must be closed or referenced")


def validate() -> None:
    schema = _load(SCHEMA_PATH)
    fixture = _load(FIXTURE_PATH)
    baseline = _load(BASELINE_PATH)

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ProjectStateSchemaError("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ProjectStateSchemaError("top-level project-state schema must be a closed object")

    required = set(schema.get("required", []))
    expected = {
        "schema_version","state_kind","project","business_track","engineering_track",
        "audit_track","safety","cost_policy","authority","external_observations",
        "findings","stop_conditions","freshness_policy"
    }
    if required != expected:
        raise ProjectStateSchemaError("top-level required field set drift")

    for section in (
        "project","business_track","audit_track","cost_policy","authority",
        "external_observations","freshness_policy"
    ):
        _require_closed_object(schema, section)

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        raise ProjectStateSchemaError("$defs is required")
    for name in ("certifiedBaseline","entryGate","businessCandidate","nextLot","workTrack","safety","finding"):
        definition = defs.get(name)
        if not isinstance(definition, dict) or definition.get("additionalProperties") is not False:
            raise ProjectStateSchemaError(f"$defs.{name} must be a closed object")

    if fixture.get("schema_version") != 1 or fixture.get("state_kind") != "project_state_v1":
        raise ProjectStateSchemaError("reference fixture schema identity drift")
    if fixture.get("project") != baseline.get("project"):
        raise ProjectStateSchemaError("fixture project identity disagrees with ENG-00 baseline")

    fixture_business = fixture.get("business_track", {})
    baseline_business = baseline.get("business", {})
    if fixture_business != baseline_business:
        raise ProjectStateSchemaError("fixture business track must be byte-structurally derived from baseline business")

    if fixture.get("safety") != baseline.get("safety"):
        raise ProjectStateSchemaError("fixture safety must match ENG-00 baseline")

    observations = fixture.get("external_observations", {})
    baseline_observations = baseline.get("external_git_observations", {})
    if observations.get("main") != baseline_observations.get("main"):
        raise ProjectStateSchemaError("fixture main observation disagrees with ENG-00 baseline")
    if observations.get("rulesets_count") != baseline_observations.get("rulesets_count"):
        raise ProjectStateSchemaError("fixture rulesets observation disagrees with ENG-00 baseline")

    candidate = fixture_business.get("candidate", {})
    if not isinstance(candidate, dict) or candidate.get("merged") is not False:
        raise ProjectStateSchemaError("reference candidate must remain unmerged")
    for key in ("source_head","implementation_merge","post_merge_audit_head","post_merge_audit_merge"):
        value = fixture_business.get("merged_certified_baseline", {}).get(key)
        if not isinstance(value, str) or SHA40.fullmatch(value) is None:
            raise ProjectStateSchemaError(f"fixture certified baseline {key} is not SHA-40")

    safety = fixture.get("safety", {})
    if safety.get("trade_allowed") is not False or safety.get("execution_allowed") is not False:
        raise ProjectStateSchemaError("reference fixture must remain fail-closed")
    if safety.get("live_execution") != "DISABLED":
        raise ProjectStateSchemaError("reference fixture live execution must remain disabled")

    cost = fixture.get("cost_policy", {})
    if any(cost.get(key) is not False for key in (
        "paid_external_api_required","paid_llm_required","paid_saas_required","paid_runner_required"
    )):
        raise ProjectStateSchemaError("reference fixture mandatory cost policy must remain zero-cost")


def main() -> int:
    try:
        validate()
    except ProjectStateSchemaError as exc:
        print(f"PROJECT_STATE_SCHEMA_INVALID: {exc}", file=sys.stderr)
        return 1
    print("PROJECT_STATE_SCHEMA_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
