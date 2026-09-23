#!/usr/bin/env python3
"""Cold-start qualification using permanent state plus the active AWU."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain an object")
    return value


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"cold-start negative scenario unexpectedly passed: {label}")


def main() -> int:
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

    state_machine.validate_current(state, policy)
    resolved = resolver.repository_resolve("GITHUB_CONNECTOR_ONLY", "engineering")
    engineering = state["engineering_track"]
    assert resolved["track"] == "DEVELOPMENT_ENGINE"
    assert resolved["active_lot"] == engineering["active_lot"]
    assert resolved["active_task"] == engineering["active_task"]
    assert resolved["active_manifest"] == engineering["active_manifest"]
    assert resolved["active_awu"] is not None
    assert resolved["active_awu"]["split_required"] is False
    assert resolved["active_awu"]["path"] in resolved["required_read_order"]
    assert resolved["required_read_order"][0] == "AGENTS.md"
    assert resolved["capabilities"]["local_execution"] is False
    assert resolved["capabilities"]["may_claim_local_test_pass"] is False

    bridge_engineering = bridge["engineering_engine"]
    assert bridge_engineering["active_lot"] == engineering["active_lot"]
    assert bridge_engineering["active_task"] == engineering["active_task"]
    assert bridge_engineering["active_manifest"] == engineering["active_manifest"]
    handoff_validator.validate_handoff(bridge, handoff)

    stale = copy.deepcopy(handoff)
    stale["next_engineering"]["active_task"] = "ENG-99.99"
    _expect(
        handoff_validator.HandoffError,
        lambda: handoff_validator.validate_handoff(bridge, stale),
        "stale handoff",
    )

    unsafe_lot46 = copy.deepcopy(state)
    unsafe_lot46["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(unsafe_lot46, policy),
        "Lot46 unlock",
    )

    paid = copy.deepcopy(state)
    paid["cost_policy"]["paid_llm_required"] = True
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(paid, policy),
        "mandatory paid LLM",
    )

    _expect(
        resolver.ResolveError,
        lambda: resolver.resolve(state, capabilities, "READ_ONLY_AUDITOR", "audit"),
        "inactive audit track",
    )

    units = active_awu.load_work_units()
    path, current = active_awu.select_active_awu(units)
    duplicate = dict(units)
    second = copy.deepcopy(current)
    second["id"] = "ENG-02.8-WU99"
    duplicate[ROOT / "engineering/work_units/cold-duplicate.json"] = second
    _expect(
        active_awu.ActiveAwuError,
        lambda: active_awu.select_active_awu(duplicate),
        "ambiguous active AWU",
    )

    print(
        "PERMANENT_COLD_START_PASS "
        f"track={resolved['track']} lot={resolved['active_lot']} "
        f"task={resolved['active_task']} awu={resolved['active_awu']['id']} scenarios=6"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
