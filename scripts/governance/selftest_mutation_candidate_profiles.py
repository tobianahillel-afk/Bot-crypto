#!/usr/bin/env python3
"""Adversarial tests for read-only Lot45 mutation candidate profiles."""

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
    raise AssertionError(f"candidate-profile negative scenario unexpectedly passed: {label}")


def main() -> int:
    validator = _module(
        "candidate_profile_validator_selftest",
        ROOT / "scripts/governance/validate_mutation_candidate_profiles.py",
    )
    selector = _module(
        "candidate_profile_selector_selftest",
        ROOT / "scripts/governance/select_mutation_candidate_profile.py",
    )
    policy = json.loads(
        (ROOT / "config/governance/mutation_candidate_profile_policy_v1.json").read_text(encoding="utf-8")
    )
    registry = json.loads(
        (ROOT / "config/governance/mutation_candidate_profiles_v1.json").read_text(encoding="utf-8")
    )
    active = json.loads(
        (ROOT / "config/governance/mutation_profiles_v1.json").read_text(encoding="utf-8")
    )
    validator.validate_all(policy, registry, active)

    cases = [
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py",
        "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py",
        "tests/test_lot45_policy_contract.py",
        "scripts/lot45_trusted_prelaunch.sh",
        "config/microstructure/order_flow_delta_and_cvd_engine_v1.json",
        "contracts/schemas/cvd_series_v1.schema.json",
        ".github/workflows/lot45-mutation-assurance.yml",
        "requirements-dev.lock",
    ]
    for path in cases:
        result = selector.select_candidates([path], registry)
        assert result["selected_candidates"] == ["LOT45_ORDER_FLOW_DELTA_CVD"]
        assert result["mutation_executed"] is False
        assert result["production_selector_visible"] is False
        assert result["execution_allowed"] is False

    unrelated = selector.select_candidates(["docs/README.md"], registry)
    assert unrelated["selected_candidates"] == []

    _expect(
        selector.MutationCandidateSelectionError,
        lambda: selector.select_candidates(["../escape.py"], registry),
        "unsafe changed path",
    )

    adopted = copy.deepcopy(registry)
    adopted["profiles"][0]["active_registry_adopted"] = True
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, adopted),
        "candidate adoption",
    )

    executable = copy.deepcopy(registry)
    executable["profiles"][0]["execution_allowed"] = True
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, executable),
        "candidate execution",
    )

    head_drift = copy.deepcopy(registry)
    head_drift["profiles"][0]["candidate_binding"]["candidate_head_sha"] = "0" * 40
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, head_drift),
        "candidate head drift",
    )

    selector_drift = copy.deepcopy(registry)
    selector_drift["profiles"][0]["selectors"][0]["pattern"] = "src/crypto_quant_bot/microstructure/*.py"
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, selector_drift),
        "selector identity drift",
    )

    source_mode_drift = copy.deepcopy(registry)
    source_mode_drift["profiles"][0]["source_binding"]["mode"] = "CURRENT_CHECKOUT"
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, source_mode_drift),
        "source-binding mode drift",
    )

    baseline_drift = copy.deepcopy(registry)
    baseline_drift["profiles"][0]["baseline_tests"][0] = "tests/test_unrelated.py"
    baseline_drift["profiles"][0]["mutation"]["tests"][0] = "tests/test_unrelated.py"
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, baseline_drift),
        "baseline test identity drift",
    )

    copy_drift = copy.deepcopy(registry)
    copy_drift["profiles"][0]["mutation"]["copy_semantics"]["microstructure_python_except_targets"][0] = (
        "src/crypto_quant_bot/microstructure/fake_dependency.py"
    )
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, copy_drift),
        "workspace copy identity drift",
    )

    workflow_blob_drift = copy.deepcopy(registry)
    workflow_blob_drift["profiles"][0]["candidate_binding"]["mutation_workflow_blob_sha"] = "0" * 40
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, workflow_blob_drift),
        "workflow blob drift",
    )

    score_drift = copy.deepcopy(registry)
    score_drift["profiles"][0]["evidence"]["killed"] = 1340
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, score_drift),
        "evidence arithmetic drift",
    )

    contamination = copy.deepcopy(active)
    contamination["profiles"].append({"id": "LOT45_ORDER_FLOW_DELTA_CVD"})
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_active_registry_isolation(contamination),
        "active registry contamination",
    )

    overlap = copy.deepcopy(registry)
    duplicate = copy.deepcopy(overlap["profiles"][0])
    duplicate["id"] = "LOT45_DUPLICATE"
    overlap["profiles"].append(duplicate)
    _expect(
        selector.MutationCandidateSelectionError,
        lambda: selector.select_candidates(
            ["src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py"], overlap
        ),
        "ambiguous candidate selection",
    )

    command = copy.deepcopy(registry)
    command["profiles"][0]["command"] = "mutmut run"
    _expect(
        validator.MutationCandidateProfileError,
        lambda: validator.validate_registry(policy, command),
        "command injection",
    )

    print("MUTATION_CANDIDATE_PROFILES_SELFTEST_PASS probes=22")


if __name__ == "__main__":
    raise SystemExit(main())
