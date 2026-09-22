#!/usr/bin/env python3
"""Resolve one exact work context from permanent project state."""

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


def _resolve_engineering(state: dict[str, Any]) -> tuple[str, str, str, str]:
    track = state.get("engineering_track")
    if not isinstance(track, dict):
        raise ResolveError("missing engineering_track")
    if track.get("phase") != "BUILDING":
        raise ResolveError(f"ENGINEERING track is not BUILDING: {track.get('phase')!r}")
    active_lot = track.get("active_lot")
    active_task = track.get("active_task")
    active_manifest = track.get("active_manifest")
    values = {"active_lot": active_lot, "active_task": active_task, "active_manifest": active_manifest}
    for name, value in values.items():
        if not isinstance(value, str) or not value:
            raise ResolveError(f"ENGINEERING {name} is not resolvable")
    return "DEVELOPMENT_ENGINE", active_lot, active_task, active_manifest


def _resolve_audit(state: dict[str, Any]) -> tuple[str, str, str, str]:
    track = state.get("audit_track")
    if not isinstance(track, dict):
        raise ResolveError("missing audit_track")
    if track.get("phase") != "BUILDING":
        raise ResolveError(f"AUDIT track is not BUILDING: {track.get('phase')!r}")
    active_batch = track.get("active_batch")
    active_task = track.get("active_task")
    active_manifest = track.get("active_manifest")
    values = {
        "active_batch": active_batch,
        "active_task": active_task,
        "active_manifest": active_manifest,
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value:
            raise ResolveError(f"AUDIT {name} is not resolvable")
    return "HISTORICAL_AUDIT_ENGINE", active_batch, active_task, active_manifest


def resolve(
    state: dict[str, Any],
    capabilities: dict[str, Any],
    profile: str,
    track: str = "engineering",
) -> dict[str, Any]:
    if state.get("schema_version") != 1 or state.get("state_kind") != "project_state_v1":
        raise ResolveError("state is not permanent project_state_v1")

    profiles = capabilities.get("profiles")
    if not isinstance(profiles, dict) or profile not in profiles:
        raise ResolveError(f"unknown capability profile: {profile}")

    if track == "engineering":
        track_name, active_lot, active_task, active_manifest = _resolve_engineering(state)
    elif track == "audit":
        track_name, active_lot, active_task, active_manifest = _resolve_audit(state)
    else:
        raise ResolveError(f"unknown work track: {track!r}")

    business = state.get("business_track", {})
    next_lot = business.get("next_lot") if isinstance(business, dict) else None
    findings = state.get("findings", [])

    return {
        "project": state.get("project", {}).get("canonical_name"),
        "track": track_name,
        "active_lot": active_lot,
        "active_task": active_task,
        "active_manifest": active_manifest,
        "capability_profile": profile,
        "capabilities": profiles[profile],
        "required_read_order": [
            "AGENTS.md",
            "config/governance/project_state.json",
            "engineering/MASTER_PLAN.md",
            active_manifest,
            "engineering/handoff/CURRENT.json",
            "engineering/AGENT_PROTOCOL.md",
        ],
        "business_development": business.get("development_status") if isinstance(business, dict) else None,
        "next_business_lot_status": next_lot.get("status") if isinstance(next_lot, dict) else None,
        "stop_conditions": state.get("stop_conditions", []),
        "finding_ids": [
            item.get("id") for item in findings
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ],
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
    parser.add_argument("--track", default="engineering", choices=["engineering", "audit"])
    parser.add_argument(
        "--state",
        type=Path,
        default=root / "config" / "governance" / "project_state.json",
    )
    parser.add_argument(
        "--capabilities",
        type=Path,
        default=root / "engineering" / "AGENT_CAPABILITIES.json",
    )
    args = parser.parse_args()

    try:
        result = resolve(_load(args.state), _load(args.capabilities), args.profile, args.track)
    except ResolveError as exc:
        print(f"NEXT_WORK_UNRESOLVED: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
