#!/usr/bin/env python3
"""Validate the repository truth registry using Python standard library only."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "engineering" / "REPOSITORY_TRUTH_REGISTRY.json"

ALLOWED_TYPES = {
    "IMMUTABLE_HISTORICAL_EVIDENCE",
    "CURRENT_OPERATIONAL_STATE",
    "NORMATIVE_POLICY",
    "CERTIFIED_GATE_STATE",
    "DERIVED_OR_HUMAN_STATUS_VIEW",
    "EXTERNAL_GIT_REALITY",
    "CANDIDATE_OR_PR_CONTEXT",
}


class TruthRegistryError(ValueError):
    pass


def load() -> dict[str, Any]:
    try:
        value = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TruthRegistryError(f"cannot load truth registry: {exc}") from exc
    if not isinstance(value, dict):
        raise TruthRegistryError("truth registry must be an object")
    return value


def validate(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise TruthRegistryError("unsupported schema_version")
    if registry.get("registry_kind") != "repository_truth_registry":
        raise TruthRegistryError("invalid registry_kind")
    if registry.get("project") != "Crypto Quant Bot V3.1-Ops":
        raise TruthRegistryError("canonical project identity drift")

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise TruthRegistryError("sources must be non-empty")

    ids: set[str] = set()
    current_state_count = 0
    historical_count = 0
    stale_locators: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise TruthRegistryError("source must be an object")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            raise TruthRegistryError("source id must be non-empty")
        if source_id in ids:
            raise TruthRegistryError(f"duplicate source id: {source_id}")
        ids.add(source_id)
        source_type = source.get("type")
        if source_type not in ALLOWED_TYPES:
            raise TruthRegistryError(f"invalid source type: {source_type}")
        if not isinstance(source.get("locator"), str) or not source["locator"]:
            raise TruthRegistryError(f"{source_id}: locator is required")
        if source_type == "CURRENT_OPERATIONAL_STATE":
            current_state_count += 1
        if source_type == "IMMUTABLE_HISTORICAL_EVIDENCE":
            historical_count += 1
            if source.get("mutation_policy") != "READ_ONLY_HISTORICAL":
                raise TruthRegistryError(f"{source_id}: historical evidence must be read-only")
        if source.get("status") in {"STALE", "PARTIALLY_STALE"}:
            stale_locators.add(source["locator"])

    if current_state_count != 1:
        raise TruthRegistryError("exactly one CURRENT_OPERATIONAL_STATE is required")
    if historical_count < 1:
        raise TruthRegistryError("at least one immutable historical evidence source is required")

    expected_stale = set(registry.get("known_drift_targets", []))
    if stale_locators != expected_stale:
        raise TruthRegistryError(
            f"known_drift_targets mismatch: expected {sorted(stale_locators)}, "
            f"got {sorted(expected_stale)}"
        )

    required = {"README.md", "docs/ROADMAP_V1_TO_V21.md", "pyproject.toml"}
    if not required.issubset(expected_stale):
        raise TruthRegistryError("known primary drift targets are missing")


def main() -> int:
    try:
        validate(load())
    except TruthRegistryError as exc:
        print(f"TRUTH_REGISTRY_INVALID: {exc}", file=sys.stderr)
        return 1
    print("TRUTH_REGISTRY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
