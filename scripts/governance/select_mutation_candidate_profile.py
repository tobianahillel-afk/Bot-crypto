#!/usr/bin/env python3
"""Select read-only mutation candidate profiles for qualification only."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config/governance/mutation_candidate_profiles_v1.json"


class MutationCandidateSelectionError(ValueError):
    pass


def _load() -> dict[str, Any]:
    try:
        value = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MutationCandidateSelectionError(f"cannot load candidate registry: {exc}") from exc
    if not isinstance(value, dict):
        raise MutationCandidateSelectionError("candidate registry must contain an object")
    return value


def _safe_changed_path(path: str) -> str:
    if not isinstance(path, str) or not path:
        raise MutationCandidateSelectionError("changed path must be non-empty")
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in path:
        raise MutationCandidateSelectionError(f"unsafe changed path: {path!r}")
    return candidate.as_posix()


def _matches(path: str, selector: dict[str, Any]) -> bool:
    mode, pattern = selector["mode"], selector["pattern"]
    if mode == "EXACT":
        return path == pattern
    if mode == "GLOB":
        return fnmatch.fnmatchcase(path, pattern)
    raise MutationCandidateSelectionError(f"unsupported selector mode: {mode}")


def select_candidates(paths: list[str], registry: dict[str, Any]) -> dict[str, Any]:
    changed = sorted({_safe_changed_path(path) for path in paths})
    profiles = registry.get("profiles")
    if not isinstance(profiles, list):
        raise MutationCandidateSelectionError("candidate profile list missing")
    matched: dict[str, list[str]] = {}
    for path in changed:
        ids = []
        for profile in profiles:
            if not isinstance(profile, dict):
                raise MutationCandidateSelectionError("candidate profile is not an object")
            if profile.get("lifecycle") != "READ_ONLY_QUALIFIED_NOT_ADOPTED":
                raise MutationCandidateSelectionError("candidate lifecycle is not qualification-only")
            if any(profile.get(flag) is not False for flag in (
                "execution_allowed","active_registry_adopted",
                "production_selector_visible","generic_runner_executable"
            )):
                raise MutationCandidateSelectionError("candidate execution/adoption flag drift")
            if any(_matches(path, sel) for sel in profile.get("selectors", [])):
                ids.append(profile["id"])
        if len(ids) > 1:
            raise MutationCandidateSelectionError(f"ambiguous candidate profile match for {path}: {ids}")
        if ids:
            matched[path] = ids
    selected = sorted({item for ids in matched.values() for item in ids})
    return {
        "candidate_selector_version":1,
        "changed_paths":changed,
        "matched_paths":matched,
        "selected_candidates":selected,
        "qualification_only":True,
        "production_selector_visible":False,
        "active_registry_adopted":False,
        "execution_allowed":False,
        "mutation_executed":False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", dest="paths", default=[])
    args = parser.parse_args()
    try:
        result = select_candidates(args.paths, _load())
    except MutationCandidateSelectionError as exc:
        print(f"MUTATION_CANDIDATE_SELECTION_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
