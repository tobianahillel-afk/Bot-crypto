#!/usr/bin/env python3
"""Adversarial qualification for final ENG-04 security-engine verification."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "verify_security_engine.py"
    spec = importlib.util.spec_from_file_location("eng04_security_engine_selftest", path)
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
    raise AssertionError(f"security-engine negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    result = mod.build_result(policy)
    assert result["verdict"] == "PASS_ENGINEERING_SECURITY"
    assert result["business_unlock_status"] == "BUSINESS_UNLOCK_BLOCKED_EXTERNAL_PROTECTION"
    assert result["zero_cost"] is True
    assert result["risk_proportional"] is True

    secret = (ROOT / policy["secret_workflow"]).read_text(encoding="utf-8")
    _expect(
        mod.SecurityEngineError,
        lambda: mod.validate_secret_routing(secret.replace("Scan introduced Git range", "Removed range step"), policy),
        "routine range removed",
    )
    _expect(
        mod.SecurityEngineError,
        lambda: mod.validate_secret_routing(secret.replace("FULL_HISTORY_FALLBACK", "UNSAFE_EMPTY_RANGE"), policy),
        "range fallback removed",
    )
    _expect(
        mod.SecurityEngineError,
        lambda: mod.validate_secret_routing(
            secret.replace(
                "Scan full Git history\n        if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'",
                "Scan full Git history\n        if: github.event_name == 'push'",
            ),
            policy,
        ),
        "full history moved to routine push",
    )
    _expect(
        mod.SecurityEngineError,
        lambda: mod.validate_secret_routing(secret.replace("  pull_request:\n", "  pull_request:\n    paths:\n      - docs/**\n"), policy),
        "secret path filtering introduced",
    )

    bad_policy = copy.deepcopy(policy)
    bad_policy["secret_weekly_cron"] = "0 0 * * *"
    _expect(mod.SecurityEngineError, lambda: mod.validate_policy(bad_policy), "assurance cadence drift")

    protection = mod._json(ROOT / policy["repository_protection_status"])
    bad_protection = copy.deepcopy(protection)
    bad_protection["business_unlock_allowed"] = True
    original_json = mod._json
    try:
        mod._json = lambda path: bad_protection if path == ROOT / policy["repository_protection_status"] else original_json(path)
        _expect(mod.SecurityEngineError, lambda: mod.validate_protection(policy), "unsafe business unlock")
    finally:
        mod._json = original_json

    cost_path = ROOT / policy["cost_policy_files"][0]
    original_cost = mod._json(cost_path)
    bad_cost = copy.deepcopy(original_cost)
    first_key = next(iter(bad_cost["cost_policy"]))
    bad_cost["cost_policy"][first_key] = True
    try:
        mod._json = lambda path: bad_cost if path == cost_path else original_json(path)
        _expect(mod.SecurityEngineError, lambda: mod.validate_zero_cost(policy), "paid control introduced")
    finally:
        mod._json = original_json

    mod.check_evidence(result)
    print("SECURITY_ENGINE_SELFTEST_PASS probes=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
