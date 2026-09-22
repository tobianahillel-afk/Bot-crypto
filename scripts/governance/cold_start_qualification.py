#!/usr/bin/env python3
"""Cold-start qualification for the Bootstrap Engineering Engine."""

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
    state_validator = _module(
        "cold_state_validator", ROOT / "scripts/governance/validate_bootstrap_state.py"
    )
    handoff_validator = _module(
        "cold_handoff_validator", ROOT / "scripts/governance/validate_handoff.py"
    )
    resolver = _module("cold_resolver", ROOT / "scripts/governance/resolve_next_work.py")

    state = _json(ROOT / "engineering/STATE.json")
    policy = _json(ROOT / "engineering/STATE_TRANSITIONS.json")
    capabilities = _json(ROOT / "engineering/AGENT_CAPABILITIES.json")
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")
    manifest = _json(ROOT / state["bootstrap_engine"]["active_manifest"])

    # Scenario 1: a context-free GitHub-only agent resolves one exact next action.
    state_validator.validate_state(state, policy, manifest)
    handoff_validator.validate_handoff(state, handoff)
    resolved = resolver.resolve(state, capabilities, "GITHUB_CONNECTOR_ONLY")
    assert resolved["active_lot"] == state["bootstrap_engine"]["active_lot"]
    assert resolved["active_task"] == state["bootstrap_engine"]["active_task"]
    assert resolved["capabilities"]["local_execution"] is False
    assert resolved["capabilities"]["may_claim_local_test_pass"] is False

    # Scenario 2: stale handoff fails closed.
    stale = copy.deepcopy(handoff)
    stale["state_snapshot"]["active_task"] = "BOOT-07.99"
    _expect(
        handoff_validator.HandoffError,
        lambda: handoff_validator.validate_handoff(state, stale),
        "stale handoff",
    )

    # Scenario 3: Lot46 unlock fails closed.
    unsafe_lot46 = copy.deepcopy(state)
    unsafe_lot46["business_track"]["next_lot"]["status"] = "UNLOCKED"
    _expect(
        state_validator.BootstrapStateError,
        lambda: state_validator.validate_state(unsafe_lot46, policy, manifest),
        "Lot46 unlock",
    )

    # Scenario 4: mandatory paid/LLM dependency fails closed.
    paid = copy.deepcopy(state)
    paid["mandatory_cost_policy"]["paid_llm_required"] = True
    _expect(
        state_validator.BootstrapStateError,
        lambda: state_validator.validate_state(paid, policy, manifest),
        "mandatory paid LLM",
    )

    print(
        "BOOTSTRAP_COLD_START_PASS "
        f"track={resolved['track']} lot={resolved['active_lot']} task={resolved['active_task']} "
        "scenarios=4"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
