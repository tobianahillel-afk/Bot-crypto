#!/usr/bin/env python3
"""Detect unnecessary or missing incremental validation work from a symbolic trace."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "unnecessary_check_policy_v1.json"


class ValidationWorkError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationWorkError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationWorkError(f"{path} must contain an object")
    return value


def load_policies(meta: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = meta.get("source_policies")
    if not isinstance(sources, dict) or set(sources) != {"t1", "t2", "t3_t4", "incremental"}:
        raise ValidationWorkError("source policy registry drift")
    return {name: _json(ROOT / path) for name, path in sources.items()}


def validate_meta(meta: dict[str, Any]) -> None:
    if meta.get("schema_version") != 1:
        raise ValidationWorkError("unsupported unnecessary-check policy version")
    if meta.get("policy_kind") != "unnecessary_check_policy_v1":
        raise ValidationWorkError("invalid unnecessary-check policy kind")
    if meta.get("semantics") != "EXACT_EXPECTED_WORK_FROM_IMPACTS_AND_RISK":
        raise ValidationWorkError("unnecessary-check semantics drift")
    if meta.get("trace_version") != 1:
        raise ValidationWorkError("trace version drift")
    required = meta.get("required_trace_fields")
    if not isinstance(required, list) or len(required) != len(set(required)):
        raise ValidationWorkError("required trace fields invalid")
    if meta.get("verdicts") != ["CLEAN", "OVERVALIDATED", "UNDERVALIDATED", "MISMATCH"]:
        raise ValidationWorkError("verdict set/order drift")
    expectations = meta.get("incremental_execution_expectations")
    if expectations != {
        "full_suite_executed": False,
        "network_used": False,
        "deep_assurance_executed": False,
        "certification_executed": False,
    }:
        raise ValidationWorkError("incremental execution expectations drift")


def validate_source_policies(policies: dict[str, dict[str, Any]]) -> None:
    t1, t2, t34, inc = (
        policies["t1"], policies["t2"], policies["t3_t4"], policies["incremental"]
    )
    if t1.get("policy_kind") != "validation_t1_policy_v1":
        raise ValidationWorkError("invalid T1 policy")
    if t2.get("policy_kind") != "validation_t2_policy_v1":
        raise ValidationWorkError("invalid T2 policy")
    if t34.get("policy_kind") != "validation_t3_t4_policy_v1":
        raise ValidationWorkError("invalid T3/T4 policy")
    if inc.get("policy_kind") != "incremental_validation_policy_v1":
        raise ValidationWorkError("invalid incremental policy")

    impacts = set(t1.get("impact_to_checks", {}))
    if not impacts or set(t2.get("impact_to_groups", {})) != impacts:
        raise ValidationWorkError("T1/T2 impact universes disagree")
    if set(t34.get("residual_impact_to_t3", {})) != impacts:
        raise ValidationWorkError("T3 impact universe disagrees")
    if inc.get("single_pass_invocations") != {
        "T0": 1, "T1": 1, "T2": 1, "T3_T4_SELECTOR": 1
    }:
        raise ValidationWorkError("single-pass invocation contract drift")


def _unique_strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValidationWorkError(f"{label} must be a list of non-empty strings")
    return value


def derive_expected(
    impact_families: list[str],
    risk_class: str,
    policies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    validate_source_policies(policies)
    t1, t2, t34, inc = (
        policies["t1"], policies["t2"], policies["t3_t4"], policies["incremental"]
    )
    impacts = _unique_strings(impact_families, "impact_families")
    if not impacts:
        raise ValidationWorkError("impact_families cannot be empty")
    known = set(t1["impact_to_checks"])
    unknown = sorted(set(impacts) - known)
    if unknown:
        raise ValidationWorkError(f"unknown impact families: {unknown}")
    if risk_class not in t34["risk_order"]:
        raise ValidationWorkError(f"invalid risk class: {risk_class}")

    t1_checks: set[str] = set()
    t1_uncovered: set[str] = set()
    t0_sufficient = set(t1["t0_sufficient_impacts"])
    for impact in set(impacts):
        checks = t1["impact_to_checks"][impact]
        if checks:
            t1_checks.update(checks)
        elif impact not in t0_sufficient:
            t1_uncovered.add(impact)

    t2_groups: set[str] = set()
    t2_covered: set[str] = set()
    t2_remaining: set[str] = set()
    for impact in t1_uncovered:
        groups = t2["impact_to_groups"][impact]
        if groups:
            t2_groups.update(groups)
            t2_covered.add(impact)
        else:
            t2_remaining.add(impact)

    t3: set[str] = set(t34["risk_to_t3"][risk_class])
    for impact in sorted(t2_remaining):
        requirements = t34["residual_impact_to_t3"][impact]
        if not requirements:
            raise ValidationWorkError(
                f"residual impact would disappear without T3 requirement: {impact}"
            )
        t3.update(requirements)

    t4: set[str] = set(t34["risk_to_t4"][risk_class])
    for impact in sorted(t2_covered):
        t4.update(t34["certification_sensitive_covered_impacts"].get(impact, []))

    return {
        "selected_t1_checks": sorted(t1_checks),
        "selected_t2_groups": sorted(t2_groups),
        "t3_requirements": sorted(t3),
        "t4_requirements": sorted(t4),
        "pytest_invoked": bool(t2_groups),
        "stage_invocations": dict(inc["single_pass_invocations"]),
        "full_suite_executed": False,
        "network_used": False,
        "deep_assurance_executed": False,
        "certification_executed": False,
    }


def _set_diff(actual: list[str], expected: list[str], label: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    values = _unique_strings(actual, label)
    over: list[dict[str, Any]] = []
    under: list[dict[str, Any]] = []
    duplicates = sorted({item for item in values if values.count(item) > 1})
    if duplicates:
        over.append({"code": "DUPLICATE_SYMBOLIC_WORK", "field": label, "values": duplicates})
    actual_set, expected_set = set(values), set(expected)
    extra = sorted(actual_set - expected_set)
    missing = sorted(expected_set - actual_set)
    if extra:
        over.append({"code": "EXTRA_SYMBOLIC_WORK", "field": label, "values": extra})
    if missing:
        under.append({"code": "MISSING_SYMBOLIC_WORK", "field": label, "values": missing})
    return over, under


def evaluate_trace(
    trace: dict[str, Any],
    meta: dict[str, Any],
    policies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    validate_meta(meta)
    validate_source_policies(policies)
    if not isinstance(trace, dict):
        raise ValidationWorkError("trace must be an object")
    if set(meta["required_trace_fields"]) - set(trace):
        missing = sorted(set(meta["required_trace_fields"]) - set(trace))
        raise ValidationWorkError(f"trace missing required fields: {missing}")
    if trace.get("trace_version") != meta["trace_version"]:
        raise ValidationWorkError("trace version mismatch")

    expected = derive_expected(trace["impact_families"], trace["risk_class"], policies)
    over: list[dict[str, Any]] = []
    under: list[dict[str, Any]] = []

    for field in ("selected_t1_checks", "selected_t2_groups", "t3_requirements", "t4_requirements"):
        extra, missing = _set_diff(trace[field], expected[field], field)
        over.extend(extra)
        under.extend(missing)

    invocations = trace.get("stage_invocations")
    if not isinstance(invocations, dict):
        raise ValidationWorkError("stage_invocations must be an object")
    expected_invocations = expected["stage_invocations"]
    extra_stages = sorted(set(invocations) - set(expected_invocations))
    missing_stages = sorted(set(expected_invocations) - set(invocations))
    if extra_stages:
        over.append({"code": "EXTRA_STAGE", "field": "stage_invocations", "values": extra_stages})
    if missing_stages:
        under.append({"code": "MISSING_STAGE", "field": "stage_invocations", "values": missing_stages})
    for stage in sorted(set(invocations) & set(expected_invocations)):
        value = invocations[stage]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValidationWorkError(f"invalid stage invocation count: {stage}")
        wanted = expected_invocations[stage]
        if value > wanted:
            over.append({"code": "REPEATED_STAGE_EXECUTION", "field": stage, "actual": value, "expected": wanted})
        elif value < wanted:
            under.append({"code": "MISSING_STAGE_EXECUTION", "field": stage, "actual": value, "expected": wanted})

    for field in (
        "pytest_invoked", "full_suite_executed", "network_used",
        "deep_assurance_executed", "certification_executed",
    ):
        actual = trace.get(field)
        if not isinstance(actual, bool):
            raise ValidationWorkError(f"{field} must be boolean")
        wanted = expected[field]
        if actual is True and wanted is False:
            over.append({"code": "UNNECESSARY_EXECUTION", "field": field})
        elif actual is False and wanted is True:
            under.append({"code": "MISSING_REQUIRED_EXECUTION", "field": field})

    verdict = (
        "MISMATCH" if over and under
        else "OVERVALIDATED" if over
        else "UNDERVALIDATED" if under
        else "CLEAN"
    )
    return {
        "detector_version": 1,
        "verdict": verdict,
        "expected": expected,
        "overvalidation_findings": over,
        "undervalidation_findings": under,
    }


def _trace(impacts: list[str], risk: str, policies: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected = derive_expected(impacts, risk, policies)
    return {
        "trace_version": 1,
        "impact_families": impacts,
        "risk_class": risk,
        **copy.deepcopy(expected),
    }


def self_check(meta: dict[str, Any], policies: dict[str, dict[str, Any]]) -> None:
    validate_meta(meta)
    validate_source_policies(policies)

    docs = _trace(["DOC_CONSISTENCY"], "R1", policies)
    assert evaluate_trace(docs, meta, policies)["verdict"] == "CLEAN"

    workflow = _trace(["WORKFLOW_SYNTAX", "ACTIONS_SECURITY"], "R1", policies)
    assert set(workflow["t3_requirements"]) == {"WORKFLOW_ASSURANCE", "SECURITY_ASSURANCE"}
    assert evaluate_trace(workflow, meta, policies)["verdict"] == "CLEAN"

    r3 = _trace(["RISK_INVARIANTS", "EXECUTION_SAFETY"], "R3", policies)
    assert "R3_FULL_CERTIFICATION_CHAIN" in r3["t4_requirements"]
    assert evaluate_trace(r3, meta, policies)["verdict"] == "CLEAN"

    repeated = copy.deepcopy(docs)
    repeated["stage_invocations"]["T0"] = 2
    assert evaluate_trace(repeated, meta, policies)["verdict"] == "OVERVALIDATED"

    missing = copy.deepcopy(workflow)
    missing["t3_requirements"] = []
    assert evaluate_trace(missing, meta, policies)["verdict"] == "UNDERVALIDATED"

    print("UNNECESSARY_CHECK_SELF_CHECK_PASS probes=5")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--trace", type=Path)
    args = parser.parse_args()
    try:
        meta = _json(POLICY_PATH)
        policies = load_policies(meta)
        if args.self_check:
            self_check(meta, policies)
            return 0
        report = evaluate_trace(_json(args.trace), meta, policies)
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
        return 0 if report["verdict"] == "CLEAN" else 1
    except (ValidationWorkError, AssertionError, KeyError) as exc:
        print(f"UNNECESSARY_CHECK_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
