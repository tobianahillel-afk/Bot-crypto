#!/usr/bin/env python3
"""Cold-start qualification using permanent project state as primary authority."""

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

    state = _json(ROOT / "config/governance/project_state.json")
    policy = _json(ROOT / "config/governance/project_state_transitions_v1.json")
    capabilities = _json(ROOT / "engineering/AGENT_CAPABILITIES.json")
    bridge = _json(ROOT / "engineering/STATE.json")
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")

    # Scenario 1: a fresh GitHub-only agent resolves exactly the permanent ENGINEERING task.
    state_machine.validate_current(state, policy)
    resolved = resolver.resolve(state, capabilities, "GITHUB_CONNECTOR_ONLY", "engineering")
    engineering = state["engineering_track"]
    assert resolved["track"] == "DEVELOPMENT_ENGINE"
    assert resolved["active_lot"] == engineering["active_lot"]
    assert resolved["active_task"] == engineering["active_task"]
    assert resolved["active_manifest"] == engineering["active_manifest"]
    assert resolved["required_read_order"][1] == "config/governance/project_state.json"
    assert resolved["capabilities"]["local_execution"] is False
    assert resolved["capabilities"]["may_claim_local_test_pass"] is False

    # Compatibility bridge remains secondary but must still agree while migration is active.
    bridge_engineering = bridge["engineering_engine"]
    assert bridge_engineering["active_lot"] == engineering["active_lot"]
    assert bridge_engineering["active_task"] == engineering["active_task"]
    assert bridge_engineering["active_manifest"] == engineering["active_manifest"]
    handoff_validator.validate_handoff(bridge, handoff)

    # Scenario 2: stale handoff fails closed.
    stale = copy.deepcopy(handoff)
    stale["next_engineering"]["active_task"] = "ENG-01.99"
    _expect(
        handoff_validator.HandoffError,
        lambda: handoff_validator.validate_handoff(bridge, stale),
        "stale handoff",
    )

    # Scenario 3: Lot46 unlock fails current-state invariants.
    unsafe_lot46 = copy.deepcopy(state)
    unsafe_lot46["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(unsafe_lot46, policy),
        "Lot46 unlock",
    )

    # Scenario 4: mandatory paid LLM dependency fails current-state invariants.
    paid = copy.deepcopy(state)
    paid["cost_policy"]["paid_llm_required"] = True
    _expect(
        state_machine.StateMachineError,
        lambda: state_machine.validate_current(paid, policy),
        "mandatory paid LLM",
    )

    # Scenario 5: inactive audit track cannot be selected as work.
    _expect(
        resolver.ResolveError,
        lambda: resolver.resolve(state, capabilities, "READ_ONLY_AUDITOR", "audit"),
        "inactive audit track",
    )

    print(
        "PERMANENT_COLD_START_PASS "
        f"track={resolved['track']} lot={resolved['active_lot']} "
        f"task={resolved['active_task']} scenarios=5"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
