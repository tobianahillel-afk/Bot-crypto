#!/usr/bin/env python3
"""Adversarial qualification for the fixed-command mutation profile runner."""

from __future__ import annotations

import copy
import importlib.util
import sys
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "run_mutation_profile.py"
    spec = importlib.util.spec_from_file_location("mutation_runner_selftest", path)
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
    raise AssertionError(f"mutation-runner negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    _policy, profile = mod._validated_profile("P06_DECISION_EVIDENCE")

    original = mod.PYPROJECT_PATH.read_text(encoding="utf-8")
    materialized = mod.materialize_pyproject_text(original, profile)
    parsed = tomllib.loads(materialized)["tool"]["mutmut"]
    assert parsed == mod.expected_mutmut_config(profile)
    assert parsed["only_mutate"] == [
        "src/crypto_quant_bot/contracts/decision_evidence.py"
    ]
    assert parsed["pytest_add_cli_args_test_selection"] == [
        "tests/test_p06_decision_evidence.py",
        "tests/test_p06_decision_evidence_properties.py",
    ]
    assert parsed["timeout_multiplier"] == 8.0
    assert parsed["timeout_constant"] == 1.0
    assert parsed["do_not_mutate_patterns"] == [r"raise \w+", r"logger\.\w+"]

    assert mod.mutmut_argv("run") == [sys.executable, "-m", "mutmut", "run"]
    assert mod.mutmut_argv("results") == [
        sys.executable,
        "-m",
        "mutmut",
        "results",
    ]
    _expect(
        mod.MutationRunnerError,
        lambda: mod.mutmut_argv("arbitrary"),
        "arbitrary mutmut action",
    )

    counts = mod.parse_counts("🎉 80  ⏰ 5  🤔 5  🙁 10")
    score, numerator, denominator = mod.score_counts(counts, profile["score"])
    assert numerator == 85 and denominator == 100 and score == 85.0

    no_eval = {"killed": 0, "timeout": 0, "suspicious": 0, "survived": 0}
    _expect(
        mod.MutationRunnerError,
        lambda: mod.score_counts(no_eval, profile["score"]),
        "zero evaluated mutants",
    )

    exact = copy.deepcopy(profile)
    exact["source_binding"] = {"mode": "EXACT_HEAD_INPUT", "exact_head": "a" * 40}
    registry = mod._load_json(mod.REGISTRY_PATH)
    for index, item in enumerate(registry["profiles"]):
        if item["id"] == exact["id"]:
            registry["profiles"][index] = exact
    original_loader = mod._load_json
    try:
        def fake_load(path: Path) -> dict[str, Any]:
            if path == mod.REGISTRY_PATH:
                return registry
            return original_loader(path)
        mod._load_json = fake_load
        _expect(
            mod.MutationRunnerError,
            lambda: mod._validated_profile("P06_DECISION_EVIDENCE"),
            "non-current source binding",
        )
    finally:
        mod._load_json = original_loader

    disabled = copy.deepcopy(profile)
    disabled["enabled"] = False
    registry = mod._load_json(mod.REGISTRY_PATH)
    for index, item in enumerate(registry["profiles"]):
        if item["id"] == disabled["id"]:
            registry["profiles"][index] = disabled
    try:
        def disabled_load(path: Path) -> dict[str, Any]:
            if path == mod.REGISTRY_PATH:
                return registry
            return original_loader(path)
        mod._load_json = disabled_load
        _expect(
            mod.MutationRunnerError,
            lambda: mod._validated_profile("P06_DECISION_EVIDENCE"),
            "disabled profile",
        )
    finally:
        mod._load_json = original_loader

    _expect(
        mod.MutationRunnerError,
        lambda: mod._validated_profile("NOT_A_PROFILE"),
        "unknown profile",
    )

    source = (ROOT / "scripts" / "governance" / "run_mutation_profile.py").read_text(
        encoding="utf-8"
    )
    assert "shell=True" not in source
    assert "os.system" not in source
    assert "subprocess.Popen" not in source
    assert '["git", *args]' in source

    validate = mod.validate_only("P06_DECISION_EVIDENCE")
    assert validate["mutation_executed"] is False
    assert validate["mutmut_version_locked"] == "3.5.0"
    assert len(validate["materialized_config_sha256"]) == 64

    print("MUTATION_RUNNER_SELFTEST_PASS probes=12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
