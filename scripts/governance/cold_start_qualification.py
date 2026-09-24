#!/usr/bin/env python3
"""Qualify bounded context-free cold start from permanent repository authority."""

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
MAX_COLD_START_MS = 1000.0
NON_AUTHORITATIVE = ["engineering/STATE.json", "chat_history", "model_memory"]


class ColdStartError(ValueError):
    pass


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ColdStartError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ColdStartError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ColdStartError(f"{path} must contain an object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ColdStartError(message)


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"cold-start negative scenario unexpectedly passed: {label}")


def validate_context_free_contract(
    state: dict[str, Any],
    resolved: dict[str, Any],
    context: dict[str, Any],
    awu: dict[str, Any],
) -> None:
    _require(
        state.get("project", {}).get("canonical_name") == "Crypto Quant Bot V3.1-Ops",
        "canonical project identity drift",
    )
    _require(resolved.get("project") == "Crypto Quant Bot V3.1-Ops", "resolved project drift")
    _require(resolved.get("track") == "DEVELOPMENT_ENGINE", "cold start must resolve engineering")
    engineering = state.get("engineering_track")
    _require(isinstance(engineering, dict), "engineering state missing")
    _require(resolved.get("active_lot") == engineering.get("active_lot"), "cold-start active lot drift")
    _require(resolved.get("active_task") == engineering.get("active_task"), "cold-start active task drift")
    _require(
        resolved.get("active_manifest") == engineering.get("active_manifest"),
        "cold-start manifest drift",
    )

    active = resolved.get("active_awu")
    _require(isinstance(active, dict), "cold-start active AWU missing")
    _require(active.get("id") == awu.get("id"), "cold-start active AWU drift")
    _require(active.get("split_required") is False, "cold-start AWU unexpectedly requires split")
    route = active.get("context_route")
    _require(isinstance(route, dict), "cold-start context route missing")

    primary = route.get("primary_files")
    reference = route.get("reference_files")
    _require(isinstance(primary, list) and isinstance(reference, list), "cold-start route invalid")
    _require(route.get("primary_count") == len(primary), "primary count drift")
    _require(route.get("reference_count") == len(reference), "reference count drift")
    _require(len(primary) == len(set(primary)), "primary route contains duplicates")
    _require(len(reference) == len(set(reference)), "reference route contains duplicates")
    _require(not (set(primary) & set(reference)), "primary/reference route overlap")
    _require(
        primary[:2] == ["AGENTS.md", "config/governance/project_state.json"],
        "authority prefix drift",
    )
    active_manifest = engineering.get("active_manifest")
    active_awu_path = active.get("path")
    _require(
        active_manifest in primary and active_awu_path in primary,
        "active manifest/AWU absent from primary route",
    )

    expected_read_order = primary + reference
    _require(resolved.get("required_read_order") == expected_read_order, "read order is not AWU route")
    _require(expected_read_order[0] == "AGENTS.md", "cold-start read order must start at AGENTS.md")
    for source in NON_AUTHORITATIVE:
        _require(source not in expected_read_order, f"non-authoritative source entered read order: {source}")

    budget = awu.get("planning", {}).get("context_budget")
    _require(isinstance(budget, dict), "active AWU context budget missing")
    for field in ("max_primary_files", "max_reference_files", "max_total_kib"):
        _require(isinstance(budget.get(field), int) and budget[field] > 0, f"invalid context budget: {field}")
    _require(len(primary) <= budget["max_primary_files"], "primary context budget exceeded")
    _require(len(reference) <= budget["max_reference_files"], "reference context budget exceeded")
    total_kib = route.get("total_kib_ceil")
    _require(
        isinstance(total_kib, int) and total_kib <= budget["max_total_kib"],
        "byte budget exceeded",
    )

    _require(
        context.get("bootstrap_read_order")
        == ["AGENTS.md", "config/governance/project_state.json", "engineering/CONTEXT_MAP.json"],
        "bootstrap read order drift",
    )
    _require(
        context.get("non_authoritative_sources") == NON_AUTHORITATIVE,
        "authority declaration drift",
    )
    _require(
        context.get("authority")
        == {
            "current_state": "config/governance/project_state.json",
            "resume_hint": "engineering/handoff/CURRENT.json",
            "resume_hint_is_authoritative": False,
        },
        "context authority declaration drift",
    )

    context_active = context.get("active_work")
    _require(isinstance(context_active, dict), "context active work missing")
    _require(context_active.get("lot") == resolved["active_lot"], "context active lot stale")
    _require(context_active.get("task") == resolved["active_task"], "context active task stale")
    _require(context_active.get("awu_id") == active["id"], "context active AWU stale")
    _require(context_active.get("awu_path") == active["path"], "context active AWU path stale")
    _require(context_active.get("risk_class") == active["risk_class"], "context risk class stale")
    _require(
        context_active.get("complexity_score") == active["complexity_score"],
        "context complexity score stale",
    )

    execution = context.get("execution_context")
    _require(isinstance(execution, dict), "generated execution context missing")
    _require(execution.get("primary_files") == primary, "context primary route stale")
    _require(execution.get("reference_files") == reference, "context reference route stale")
    _require(execution.get("primary_count") == len(primary), "context primary count stale")
    _require(execution.get("reference_count") == len(reference), "context reference count stale")
    _require(execution.get("total_kib_ceil") == total_kib, "context byte count stale")
    _require(execution.get("budget") == budget, "context budget stale")
    _require(execution.get("implicit_expansion") == "FORBIDDEN", "implicit expansion enabled")

    profile = resolved.get("capabilities")
    _require(isinstance(profile, dict), "resolved capability profile missing")
    _require(resolved.get("capability_profile") == "GITHUB_CONNECTOR_ONLY", "capability profile drift")
    _require(profile.get("local_execution") is False, "GitHub-only agent claimed local execution")
    _require(profile.get("ci_execution") is False, "GitHub-only agent claimed direct CI execution")
    _require(
        profile.get("may_claim_local_test_pass") is False,
        "GitHub-only agent may claim local PASS",
    )

    business = state.get("business_track", {})
    safety = state.get("safety", {})
    _require(business.get("development_status") == "PAUSED", "business development hold lifted")
    _require(business.get("next_lot", {}).get("status") == "LOCKED", "Lot46 is not locked")
    _require(safety.get("trade_allowed") is False, "trading unexpectedly enabled")
    _require(safety.get("execution_allowed") is False, "execution unexpectedly enabled")
    _require(safety.get("live_execution") == "DISABLED", "live execution unexpectedly enabled")

    _require(
        context.get("business_hold", {}).get("development_status") == "PAUSED",
        "context business hold drift",
    )
    _require(
        context.get("business_hold", {}).get("next_lot", {}).get("status") == "LOCKED",
        "context Lot46 lock drift",
    )
    _require(
        context.get("safety", {}).get("trade_allowed") is False,
        "context trade safety drift",
    )
    _require(
        context.get("safety", {}).get("execution_allowed") is False,
        "context execution safety drift",
    )


