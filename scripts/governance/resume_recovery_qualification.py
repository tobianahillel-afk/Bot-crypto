#!/usr/bin/env python3
"""Qualify deterministic resume/recovery after interruption or context loss."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_MISSING = object()


class ResumeRecoveryError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResumeRecoveryError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ResumeRecoveryError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ResumeRecoveryError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _handoff_status(
    state: dict[str, Any],
    handoff: dict[str, Any] | None,
    validator: ModuleType,
) -> str:
    if handoff is None:
        return "MISSING"
    if not isinstance(handoff, dict):
        return "STALE"
    try:
        validator.validate_handoff(state, handoff)
    except validator.HandoffError:
        return "STALE"
    return "VALID"


def _context_status(context: dict[str, Any] | None, resolved: dict[str, Any]) -> str:
    if context is None:
        return "MISSING"
    if not isinstance(context, dict):
        return "STALE"
    active = context.get("active_work")
    execution = context.get("execution_context")
    awu = resolved.get("active_awu")
    if not isinstance(active, dict) or not isinstance(execution, dict) or not isinstance(awu, dict):
        return "STALE"
    expected_active = {
        "track": "ENGINEERING",
        "lot": resolved["active_lot"],
        "task": resolved["active_task"],
        "manifest": resolved["active_manifest"],
        "awu_id": awu["id"],
        "awu_path": awu["path"],
        "risk_class": awu["risk_class"],
        "complexity_score": awu["complexity_score"],
    }
    actual_active = {
        "track": active.get("track"),
        "lot": active.get("lot"),
        "task": active.get("task"),
        "manifest": active.get("manifest"),
        "awu_id": active.get("awu_id"),
        "awu_path": active.get("awu_path"),
        "risk_class": active.get("risk_class"),
        "complexity_score": active.get("complexity_score"),
    }
    route = awu.get("context_route")
    if not isinstance(route, dict):
        raise ResumeRecoveryError("resolved AWU lacks context route")
    if actual_active != expected_active:
        return "STALE"
    if execution.get("primary_files") != route.get("primary_files"):
        return "STALE"
    if execution.get("reference_files") != route.get("reference_files"):
        return "STALE"
    if context.get("authority", {}).get("resume_hint_is_authoritative") is not False:
        return "STALE"
    return "VALID"


def recover(
    state: dict[str, Any],
    capabilities: dict[str, Any],
    awu_bundle: tuple[Path, dict[str, Any], dict[str, Any]],
    handoff: dict[str, Any] | None,
    context: dict[str, Any] | None,
    resolver: ModuleType,
    handoff_validator: ModuleType,
) -> dict[str, Any]:
    try:
        resolved = resolver.resolve(
            state,
            capabilities,
            "GITHUB_CONNECTOR_ONLY",
            "engineering",
            awu_bundle,
        )
    except resolver.ResolveError as exc:
        raise ResumeRecoveryError(str(exc)) from exc

    handoff_status = _handoff_status(state, handoff, handoff_validator)
    context_status = _context_status(context, resolved)
    awu = resolved.get("active_awu")
    if not isinstance(awu, dict):
        raise ResumeRecoveryError("engineering recovery requires active AWU")

    read_order = resolved.get("required_read_order")
    if not isinstance(read_order, list) or not read_order:
        raise ResumeRecoveryError("recovered bounded read order missing")
    if read_order[0] != "AGENTS.md":
        raise ResumeRecoveryError("recovered read order must start with AGENTS.md")
    forbidden = {"engineering/STATE.json", "chat_history", "model_memory"}
    if any(item in forbidden for item in read_order):
        raise ResumeRecoveryError("non-authoritative source entered recovered read order")

    reconciliation = handoff_status != "VALID" or context_status != "VALID"
    return {
        "recovery_version": 1,
        "authority": "config/governance/project_state.json",
        "active_lot": resolved["active_lot"],
        "active_task": resolved["active_task"],
        "active_manifest": resolved["active_manifest"],
        "active_awu_id": awu["id"],
        "active_awu_path": awu["path"],
        "handoff_status": handoff_status,
        "context_map_status": context_status,
        "reconciliation_required": reconciliation,
        "recovered_read_order": read_order,
        "conversational_context_required": False,
        "state_auto_healed": False,
        "write_authorized": False,
        "required_before_write": ["LIVE_GIT_REVERIFY_REQUIRED"],
        "business_development": resolved["business_development"],
        "next_business_lot_status": resolved["next_business_lot_status"],
        "stop_conditions": resolved["stop_conditions"],
    }


def repository_recover(
    *,
    handoff_override: object = _MISSING,
    context_override: object = _MISSING,
) -> dict[str, Any]:
    state_machine = _module(
        "resume_state_machine",
        ROOT / "scripts/governance/validate_project_state_machine.py",
    )
    resolver = _module(
        "resume_next_work",
        ROOT / "scripts/governance/resolve_next_work.py",
    )
    active = _module(
        "resume_active_awu",
        ROOT / "scripts/governance/resolve_active_awu.py",
    )
    handoff_validator = _module(
        "resume_handoff_validator",
        ROOT / "scripts/governance/validate_handoff.py",
    )

    state = _json(ROOT / "config/governance/project_state.json")
    policy = _json(ROOT / "config/governance/project_state_transitions_v1.json")
    capabilities = _json(ROOT / "engineering/AGENT_CAPABILITIES.json")
    state_machine.validate_current(state, policy)

    try:
        awu_bundle = active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise ResumeRecoveryError(str(exc)) from exc

    handoff = (
        _json(ROOT / "engineering/handoff/CURRENT.json")
        if handoff_override is _MISSING
        else handoff_override
    )
    context = (
        _json(ROOT / "engineering/CONTEXT_MAP.json")
        if context_override is _MISSING
        else context_override
    )
    if handoff is not None and not isinstance(handoff, dict):
        handoff = None
    if context is not None and not isinstance(context, dict):
        context = None

    return recover(
        state,
        capabilities,
        awu_bundle,
        handoff,
        context,
        resolver,
        handoff_validator,
    )


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"resume/recovery negative scenario unexpectedly passed: {label}")


def main() -> int:
    state_machine = _module(
        "resume_qualification_state_machine",
        ROOT / "scripts/governance/validate_project_state_machine.py",
    )
    active = _module(
        "resume_qualification_active",
        ROOT / "scripts/governance/resolve_active_awu.py",
    )
    state = _json(ROOT / "config/governance/project_state.json")
    policy = _json(ROOT / "config/governance/project_state_transitions_v1.json")
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")
    context = _json(ROOT / "engineering/CONTEXT_MAP.json")

    normal = repository_recover()
    assert normal["handoff_status"] == "VALID"
    assert normal["context_map_status"] == "VALID"
    assert normal["active_awu_id"] == "ENG-05.5-WU01"
    assert normal["write_authorized"] is False
    assert normal["required_before_write"] == ["LIVE_GIT_REVERIFY_REQUIRED"]
    assert normal["conversational_context_required"] is False

    stale_handoff = copy.deepcopy(handoff)
    stale_handoff["next_engineering"]["active_task"] = "ENG-99.99"
    recovered_stale = repository_recover(handoff_override=stale_handoff)
    assert recovered_stale["handoff_status"] == "STALE"
    assert recovered_stale["active_awu_id"] == normal["active_awu_id"]
    assert recovered_stale["reconciliation_required"] is True

    missing_handoff = repository_recover(handoff_override=None)
    assert missing_handoff["handoff_status"] == "MISSING"
    assert missing_handoff["active_awu_id"] == normal["active_awu_id"]

    stale_context = copy.deepcopy(context)
    stale_context["active_work"]["awu_id"] = "ENG-99-WU99"
    recovered_context = repository_recover(context_override=stale_context)
    assert recovered_context["context_map_status"] == "STALE"
    assert recovered_context["active_awu_id"] == normal["active_awu_id"]
    assert recovered_context["recovered_read_order"] == normal["recovered_read_order"]

    unsafe = copy.deepcopy(state)
    unsafe["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(unsafe, policy),
        "Lot46 unlock",
    )

    paid = copy.deepcopy(state)
    paid["cost_policy"]["paid_llm_required"] = True
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(paid, policy),
        "mandatory paid LLM",
    )

    units = active.load_work_units()
    _path, current = active.select_active_awu(units)
    duplicate = dict(units)
    second = copy.deepcopy(current)
    second["id"] = "ENG-05.5-WU99"
    duplicate[ROOT / "engineering/work_units/resume-duplicate.json"] = second
    _expect(
        active.ActiveAwuError,
        lambda: active.select_active_awu(duplicate),
        "ambiguous active AWU",
    )

    print(
        "RESUME_RECOVERY_PASS "
        f"awu={normal['active_awu_id']} handoff={normal['handoff_status']} "
        f"context={normal['context_map_status']} scenarios=7"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
