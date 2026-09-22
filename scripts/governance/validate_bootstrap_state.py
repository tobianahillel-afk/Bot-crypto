#!/usr/bin/env python3
"""Cheap fail-closed validator for Bootstrap and permanent-engine entry state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
WORK_ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]*(?:[.-][A-Z0-9_-]+)*$")
ALLOWED_TASK_STATUSES = {"PLANNED", "IN_PROGRESS", "BLOCKED", "DONE"}


class BootstrapStateError(ValueError):
    """Raised when governance state violates a mandatory invariant."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapStateError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BootstrapStateError(f"{path} must contain a JSON object")
    return data


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise BootstrapStateError(f"missing {where}.{key}")
    return mapping[key]


def _require_false(mapping: dict[str, Any], key: str, where: str) -> None:
    if _require(mapping, key, where) is not False:
        raise BootstrapStateError(f"{where}.{key} must be false")


def _validate_active_manifest(
    engine: dict[str, Any],
    manifest: dict[str, Any],
    *,
    completed_bootstrap: list[str],
) -> None:
    active_lot = _require(engine, "active_lot", "active_engine")
    active_task = _require(engine, "active_task", "active_engine")

    if manifest.get("schema_version") != 1:
        raise BootstrapStateError("unsupported active manifest schema_version")
    if manifest.get("id") != active_lot:
        raise BootstrapStateError("active manifest id does not match active_lot")
    if WORK_ID_RE.fullmatch(str(active_lot)) is None:
        raise BootstrapStateError("invalid active_lot id")
    if manifest.get("status") != "IN_PROGRESS":
        raise BootstrapStateError("active manifest must be IN_PROGRESS")

    dependencies = manifest.get("depends_on")
    if not isinstance(dependencies, list) or any(not isinstance(item, str) for item in dependencies):
        raise BootstrapStateError("active manifest depends_on must be a list")
    completed_engine = engine.get("completed", [])
    missing_dependencies = [
        item
        for item in dependencies
        if item not in completed_engine and item not in completed_bootstrap
    ]
    if missing_dependencies:
        raise BootstrapStateError("active manifest has incomplete dependencies")

    allowed_paths = manifest.get("allowed_paths")
    if not isinstance(allowed_paths, list) or not allowed_paths:
        raise BootstrapStateError("active manifest must declare allowed_paths")

    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise BootstrapStateError("active manifest must declare tasks")

    in_progress: list[str] = []
    seen_unfinished = False
    seen_ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise BootstrapStateError("task must be an object")
        task_id = task.get("id")
        status = task.get("status")
        if not isinstance(task_id, str) or not task_id.startswith(f"{active_lot}."):
            raise BootstrapStateError("task does not belong to active lot")
        if task_id in seen_ids:
            raise BootstrapStateError("duplicate task id")
        seen_ids.add(task_id)
        if status not in ALLOWED_TASK_STATUSES:
            raise BootstrapStateError("invalid task status")
        if status == "IN_PROGRESS":
            in_progress.append(task_id)
        if status == "DONE":
            if seen_unfinished:
                raise BootstrapStateError("DONE task appears after unfinished work")
        else:
            seen_unfinished = True

    if in_progress != [active_task]:
        raise BootstrapStateError("exactly active_task must be IN_PROGRESS")


