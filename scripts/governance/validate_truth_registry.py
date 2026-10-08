#!/usr/bin/env python3
"""Validate repository truth classification and permanent current-state authority."""

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


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TruthRegistryError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TruthRegistryError(f"{path} must contain an object")
    return value


def _text(path: str) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except OSError as exc:
        raise TruthRegistryError(f"cannot read {path}: {exc}") from exc


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
    historical_count = 0
    stale_locators: set[str] = set()
    by_locator: dict[str, dict[str, Any]] = {}
    current_sources: list[dict[str, Any]] = []

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
        locator = source.get("locator")
        if not isinstance(locator, str) or not locator:
            raise TruthRegistryError(f"{source_id}: locator is required")
        if locator in by_locator:
            raise TruthRegistryError(f"duplicate source locator: {locator}")
        by_locator[locator] = source

        if source_type == "CURRENT_OPERATIONAL_STATE":
            current_sources.append(source)
        if source_type == "IMMUTABLE_HISTORICAL_EVIDENCE":
            historical_count += 1
            if source.get("mutation_policy") != "READ_ONLY_HISTORICAL":
                raise TruthRegistryError(f"{source_id}: historical evidence must be read-only")
        if source.get("status") in {"STALE", "PARTIALLY_STALE"}:
            stale_locators.add(locator)

    if len(current_sources) != 1:
        raise TruthRegistryError("exactly one CURRENT_OPERATIONAL_STATE is required")
    if current_sources[0].get("locator") != "config/governance/project_state.json":
        raise TruthRegistryError("permanent project state must be sole current operational state")
    if not (ROOT / "config/governance/project_state.json").exists():
        raise TruthRegistryError("permanent project state file is missing")
    if historical_count < 1:
        raise TruthRegistryError("immutable historical evidence is required")

    bridge = by_locator.get("engineering/STATE.json")
    if bridge is None:
        raise TruthRegistryError("bootstrap migration bridge must remain registered during ENG-01")
    if bridge.get("type") != "DERIVED_OR_HUMAN_STATUS_VIEW":
        raise TruthRegistryError("migration bridge must not be CURRENT_OPERATIONAL_STATE")
    if bridge.get("status") != "MIGRATION_BRIDGE":
        raise TruthRegistryError("engineering/STATE.json must be marked MIGRATION_BRIDGE")

    declared_stale = set(registry.get("known_drift_targets", []))
    if stale_locators != declared_stale:
        raise TruthRegistryError(
            f"known_drift_targets mismatch: expected {sorted(stale_locators)}, "
            f"got {sorted(declared_stale)}"
        )
    resolved = set(registry.get("resolved_drift_targets", []))
    if declared_stale & resolved:
        raise TruthRegistryError("a locator cannot be both stale and resolved")

    required_resolved = {
        "README.md",
        "docs/ROADMAP_V1_TO_V21.md",
        "pyproject.toml",
        "docs/FUNCTIONAL_COVERAGE_REGISTRY.md",
        "docs/SYSTEM_EXECUTION_ARCHITECTURE.md",
    }
    if not required_resolved.issubset(resolved):
        raise TruthRegistryError("ENG-00.2 primary reconciliation targets are incomplete")
    for locator in required_resolved:
        source = by_locator.get(locator)
        if source is None or not str(source.get("status", "")).startswith("RECONCILED_"):
            raise TruthRegistryError(f"{locator}: registry does not mark reconciliation")

    permanent = _json(ROOT / "config/governance/project_state.json")
    if permanent.get("authority", {}).get("current_state") != "config/governance/project_state.json":
        raise TruthRegistryError("permanent state does not self-declare current-state authority")

    readme = _text("README.md")
    if not readme.startswith("# Crypto Quant Bot V3.1-Ops"):
        raise TruthRegistryError("README canonical identity is not reconciled")
    for marker in ("Lot 44", "0.44.0", "Lot 45", "Lot 46"):
        if marker not in readme:
            raise TruthRegistryError(f"README current status missing {marker!r}")

    roadmap = _text("docs/ROADMAP_V1_TO_V21.md")
    for marker in (
        "Projet : **Crypto Quant Bot V3.1-Ops**",
        "## Autorité d’état courant",
        "config/governance/project_state.json",
        "engineering/CURRENT_STATUS.md",
    ):
        if marker not in roadmap:
            raise TruthRegistryError(f"roadmap authority reconciliation missing {marker!r}")
    if "## État actuel" in roadmap:
        raise TruthRegistryError("roadmap must not duplicate current operational status")
    if "engineering/STATE.json" in roadmap:
        raise TruthRegistryError("roadmap must not present migration bridge as current authority")

    pyproject = _text("pyproject.toml")
    if 'version = "0.44.0"' not in pyproject:
        raise TruthRegistryError("pyproject version is not the certified Lot44 baseline")
    if "Crypto Quant Bot V3.1-Ops" not in pyproject:
        raise TruthRegistryError("pyproject project identity is not reconciled")

    coverage = _text("docs/FUNCTIONAL_COVERAGE_REGISTRY.md")
    for marker in ("V2 | 21–30", "DONE_VALIDATED", "ACTIVE_PARTIAL_THROUGH_LOT44"):
        if marker not in coverage:
            raise TruthRegistryError(f"functional coverage reconciliation missing {marker!r}")

    architecture = _text("docs/SYSTEM_EXECUTION_ARCHITECTURE.md")
    for marker in (
        "## 8. Autorité d’état courant",
        "config/governance/project_state.json",
        "engineering/CURRENT_STATUS.md",
    ):
        if marker not in architecture:
            raise TruthRegistryError(
                f"system execution authority reconciliation missing {marker!r}"
            )
    if "## 8. État actuel" in architecture:
        raise TruthRegistryError("system execution architecture must not duplicate current state")
    if "engineering/STATE.json" in architecture:
        raise TruthRegistryError(
            "system execution architecture must not present migration bridge as current authority"
        )


def main() -> int:
    try:
        validate(_json(REGISTRY))
    except TruthRegistryError as exc:
        print(f"TRUTH_REGISTRY_INVALID: {exc}", file=sys.stderr)
        return 1
    print("TRUTH_REGISTRY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
