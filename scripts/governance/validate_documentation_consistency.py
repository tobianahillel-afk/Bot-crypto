#!/usr/bin/env python3
"""Validate current-authority documentation consistency without scanning historical evidence."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "documentation_consistency_policy_v1.json"


class DocumentationConsistencyError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentationConsistencyError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DocumentationConsistencyError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise DocumentationConsistencyError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _field(value: dict[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise DocumentationConsistencyError(f"state field missing: {dotted}")
        current = current[part]
    return current


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise DocumentationConsistencyError("unsupported documentation consistency policy version")
    if policy.get("policy_kind") != "documentation_consistency_policy_v1":
        raise DocumentationConsistencyError("invalid documentation consistency policy kind")
    if policy.get("semantics") != "REGISTERED_CURRENT_AUTHORITY_DOCS_FAIL_CLOSED":
        raise DocumentationConsistencyError("documentation consistency semantics drift")
    if policy.get("state_source") != "config/governance/project_state.json":
        raise DocumentationConsistencyError("current-state source drift")
    if policy.get("authority_registry") != "engineering/DOCUMENTATION_AUTHORITY_REGISTRY.json":
        raise DocumentationConsistencyError("documentation authority registry path drift")
    if policy.get("scan_scope") != "REGISTERED_DOCUMENTS_ONLY":
        raise DocumentationConsistencyError("historical documents must not be globally scanned as current status")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise DocumentationConsistencyError("documentation consistency path must remain zero-cost")


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise DocumentationConsistencyError("unsupported documentation authority registry version")
    if registry.get("registry_kind") != "documentation_authority_registry_v1":
        raise DocumentationConsistencyError("invalid documentation authority registry kind")
    if registry.get("semantics") != "PROGRESSIVE_DISCLOSURE_WITH_SINGLE_CURRENT_STATE_AUTHORITY":
        raise DocumentationConsistencyError("documentation authority semantics drift")
    if registry.get("current_state_authority") != "config/governance/project_state.json":
        raise DocumentationConsistencyError("registry current-state authority drift")
    bridge = registry.get("compatibility_bridge")
    if not isinstance(bridge, dict) or bridge.get("path") != "engineering/STATE.json":
        raise DocumentationConsistencyError("compatibility bridge registration missing")
    if bridge.get("authorization_allowed") is not False:
        raise DocumentationConsistencyError("compatibility bridge cannot authorize work")

    docs = registry.get("documents")
    if not isinstance(docs, list) or not docs:
        raise DocumentationConsistencyError("documentation registry is empty")
    paths = [item.get("path") for item in docs if isinstance(item, dict)]
    if len(paths) != len(docs) or len(paths) != len(set(paths)):
        raise DocumentationConsistencyError("registered document paths must be unique")
    for item in docs:
        if item.get("bridge_policy") not in {"FORBIDDEN", "COMPATIBILITY_ONLY"}:
            raise DocumentationConsistencyError(f"invalid bridge policy for {item.get('path')}")
        for key in ("required_substrings", "forbidden_substrings"):
            values = item.get(key)
            if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
                raise DocumentationConsistencyError(f"{key} invalid for {item.get('path')}")


def validate_document(
    item: dict[str, Any],
    text: str,
    *,
    canonical_identity: str,
    bridge_path: str,
) -> None:
    path = item["path"]
    for required in item["required_substrings"]:
        if required not in text:
            raise DocumentationConsistencyError(f"{path} missing required content: {required}")
    for forbidden in item["forbidden_substrings"]:
        if forbidden in text:
            raise DocumentationConsistencyError(f"{path} contains forbidden content: {forbidden}")
    if item.get("canonical_identity_required") is True and canonical_identity not in text:
        raise DocumentationConsistencyError(f"{path} does not contain canonical identity {canonical_identity}")
    bridge_count = text.count(bridge_path)
    if item["bridge_policy"] == "FORBIDDEN" and bridge_count:
        raise DocumentationConsistencyError(f"{path} must not reference compatibility bridge {bridge_path}")
    if item["bridge_policy"] == "COMPATIBILITY_ONLY":
        if bridge_count != 1:
            raise DocumentationConsistencyError(f"{path} must contain exactly one compatibility bridge reference")
        if "migration compatibility bridge" not in text:
            raise DocumentationConsistencyError(f"{path} bridge reference lacks compatibility-only label")


def validate_registered_documents(
    state: dict[str, Any],
    registry: dict[str, Any],
    *,
    root: Path = ROOT,
) -> None:
    canonical_identity = _field(state, "project.canonical_name")
    bridge_path = registry["compatibility_bridge"]["path"]
    for item in registry["documents"]:
        path = root / item["path"]
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise DocumentationConsistencyError(f"cannot read registered document {path}: {exc}") from exc
        validate_document(
            item, text, canonical_identity=canonical_identity, bridge_path=bridge_path
        )


def validate_generated_status(policy: dict[str, Any]) -> None:
    renderer = _module(
        "documentation_consistency_status_renderer",
        ROOT / policy["generated_status_renderer"],
    )
    try:
        renderer.run("check")
    except renderer.CurrentStatusError as exc:
        raise DocumentationConsistencyError(f"generated current status drift: {exc}") from exc


def validate_snapshot_binding(
    state: dict[str, Any],
    registry: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    lot = _field(state, policy["status_snapshot"]["baseline_lot_field"])
    version = _field(state, policy["status_snapshot"]["baseline_version_field"])
    entry = next(
        (item for item in registry["documents"] if item["role"] == "REFERENCE_BASELINE_SNAPSHOT"),
        None,
    )
    if entry is None:
        raise DocumentationConsistencyError("reference baseline snapshot document missing")
    text = (ROOT / entry["path"]).read_text(encoding="utf-8")
    expected = f"Snapshot de couverture métier : baseline certifiée Lot {lot} (`{version}`)"
    if expected not in text:
        raise DocumentationConsistencyError(
            f"reference coverage snapshot does not match certified baseline: {expected}"
        )


def run() -> None:
    policy = _json(POLICY_PATH)
    validate_policy(policy)
    state = _json(ROOT / policy["state_source"])
    registry = _json(ROOT / policy["authority_registry"])
    validate_registry(registry)
    validate_registered_documents(state, registry)
    validate_snapshot_binding(state, registry, policy)
    validate_generated_status(policy)


def main() -> int:
    try:
        run()
    except (DocumentationConsistencyError, OSError, KeyError) as exc:
        print(f"DOCUMENTATION_CONSISTENCY_INVALID: {exc}", file=sys.stderr)
        return 1
    print("DOCUMENTATION_CONSISTENCY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
