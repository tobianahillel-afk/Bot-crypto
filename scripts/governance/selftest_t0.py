#!/usr/bin/env python3
"""Adversarial qualification for the zero-dependency T0 gate."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
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
    raise AssertionError(f"T0 negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module("t0_selftest_runner", ROOT / "scripts/governance/run_t0.py")
    classifier = _module("t0_selftest_classifier", ROOT / "scripts/governance/classify_diff.py")
    impact = _module("t0_selftest_impact", ROOT / "scripts/governance/map_diff_impact.py")
    policy = mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        original_root = mod.ROOT
        mod.ROOT = tmp
        try:
            (tmp / "good.py").write_text("x = 1\n", encoding="utf-8")
            (tmp / "good.json").write_text('{"x": 1}\n', encoding="utf-8")
            (tmp / "good.toml").write_text('x = 1\n', encoding="utf-8")
            for name in ("good.py", "good.json", "good.toml"):
                assert mod.validate_present_file(name, policy)["status"] == "PASS"

            (tmp / "bad.py").write_text("def nope(:\n", encoding="utf-8")
            _expect(mod.T0Error, lambda: mod.validate_present_file("bad.py", policy), "bad python")

            (tmp / "bad.json").write_text('{"x": }\n', encoding="utf-8")
            _expect(mod.T0Error, lambda: mod.validate_present_file("bad.json", policy), "bad json")

            (tmp / "bad.toml").write_text('x = [\n', encoding="utf-8")
            _expect(mod.T0Error, lambda: mod.validate_present_file("bad.toml", policy), "bad toml")

            deleted = mod.run_t0_for_changes(
                [mod.Change(status="D", path="missing.py")], policy, classifier, impact
            )
            assert deleted["parse_results"][0]["status"] == "SKIPPED_DELETED"

            (tmp / "docs").mkdir()
            (tmp / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            docs = mod.run_t0_for_changes(
                [mod.Change(status="M", path="docs/guide.md")], policy, classifier, impact
            )
            assert docs["classification"]["docs_only"] is True
            assert docs["parse_results"][0]["status"] == "SKIPPED_NON_PARSEABLE"
            assert docs["test_suite_executed"] is False

            (tmp / "experimental-zone").mkdir()
            (tmp / "experimental-zone" / "x.zzz").write_text("x\n", encoding="utf-8")
            unknown = mod.run_t0_for_changes(
                [mod.Change(status="A", path="experimental-zone/x.zzz")],
                policy,
                classifier,
                impact,
            )
            assert unknown["escalation_recommended"] is True
            assert any("UNKNOWN_REQUIRES_REVIEW" in x for x in unknown["escalation_reasons"])

            risk_dir = tmp / "src" / "crypto_quant_bot" / "risk"
            risk_dir.mkdir(parents=True)
            (risk_dir / "gate.py").write_text("ALLOW = False\n", encoding="utf-8")
            critical = mod.run_t0_for_changes(
                [mod.Change(status="M", path="src/crypto_quant_bot/risk/gate.py")],
                policy,
                classifier,
                impact,
            )
            assert critical["escalation_recommended"] is True
            assert any("RISK_EXECUTION_CRITICAL" in x for x in critical["escalation_reasons"])
            assert critical["selected_validation_tiers"] == ["T0"]
            assert critical["deeper_tiers_executed"] == []
            assert critical["network_used"] is False

            _expect(
                mod.T0Error,
                lambda: mod.run_t0_for_changes([], policy, classifier, impact),
                "empty changed-file set",
            )

            too_many = [mod.Change(status="M", path=f"x{i}.txt") for i in range(policy["max_changed_files"] + 1)]
            _expect(
                mod.T0Error,
                lambda: mod.run_t0_for_changes(too_many, policy, classifier, impact),
                "changed-file flood",
            )
        finally:
            mod.ROOT = original_root

    assert json.loads('{"x":1}')["x"] == 1
    assert tomllib.loads("x=1")["x"] == 1
    print("T0_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
