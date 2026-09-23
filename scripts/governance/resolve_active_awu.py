#!/usr/bin/env python3
"""Resolve and fully validate the single active Agent Work Unit."""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "config" / "governance" / "project_state.json"
WORK_UNITS_DIR = ROOT / "engineering" / "work_units"


class ActiveAwuError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ActiveAwuError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActiveAwuError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ActiveAwuError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_work_units(directory: Path = WORK_UNITS_DIR) -> dict[Path, dict[str, Any]]:
    if not directory.is_dir():
        raise ActiveAwuError(f"work-unit directory missing: {directory}")
    units: dict[Path, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        units[path] = _load(path)
    if not units:
        raise ActiveAwuError("no operational Agent Work Units found")
    return units


def select_active_awu(
    units: dict[Path, dict[str, Any]],
) -> tuple[Path, dict[str, Any]]:
    active = [(path, unit) for path, unit in units.items() if unit.get("status") == "IN_PROGRESS"]
    if len(active) != 1:
        raise ActiveAwuError(f"exactly one IN_PROGRESS AWU required, found {len(active)}")
    return active[0]


def _covered_by_parent(child: str, parent_patterns: list[str]) -> bool:
    return any(child == pattern or fnmatch.fnmatchcase(child, pattern) for pattern in parent_patterns)


def validate_parent_binding(
    state: dict[str, Any],
    awu_path: Path,
    awu: dict[str, Any],
) -> dict[str, Any]:
    engineering = state.get("engineering_track")
    if not isinstance(engineering, dict) or engineering.get("phase") != "BUILDING":
        raise ActiveAwuError("ENGINEERING track must be BUILDING")

    parent = awu.get("parent")
    if not isinstance(parent, dict):
        raise ActiveAwuError("AWU parent is missing")
    expected = {
        "work_item_id": engineering.get("active_lot"),
        "task_id": engineering.get("active_task"),
        "manifest": engineering.get("active_manifest"),
    }
    for key, value in expected.items():
        if parent.get(key) != value:
            raise ActiveAwuError(
                f"{awu_path}: parent {key} mismatch: {parent.get(key)!r} != {value!r}"
            )

    manifest_path = parent["manifest"]
    manifest = _load(ROOT / manifest_path)
    if manifest.get("id") != parent["work_item_id"]:
        raise ActiveAwuError("parent manifest id disagrees with permanent state")
    active_tasks = [
        task.get("id")
        for task in manifest.get("tasks", [])
        if isinstance(task, dict) and task.get("status") == "IN_PROGRESS"
    ]
    if active_tasks != [parent["task_id"]]:
        raise ActiveAwuError("parent task is not the unique IN_PROGRESS work-item task")

    parent_allowed = manifest.get("allowed_paths")
    child_allowed = awu.get("scope", {}).get("allowed_paths")
    if not isinstance(parent_allowed, list) or not isinstance(child_allowed, list):
        raise ActiveAwuError("parent/AWU allowed paths are invalid")
    escaped = [
        path for path in child_allowed
        if not _covered_by_parent(path, parent_allowed)
    ]
    if escaped:
        raise ActiveAwuError(f"AWU allowlist escapes parent work-item scope: {escaped}")
    return manifest


def validate_full_awu(
    state: dict[str, Any],
    awu_path: Path,
    awu: dict[str, Any],
) -> dict[str, Any]:
    manifest = validate_parent_binding(state, awu_path, awu)
    contract = _module("active_awu_contract", ROOT / "scripts/governance/validate_agent_work_unit.py")
    complexity = _module("active_awu_complexity", ROOT / "scripts/governance/validate_awu_complexity.py")
    split = _module("active_awu_split", ROOT / "scripts/governance/validate_awu_split.py")
    risk = _module("active_awu_risk", ROOT / "scripts/governance/validate_awu_risk.py")
    context = _module("active_awu_context", ROOT / "scripts/governance/validate_awu_context.py")
    try:
        contract.validate_awu(awu, source=str(awu_path))
        complexity.validate_complexity(
            awu, _load(ROOT / "config/governance/awu_complexity_policy_v1.json")
        )
        split.validate_split(
            awu, _load(ROOT / "config/governance/awu_split_policy_v1.json")
        )
        risk.validate_risk(
            awu, _load(ROOT / "config/governance/awu_risk_policy_v1.json")
        )
        route = context.validate_context(
            awu, awu_path.resolve(), _load(ROOT / "config/governance/awu_context_policy_v1.json")
        )
    except Exception as exc:
        expected = (
            contract.AgentWorkUnitError,
            complexity.AwuComplexityError,
            split.AwuSplitError,
            risk.AwuRiskError,
            context.AwuContextError,
        )
        if isinstance(exc, expected):
            raise ActiveAwuError(str(exc)) from exc
        raise
    if route is None:
        raise ActiveAwuError("active AWU must have an executable context route")
    return {"parent_manifest": manifest, "context_route": route}


def resolve_active_awu() -> tuple[Path, dict[str, Any], dict[str, Any]]:
    state = _load(STATE_PATH)
    path, awu = select_active_awu(load_work_units())
    evidence = validate_full_awu(state, path, awu)
    return path, awu, evidence


def main() -> int:
    try:
        path, awu, evidence = resolve_active_awu()
    except ActiveAwuError as exc:
        print(f"ACTIVE_AWU_UNRESOLVED: {exc}", file=sys.stderr)
        return 1
    route = evidence["context_route"]
    print(
        "ACTIVE_AWU_RESOLVED "
        f"id={awu['id']} path={path.relative_to(ROOT)} "
        f"task={awu['parent']['task_id']} risk={awu['planning']['risk_class']} "
        f"score={awu['planning']['complexity_score']} "
        f"context=P{route['primary_count']}:R{route['reference_count']}:K{route['total_kib_ceil']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
