#!/usr/bin/env python3
"""Resolve one exact work context across engineering, terminal business, or explicit audit work."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


class ResolveError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResolveError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ResolveError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ResolveError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _resolve_engineering(state: dict[str, Any]) -> tuple[str, str, str, str]:
    track = state.get("engineering_track")
    if not isinstance(track, dict) or track.get("phase") != "BUILDING":
        raise ResolveError("ENGINEERING track is not BUILDING")
    values = {
        "active_lot": track.get("active_lot"),
        "active_task": track.get("active_task"),
        "active_manifest": track.get("active_manifest"),
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value:
            raise ResolveError(f"ENGINEERING {name} is not resolvable")
    return (
        "DEVELOPMENT_ENGINE",
        values["active_lot"],
        values["active_task"],
        values["active_manifest"],
    )


def _resolve_business(
    state: dict[str, Any],
    awu_bundle: tuple[Path, dict[str, Any], dict[str, Any]] | None,
) -> tuple[str, str, str, str]:
    engineering = state.get("engineering_track")
    business = state.get("business_track")
    authority = state.get("authority")
    if not isinstance(engineering, dict) or engineering.get("phase") not in {"STABLE", "COMPLETE"}:
        raise ResolveError("BUSINESS route requires terminal ENGINEERING")
    if not isinstance(business, dict) or business.get("development_status") != "ACTIVE":
        raise ResolveError("BUSINESS route requires explicit ACTIVE authority")
    candidate = business.get("candidate")
    if (
        not isinstance(candidate, dict)
        or candidate.get("status") != "ACTIVE_CANDIDATE"
        or candidate.get("state") != "OPEN"
        or candidate.get("merged") is not False
    ):
        raise ResolveError("BUSINESS route requires active open unmerged Lot45 candidate")
    if business.get("next_lot") != {"lot": 46, "status": "LOCKED"}:
        raise ResolveError("BUSINESS route requires Lot46 to remain LOCKED")
    if awu_bundle is None:
        raise ResolveError("BUSINESS resolution requires the validated active AWU")
    _path, awu, evidence = awu_bundle
    if evidence.get("track") != "BUSINESS":
        raise ResolveError("validated AWU track is not BUSINESS")
    parent = awu.get("parent")
    if not isinstance(parent, dict):
        raise ResolveError("BUSINESS active AWU parent missing")
    expected_lot = f"LOT-{candidate.get('lot')}"
    manifest = authority.get("active_manifest") if isinstance(authority, dict) else None
    if parent.get("work_item_id") != expected_lot:
        raise ResolveError("BUSINESS active AWU lot disagrees with active candidate")
    if parent.get("manifest") != manifest or not isinstance(manifest, str):
        raise ResolveError("BUSINESS active AWU manifest disagrees with canonical authority")
    task = parent.get("task_id")
    if not isinstance(task, str) or not task:
        raise ResolveError("BUSINESS active task is not resolvable")
    return "BUSINESS", expected_lot, task, manifest


def _resolve_audit(state: dict[str, Any]) -> tuple[str, str, str, str]:
    track = state.get("audit_track")
    if not isinstance(track, dict) or track.get("phase") != "BUILDING":
        raise ResolveError("AUDIT track is not BUILDING")
    values = {
        "active_batch": track.get("active_batch"),
        "active_task": track.get("active_task"),
        "active_manifest": track.get("active_manifest"),
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value:
            raise ResolveError(f"AUDIT {name} is not resolvable")
    return (
        "HISTORICAL_AUDIT_ENGINE",
        values["active_batch"],
        values["active_task"],
        values["active_manifest"],
    )


def _active_awu_descriptor(
    awu_bundle: tuple[Path, dict[str, Any], dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    awu_path, awu, evidence = awu_bundle
    route = evidence.get("context_route")
    if not isinstance(route, dict):
        raise ResolveError("active AWU context route is missing")
    primary = route.get("primary_files")
    reference = route.get("reference_files")
    if not isinstance(primary, list) or not isinstance(reference, list):
        raise ResolveError("active AWU context route is malformed")
    active = {
        "id": awu.get("id"),
        "path": str(awu_path.relative_to(ROOT)),
        "scope_base_sha": awu.get("scope", {}).get("scope_base_sha"),
        "risk_class": awu.get("planning", {}).get("risk_class"),
        "complexity_score": awu.get("planning", {}).get("complexity_score"),
        "split_required": awu.get("planning", {}).get("split_required"),
        "context_route": route,
    }
    return active, primary + reference


def resolve(
    state: dict[str, Any],
    capabilities: dict[str, Any],
    profile: str,
    track: str = "engineering",
    awu_bundle: tuple[Path, dict[str, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if state.get("schema_version") != 1 or state.get("state_kind") != "project_state_v1":
        raise ResolveError("state is not permanent project_state_v1")

    profiles = capabilities.get("profiles")
    if not isinstance(profiles, dict) or profile not in profiles:
        raise ResolveError(f"unknown capability profile: {profile}")

    active_awu: dict[str, Any] | None = None
    if track == "engineering":
        track_name, active_lot, active_task, active_manifest = _resolve_engineering(state)
        if awu_bundle is None:
            raise ResolveError("ENGINEERING resolution requires the validated active AWU")
        if awu_bundle[2].get("track") != "ENGINEERING":
            raise ResolveError("validated AWU track is not ENGINEERING")
        active_awu, required_read_order = _active_awu_descriptor(awu_bundle)
    elif track == "business":
        track_name, active_lot, active_task, active_manifest = _resolve_business(
            state, awu_bundle
        )
        if awu_bundle is None:
            raise ResolveError("BUSINESS resolution requires the validated active AWU")
        active_awu, required_read_order = _active_awu_descriptor(awu_bundle)
    elif track == "audit":
        track_name, active_lot, active_task, active_manifest = _resolve_audit(state)
        required_read_order = [
            "AGENTS.md",
            "config/governance/project_state.json",
            active_manifest,
            "engineering/handoff/CURRENT.json",
            "engineering/AGENT_PROTOCOL.md",
        ]
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
        "active_awu": active_awu,
        "capability_profile": profile,
        "capabilities": profiles[profile],
        "required_read_order": required_read_order,
        "business_development": (
            business.get("development_status") if isinstance(business, dict) else None
        ),
        "next_business_lot_status": (
            next_lot.get("status") if isinstance(next_lot, dict) else None
        ),
        "stop_conditions": state.get("stop_conditions", []),
        "finding_ids": [
            item.get("id")
            for item in findings
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ],
    }


def repository_resolve(profile: str, track: str = "auto") -> dict[str, Any]:
    state = _load(ROOT / "config/governance/project_state.json")
    capabilities = _load(ROOT / "engineering/AGENT_CAPABILITIES.json")
    if track == "audit":
        return resolve(state, capabilities, profile, "audit", None)

    active = _module(
        "next_work_active_awu",
        ROOT / "scripts/governance/resolve_active_awu.py",
    )
    try:
        awu_bundle = active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise ResolveError(str(exc)) from exc
    validated_track = awu_bundle[2].get("track")
    selected = (
        validated_track.lower()
        if track == "auto" and isinstance(validated_track, str)
        else track
    )
    if selected not in {"engineering", "business"}:
        raise ResolveError(f"unsupported ordinary work route: {selected!r}")
    if validated_track != selected.upper():
        raise ResolveError(
            f"requested route {selected.upper()} disagrees with validated active route {validated_track}"
        )
    return resolve(state, capabilities, profile, selected, awu_bundle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument(
        "--track",
        default="auto",
        choices=["auto", "engineering", "business", "audit"],
    )
    args = parser.parse_args()
    try:
        result = repository_resolve(args.profile, args.track)
    except ResolveError as exc:
        print(f"NEXT_WORK_UNRESOLVED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
