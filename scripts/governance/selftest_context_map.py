#!/usr/bin/env python3
"""Adversarial tests for the generated progressive-disclosure context map."""

from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "render_context_map.py"
    spec = importlib.util.spec_from_file_location("context_map_selftest_renderer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"context-map negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)
    value, markdown = mod.desired()
    mod.validate_map(value)

    assert value["bootstrap_read_order"] == [
        "AGENTS.md", "config/governance/project_state.json", "engineering/CONTEXT_MAP.json"
    ]
    assert value["active_work"]["awu_id"] == "ENG-05.3-WU01"
    assert value["execution_context"]["primary_files"][:2] == [
        "AGENTS.md", "config/governance/project_state.json"
    ]
    assert value["resume"]["handoff"] == "engineering/handoff/CURRENT.json"
    assert "engineering/STATE.json" not in value["execution_context"]["primary_files"]
    assert "chat_history" in value["non_authoritative_sources"]
    assert "model_memory" in value["non_authoritative_sources"]
    assert "Implicit repository expansion: FORBIDDEN" in markdown

    bad_policy = copy.deepcopy(policy)
    bad_policy["bootstrap_read_order"][0] = "README.md"
    _expect(mod.ContextMapError, lambda: mod.validate_policy(bad_policy), "wrong authority prefix")

    duplicate = copy.deepcopy(value)
    duplicate["execution_context"]["primary_files"].append(
        duplicate["execution_context"]["primary_files"][0]
    )
    _expect(mod.ContextMapError, lambda: mod.validate_map(duplicate), "duplicate primary path")

    overlap = copy.deepcopy(value)
    overlap["execution_context"]["reference_files"].append(
        overlap["execution_context"]["primary_files"][0]
    )
    _expect(mod.ContextMapError, lambda: mod.validate_map(overlap), "route overlap")

    bridge = copy.deepcopy(value)
    bridge["execution_context"]["reference_files"].append("engineering/STATE.json")
    _expect(mod.ContextMapError, lambda: mod.validate_map(bridge), "bridge in execution context")

    state = mod._json(ROOT / policy["state_source"])
    handoff = mod._json(ROOT / policy["handoff_source"])
    stale = copy.deepcopy(handoff)
    stale["next_engineering"]["active_task"] = "ENG-05.999"
    _expect(
        mod.ContextMapError,
        lambda: mod._validate_handoff(stale, state["engineering_track"]),
        "stale handoff",
    )

    malformed = copy.deepcopy(value)
    malformed["non_authoritative_sources"] = ["chat_history"]
    _expect(mod.ContextMapError, lambda: mod.validate_map(malformed), "authority laundering")

    with tempfile.TemporaryDirectory() as raw:
        _expect(
            mod.ContextMapError,
            lambda: mod._safe_existing("../x", Path(raw)),
            "repository escape",
        )

    print("CONTEXT_MAP_SELFTEST_PASS probes=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
