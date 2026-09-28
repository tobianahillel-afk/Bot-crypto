#!/usr/bin/env python3
"""Adversarial qualification for deterministic mutation profiles."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
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
    raise AssertionError(f"mutation-profile negative scenario unexpectedly passed: {label}")


def main() -> int:
    validator = _module(
        "mutation_profile_validator_selftest",
        ROOT / "scripts" / "governance" / "validate_mutation_profiles.py",
    )
    selector = _module(
        "mutation_profile_selector_selftest",
        ROOT / "scripts" / "governance" / "select_mutation_profile.py",
    )
    policy = json.loads(
        (ROOT / "config/governance/mutation_profile_policy_v1.json").read_text(encoding="utf-8")
    )
    registry = json.loads(
        (ROOT / "config/governance/mutation_profiles_v1.json").read_text(encoding="utf-8")
    )

    validator.validate_all(policy, registry)

    exact = selector.select_profiles(
        ["src/crypto_quant_bot/contracts/decision_evidence.py"], registry
    )
    assert exact["selected_profiles"] == ["P06_DECISION_EVIDENCE"]
    assert exact["mutation_executed"] is False

    glob = selector.select_profiles(
        ["tests/test_p06_decision_evidence_regression.py"], registry
    )
    assert glob["selected_profiles"] == ["P06_DECISION_EVIDENCE"]

    generic_workflow = selector.select_profiles(
        [".github/workflows/ci-mutation.yml"], registry
    )
    assert generic_workflow["selected_profiles"] == ["P06_DECISION_EVIDENCE"]

    retired_workflow = selector.select_profiles(
        [".github/workflows/p06-extended-mutation.yml"], registry
    )
    assert retired_workflow["selected_profiles"] == []

    unrelated = selector.select_profiles(["docs/README.md"], registry)
    assert unrelated["selected_profiles"] == []

    combined = selector.select_profiles(
        ["pyproject.toml", "requirements-dev.lock", "pyproject.toml"], registry
    )
    assert combined["selected_profiles"] == ["P06_DECISION_EVIDENCE"]
    assert combined["changed_paths"] == ["pyproject.toml", "requirements-dev.lock"]

    _expect(
        selector.MutationProfileSelectionError,
        lambda: selector.select_profiles(["../escape.py"], registry),
        "unsafe changed path",
    )

    overlap = copy.deepcopy(registry)
    duplicate = copy.deepcopy(overlap["profiles"][0])
    duplicate["id"] = "SECOND_PROFILE"
    duplicate["selectors"] = [
        {"mode": "EXACT", "pattern": "src/crypto_quant_bot/contracts/decision_evidence.py"}
    ]
    overlap["profiles"].append(duplicate)
    _expect(
        selector.MutationProfileSelectionError,
        lambda: selector.select_profiles(
            ["src/crypto_quant_bot/contracts/decision_evidence.py"], overlap
        ),
        "ambiguous profile match",
    )

    command_injection = copy.deepcopy(registry)
    command_injection["profiles"][0]["command"] = "mutmut run"
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_registry(policy, command_injection),
        "command injection",
    )

    threshold_drift = copy.deepcopy(registry)
    threshold_drift["profiles"][0]["score"]["minimum_percent"] = 79.0
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_p06_parity(threshold_drift),
        "P0.6 threshold drift",
    )

    target_drift = copy.deepcopy(registry)
    target_drift["profiles"][0]["mutation"]["targets"] = ["pyproject.toml"]
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_p06_parity(target_drift),
        "P0.6 target drift",
    )

    setting_drift = copy.deepcopy(registry)
    setting_drift["profiles"][0]["mutation"]["settings"]["timeout_multiplier"] = 7.0
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_p06_parity(setting_drift),
        "P0.6 inherited setting drift",
    )

    stale_binding = copy.deepcopy(registry)
    stale_binding["profiles"][0]["source_binding"]["exact_head"] = "0" * 40
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_registry(policy, stale_binding),
        "CURRENT_CHECKOUT exact-head injection",
    )

    legacy_blob_drift = copy.deepcopy(registry)
    legacy_blob_drift["profiles"][0]["legacy_reference"]["workflow_blob_sha"] = "0" * 40
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_p06_parity(legacy_blob_drift),
        "legacy blob drift",
    )

    lifecycle_drift = copy.deepcopy(registry)
    lifecycle_drift["profiles"][0]["legacy_reference"]["lifecycle"] = "PARITY_REFERENCE_UNTIL_WU12_MIGRATION"
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_p06_parity(lifecycle_drift),
        "migrated lifecycle drift",
    )

    workflow_text = (ROOT / ".github/workflows/ci-mutation.yml").read_text(encoding="utf-8")
    validator.validate_p06_migrated_workflow(workflow_text)

    missing_pr_path = workflow_text.replace(
        "      - 'pyproject.toml'\n  push:",
        "  push:",
        1,
    )
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_p06_migrated_workflow(missing_pr_path),
        "generic pull-request path drift",
    )

    missing_engineering = workflow_text.replace(
        "      - engineering/bootstrap-development-engine\n",
        "",
        1,
    )
    _expect(
        validator.MutationProfileError,
        lambda: validator.validate_p06_migrated_workflow(missing_engineering),
        "generic engineering maintenance branch drift",
    )

    print("MUTATION_PROFILES_SELFTEST_PASS probes=17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