def validate_state(
    state: dict[str, Any],
    policy: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    if state.get("schema_version") != 1:
        raise BootstrapStateError("unsupported state schema_version")
    if state.get("state_kind") != "bootstrap_engine_state":
        raise BootstrapStateError("invalid state_kind")

    project = _require(state, "project", "state")
    if project.get("canonical_name") != "Crypto Quant Bot V3.1-Ops":
        raise BootstrapStateError("canonical project identity drift")
    if project.get("repository") != "tobianahillel-afk/Bot-crypto":
        raise BootstrapStateError("repository identity drift")

    baseline = _require(state, "observed_git_baseline", "state")
    if baseline.get("default_branch") != "main":
        raise BootstrapStateError("default branch must remain main")
    if SHA40_RE.fullmatch(str(baseline.get("main_sha", ""))) is None:
        raise BootstrapStateError("observed main_sha must be a lowercase SHA-40")

    bootstrap = _require(state, "bootstrap_engine", "state")
    phase = bootstrap.get("phase")
    order = policy.get("bootstrap_order")
    if not isinstance(order, list) or not order:
        raise BootstrapStateError("transition policy bootstrap_order is invalid")
    completed_bootstrap = bootstrap.get("completed")
    if not isinstance(completed_bootstrap, list) or len(completed_bootstrap) != len(set(completed_bootstrap)):
        raise BootstrapStateError("bootstrap completed must be a unique list")

    if phase == "BUILDING":
        active = bootstrap.get("active_lot")
        if active not in order:
            raise BootstrapStateError("BUILDING requires one valid bootstrap active_lot")
        index = order.index(active)
        if completed_bootstrap != order[:index]:
            raise BootstrapStateError("bootstrap completed lots must be the strict prefix")
        expected_next = order[index + 1] if index + 1 < len(order) else None
        if bootstrap.get("next_lot") != expected_next:
            raise BootstrapStateError("bootstrap next_lot is inconsistent")
        _validate_active_manifest(bootstrap, manifest, completed_bootstrap=completed_bootstrap)
    elif phase == "STABLE":
        if completed_bootstrap != order:
            raise BootstrapStateError("STABLE bootstrap requires every BOOT lot completed")
        for field in ("active_lot", "active_task", "active_manifest", "next_lot"):
            if bootstrap.get(field) is not None:
                raise BootstrapStateError(f"STABLE bootstrap requires {field}=null")
        engineering = _require(state, "engineering_engine", "state")
        if engineering.get("phase") != "BUILDING":
            raise BootstrapStateError("STABLE bootstrap must hand off to BUILDING engineering_engine")
        active = engineering.get("active_lot")
        task = engineering.get("active_task")
        if not isinstance(active, str) or not active.startswith("ENG-"):
            raise BootstrapStateError("engineering_engine active_lot must be ENG-*")
        if not isinstance(task, str) or not task.startswith(f"{active}."):
            raise BootstrapStateError("engineering_engine active_task must belong to active_lot")
        _validate_active_manifest(engineering, manifest, completed_bootstrap=completed_bootstrap)
    else:
        raise BootstrapStateError("unknown bootstrap phase")

    business = _require(state, "business_track", "state")
    if business.get("business_development") != "PAUSED":
        raise BootstrapStateError("business development must remain PAUSED during engine construction")
    next_lot = business.get("next_lot")
    if not isinstance(next_lot, dict) or next_lot.get("lot") != 46 or next_lot.get("status") != "LOCKED":
        raise BootstrapStateError("Lot46 must remain LOCKED during engine construction")

    safety = _require(state, "safety", "state")
    _require_false(safety, "trade_allowed", "safety")
    _require_false(safety, "execution_allowed", "safety")
    if safety.get("live_execution") != "DISABLED":
        raise BootstrapStateError("live_execution must remain DISABLED")
    if safety.get("leverage") != "FORBIDDEN":
        raise BootstrapStateError("leverage must remain FORBIDDEN")
    if safety.get("withdrawals") != "FORBIDDEN":
        raise BootstrapStateError("withdrawals must remain FORBIDDEN")

    cost = _require(state, "mandatory_cost_policy", "state")
    for key in (
        "paid_external_api_required",
        "paid_llm_required",
        "paid_saas_required",
        "paid_runner_required",
    ):
        _require_false(cost, key, "mandatory_cost_policy")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--state", type=Path, default=root / "engineering" / "STATE.json")
    parser.add_argument("--policy", type=Path, default=root / "engineering" / "STATE_TRANSITIONS.json")
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    try:
        state = _load_json(args.state)
        policy = _load_json(args.policy)
        phase = state.get("bootstrap_engine", {}).get("phase")
        active_engine = (
            state.get("bootstrap_engine", {})
            if phase == "BUILDING"
            else state.get("engineering_engine", {})
        )
        manifest_path = args.manifest
        if manifest_path is None:
            declared = _require(active_engine, "active_manifest", "active_engine")
            if not isinstance(declared, str):
                raise BootstrapStateError("active_manifest must be a path")
            manifest_path = root / declared
        validate_state(state, policy, _load_json(manifest_path))
    except BootstrapStateError as exc:
        print(f"BOOTSTRAP_STATE_INVALID: {exc}", file=sys.stderr)
        return 1

    print("BOOTSTRAP_STATE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