def main() -> int:
    started = time.perf_counter()

    state_machine = _module(
        "cold_permanent_state_machine",
        ROOT / "scripts/governance/validate_project_state_machine.py",
    )
    handoff_validator = _module(
        "cold_handoff_validator",
        ROOT / "scripts/governance/validate_handoff.py",
    )
    resolver = _module(
        "cold_permanent_resolver",
        ROOT / "scripts/governance/resolve_next_work.py",
    )
    active_awu = _module(
        "cold_active_awu_resolver",
        ROOT / "scripts/governance/resolve_active_awu.py",
    )

    state = _json(ROOT / "config/governance/project_state.json")
    policy = _json(ROOT / "config/governance/project_state_transitions_v1.json")
    capabilities = _json(ROOT / "engineering/AGENT_CAPABILITIES.json")
    bridge = _json(ROOT / "engineering/STATE.json")
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")
    context = _json(ROOT / "engineering/CONTEXT_MAP.json")

    state_machine.validate_current(state, policy)
    try:
        awu_path, awu, awu_evidence = active_awu.resolve_active_awu()
    except active_awu.ActiveAwuError as exc:
        raise ColdStartError(str(exc)) from exc
    try:
        resolved = resolver.resolve(
            state,
            capabilities,
            "GITHUB_CONNECTOR_ONLY",
            "engineering",
            (awu_path, awu, awu_evidence),
        )
    except resolver.ResolveError as exc:
        raise ColdStartError(str(exc)) from exc

    validate_context_free_contract(state, resolved, context, awu)

    engineering = state["engineering_track"]
    bridge_engineering = bridge["engineering_engine"]
    _require(bridge_engineering["active_lot"] == engineering["active_lot"], "bridge lot drift")
    _require(bridge_engineering["active_task"] == engineering["active_task"], "bridge task drift")
    _require(
        bridge_engineering["active_manifest"] == engineering["active_manifest"],
        "bridge manifest drift",
    )
    handoff_validator.validate_handoff(state, handoff)

    probes = 0

    stale = copy.deepcopy(handoff)
    stale["next_engineering"]["active_task"] = "ENG-99.99"
    _expect(
        handoff_validator.HandoffError,
        lambda: handoff_validator.validate_handoff(state, stale),
        "stale handoff",
    )
    probes += 1

    unsafe_lot46 = copy.deepcopy(state)
    unsafe_lot46["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(unsafe_lot46, policy),
        "Lot46 unlock",
    )
    probes += 1

    paid = copy.deepcopy(state)
    paid["cost_policy"]["paid_llm_required"] = True
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(paid, policy),
        "mandatory paid LLM",
    )
    probes += 1

    _expect(
        resolver.ResolveError,
        lambda: resolver.resolve(state, capabilities, "READ_ONLY_AUDITOR", "audit"),
        "inactive audit track",
    )
    probes += 1

    units = active_awu.load_work_units()
    duplicate = dict(units)
    second = copy.deepcopy(awu)
    second["id"] = f"{awu['parent']['task_id']}-WU99"
    duplicate[ROOT / "engineering/work_units/cold-duplicate.json"] = second
    _expect(
        active_awu.ActiveAwuError,
        lambda: active_awu.select_active_awu(duplicate),
        "ambiguous active AWU",
    )
    probes += 1

    stale_context = copy.deepcopy(context)
    stale_context["active_work"]["awu_id"] = "ENG-99-WU99"
    _expect(
        ColdStartError,
        lambda: validate_context_free_contract(state, resolved, stale_context, awu),
        "stale context active AWU",
    )
    probes += 1

    expanded = copy.deepcopy(context)
    expanded["execution_context"]["implicit_expansion"] = "ALLOWED"
    _expect(
        ColdStartError,
        lambda: validate_context_free_contract(state, resolved, expanded, awu),
        "implicit repository expansion",
    )
    probes += 1

    injected = copy.deepcopy(resolved)
    injected["required_read_order"] = list(injected["required_read_order"]) + ["chat_history"]
    _expect(
        ColdStartError,
        lambda: validate_context_free_contract(state, injected, context, awu),
        "chat history injected into read order",
    )
    probes += 1

    oversized = copy.deepcopy(resolved)
    oversized["active_awu"]["context_route"]["total_kib_ceil"] = (
        awu["planning"]["context_budget"]["max_total_kib"] + 1
    )
    _expect(
        ColdStartError,
        lambda: validate_context_free_contract(state, oversized, context, awu),
        "context byte budget overflow",
    )
    probes += 1

    escalated = copy.deepcopy(resolved)
    escalated["capabilities"]["local_execution"] = True
    _expect(
        ColdStartError,
        lambda: validate_context_free_contract(state, escalated, context, awu),
        "GitHub-only local-execution escalation",
    )
    probes += 1

    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    _require(elapsed_ms < MAX_COLD_START_MS, f"cold-start budget exceeded: {elapsed_ms} ms")

    route = resolved["active_awu"]["context_route"]
    result = {
        "verdict": "CONTEXT_FREE_COLD_START_PASS",
        "track": resolved["track"],
        "lot": resolved["active_lot"],
        "task": resolved["active_task"],
        "awu": resolved["active_awu"]["id"],
        "authority": "config/governance/project_state.json",
        "profile": resolved["capability_profile"],
        "primary_count": route["primary_count"],
        "reference_count": route["reference_count"],
        "total_kib_ceil": route["total_kib_ceil"],
        "elapsed_ms": elapsed_ms,
        "budget_ms": MAX_COLD_START_MS,
        "negative_probes": probes,
        "conversational_context_required": False,
        "implicit_expansion": "FORBIDDEN",
        "business_development": resolved["business_development"],
        "next_business_lot_status": resolved["next_business_lot_status"],
        "trade_allowed": state["safety"]["trade_allowed"],
        "execution_allowed": state["safety"]["execution_allowed"],
    }
    print(
        "CONTEXT_FREE_COLD_START_PASS "
        + json.dumps(result, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
