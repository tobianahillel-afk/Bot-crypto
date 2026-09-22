#!/usr/bin/env python3
"""Negative self-tests for bootstrap governance validators."""

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


def _expect_failure(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"negative probe unexpectedly passed: {label}")


def main() -> int:
    state_mod = _module("bootstrap_state_validator", ROOT / "scripts/governance/validate_bootstrap_state.py")
    item_mod = _module("work_item_validator", ROOT / "scripts/governance/validate_work_item.py")
    handoff_mod = _module("handoff_validator", ROOT / "scripts/governance/validate_handoff.py")

    state = _json(ROOT / "engineering/STATE.json")
    policy = _json(ROOT / "engineering/STATE_TRANSITIONS.json")
    active_manifest = _json(ROOT / state["bootstrap_engine"]["active_manifest"])
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")

    state_mod.validate_state(state, policy, active_manifest)
    item_mod.validate_manifest(active_manifest, source=active_manifest["id"])
    handoff_mod.validate_handoff(state, handoff)

    unsafe_state = copy.deepcopy(state)
    unsafe_state["safety"]["trade_allowed"] = True
    _expect_failure(
        state_mod.BootstrapStateError,
        lambda: state_mod.validate_state(unsafe_state, policy, active_manifest),
        "trade_allowed true",
    )

    mismatched_state = copy.deepcopy(state)
    mismatched_state["bootstrap_engine"]["active_task"] = "BOOT-06.99"
    _expect_failure(
        state_mod.BootstrapStateError,
        lambda: state_mod.validate_state(mismatched_state, policy, active_manifest),
        "active task mismatch",
    )

    invalid_manifest = copy.deepcopy(active_manifest)
    invalid_manifest["status"] = "DONE"
    _expect_failure(
        item_mod.WorkItemError,
        lambda: item_mod.validate_manifest(invalid_manifest, source="negative-manifest"),
        "DONE item with unfinished tasks",
    )

    stale_handoff = copy.deepcopy(handoff)
    stale_handoff["state_snapshot"]["active_task"] = "BOOT-06.99"
    _expect_failure(
        handoff_mod.HandoffError,
        lambda: handoff_mod.validate_handoff(state, stale_handoff),
        "stale handoff task",
    )

    print("BOOTSTRAP_VALIDATOR_SELFTEST_PASS probes=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
