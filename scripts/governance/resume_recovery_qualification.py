#!/usr/bin/env python3
"""Qualify deterministic resume/recovery after interruption or context loss."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_MISSING = object()
MAX_RECOVERY_MS = 1000.0
WRITE_GATE = "LIVE_GIT_REVERIFY_REQUIRED"
NON_AUTHORITATIVE = {"engineering/STATE.json", "chat_history", "model_memory"}


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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResumeRecoveryError(message)


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
    authority = context.get("authority")
    awu = resolved.get("active_awu")
    if not all(isinstance(item, dict) for item in (active, execution, authority, awu)):
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
    for field in ("primary_files", "reference_files", "primary_count", "reference_count", "total_kib_ceil"):
        if execution.get(field) != route.get(field):
            return "STALE"
    if execution.get("budget") != route.get("budget"):
        return "STALE"
    if execution.get("implicit_expansion") != "FORBIDDEN":
        return "STALE"
    if authority.get("current_state") != "config/governance/project_state.json":
        return "STALE"
    if authority.get("resume_hint_is_authoritative") is not False:
        return "STALE"
    return "VALID"


def _validate_recovered_route(awu: dict[str, Any], read_order: list[str]) -> dict[str, Any]:
    route = awu.get("context_route")
    if not isinstance(route, dict):
        raise ResumeRecoveryError("resolved AWU context route missing")
    primary = route.get("primary_files")
    reference = route.get("reference_files")
    budget = route.get("budget")
    if not isinstance(primary, list) or not isinstance(reference, list) or not isinstance(budget, dict):
        raise ResumeRecoveryError("resolved AWU context route malformed")
    expected = primary + reference
    if read_order != expected:
        raise ResumeRecoveryError("recovered read order is not the exact bounded AWU route")
    if route.get("primary_count") != len(primary):
        raise ResumeRecoveryError("recovered primary route count drift")
    if route.get("reference_count") != len(reference):
        raise ResumeRecoveryError("recovered reference route count drift")
    if len(primary) > budget.get("max_primary_files", -1):
        raise ResumeRecoveryError("recovered primary route exceeds budget")
    if len(reference) > budget.get("max_reference_files", -1):
        raise ResumeRecoveryError("recovered reference route exceeds budget")
    total_kib = route.get("total_kib_ceil")
    if not isinstance(total_kib, int) or total_kib > budget.get("max_total_kib", -1):
        raise ResumeRecoveryError("recovered route exceeds byte budget")
    if set(primary) & set(reference):
        raise ResumeRecoveryError("recovered primary/reference routes overlap")
    if any(item in NON_AUTHORITATIVE for item in read_order):
        raise ResumeRecoveryError("non-authoritative source entered recovered read order")
    return {
        "primary_count": len(primary),
        "reference_count": len(reference),
        "total_kib_ceil": total_kib,
        "budget": budget,
    }


def _validate_safety(state: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    business = state.get("business_track")
    safety = state.get("safety")
    if not isinstance(business, dict) or not isinstance(safety, dict):
        raise ResumeRecoveryError("business/safety state missing")
    next_lot = business.get("next_lot")
    if not isinstance(next_lot, dict):
        raise ResumeRecoveryError("next business lot state missing")

    _require(resolved.get("business_development") == "PAUSED", "business development hold lifted")
    _require(resolved.get("next_business_lot_status") == "LOCKED", "Lot46 lock lifted")
    _require(business.get("development_status") == "PAUSED", "canonical business hold lifted")
    _require(next_lot.get("lot") == 46 and next_lot.get("status") == "LOCKED", "Lot46 state drift")
    _require(safety.get("trade_allowed") is False, "trading unexpectedly enabled")
    _require(safety.get("execution_allowed") is False, "execution unexpectedly enabled")
    _require(safety.get("live_execution") == "DISABLED", "live execution unexpectedly enabled")
    _require(safety.get("leverage") == "FORBIDDEN", "leverage unexpectedly enabled")
    _require(safety.get("withdrawals") == "FORBIDDEN", "withdrawals unexpectedly enabled")
    return {
        "business_development": "PAUSED",
        "next_business_lot": 46,
        "next_business_lot_status": "LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "withdrawals": "FORBIDDEN",
    }


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

    route_metrics = _validate_recovered_route(awu, read_order)
    safety_snapshot = _validate_safety(state, resolved)
    reconciliation = handoff_status != "VALID" or context_status != "VALID"

    return {
        "recovery_version": 2,
        "authority": "config/governance/project_state.json",
        "active_lot": resolved["active_lot"],
        "active_task": resolved["active_task"],
        "active_manifest": resolved["active_manifest"],
        "active_awu_id": awu["id"],
        "active_awu_path": awu["path"],
        "handoff_status": handoff_status,
        "context_map_status": context_status,
        "hints_authoritative": False,
        "reconciliation_required": reconciliation,
        "recovered_read_order": read_order,
        "route_metrics": route_metrics,
        "conversational_context_required": False,
        "state_auto_healed": False,
        "write_authorized": False,
        "live_git_reverify_satisfied": False,
        "required_before_write": [WRITE_GATE],
        "safety_snapshot": safety_snapshot,
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
    started = time.perf_counter()
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

    scenarios = 0
    normal = repository_recover()
    scenarios += 1
    assert normal["recovery_version"] == 2
    assert normal["handoff_status"] == "VALID"
    assert normal["context_map_status"] == "VALID"
    assert normal["active_awu_id"] == "ENG-08.6-WU01"
    assert normal["active_task"] == "ENG-08.6"
    assert normal["write_authorized"] is False
    assert normal["live_git_reverify_satisfied"] is False
    assert normal["required_before_write"] == [WRITE_GATE]
    assert normal["conversational_context_required"] is False
    assert normal["state_auto_healed"] is False
    assert normal["hints_authoritative"] is False
    assert normal["safety_snapshot"]["business_development"] == "PAUSED"
    assert normal["safety_snapshot"]["next_business_lot_status"] == "LOCKED"
    assert normal["safety_snapshot"]["trade_allowed"] is False
    assert normal["safety_snapshot"]["execution_allowed"] is False

    stale_handoff = copy.deepcopy(handoff)
    stale_handoff["next_engineering"]["active_task"] = "ENG-99.99"
    recovered_stale = repository_recover(handoff_override=stale_handoff)
    scenarios += 1
    assert recovered_stale["handoff_status"] == "STALE"
    assert recovered_stale["active_awu_id"] == normal["active_awu_id"]
    assert recovered_stale["reconciliation_required"] is True

    missing_handoff = repository_recover(handoff_override=None)
    scenarios += 1
    assert missing_handoff["handoff_status"] == "MISSING"
    assert missing_handoff["active_awu_id"] == normal["active_awu_id"]
    assert missing_handoff["write_authorized"] is False

    stale_context = copy.deepcopy(context)
    stale_context["active_work"]["awu_id"] = "ENG-99-WU99"
    recovered_context = repository_recover(context_override=stale_context)
    scenarios += 1
    assert recovered_context["context_map_status"] == "STALE"
    assert recovered_context["active_awu_id"] == normal["active_awu_id"]
    assert recovered_context["recovered_read_order"] == normal["recovered_read_order"]

    missing_context = repository_recover(context_override=None)
    scenarios += 1
    assert missing_context["context_map_status"] == "MISSING"
    assert missing_context["active_task"] == normal["active_task"]
    assert missing_context["required_before_write"] == [WRITE_GATE]

    both_stale_handoff = copy.deepcopy(handoff)
    both_stale_handoff["state_snapshot"]["active_task"] = "ENG-00.1"
    both_stale_context = copy.deepcopy(context)
    both_stale_context["active_work"]["task"] = "ENG-00.1"
    both_stale = repository_recover(
        handoff_override=both_stale_handoff,
        context_override=both_stale_context,
    )
    scenarios += 1
    assert both_stale["handoff_status"] == "STALE"
    assert both_stale["context_map_status"] == "STALE"
    assert both_stale["active_task"] == "ENG-08.6"
    assert both_stale["active_awu_id"] == "ENG-08.6-WU01"

    both_missing = repository_recover(handoff_override=None, context_override=None)
    scenarios += 1
    assert both_missing["handoff_status"] == "MISSING"
    assert both_missing["context_map_status"] == "MISSING"
    assert both_missing["active_task"] == "ENG-08.6"
    assert both_missing["state_auto_healed"] is False

    stale_safety = copy.deepcopy(handoff)
    stale_safety["state_snapshot"]["trade_allowed"] = True
    recovered_safety = repository_recover(handoff_override=stale_safety)
    scenarios += 1
    assert recovered_safety["handoff_status"] == "STALE"
    assert recovered_safety["safety_snapshot"]["trade_allowed"] is False

    expanded_context = copy.deepcopy(context)
    expanded_context["execution_context"]["implicit_expansion"] = "ALLOWED"
    recovered_expanded = repository_recover(context_override=expanded_context)
    scenarios += 1
    assert recovered_expanded["context_map_status"] == "STALE"
    assert recovered_expanded["route_metrics"] == normal["route_metrics"]

    authoritative_hint = copy.deepcopy(context)
    authoritative_hint["authority"]["resume_hint_is_authoritative"] = True
    recovered_hint = repository_recover(context_override=authoritative_hint)
    scenarios += 1
    assert recovered_hint["context_map_status"] == "STALE"
    assert recovered_hint["hints_authoritative"] is False

    unsafe = copy.deepcopy(state)
    unsafe["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(unsafe, policy),
        "Lot46 unlock",
    )
    scenarios += 1

    paid = copy.deepcopy(state)
    paid["cost_policy"]["paid_llm_required"] = True
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(paid, policy),
        "mandatory paid LLM",
    )
    scenarios += 1

    units = active.load_work_units()
    _path, current = active.select_active_awu(units)
    duplicate = dict(units)
    second = copy.deepcopy(current)
    second["id"] = f"{current['parent']['task_id']}-WU99"
    duplicate[ROOT / "engineering/work_units/resume-duplicate.json"] = second
    _expect(
        active.ActiveAwuError,
        lambda: active.select_active_awu(duplicate),
        "ambiguous active AWU",
    )
    scenarios += 1

    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    _require(elapsed_ms < MAX_RECOVERY_MS, f"recovery budget exceeded: {elapsed_ms} ms")
    result = {
        "verdict": "INTERRUPTION_RECOVERY_PASS",
        "awu": normal["active_awu_id"],
        "task": normal["active_task"],
        "authority": normal["authority"],
        "handoff_status": normal["handoff_status"],
        "context_map_status": normal["context_map_status"],
        "required_before_write": WRITE_GATE,
        "write_authorized": normal["write_authorized"],
        "primary_count": normal["route_metrics"]["primary_count"],
        "reference_count": normal["route_metrics"]["reference_count"],
        "total_kib_ceil": normal["route_metrics"]["total_kib_ceil"],
        "elapsed_ms": elapsed_ms,
        "budget_ms": MAX_RECOVERY_MS,
        "scenarios": scenarios,
        "business_development": normal["business_development"],
        "next_business_lot_status": normal["next_business_lot_status"],
        "trade_allowed": normal["safety_snapshot"]["trade_allowed"],
        "execution_allowed": normal["safety_snapshot"]["execution_allowed"],
        "live_execution": normal["safety_snapshot"]["live_execution"],
        "state_auto_healed": normal["state_auto_healed"],
        "conversational_context_required": normal["conversational_context_required"],
    }
    print(
        "INTERRUPTION_RECOVERY_PASS "
        + json.dumps(result, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
