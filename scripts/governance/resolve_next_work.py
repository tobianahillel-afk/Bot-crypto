#!/usr/bin/env python3
"""Resolve the exact next work context from canonical repository state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ResolveError(ValueError):
    """Raised when current work cannot be resolved unambiguously."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResolveError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ResolveError(f"{path} must contain an object")
    return value


def resolve(state: dict[str, Any], capabilities: dict[str, Any], profile: str) -> dict[str, Any]:
    profiles = capabilities.get("profiles")
    if not isinstance(profiles, dict) or profile not in profiles:
        raise ResolveError(f"unknown capability profile: {profile}")

    bootstrap = state.get("bootstrap_engine")
    if not isinstance(bootstrap, dict):
        raise ResolveError("missing bootstrap_engine state")

    phase = bootstrap.get("phase")
    if phase == "BUILDING":
        active_lot = bootstrap.get("active_lot")
        active_task = bootstrap.get("active_task")
        active_manifest = bootstrap.get("active_manifest")
        track = "BOOTSTRAP_ENGINE"
    elif phase == "STABLE":
        engineering = state.get("engineering_engine")
        if not isinstance(engineering, dict):
            raise ResolveError("bootstrap is STABLE but engineering_engine is missing")
        active_lot = engineering.get("active_lot")
        active_task = engineering.get("active_task")
        active_manifest = engineering.get("active_manifest")
        track = "DEVELOPMENT_ENGINE"
    else:
        raise ResolveError(f"unknown bootstrap phase: {phase!r}")

    for name, value in {
        "active_lot": active_lot,
        "active_task": active_task,
        "active_manifest": active_manifest,
    }.items():
        if not isinstance(value, str) or not value:
            raise ResolveError(f"{track} {name} is not resolvable")

    profile_data = profiles[profile]
    return {
        "project": state.get("project", {}).get("canonical_name"),
        "track": track,
        "active_lot": active_lot,
        "active_task": active_task,
        "active_manifest": active_manifest,
        "capability_profile": profile,
        "capabilities": profile_data,
        "required_read_order": [
            "AGENTS.md",
            "engineering/STATE.json",
            "engineering/MASTER_PLAN.md",
            active_manifest,
            "engineering/handoff/CURRENT.json",
            "engineering/AGENT_PROTOCOL.md",
        ],
        "business_development": state.get("business_track", {}).get("business_development"),
        "lot46_status": state.get("business_track", {}).get("next_lot", {}).get("status"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--profile",
        default="GITHUB_CONNECTOR_ONLY",
        choices=[
            "GITHUB_CONNECTOR_ONLY",
            "LOCAL_REPOSITORY",
            "CI_EXECUTION",
            "READ_ONLY_AUDITOR",
        ],
    )
    parser.add_argument("--state", type=Path, default=root / "engineering" / "STATE.json")
    parser.add_argument(
        "--capabilities",
        type=Path,
        default=root / "engineering" / "AGENT_CAPABILITIES.json",
    )
    args = parser.parse_args()

    try:
        result = resolve(_load(args.state), _load(args.capabilities), args.profile)
    except ResolveError as exc:
        print(f"NEXT_WORK_UNRESOLVED: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
