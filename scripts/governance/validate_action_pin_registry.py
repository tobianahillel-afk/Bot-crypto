#!/usr/bin/env python3
"""Validate the offline approved GitHub Action pin registry and repository coverage."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config" / "governance" / "action_pin_registry_v1.json"

EXPECTED = {
    "actions/checkout": ("v4", "commit", "11d5960a326750d5838078e36cf38b85af677262", "11d5960a326750d5838078e36cf38b85af677262"),
    "actions/setup-python": ("v5", "commit", "a26af69be951a213d495a4c3e4e4022e16d87065", "a26af69be951a213d495a4c3e4e4022e16d87065"),
    "actions/upload-artifact": ("v4", "commit", "ea165f8d65b6e75b540449e92b4886f43607fa02", "ea165f8d65b6e75b540449e92b4886f43607fa02"),
    "actions/setup-go": ("v7.0.0", "commit", "b7ad1dad31e06c5925ef5d2fc7ad053ef454303e", "b7ad1dad31e06c5925ef5d2fc7ad053ef454303e"),
    "actions/dependency-review-action": ("v5.0.0", "commit", "a1d282b36b6f3519aa1f3fc636f609c47dddb294", "a1d282b36b6f3519aa1f3fc636f609c47dddb294"),
    "github/codeql-action": ("v4.38.1", "tag", "c23de5a82f64bb08c6d9f28844551440ca298e76", "1c5b675653bb5c22dbe9b12b556ec555138e09fd"),
}

LEGACY_REFS = {
    "actions/checkout": {"v4"},
    "actions/setup-python": {"v5"},
    "actions/upload-artifact": {"v4"},
    "actions/setup-go": set(),
    "actions/dependency-review-action": set(),
    "github/codeql-action": set(),
}


class ActionPinRegistryError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ActionPinRegistryError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActionPinRegistryError(f"{path} must contain an object")
    return value


def _auditor() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "audit_action_supply_chain.py"
    spec = importlib.util.spec_from_file_location("action_pin_registry_auditor", path)
    if spec is None or spec.loader is None:
        raise ActionPinRegistryError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_registry_only(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise ActionPinRegistryError("unsupported registry schema_version")
    if registry.get("registry_kind") != "action_pin_registry_v1":
        raise ActionPinRegistryError("invalid registry kind")
    if registry.get("semantics") != "OFFLINE_APPROVED_REMOTE_ACTION_PINS":
        raise ActionPinRegistryError("registry semantics drift")
    if registry.get("observed_date") != "2026-09-23":
        raise ActionPinRegistryError("registry observation date drift")
    if not isinstance(registry.get("evidence_source"), str) or not registry["evidence_source"]:
        raise ActionPinRegistryError("registry evidence source missing")

    entries = registry.get("entries")
    if not isinstance(entries, list) or len(entries) != 6:
        raise ActionPinRegistryError("registry must contain exactly six repositories")

    by_repo: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ActionPinRegistryError("registry entry must be an object")
        repository = entry.get("repository")
        if not isinstance(repository, str) or repository in by_repo:
            raise ActionPinRegistryError("repository entries must be unique")
        by_repo[repository] = entry

    if set(by_repo) != set(EXPECTED):
        raise ActionPinRegistryError("registry repository set drift")

    for repository, (source_ref, ref_type, ref_sha, approved_sha) in EXPECTED.items():
        entry = by_repo[repository]
        if entry.get("source_ref") != source_ref:
            raise ActionPinRegistryError(f"{repository} source ref drift")
        if entry.get("ref_object_type") != ref_type:
            raise ActionPinRegistryError(f"{repository} ref type drift")
        if entry.get("ref_object_sha") != ref_sha:
            raise ActionPinRegistryError(f"{repository} ref object SHA drift")
        if entry.get("approved_commit_sha") != approved_sha:
            raise ActionPinRegistryError(f"{repository} approved SHA drift")
        if re.fullmatch(r"[0-9a-f]{40}", approved_sha) is None:
            raise ActionPinRegistryError(f"{repository} approved SHA must be lowercase 40-hex")
        if ref_type == "commit" and ref_sha != approved_sha:
            raise ActionPinRegistryError(f"{repository} direct ref must equal approved commit")
        if ref_type == "tag" and entry.get("dereferenced_commit_sha") != approved_sha:
            raise ActionPinRegistryError(f"{repository} annotated tag dereference mismatch")
        if entry.get("license") != "MIT":
            raise ActionPinRegistryError(f"{repository} license must be MIT")
        if not str(entry.get("license_url", "")).startswith("https://raw.githubusercontent.com/"):
            raise ActionPinRegistryError(f"{repository} license evidence URL invalid")
        if entry.get("public") is not True or entry.get("archived") is not False:
            raise ActionPinRegistryError(f"{repository} repository state evidence invalid")
        if entry.get("owner") != repository.split("/", 1)[0]:
            raise ActionPinRegistryError(f"{repository} owner drift")
        if set(entry.get("legacy_floating_refs", [])) != LEGACY_REFS[repository]:
            raise ActionPinRegistryError(f"{repository} legacy floating mapping drift")


def validate_repository_coverage(registry: dict[str, Any]) -> dict[str, int]:
    auditor = _auditor()
    policy = auditor._json(auditor.POLICY_PATH)
    auditor.validate_policy(policy)
    result = auditor.audit(auditor.discover_files(policy), policy)

    by_repo = {entry["repository"]: entry for entry in registry["entries"]}
    current_repositories = set(result["remote_repositories"])
    if current_repositories != set(by_repo):
        raise ActionPinRegistryError(
            f"remote repository coverage drift: current={sorted(current_repositories)}"
        )

    approved = {
        repository: entry["approved_commit_sha"]
        for repository, entry in by_repo.items()
    }
    pinned_count = 0
    floating_count = 0
    for record in result["records"]:
        repository = (
            f"{record['owner']}/{record['repo']}"
            if record.get("owner") and record.get("repo")
            else None
        )
        if record["classification"] == "REMOTE_PINNED_SHA":
            if repository is None or record["ref"] != approved.get(repository):
                raise ActionPinRegistryError(
                    f"current pinned use is not approved: {record['file']}:{record['line']}"
                )
            pinned_count += 1
        elif record["classification"] == "REMOTE_FLOATING_REF":
            if repository is None or record["ref"] not in set(
                by_repo[repository]["legacy_floating_refs"]
            ):
                raise ActionPinRegistryError(
                    f"legacy floating ref lacks replacement: {record['file']}:{record['line']}"
                )
            floating_count += 1

    return {
        "registry_entries": len(by_repo),
        "remote_repositories": len(current_repositories),
        "approved_pinned_uses": pinned_count,
        "mapped_legacy_floating_uses": floating_count,
    }


def main() -> int:
    try:
        registry = _json(REGISTRY_PATH)
        validate_registry_only(registry)
        summary = validate_repository_coverage(registry)
    except ActionPinRegistryError as exc:
        print(f"ACTION_PIN_REGISTRY_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "ACTION_PIN_REGISTRY_VALID", **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
