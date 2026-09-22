#!/usr/bin/env python3
"""Adversarial tests for agent capability and evidence claims."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_agent_evidence_policy.py"
    spec = importlib.util.spec_from_file_location("agent_evidence_policy_validator", path)
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
    raise AssertionError(f"evidence-policy negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod.load_policy()
    mod.validate_policy(policy)

    _expect(
        mod.EvidencePolicyError,
        lambda: mod.validate_claim(
            policy,
            "GITHUB_CONNECTOR_ONLY",
            {
                "claim_kind": "LOCAL_TEST_PASS",
                "evidence_class": "LOCAL_COMMAND_OUTPUT",
                "evidence": {"command": "pytest", "exit_code": 0, "executed": True},
            },
        ),
        "GitHub-only local test PASS",
    )

    _expect(
        mod.EvidencePolicyError,
        lambda: mod.validate_claim(
            policy,
            "GITHUB_CONNECTOR_ONLY",
            {
                "claim_kind": "CI_PASS",
                "evidence_class": "EXACT_GITHUB_ACTIONS_RUN",
                "evidence": {
                    "run_id": 123,
                    "head_sha": "0" * 40,
                    "conclusion": "failure",
                },
            },
        ),
        "failed CI presented as PASS",
    )

    mod.validate_claim(
        policy,
        "GITHUB_CONNECTOR_ONLY",
        {
            "claim_kind": "CI_PASS",
            "evidence_class": "EXACT_GITHUB_ACTIONS_RUN",
            "evidence": {
                "run_id": 35793777054,
                "head_sha": "5ffe1f6711cee629a6cdcc2c351f4079a5afb2a5",
                "conclusion": "success",
            },
        },
    )

    _expect(
        mod.EvidencePolicyError,
        lambda: mod.validate_claim(
            policy,
            "LOCAL_REPOSITORY",
            {
                "claim_kind": "LOCAL_TEST_PASS",
                "evidence_class": "LOCAL_COMMAND_OUTPUT",
                "evidence": {"command": "pytest", "exit_code": 0, "executed": False},
            },
        ),
        "unexecuted local command",
    )

    mod.validate_claim(
        policy,
        "LOCAL_REPOSITORY",
        {
            "claim_kind": "LOCAL_TEST_PASS",
            "evidence_class": "LOCAL_COMMAND_OUTPUT",
            "evidence": {"command": "pytest -q tests/example.py", "exit_code": 0, "executed": True},
        },
    )

    _expect(
        mod.EvidencePolicyError,
        lambda: mod.validate_claim(
            policy,
            "READ_ONLY_AUDITOR",
            {
                "claim_kind": "REPOSITORY_MUTATION",
                "evidence_class": "EXACT_GITHUB_REF",
                "evidence": {"ref": "refs/heads/example", "sha": "1" * 40},
            },
        ),
        "read-only mutation claim",
    )

    print("AGENT_EVIDENCE_POLICY_SELFTEST_PASS probes=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
