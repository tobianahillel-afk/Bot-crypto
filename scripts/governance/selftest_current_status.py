#!/usr/bin/env python3
"""Adversarial tests for deterministic generated current-status documentation."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts/governance/render_current_status.py"
    spec = importlib.util.spec_from_file_location("current_status_selftest", path)
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
    raise AssertionError(f"current-status negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)
    state = mod._json(ROOT / policy["source"])
    first = mod.render_block(state)
    second = mod.render_block(state)
    assert first == second
    assert "generated_at" not in first.lower()
    assert state["business_track"]["candidate"]["status"] in first
    assert "Lot 46 / LOCKED" in first
    assert "Trading allowed: `false`" in first

    changed = json.loads(json.dumps(state))
    changed["business_track"]["merged_certified_baseline"]["version"] = "SELFTEST-SENTINEL"
    assert mod.render_block(changed) != first

    terminal = json.loads(json.dumps(state))
    terminal_engineering = terminal["engineering_track"]
    terminal_business = terminal["business_track"]
    terminal_engineering["phase"] = "STABLE"
    if not terminal_engineering["completed"] or terminal_engineering["completed"][-1] != "ENG-09":
        terminal_engineering["completed"].append("ENG-09")
    terminal_engineering["active_lot"] = None
    terminal_engineering["active_task"] = None
    terminal_engineering["active_manifest"] = None
    terminal_engineering["next_lot"] = None
    terminal_engineering["blockers"] = []
    terminal_business["development_status"] = "ACTIVE"
    terminal_business["candidate"]["status"] = "ACTIVE_CANDIDATE"
    terminal["authority"]["active_manifest"] = "business/lots/LOT-45.json"
    terminal_block = mod.render_block(terminal)
    assert "Business development: **ACTIVE**" in terminal_block
    assert "Active business candidate: **Lot 45 / PR #66 / ACTIVE_CANDIDATE**" in terminal_block
    assert "Engineering: **terminal / STABLE**" in terminal_block
    assert "Next engineering lot: **ENGINE_COMPLETE**" in terminal_block
    assert "Lot 46 / LOCKED" in terminal_block
    assert "Trading allowed: `false`" in terminal_block

    unsafe_terminal = json.loads(json.dumps(terminal))
    unsafe_terminal["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(
        mod.CurrentStatusError,
        lambda: mod.render_block(unsafe_terminal),
        "terminal Lot46 unlock",
    )

    _expect(
        mod.CurrentStatusError,
        lambda: mod.replace_block("# x\n", "<!-- BEGIN GENERATED CURRENT STATUS -->", "<!-- END GENERATED CURRENT STATUS -->", first),
        "missing markers",
    )
    duplicate = first + "\n" + first
    _expect(
        mod.CurrentStatusError,
        lambda: mod.replace_block(duplicate, "<!-- BEGIN GENERATED CURRENT STATUS -->", "<!-- END GENERATED CURRENT STATUS -->", first),
        "duplicate markers",
    )

    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        (temp / "config/governance").mkdir(parents=True)
        (temp / "engineering").mkdir()
        shutil.copy2(ROOT / policy["source"], temp / policy["source"])
        shutil.copy2(mod.POLICY_PATH, temp / "config/governance/generated_status_policy_v1.json")
        for rel in ("README.md", "AGENTS.md", "engineering/CURRENT_STATUS.md"):
            src = ROOT / rel
            dst = temp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        mod.run("check", temp)
        before = {rel: (temp / rel).read_bytes() for rel in ("README.md","AGENTS.md","engineering/CURRENT_STATUS.md")}
        mod.run("update", temp)
        mod.run("update", temp)
        after = {rel: (temp / rel).read_bytes() for rel in before}
        assert before == after

        readme = temp / "README.md"
        lifecycle = state["business_track"]["development_status"]
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                f"Business development: **{lifecycle}**",
                "Business development: **STALE**",
                1,
            ),
            encoding="utf-8",
        )
        _expect(mod.CurrentStatusError, lambda: mod.run("check", temp), "stale generated block")
        mod.run("update", temp)
        mod.run("check", temp)

    print("CURRENT_STATUS_SELFTEST_PASS probes=11")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
