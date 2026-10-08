#!/usr/bin/env python3
"""Adversarial qualification for ENG-06.1 certification candidate lifecycle."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_certification_candidate_lifecycle.py"
    spec = importlib.util.spec_from_file_location("candidate_lifecycle_selftest", path)
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
    raise AssertionError(f"candidate-lifecycle negative scenario unexpectedly passed: {label}")


def _base(state: str = "DRAFT") -> dict[str, Any]:
    return {
        "candidate_id": "ENG06-DEMO-1",
        "head_sha": "a" * 40,
        "risk_class": "R1",
        "state": state,
        "evidence_fresh": True,
        "evidence_bindings": {},
        "required_t3": [],
        "satisfied_t3": [],
        "required_t4": [],
        "satisfied_t4": [],
    }


def main() -> int:
    mod = _module()
    lifecycle, evidence, assurance = mod._load_policies()
    mod.validate_policy(lifecycle, evidence, assurance)

    draft = _base()
    mod.validate_candidate(draft, lifecycle, evidence, assurance)

    validating = copy.deepcopy(draft)
    validating["state"] = "VALIDATING"
    validating["evidence_bindings"]["CANDIDATE_REF_BOUND"] = "EXACT_GITHUB_REF"
    mod.validate_transition(draft, validating, lifecycle, evidence, assurance)

    assurance_required = copy.deepcopy(validating)
    assurance_required["state"] = "ASSURANCE_REQUIRED"
    assurance_required["evidence_bindings"].update({
        "VALIDATION_PASS_BOUND": "EXACT_GITHUB_ACTIONS_RUN",
        "ASSURANCE_SELECTION_BOUND": "REPOSITORY_ARTIFACT",
    })
    assurance_required["required_t3"] = ["SECURITY_ASSURANCE"]
    mod.validate_transition(
        validating, assurance_required, lifecycle, evidence, assurance
    )

    ready = copy.deepcopy(assurance_required)
    ready["state"] = "CERTIFICATION_READY"
    ready["satisfied_t3"] = ["SECURITY_ASSURANCE"]
    ready["required_t4"] = ["EXACT_HEAD_CERTIFICATION"]
    ready["evidence_bindings"]["NO_OPEN_BLOCKER"] = "OBSERVATION"
    mod.validate_transition(assurance_required, ready, lifecycle, evidence, assurance)

    certified = copy.deepcopy(ready)
    certified["state"] = "CERTIFIED"
    certified["satisfied_t4"] = ["EXACT_HEAD_CERTIFICATION"]
    certified["evidence_bindings"].update({
        "EXACT_HEAD_CERTIFICATION_EVIDENCE": "EXACT_GITHUB_ACTIONS_RUN",
        "CERTIFICATION_VERDICT_PASS": "REPOSITORY_ARTIFACT",
    })
    mod.validate_transition(ready, certified, lifecycle, evidence, assurance)

    resurrected = copy.deepcopy(certified)
    resurrected["state"] = "VALIDATING"
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_transition(certified, resurrected, lifecycle, evidence, assurance),
        "terminal resurrection",
    )

    changed_head = copy.deepcopy(validating)
    changed_head["head_sha"] = "b" * 40
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_transition(validating, changed_head, lifecycle, evidence, assurance),
        "head mutation",
    )

    stale_ready = copy.deepcopy(ready)
    stale_ready["evidence_fresh"] = False
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_candidate(stale_ready, lifecycle, evidence, assurance),
        "ready with stale evidence",
    )

    stale = copy.deepcopy(assurance_required)
    stale["state"] = "STALE"
    stale["evidence_fresh"] = False
    mod.validate_transition(assurance_required, stale, lifecycle, evidence, assurance)

    fake_stale = copy.deepcopy(stale)
    fake_stale["evidence_fresh"] = True
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_candidate(fake_stale, lifecycle, evidence, assurance),
        "STALE marked fresh",
    )

    no_missing_assurance = copy.deepcopy(assurance_required)
    no_missing_assurance["satisfied_t3"] = ["SECURITY_ASSURANCE"]
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_candidate(no_missing_assurance, lifecycle, evidence, assurance),
        "ASSURANCE_REQUIRED with no missing T3",
    )

    uncertified = copy.deepcopy(certified)
    uncertified["satisfied_t4"] = []
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_candidate(uncertified, lifecycle, evidence, assurance),
        "CERTIFIED with unsatisfied T4",
    )

    r3 = copy.deepcopy(validating)
    r3["risk_class"] = "R3"
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_candidate(r3, lifecycle, evidence, assurance),
        "R3 missing assurance floors",
    )

    bad_evidence = copy.deepcopy(validating)
    bad_evidence["evidence_bindings"]["CANDIDATE_REF_BOUND"] = "OBSERVATION"
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_candidate(bad_evidence, lifecycle, evidence, assurance),
        "wrong evidence class",
    )

    skipped = copy.deepcopy(ready)
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_transition(draft, skipped, lifecycle, evidence, assurance),
        "DRAFT skipped directly to ready",
    )

    unknown = copy.deepcopy(validating)
    unknown["state"] = "MAGIC"
    _expect(
        mod.CandidateLifecycleError,
        lambda: mod.validate_candidate(unknown, lifecycle, evidence, assurance),
        "unknown state",
    )

    print("CERTIFICATION_CANDIDATE_LIFECYCLE_SELFTEST_PASS probes=12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
