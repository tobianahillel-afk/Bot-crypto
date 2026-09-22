#!/usr/bin/env python3
"""Cheap fail-closed validator for the Bootstrap Engineering Engine state.

This script intentionally uses only the Python 3.11 standard library.
It validates the canonical bootstrap state and its active work-item manifest.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
WORK_ID_RE = re.compile(r"^BOOT-\d{2}$")
TASK_ID_RE = re.compile(r"^(BOOT-\d{2})\.(\d+)$")
ALLOWED_TASK_STATUSES = {"PLANNED", "IN_PROGRESS", "BLOCKED", "DONE"}


class BootstrapStateError(ValueError):
    """Raised when bootstrap state violates a mandatory invariant."""


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
    state: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    engine = _require(state, "bootstrap_engine", "state")
    active_lot = _require(engine, "active_lot", "bootstrap_engine")
    active_task = _require(engine, "active_task", "bootstrap_engine")

    if manifest.get("schema_version") != 1:
        raise BootstrapStateError("unsupported active manifest schema_version")
    if manifest.get("kind") != "bootstrap_work_item":
        raise BootstrapStateError("active manifest kind must be bootstrap_work_item")
    if manifest.get("id") != active_lot:
        raise BootstrapStateError(
            f"active manifest id {manifest.get('id')!r} does not match active_lot {active_lot!r}"
        )
    if not WORK_ID_RE.fullmatch(str(active_lot)):
        raise BootstrapStateError(f"invalid active_lot id: {active_lot!r}")
    if manifest.get("status") != "IN_PROGRESS":
        raise BootstrapStateError("active manifest must be IN_PROGRESS while bootstrap is BUILDING")

    dependencies = manifest.get("depends_on")
    if not isinstance(dependencies, list) or any(not isinstance(item, str) for item in dependencies):
        raise BootstrapStateError("active manifest depends_on must be a list of work-item ids")
    completed_lots = engine.get("completed", [])
    missing_dependencies = [item for item in dependencies if item not in completed_lots]
    if missing_dependencies:
        raise BootstrapStateError(
            f"active manifest dependencies are not completed: {missing_dependencies}"
        )

    allowed_paths = manifest.get("allowed_paths")
    if not isinstance(allowed_paths, list) or not allowed_paths:
        raise BootstrapStateError("active manifest must declare at least one allowed path")

    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise BootstrapStateError("active manifest must declare tasks")

    task_ids: list[str] = []
    in_progress: list[str] = []
    seen_planned_or_active = False
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise BootstrapStateError(f"task at index {index} must be an object")
        task_id = task.get("id")
        status = task.get("status")
        match = TASK_ID_RE.fullmatch(str(task_id))
        if match is None or match.group(1) != active_lot:
            raise BootstrapStateError(f"task id {task_id!r} does not belong to {active_lot}")
        if task_id in task_ids:
            raise BootstrapStateError(f"duplicate task id: {task_id}")
        task_ids.append(task_id)

        if status not in ALLOWED_TASK_STATUSES:
            raise BootstrapStateError(f"invalid status {status!r} for {task_id}")
        if status == "IN_PROGRESS":
            in_progress.append(task_id)

        if status == "DONE":
            if seen_planned_or_active:
                raise BootstrapStateError(
                    f"DONE task {task_id} appears after unfinished work; task order is inconsistent"
                )
        else:
            seen_planned_or_active = True

    if in_progress != [active_task]:
        raise BootstrapStateError(
            f"exactly active_task must be IN_PROGRESS: expected {[active_task]}, got {in_progress}"
        )

    if active_task not in task_ids:
        raise BootstrapStateError(f"active_task {active_task!r} is absent from active manifest")


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
        raise BootstrapStateError("default branch must remain main during bootstrap")
    if not SHA40_RE.fullmatch(str(baseline.get("main_sha", ""))):
        raise BootstrapStateError("observed main_sha must be a 40-character lowercase SHA")

    engine = _require(state, "bootstrap_engine", "state")
    phase = engine.get("phase")
    phase_transitions = policy.get("phase_transitions", {})
    if phase not in phase_transitions:
        raise BootstrapStateError(f"unknown bootstrap phase: {phase!r}")

    order = policy.get("bootstrap_order")
    if not isinstance(order, list) or not order:
        raise BootstrapStateError("transition policy bootstrap_order is invalid")

    completed = engine.get("completed")
    if not isinstance(completed, list) or len(completed) != len(set(completed)):
        raise BootstrapStateError("completed must be a unique list")

    active = engine.get("active_lot")
    if phase == "BUILDING":
        if active not in order:
            raise BootstrapStateError("BUILDING requires one valid active_lot")
        active_index = order.index(active)
        expected_completed = order[:active_index]
        if completed != expected_completed:
            raise BootstrapStateError(
                f"completed lots must be the strict prefix before {active}: "
                f"expected {expected_completed}, got {completed}"
            )
        expected_next = order[active_index + 1] if active_index + 1 < len(order) else None
        if engine.get("next_lot") != expected_next:
            raise BootstrapStateError(
                f"next_lot mismatch: expected {expected_next!r}, got {engine.get('next_lot')!r}"
            )
        active_task = engine.get("active_task")
        if not isinstance(active_task, str) or not active_task.startswith(f"{active}."):
            raise BootstrapStateError("active_task must belong to active_lot")

    business = _require(state, "business_track", "state")
    if phase == "BUILDING":
        if business.get("business_development") != "PAUSED":
            raise BootstrapStateError("business development must remain PAUSED while BUILDING")
        next_lot = business.get("next_lot")
        if not isinstance(next_lot, dict) or next_lot.get("lot") != 46:
            raise BootstrapStateError("business next_lot must remain Lot46 during bootstrap")
        if next_lot.get("status") != "LOCKED":
            raise BootstrapStateError("Lot46 must remain LOCKED while BUILDING")

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

    required_stops = {
        "STATE_DRIFT",
        "BUSINESS_SCOPE_TOUCHED_WITHOUT_UNLOCK",
        "FROZEN_EVIDENCE_MUTATION",
        "LOT46_UNLOCK_ATTEMPT",
        "MANDATORY_PAID_DEPENDENCY_INTRODUCED",
    }
    stops = set(state.get("stop_conditions", []))
    missing = sorted(required_stops - stops)
    if missing:
        raise BootstrapStateError(f"missing mandatory stop conditions: {missing}")

    _validate_active_manifest(state, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--state",
        type=Path,
        default=root / "engineering" / "STATE.json",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=root / "engineering" / "STATE_TRANSITIONS.json",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Override active manifest path; defaults to bootstrap_engine.active_manifest.",
    )
    args = parser.parse_args()

    try:
        state = _load_json(args.state)
        policy = _load_json(args.policy)
        engine = _require(state, "bootstrap_engine", "state")
        manifest_path = args.manifest
        if manifest_path is None:
            declared_manifest = _require(engine, "active_manifest", "bootstrap_engine")
            if not isinstance(declared_manifest, str):
                raise BootstrapStateError("bootstrap_engine.active_manifest must be a path")
            manifest_path = root / declared_manifest
        manifest = _load_json(manifest_path)
        validate_state(state, policy, manifest)
    except BootstrapStateError as exc:
        print(f"BOOTSTRAP_STATE_INVALID: {exc}", file=sys.stderr)
        return 1

    print("BOOTSTRAP_STATE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
