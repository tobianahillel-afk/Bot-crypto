#!/usr/bin/env python3
"""Adversarial tests for the deterministic conservative diff classifier."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "classify_diff.py"
    spec = importlib.util.spec_from_file_location("diff_classifier_selftest", path)
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
    raise AssertionError(f"diff-classifier negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    policy = mod._load_policy()
    mod.validate_policy(policy)

    docs = mod.classify_paths(["docs/guide.md", "README.md"], policy)
    assert docs["docs_only"] is True
    assert "DOC_ONLY" in docs["labels"]
    assert set(docs["labels"]) == {"DOCUMENTATION", "DOC_ONLY"}

    workflow = mod.classify_paths([".github/workflows/check.yml"], policy)
    assert "CI_WORKFLOW" in workflow["labels"]
    assert workflow["docs_only"] is False

    contract = mod.classify_paths(["contracts/schemas/foo.schema.json"], policy)
    assert "CONTRACT_SCHEMA" in contract["labels"]

    security = mod.classify_paths(["src/crypto_quant_bot/security/policy.py"], policy)
    assert {"SECURITY", "BUSINESS_PRODUCTION"} <= set(security["labels"])
    assert security["requires_review"] is True

    critical = mod.classify_paths(["src/crypto_quant_bot/execution/router.py"], policy)
    assert {"RISK_EXECUTION_CRITICAL", "BUSINESS_PRODUCTION"} <= set(critical["labels"])
    assert critical["requires_review"] is True

    mixed = mod.classify_paths(
        ["docs/guide.md", "src/crypto_quant_bot/strategy/example.py"],
        policy,
    )
    assert mixed["docs_only"] is False
    assert "DOC_ONLY" not in mixed["labels"]
    assert {"DOCUMENTATION", "BUSINESS_PRODUCTION"} <= set(mixed["labels"])

    unknown = mod.classify_paths(["experimental-zone/file.zzz"], policy)
    assert unknown["labels"] == ["UNKNOWN_REQUIRES_REVIEW"]
    assert unknown["requires_review"] is True

    governance_doc = mod.classify_paths(["engineering/AGENT_PROTOCOL.md"], policy)
    assert {"GOVERNANCE_CONTROL", "DOCUMENTATION"} <= set(governance_doc["labels"])
    assert governance_doc["docs_only"] is False

    additive = copy.deepcopy(policy)
    additive["rules"].append(
        {"code": "EXTRA", "label": "SECURITY", "patterns": [".github/workflows/**"]}
    )
    result = mod.classify_paths([".github/workflows/check.yml"], additive)
    assert {"CI_WORKFLOW", "SECURITY"} <= set(result["labels"])

    dependency_pyproject = mod.classify_paths(["pyproject.toml"], policy)
    assert {"CONFIG_POLICY", "SECURITY"} <= set(dependency_pyproject["labels"])
    assert "UNKNOWN_REQUIRES_REVIEW" not in dependency_pyproject["labels"]
    assert dependency_pyproject["requires_review"] is True

    dependency_lock = mod.classify_paths(["requirements-dev.lock"], policy)
    assert {"CONFIG_POLICY", "SECURITY"} <= set(dependency_lock["labels"])
    assert "UNKNOWN_REQUIRES_REVIEW" not in dependency_lock["labels"]

    pilot_paths = {
        "scripts/lot45_trusted_prelaunch.sh": {"BUSINESS_PRODUCTION"},
        "scripts/run_lot45_order_flow_delta_and_cvd_engine.py": {"BUSINESS_PRODUCTION"},
        "scripts/validate_lot45.py": {"BUSINESS_PRODUCTION"},
        "scripts/validate_lot45_frozen_evidence.py": {
            "BUSINESS_PRODUCTION",
            "CERTIFICATION_EVIDENCE",
        },
    }
    for path, expected in pilot_paths.items():
        classified = mod.classify_paths([path], policy)
        assert expected <= set(classified["labels"])
        assert "UNKNOWN_REQUIRES_REVIEW" not in classified["labels"]

    post_merge = mod.classify_paths(["scripts/validate_lot44_post_merge.py"], policy)
    assert {"BUSINESS_PRODUCTION", "CERTIFICATION_EVIDENCE"} <= set(post_merge["labels"])

    entry_gate = mod.classify_paths(["scripts/validate_lot46_entry_gate.py"], policy)
    assert {"BUSINESS_PRODUCTION", "CERTIFICATION_EVIDENCE"} <= set(entry_gate["labels"])

    broken = copy.deepcopy(policy)
    broken["aggregate_rules"]["unknown_fallback"] = "DOCUMENTATION"
    _expect(mod.DiffClassifierError, lambda: mod.validate_policy(broken), "unsafe fallback")

    _expect(
        mod.DiffClassifierError,
        lambda: mod.classify_paths([], policy),
        "empty diff",
    )

    print("DIFF_CLASSIFIER_SELFTEST_PASS probes=21")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
