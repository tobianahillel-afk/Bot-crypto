#!/usr/bin/env python3
"""Validate current permanent state and the actual HEAD^ -> HEAD state transition."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = "config/governance/project_state.json"
POLICY_PATH = ROOT / "config" / "governance" / "project_state_transitions_v1.json"


class StateMachineError(ValueError):
    pass


def _load_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateMachineError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateMachineError(f"{path} must contain an object")
    return value


def _git_show_json(ref: str, path: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise StateMachineError(f"cannot read {path} at {ref}: {result.stderr.strip()}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise StateMachineError(f"invalid JSON for {path} at {ref}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateMachineError(f"{path} at {ref} must contain an object")
    return value


def _manifest_current(state: dict[str, Any]) -> dict[str, Any]:
    path = state.get("engineering_track", {}).get("active_manifest")
    if not isinstance(path, str) or not path:
        raise StateMachineError("current engineering active_manifest is missing")
    return _load_file(ROOT / path)


def _manifest_at(ref: str, state: dict[str, Any]) -> dict[str, Any]:
    path = state.get("engineering_track", {}).get("active_manifest")
    if not isinstance(path, str) or not path:
        raise StateMachineError("previous engineering active_manifest is missing")
    return _git_show_json(ref, path)


def _task_order(manifest: dict[str, Any]) -> list[str]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise StateMachineError("manifest tasks are missing")
    ids: list[str] = []
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            raise StateMachineError("manifest task id is invalid")
        ids.append(task["id"])
    if len(ids) != len(set(ids)):
        raise StateMachineError("manifest task ids are duplicated")
    return ids


def validate_current(state: dict[str, Any], policy: dict[str, Any]) -> None:
    if state.get("schema_version") != 1 or state.get("state_kind") != "project_state_v1":
        raise StateMachineError("current permanent state identity drift")

    business = state.get("business_track", {})
    engineering = state.get("engineering_track", {})
    audit = state.get("audit_track", {})
    safety = state.get("safety", {})
    cost = state.get("cost_policy", {})

    if business.get("development_status") != "PAUSED":
        raise StateMachineError("BUSINESS must remain PAUSED during engine foundation")
    if business.get("next_lot") != {"lot": 46, "status": "LOCKED"}:
        raise StateMachineError("Lot46 must remain LOCKED")
    candidate = business.get("candidate")
    if not isinstance(candidate, dict) or candidate.get("merged") is not False:
        raise StateMachineError("Lot45 candidate must remain explicitly unmerged")

    if safety.get("trade_allowed") is not False or safety.get("execution_allowed") is not False:
        raise StateMachineError("trade/execution must remain disabled")
    if safety.get("live_execution") != "DISABLED":
        raise StateMachineError("live execution must remain disabled")
    if safety.get("leverage") != "FORBIDDEN" or safety.get("withdrawals") != "FORBIDDEN":
        raise StateMachineError("leverage/withdrawals must remain forbidden")
    if any(cost.get(key) is not False for key in (
        "paid_external_api_required","paid_llm_required","paid_saas_required","paid_runner_required"
    )):
        raise StateMachineError("mandatory path must remain zero-cost")

    phase = engineering.get("phase")
    if phase not in policy.get("engineering_phase_transitions", {}):
        raise StateMachineError(f"unknown ENGINEERING phase: {phase!r}")
    if phase == "BUILDING":
        for key in ("active_lot","active_task","next_lot","active_manifest","branch"):
            if not isinstance(engineering.get(key), str) or not engineering[key]:
                raise StateMachineError(f"ENGINEERING BUILDING requires {key}")
        manifest = _manifest_current(state)
        if manifest.get("id") != engineering.get("active_lot"):
            raise StateMachineError("ENGINEERING manifest id disagrees with active_lot")
        if manifest.get("status") != "IN_PROGRESS":
            raise StateMachineError("active ENGINEERING manifest must be IN_PROGRESS")
        active_tasks = [
            task.get("id")
            for task in manifest.get("tasks", [])
            if isinstance(task, dict) and task.get("status") == "IN_PROGRESS"
        ]
        if active_tasks != [engineering.get("active_task")]:
            raise StateMachineError("ENGINEERING active_task/manfiest status mismatch")

    audit_phase = audit.get("phase")
    if audit_phase not in policy.get("audit_phase_transitions", {}):
        raise StateMachineError(f"unknown AUDIT phase: {audit_phase!r}")
    if audit_phase == "NOT_STARTED":
        if audit.get("completed") != [] or audit.get("blockers") != []:
            raise StateMachineError("AUDIT NOT_STARTED must have empty completed/blockers")
        for key in ("active_batch","active_task","next_batch","active_manifest"):
            if audit.get(key) is not None:
                raise StateMachineError(f"AUDIT NOT_STARTED requires {key}=null")


def _validate_phase_transition(previous: str, current: str, mapping: dict[str, Any], label: str) -> None:
    allowed = mapping.get(previous)
    if not isinstance(allowed, list) or current not in allowed:
        raise StateMachineError(f"illegal {label} phase transition: {previous} -> {current}")


def _validate_findings(previous: dict[str, Any], current: dict[str, Any]) -> None:
    prev = previous.get("findings", [])
    cur = current.get("findings", [])
    if not isinstance(prev, list) or not isinstance(cur, list):
        raise StateMachineError("findings must be lists")
    prev_ids = [item.get("id") for item in prev if isinstance(item, dict)]
    cur_ids = [item.get("id") for item in cur if isinstance(item, dict)]
    missing = [item for item in prev_ids if item not in cur_ids]
    if missing:
        raise StateMachineError(f"findings silently removed: {missing}")


def validate_transition(previous: dict[str, Any], current: dict[str, Any], policy: dict[str, Any]) -> None:
    if previous.get("project") != current.get("project"):
        raise StateMachineError("project identity is immutable")

    if policy.get("business_mutation_mode") == "LOCKED_DURING_ENGINE_FOUNDATION":
        if previous.get("business_track") != current.get("business_track"):
            raise StateMachineError("BUSINESS track mutated while foundation lock is active")
    if policy.get("safety_mutation_mode") == "LOCKED_FAIL_CLOSED_DURING_ENGINE_FOUNDATION":
        if previous.get("safety") != current.get("safety"):
            raise StateMachineError("safety mutated while foundation lock is active")
    if policy.get("cost_mutation_mode") == "LOCKED_ZERO_COST_DURING_ENGINE_FOUNDATION":
        if previous.get("cost_policy") != current.get("cost_policy"):
            raise StateMachineError("cost policy mutated while foundation lock is active")

    prev_eng = previous.get("engineering_track", {})
    cur_eng = current.get("engineering_track", {})
    _validate_phase_transition(
        str(prev_eng.get("phase")),
        str(cur_eng.get("phase")),
        policy.get("engineering_phase_transitions", {}),
        "ENGINEERING",
    )

    prev_completed = prev_eng.get("completed", [])
    cur_completed = cur_eng.get("completed", [])
    if not isinstance(prev_completed, list) or not isinstance(cur_completed, list):
        raise StateMachineError("ENGINEERING completed must be lists")
    if cur_completed[: len(prev_completed)] != prev_completed:
        raise StateMachineError("ENGINEERING completed is not append-only")

    prev_lot = prev_eng.get("active_lot")
    cur_lot = cur_eng.get("active_lot")
    if prev_lot == cur_lot:
        if cur_completed != prev_completed:
            raise StateMachineError("completed lots changed without active-lot transition")
        if prev_eng.get("next_lot") != cur_eng.get("next_lot"):
            raise StateMachineError("next_lot changed within the same active lot")
        if prev_eng.get("branch") != cur_eng.get("branch"):
            raise StateMachineError("engineering branch changed within active lot")
        prev_task = prev_eng.get("active_task")
        cur_task = cur_eng.get("active_task")
        if prev_task != cur_task:
            order = _task_order(_manifest_current(current))
            if prev_task not in order or cur_task not in order:
                raise StateMachineError("task transition references unknown task")
            if order.index(cur_task) != order.index(prev_task) + 1:
                raise StateMachineError(f"ENGINEERING task skip: {prev_task} -> {cur_task}")
    else:
        if cur_lot != prev_eng.get("next_lot"):
            raise StateMachineError("ENGINEERING lot may only advance to previous next_lot")
        if cur_completed != prev_completed + [prev_lot]:
            raise StateMachineError("previous active lot must be appended exactly once")
        previous_manifest = _manifest_at("HEAD^", previous)
        previous_order = _task_order(previous_manifest)
        if prev_eng.get("active_task") != previous_order[-1]:
            raise StateMachineError("previous ENGINEERING lot was not on its final task")
        current_order = _task_order(_manifest_current(current))
        if cur_eng.get("active_task") != current_order[0]:
            raise StateMachineError("new ENGINEERING lot must start on its first task")

    prev_audit = previous.get("audit_track", {})
    cur_audit = current.get("audit_track", {})
    _validate_phase_transition(
        str(prev_audit.get("phase")),
        str(cur_audit.get("phase")),
        policy.get("audit_phase_transitions", {}),
        "AUDIT",
    )

    _validate_findings(previous, current)

    freshness = current.get("freshness_policy", {})
    if freshness.get("auto_heal_state_from_external_git") is not False:
        raise StateMachineError("external Git drift must never auto-heal")


def main() -> int:
    try:
        policy = _load_file(POLICY_PATH)
        current = _load_file(ROOT / STATE_PATH)
        previous = _git_show_json("HEAD^", STATE_PATH)
        validate_current(current, policy)
        validate_transition(previous, current, policy)
    except StateMachineError as exc:
        print(f"PROJECT_STATE_MACHINE_INVALID: {exc}", file=sys.stderr)
        return 1
    print("PROJECT_STATE_MACHINE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
