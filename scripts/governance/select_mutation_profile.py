#!/usr/bin/env python3
"""Select mutation profiles deterministically from changed repository paths."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "mutation_profile_policy_v1.json"
REGISTRY_PATH = ROOT / "config" / "governance" / "mutation_profiles_v1.json"


class MutationProfileSelectionError(ValueError):
    pass


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_mutation_profiles.py"
    spec = importlib.util.spec_from_file_location("mutation_profile_validator_for_selector", path)
    if spec is None or spec.loader is None:
        raise MutationProfileSelectionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MutationProfileSelectionError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MutationProfileSelectionError(f"{path} must contain an object")
    return value


def _safe_changed_path(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise MutationProfileSelectionError("changed path must be a non-empty string")
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in path:
        raise MutationProfileSelectionError(f"unsafe changed path: {path!r}")
    if path.startswith("./") or "//" in path:
        raise MutationProfileSelectionError(f"non-canonical changed path: {path!r}")
    return candidate.as_posix()


def _matches(path: str, selector: dict[str, str]) -> bool:
    if selector["mode"] == "EXACT":
        return path == selector["pattern"]
    if selector["mode"] == "GLOB":
        return fnmatch.fnmatchcase(path, selector["pattern"])
    raise MutationProfileSelectionError(f"unsupported selector mode: {selector['mode']!r}")


def select_profiles(changed_paths: list[str], registry: dict[str, Any]) -> dict[str, Any]:
    paths = sorted({_safe_changed_path(path) for path in changed_paths})
    profiles = [
        profile for profile in registry.get("profiles", [])
        if isinstance(profile, dict) and profile.get("enabled") is True
    ]
    selected: set[str] = set()
    path_matches: list[dict[str, Any]] = []

    for path in paths:
        matches: list[str] = []
        for profile in profiles:
            if any(_matches(path, selector) for selector in profile["selectors"]):
                matches.append(profile["id"])
        matches = sorted(set(matches))
        if len(matches) > 1:
            raise MutationProfileSelectionError(
                f"changed path matches multiple mutation profiles: {path}: {matches}"
            )
        if matches:
            selected.add(matches[0])
        path_matches.append({"path": path, "profiles": matches})

    return {
        "selector_version": 1,
        "changed_paths": paths,
        "path_matches": path_matches,
        "selected_profiles": sorted(selected),
        "mutation_executed": False,
    }


def repository_select(changed_paths: list[str]) -> dict[str, Any]:
    validator = _module()
    policy = _load_json(POLICY_PATH)
    registry = _load_json(REGISTRY_PATH)
    try:
        validator.validate_all(policy, registry)
    except validator.MutationProfileError as exc:
        raise MutationProfileSelectionError(str(exc)) from exc
    return select_profiles(changed_paths, registry)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Repository-relative changed paths.")
    parser.add_argument(
        "--path", action="append", default=[],
        help="Repository-relative changed path; may be repeated."
    )
    args = parser.parse_args()
    try:
        result = repository_select([*args.paths, *args.path])
    except (MutationProfileSelectionError, OSError, KeyError, TypeError) as exc:
        print(f"MUTATION_PROFILE_SELECTION_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
