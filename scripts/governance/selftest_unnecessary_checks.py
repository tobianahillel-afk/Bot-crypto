#!/usr/bin/env python3
"""Adversarial qualification for unnecessary/missing validation-work detection."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "detect_unnecessary_checks.py"
    spec = importlib.util.spec_from_file_location("unnecessary_checks_selftest", path)
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
    raise AssertionError(f"unnecessary-check negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module()
    meta = mod._json(mod.POLICY_PATH)
    policies = mod.load_policies(meta)
    mod.validate_meta(meta)
    mod.validate_source_policies(policies)
    probes = 0

    def clean(impacts: list[str], risk: str = "R1") -> dict[str, Any]:
        return mod._trace(impacts, risk, policies)

    def verdict(trace: dict[str, Any], expected: str, label: str) -> dict[str, Any]:
        nonlocal probes
        report = mod.evaluate_trace(trace, meta, policies)
        assert report["verdict"] == expected, (label, report)
        probes += 1
        return report

    verdict(clean(["DOC_CONSISTENCY"]), "CLEAN", "docs clean")
    verdict(
        clean(["GOVERNANCE_VALIDATORS", "CONFIG_POLICY_VALIDATION"]),
        "CLEAN",
        "governance clean",
    )
    verdict(
        clean(["WORKFLOW_SYNTAX", "ACTIONS_SECURITY"]),
        "CLEAN",
        "workflow/security clean",
    )
    verdict(
        clean(["RISK_INVARIANTS", "EXECUTION_SAFETY"], "R3"),
        "CLEAN",
        "R3 clean",
    )

    trace = clean(["GOVERNANCE_VALIDATORS"])
    trace["selected_t1_checks"].append("NOT_REQUIRED_CHECK")
    verdict(trace, "OVERVALIDATED", "extra T1")

    trace = clean(["GOVERNANCE_VALIDATORS"])
    trace["selected_t1_checks"] = []
    verdict(trace, "UNDERVALIDATED", "missing T1")

    trace = clean(["DATA_CONTRACTS"])
    trace["selected_t2_groups"].append("EXTRA_GROUP")
    verdict(trace, "OVERVALIDATED", "extra T2")

    trace = clean(["DATA_CONTRACTS"])
    trace["selected_t2_groups"] = []
    verdict(trace, "UNDERVALIDATED", "missing T2")

    trace = clean(["WORKFLOW_SYNTAX"])
    trace["t3_requirements"].append("EXTRA_ASSURANCE")
    verdict(trace, "OVERVALIDATED", "extra T3")

    trace = clean(["WORKFLOW_SYNTAX"])
    trace["t3_requirements"] = []
    verdict(trace, "UNDERVALIDATED", "missing T3")

    trace = clean(["RISK_INVARIANTS"], "R3")
    trace["t4_requirements"].append("EXTRA_CERTIFICATION")
    verdict(trace, "OVERVALIDATED", "extra T4")

    trace = clean(["RISK_INVARIANTS"], "R3")
    trace["t4_requirements"] = []
    verdict(trace, "UNDERVALIDATED", "missing T4")

    for stage in ("T0", "T1", "T2", "T3_T4_SELECTOR"):
        trace = clean(["DOC_CONSISTENCY"])
        trace["stage_invocations"][stage] = 2
        verdict(trace, "OVERVALIDATED", f"repeated {stage}")

    trace = clean(["DOC_CONSISTENCY"])
    trace["stage_invocations"]["T1"] = 0
    verdict(trace, "UNDERVALIDATED", "missing stage execution")

    trace = clean(["DOC_CONSISTENCY"])
    trace["stage_invocations"]["EXTRA"] = 1
    verdict(trace, "OVERVALIDATED", "extra stage")

    trace = clean(["DOC_CONSISTENCY"])
    trace["stage_invocations"].pop("T2")
    verdict(trace, "UNDERVALIDATED", "missing stage")

    trace = clean(["DOC_CONSISTENCY"])
    trace["pytest_invoked"] = True
    verdict(trace, "OVERVALIDATED", "unnecessary pytest")

    trace = clean(["DATA_CONTRACTS"])
    assert trace["pytest_invoked"] is True
    trace["pytest_invoked"] = False
    verdict(trace, "UNDERVALIDATED", "missing required pytest")

    for field in (
        "full_suite_executed",
        "network_used",
        "deep_assurance_executed",
        "certification_executed",
    ):
        trace = clean(["DOC_CONSISTENCY"])
        trace[field] = True
        verdict(trace, "OVERVALIDATED", f"unnecessary {field}")

    trace = clean(["GOVERNANCE_VALIDATORS"])
    trace["selected_t1_checks"] = []
    trace["network_used"] = True
    verdict(trace, "MISMATCH", "mixed extra and missing")

    trace = clean(["GOVERNANCE_VALIDATORS"])
    trace["selected_t1_checks"].append(trace["selected_t1_checks"][0])
    report = verdict(trace, "OVERVALIDATED", "duplicate symbolic work")
    assert any(
        finding["code"] == "DUPLICATE_SYMBOLIC_WORK"
        for finding in report["overvalidation_findings"]
    )

    bad = clean(["DOC_CONSISTENCY"])
    bad.pop("risk_class")
    _expect(
        mod.ValidationWorkError,
        lambda: mod.evaluate_trace(bad, meta, policies),
        "missing required field",
    )
    probes += 1

    bad = clean(["DOC_CONSISTENCY"])
    bad["impact_families"] = ["NOT_A_REAL_IMPACT"]
    _expect(
        mod.ValidationWorkError,
        lambda: mod.evaluate_trace(bad, meta, policies),
        "unknown impact",
    )
    probes += 1

    bad = clean(["DOC_CONSISTENCY"])
    bad["risk_class"] = "R9"
    _expect(
        mod.ValidationWorkError,
        lambda: mod.evaluate_trace(bad, meta, policies),
        "invalid risk",
    )
    probes += 1

    bad = clean(["DOC_CONSISTENCY"])
    bad["stage_invocations"]["T0"] = True
    _expect(
        mod.ValidationWorkError,
        lambda: mod.evaluate_trace(bad, meta, policies),
        "boolean invocation count",
    )
    probes += 1

    assert probes >= 18
    print(f"UNNECESSARY_CHECK_SELFTEST_PASS probes={probes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
