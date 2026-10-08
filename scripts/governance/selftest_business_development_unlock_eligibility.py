#!/usr/bin/env python3
"""Adversarial qualification for post-remediation business unlock eligibility."""

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
    path = ROOT / "scripts/governance/validate_business_development_unlock_eligibility.py"
    spec = importlib.util.spec_from_file_location("business_unlock_eligibility_selftest", path)
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
    raise AssertionError(f"unlock-eligibility negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    evidence = _load("engineering/BUSINESS_DEVELOPMENT_UNLOCK_ELIGIBILITY.json")
    policy = _load("config/governance/business_unlock_eligibility_policy_v1.json")
    state = _load("config/governance/project_state.json")
    blocked = _load("engineering/BUSINESS_DEVELOPMENT_UNLOCK_DECISION.json")
    security = _load("engineering/SECURITY_ENGINE_VERIFICATION.json")
    cert = _load("engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_EVIDENCE.json")
    mod.validate_snapshot(evidence, policy, state, blocked, security, cert)

    ruleset = evidence["live_reverification"]["observed_ruleset"]
    by_type = {item["type"]: item for item in ruleset["rules"]}
    assert by_type["required_status_checks"]["parameters"]["strict_required_status_checks_policy"] is False
    assert by_type["pull_request"]["parameters"]["required_approving_review_count"] == 0
    assert by_type["pull_request"]["parameters"]["required_review_thread_resolution"] is False

    disabled = copy.deepcopy(evidence)
    disabled["live_reverification"]["observed_ruleset"]["enforcement"] = "disabled"
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(disabled, policy, state, blocked, security, cert), "disabled ruleset")

    no_main = copy.deepcopy(evidence)
    no_main["live_reverification"]["observed_ruleset"]["conditions"]["ref_name"]["include"] = []
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(no_main, policy, state, blocked, security, cert), "missing main scope")

    for rule_type in ("pull_request","required_status_checks","deletion","non_fast_forward"):
        missing = copy.deepcopy(evidence)
        missing["live_reverification"]["observed_ruleset"]["rules"] = [
            item for item in missing["live_reverification"]["observed_ruleset"]["rules"]
            if item["type"] != rule_type
        ]
        _expect(
            mod.BusinessUnlockEligibilityError,
            lambda value=missing: mod.validate_snapshot(value, policy, state, blocked, security, cert),
            f"missing {rule_type}",
        )

    missing_quality = copy.deepcopy(evidence)
    status_rule = next(
        item for item in missing_quality["live_reverification"]["observed_ruleset"]["rules"]
        if item["type"] == "required_status_checks"
    )
    status_rule["parameters"]["required_status_checks"] = [
        item for item in status_rule["parameters"]["required_status_checks"]
        if item["context"] != "quality"
    ]
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(missing_quality, policy, state, blocked, security, cert), "missing quality check")

    bypass = copy.deepcopy(evidence)
    bypass["live_reverification"]["observed_ruleset"]["bypass_actors"] = [{"actor_id":1}]
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(bypass, policy, state, blocked, security, cert), "ruleset bypass")

    unprotected = copy.deepcopy(evidence)
    unprotected["live_reverification"]["main_branch_protected"] = False
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(unprotected, policy, state, blocked, security, cert), "unprotected main")

    changed_candidate = copy.deepcopy(evidence)
    changed_candidate["live_reverification"]["lot45_head_sha"] = "1" * 40
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(changed_candidate, policy, state, blocked, security, cert), "candidate head drift")

    hardening_forged = copy.deepcopy(evidence)
    hardening_forged["hardening_snapshot"]["strict_required_status_checks_policy"] = True
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(hardening_forged, policy, state, blocked, security, cert), "hardening snapshot forgery")

    auto = copy.deepcopy(evidence)
    auto["authority"]["business_development_unlock_executed"] = True
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(auto, policy, state, blocked, security, cert), "automatic business unlock")

    lot46 = copy.deepcopy(evidence)
    lot46["authority"]["lot46_status"] = "OPEN"
    lot46["authority"]["lot46_unlock_allowed"] = True
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(lot46, policy, state, blocked, security, cert), "Lot46 unlock")

    verdict = copy.deepcopy(evidence)
    verdict["verdict"] = "ALLOW_UNLOCK"
    _expect(mod.BusinessUnlockEligibilityError, lambda: mod.validate_snapshot(verdict, policy, state, blocked, security, cert), "activation-style verdict")

    print("BUSINESS_UNLOCK_ELIGIBILITY_SELFTEST_PASS probes=14 optional_hardening=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
