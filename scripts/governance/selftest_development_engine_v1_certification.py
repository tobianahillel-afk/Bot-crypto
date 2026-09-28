#!/usr/bin/env python3
"""Adversarial qualification for Development Engine V1 candidate assembly."""

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
    path = ROOT / "scripts" / "governance" / "validate_development_engine_v1_certification.py"
    spec = importlib.util.spec_from_file_location("development_engine_v1_selftest", path)
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
    raise AssertionError(
        f"Development Engine V1 negative scenario unexpectedly passed: {label}"
    )


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    state = mod._json(ROOT / policy["state_source"])
    payloads, blobs = mod.load_evidence(policy)
    mod.validate_policy(policy)
    mod.validate_state(state, policy)
    mod.validate_evidence(payloads, policy)
    expected = mod.expected_candidate(policy, state, payloads, blobs)
    candidate = mod._json(mod.CANDIDATE_PATH)
    mod.validate_candidate(candidate, expected)

    bad_policy = copy.deepcopy(policy)
    bad_policy["fast_budgets_ms"]["T0"] = 251
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_policy(bad_policy),
        "weakened T0 budget",
    )

    bad_status_policy = copy.deepcopy(policy)
    bad_status_policy["candidate_status"] = "CERTIFIED"
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_policy(bad_status_policy),
        "CERTIFIED policy status",
    )

    bad_security = copy.deepcopy(payloads)
    bad_security["security_engine"]["verdict"] = "PASS_BUT_WEAK"
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(bad_security, policy),
        "security verdict drift",
    )

    bad_cost = copy.deepcopy(payloads)
    bad_cost["mandatory_cost"]["claim_scope"]["account_wide_no_bill_claim"] = True
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(bad_cost, policy),
        "account-wide zero-bill claim",
    )

    slow_cold = copy.deepcopy(payloads)
    slow_cold["cold_start"]["metrics"]["elapsed_ms"] = 1000.001
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(slow_cold, policy),
        "cold-start budget bypass",
    )

    bad_recovery = copy.deepcopy(payloads)
    bad_recovery["interruption_recovery"]["recovery_metrics"]["state_auto_healed"] = True
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(bad_recovery, policy),
        "state auto-heal",
    )

    slow_recovery = copy.deepcopy(payloads)
    slow_recovery["interruption_recovery"]["recovery_metrics"]["elapsed_ms"] = 1000.001
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(slow_recovery, policy),
        "recovery budget bypass",
    )

    bad_r3 = copy.deepcopy(payloads)
    bad_r3["critical_r3_bypass"]["same_head_evidence"] = False
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(bad_r3, policy),
        "R3 same-head bypass",
    )

    bad_pilot = copy.deepcopy(payloads)
    bad_pilot["lot45_pilot"]["candidate_ready_for_merge"] = True
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(bad_pilot, policy),
        "Lot45 merge-ready drift",
    )

    bad_profile = copy.deepcopy(payloads)
    bad_profile["lot45_profile"]["candidate_profile"]["active_registry_adopted"] = True
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_evidence(bad_profile, policy),
        "Lot45 profile adoption",
    )

    unlocked_state = copy.deepcopy(state)
    unlocked_state["business_track"]["development_status"] = "ACTIVE"
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_state(unlocked_state, policy),
        "business unlock",
    )

    suppressed = copy.deepcopy(state)
    next(
        item for item in suppressed["findings"] if item["id"] == "BOOT-FINDING-001"
    )["observed"] = False
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_state(suppressed, policy),
        "blocker suppression",
    )

    tampered = copy.deepcopy(candidate)
    tampered["material"]["certification_gate"]["certified"] = True
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_candidate(tampered, expected),
        "false CERTIFIED claim",
    )

    fake_t4 = copy.deepcopy(candidate)
    fake_t4["material"]["certification_gate"]["exact_head_t4_executed"] = True
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_candidate(fake_t4, expected),
        "false T4 execution claim",
    )

    blob_drift = copy.deepcopy(candidate)
    blob_drift["material"]["evidence_bindings"]["security_engine"]["blob_sha"] = "0" * 40
    _expect(
        mod.EngineV1CertificationError,
        lambda: mod.validate_candidate(blob_drift, expected),
        "evidence blob drift",
    )

    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        workflow = (
            temp / ".github/workflows/eng09-wu13-candidate-profile-qualification.yml"
        )
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: should-not-exist\n", encoding="utf-8")
        _expect(
            mod.EngineV1CertificationError,
            lambda: mod.validate_temporary_workflow_absent(
                payloads["lot45_profile"], temp
            ),
            "temporary WU13 workflow resurrection",
        )

    print("DEVELOPMENT_ENGINE_V1_SELFTEST_PASS probes=16")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
