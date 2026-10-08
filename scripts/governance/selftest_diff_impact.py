#!/usr/bin/env python3
"""Adversarial tests for execution-free diff impact mapping."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "map_diff_impact.py"
    spec = importlib.util.spec_from_file_location("diff_impact_selftest", path)
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
    raise AssertionError(f"diff-impact negative scenario unexpectedly passed: {label}")


def _classification(*labels: str, docs_only: bool = False) -> dict[str, Any]:
    return {
        "classifier_version": 1,
        "files": [{"path": "x", "labels": list(labels)}],
        "labels": sorted(set(labels) | ({"DOC_ONLY"} if docs_only else set())),
        "critical_labels": [],
        "docs_only": docs_only,
        "requires_review": False,
    }


def main() -> int:
    mod = _module()
    policy = mod._load(mod.POLICY_PATH)
    mod.validate_policy(policy)

    docs = mod.map_impact(_classification("DOCUMENTATION", docs_only=True), policy)
    assert docs["impact_families"] == ["DOC_CONSISTENCY"]
    assert docs["domains"] == ["DOCUMENTATION"]
    assert docs["validation_tiers"] == []
    assert docs["execution_commands"] == []

    ci = mod.map_impact(_classification("CI_WORKFLOW"), policy)
    assert {"WORKFLOW_SYNTAX", "ACTIONS_SECURITY"} <= set(ci["impact_families"])

    contract = mod.map_impact(_classification("CONTRACT_SCHEMA"), policy)
    assert {"CONTRACT_SCHEMA_VALIDATION", "CONTRACT_COMPATIBILITY"} <= set(
        contract["impact_families"]
    )

    production = mod.map_impact(_classification("BUSINESS_PRODUCTION"), policy)
    assert {"STATIC_ANALYSIS", "UNIT_BEHAVIOR"} <= set(production["impact_families"])

    critical = mod.map_impact(
        _classification("BUSINESS_PRODUCTION", "RISK_EXECUTION_CRITICAL"),
        policy,
    )
    assert {"RISK_INVARIANTS", "EXECUTION_SAFETY"} <= set(critical["impact_families"])
    assert critical["sensitivity"] == "CRITICAL"

    unknown = mod.map_impact(_classification("UNKNOWN_REQUIRES_REVIEW"), policy)
    assert unknown["requires_human_review"] is True
    assert {"CONSERVATIVE_BROAD_IMPACT", "HUMAN_REVIEW_REQUIRED"} <= set(
        unknown["impact_families"]
    )

    mixed = mod.map_impact(
        _classification("DOCUMENTATION", "CONTRACT_SCHEMA", "CI_WORKFLOW"),
        policy,
    )
    assert {
        "DOC_CONSISTENCY", "CONTRACT_SCHEMA_VALIDATION", "WORKFLOW_SYNTAX"
    } <= set(mixed["impact_families"])
    assert mixed["docs_only_candidate"] is False

    unmapped = _classification("NOT_A_REAL_LABEL")
    _expect(
        mod.DiffImpactError,
        lambda: mod.map_impact(unmapped, policy),
        "unmapped classifier label",
    )

    forged_docs = _classification("DOCUMENTATION")
    forged_docs["labels"].append("DOC_ONLY")
    _expect(
        mod.DiffImpactError,
        lambda: mod.map_impact(forged_docs, policy),
        "forged DOC_ONLY",
    )

    broken = copy.deepcopy(policy)
    broken["mappings"]["UNKNOWN_REQUIRES_REVIEW"]["impact_families"] = ["DOC_CONSISTENCY"]
    _expect(
        mod.DiffImpactError,
        lambda: mod.validate_policy(broken),
        "unsafe unknown mapping",
    )

    print("DIFF_IMPACT_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
