#!/usr/bin/env python3
"""Adversarial self-tests for permanent project-state transition semantics."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_project_state_machine.py"
    spec = importlib.util.spec_from_file_location("project_state_machine_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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
    raise AssertionError(f"state-machine negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    current = _json(ROOT / "config" / "governance" / "project_state.json")
    policy = _json(ROOT / "config" / "governance" / "project_state_transitions_v1.json")

    mod.validate_current(current, policy)

    unsafe = copy.deepcopy(current)
    unsafe["safety"]["trade_allowed"] = True
    _expect(mod.StateMachineError, lambda: mod.validate_current(unsafe, policy), "trade unlock")

    paid = copy.deepcopy(current)
    paid["cost_policy"]["paid_llm_required"] = True
    _expect(mod.StateMachineError, lambda: mod.validate_current(paid, policy), "paid LLM")

    business = copy.deepcopy(current)
    business["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(mod.StateMachineError, lambda: mod.validate_current(business, policy), "Lot46 unlock")

    previous = copy.deepcopy(current)
    previous["engineering_track"]["active_task"] = "ENG-01.1"
    skipped = copy.deepcopy(current)
    skipped["engineering_track"]["active_task"] = "ENG-01.3"
    _expect(
        mod.StateMachineError,
        lambda: mod.validate_transition(previous, skipped, policy),
        "task skip",
    )

    removed = copy.deepcopy(current)
    removed["findings"] = []
    _expect(
        mod.StateMachineError,
        lambda: mod.validate_transition(current, removed, policy),
        "finding removal",
    )

    print("PROJECT_STATE_MACHINE_SELFTEST_PASS probes=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
