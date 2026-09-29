#!/usr/bin/env python3
"""Adversarial qualification for the explicit business unlock decision."""

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
    path = ROOT / "scripts" / "governance" / "validate_business_development_unlock_decision.py"
    spec = importlib.util.spec_from_file_location("business_unlock_decision_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"unlock-decision negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    decision = _load("engineering/BUSINESS_DEVELOPMENT_UNLOCK_DECISION.json")
    state = _load("config/governance/project_state.json")
    policy = _load("config/governance/repository_protection_policy_v1.json")
    protection = _load("engineering/REPOSITORY_PROTECTION_STATUS.json")
    security = _load("engineering/SECURITY_ENGINE_VERIFICATION.json")
    cert = _load("engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json")

    mod.validate(decision, state, policy, protection, security, cert)

    # Baseline intentionally contains one disabled/incomplete ruleset.
    assert state["external_observations"]["rulesets_count"] == 1
    assert state["external_observations"]["rulesets_enabled_count"] == 0
    assert state["external_observations"]["rulesets"][0]["enforcement"] == "disabled"

    forged_snapshot = copy.deepcopy(decision)
    forged_snapshot["repository_protection"]["rulesets_count"] = 0
    _expect(
        mod.BusinessUnlockDecisionError,
        lambda: mod.validate(forged_snapshot, state, policy, protection, security, cert),
        "decision ruleset snapshot mismatch",
    )

    bad_counter = copy.deepcopy(state)
    bad_counter["external_observations"]["rulesets_count"] = 2
    _expect(
        mod.BusinessUnlockDecisionError,
        lambda: mod.validate(decision, bad_counter, policy, protection, security, cert),
        "ruleset counter mismatch",
    )

    # Even an active ruleset is insufficient while policy evidence remains UNPROTECTED:
    # the observed rules only cover deletion/non-fast-forward and omit PR/status-check rules.
    active_incomplete = copy.deepcopy(state)
    active_incomplete["external_observations"]["rulesets"][0]["enforcement"] = "active"
    active_incomplete["external_observations"]["rulesets_enabled_count"] = 1
    active_incomplete["external_observations"]["rulesets_disabled_count"] = 0
    active_decision = copy.deepcopy(decision)
    active_decision["repository_protection"]["observed_rulesets"] = copy.deepcopy(
        active_incomplete["external_observations"]["rulesets"]
    )
    active_decision["repository_protection"]["rulesets_enabled_count"] = 1
    active_decision["repository_protection"]["rulesets_disabled_count"] = 0
    active_decision["live_reverification"]["active_rulesets_count"] = 1
    active_decision["live_reverification"]["observed_ruleset"]["enforcement"] = "active"
    mod.validate(active_decision, active_incomplete, policy, protection, security, cert)

    allowed = copy.deepcopy(decision)
    allowed["verdict"] = "ALLOW_UNLOCK"
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(allowed, state, policy, protection, security, cert), "unsafe allow verdict")

    active_business = copy.deepcopy(state)
    active_business["business_track"]["development_status"] = "ACTIVE"
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(decision, active_business, policy, protection, security, cert), "business activation while blocker open")

    lot46_open = copy.deepcopy(state)
    lot46_open["business_track"]["next_lot"]["status"] = "OPEN"
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(decision, lot46_open, policy, protection, security, cert), "Lot46 unlock while blocker open")

    finding_closed = copy.deepcopy(state)
    finding_closed["findings"][0]["observed"] = False
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(decision, finding_closed, policy, protection, security, cert), "decision reused after blocker state changes")

    protected = copy.deepcopy(protection)
    protected["overall_status"] = "PROTECTED"
    protected["business_unlock_allowed"] = True
    protected["manual_admin_action_required"] = False
    protected_state = copy.deepcopy(state)
    protected_state["external_observations"]["main"]["branch_protected"] = True
    protected_state["external_observations"]["rulesets_count"] = 1
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(decision, protected_state, policy, protected, security, cert), "stale blocked decision after protection changes")

    no_engine_cert = copy.deepcopy(cert)
    no_engine_cert["verdict"] = "FAIL"
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(decision, state, policy, protection, security, no_engine_cert), "missing engine certification")

    no_security = copy.deepcopy(security)
    no_security["verdict"] = "FAIL"
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(decision, state, policy, protection, no_security, cert), "missing security verification")

    no_blocker = copy.deepcopy(state)
    no_blocker["engineering_track"]["blockers"] = []
    _expect(mod.BusinessUnlockDecisionError, lambda: mod.validate(decision, no_blocker, policy, protection, security, cert), "engineering blocker removed")

    print("BUSINESS_UNLOCK_DECISION_SELFTEST_PASS probes=11")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
