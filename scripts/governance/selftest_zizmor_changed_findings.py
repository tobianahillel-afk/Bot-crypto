#!/usr/bin/env python3
"""Adversarial qualification for diff-local zizmor finding gating."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "filter_zizmor_changed_findings.py"
    spec = importlib.util.spec_from_file_location("zizmor_changed_filter_selftest", path)
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
    raise AssertionError(f"zizmor filter negative scenario unexpectedly passed: {label}")


def _finding(path: str | None, row_zero: int | None) -> dict[str, Any]:
    location: dict[str, Any] = {}
    if path is not None:
        location["symbolic"] = {"key": {"Local": {"verbatim_path": path}}}
    if row_zero is not None:
        location["concrete"] = {
            "location": {"start_point": {"row": row_zero}}
        }
    return {
        "ident": "probe",
        "determinations": {"severity": "High", "confidence": "High"},
        "locations": [location] if location else [],
    }


def main() -> int:
    mod = _module()
    target = ".github/workflows/probe.yml"
    changed = {target: {3}}

    legacy = mod.evaluate_findings([_finding(target, 8)], changed, [target], 1)
    assert len(legacy["legacy_findings"]) == 1
    assert legacy["blocking_findings"] == []

    new = mod.evaluate_findings([_finding(target, 2)], changed, [target], 1)
    assert len(new["blocking_findings"]) == 1
    assert new["blocking_findings"][0]["decision"] == "BLOCK_CHANGED_HEAD_LINE"

    missing = mod.evaluate_findings([_finding(None, None)], changed, [target], 1)
    assert missing["blocking_findings"][0]["decision"] == "BLOCK_UNLOCATED"

    untargeted = mod.evaluate_findings(
        [_finding(".github/workflows/other.yml", 2)], changed, [target], 1
    )
    assert untargeted["blocking_findings"][0]["decision"] == "BLOCK_UNLOCATED"

    _expect(
        mod.ZizmorChangedFindingError,
        lambda: mod.evaluate_findings([], changed, [target], 1),
        "nonzero status without findings",
    )

    clean = mod.evaluate_findings([], changed, [target], 0)
    assert clean["total_findings"] == 0

    diff_probe = """diff --git a/.github/workflows/probe.yml b/.github/workflows/probe.yml
--- a/.github/workflows/probe.yml
+++ b/.github/workflows/probe.yml
@@ -1,2 +1 @@
-on:
-  pull_request:
+on: workflow_dispatch
@@ -8,0 +8 @@
+      - run: echo changed
"""
    assert mod.parse_changed_head_lines(diff_probe) == {target: {1, 8}}

    _expect(
        mod.ZizmorChangedFindingError,
        lambda: mod.evaluate_findings([_finding("../escape.yml", 0)], changed, [target], 1),
        "path escape",
    )
    _expect(
        mod.ZizmorChangedFindingError,
        lambda: mod.evaluate_findings([], changed, [target], -1),
        "negative tool status",
    )

    print("ZIZMOR_CHANGED_FINDING_SELFTEST_PASS probes=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
