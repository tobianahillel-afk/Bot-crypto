#!/usr/bin/env python3
"""Select symbolic T3/T4 requirements without executing assurance or certification."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "validation_t3_t4_policy_v1.json"
ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class T3T4SelectionError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise T3T4SelectionError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise T3T4SelectionError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise T3T4SelectionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _known_impacts() -> set[str]:
    impact = _json(ROOT / "config" / "governance" / "diff_impact_policy_v1.json")
    families = impact.get("impact_families")
    if not isinstance(families, list):
        raise T3T4SelectionError("impact policy families invalid")
    return set(families)


def _validate_ids(values: Any, label: str) -> set[str]:
    if not isinstance(values, list) or len(values) != len(set(values)):
        raise T3T4SelectionError(f"{label} must be a unique list")
    for value in values:
        if not isinstance(value, str) or ID_RE.fullmatch(value) is None:
            raise T3T4SelectionError(f"{label} contains invalid symbolic id: {value!r}")
    return set(values)


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise T3T4SelectionError("unsupported T3/T4 policy schema_version")
    if policy.get("policy_kind") != "validation_t3_t4_policy_v1":
        raise T3T4SelectionError("invalid T3/T4 policy kind")
    if policy.get("semantics") != "SYMBOLIC_ASSURANCE_CERTIFICATION_SELECTION_ONLY":
        raise T3T4SelectionError("T3/T4 selector must remain execution-free")
    if policy.get("risk_order") != ["R0","R1","R2","R3"]:
        raise T3T4SelectionError("risk order drift")

    t3_ids = _validate_ids(policy.get("t3_requirement_ids"), "t3_requirement_ids")
    t4_ids = _validate_ids(policy.get("t4_requirement_ids"), "t4_requirement_ids")
    if t3_ids & t4_ids:
        raise T3T4SelectionError("T3 and T4 requirement ids must be disjoint")

    known_impacts = _known_impacts()
    residual = policy.get("residual_impact_to_t3")
    if not isinstance(residual, dict) or set(residual) != known_impacts:
        raise T3T4SelectionError("residual T3 map must explicitly cover every impact family")
    for impact, requirements in residual.items():
        ids = _validate_ids(requirements, f"residual_impact_to_t3[{impact}]")
        if not ids <= t3_ids:
            raise T3T4SelectionError(f"residual impact {impact} references unknown T3 ids")

    for name, allowed, known in (
        ("risk_to_t3", t3_ids, t3_ids),
        ("risk_to_t4", t4_ids, t4_ids),
    ):
        mapping = policy.get(name)
        if not isinstance(mapping, dict) or set(mapping) != {"R0","R1","R2","R3"}:
            raise T3T4SelectionError(f"{name} must map all risk classes")
        for risk, requirements in mapping.items():
            ids = _validate_ids(requirements, f"{name}[{risk}]")
            if not ids <= known:
                raise T3T4SelectionError(f"{name}[{risk}] references unknown ids")

    r3_t4 = set(policy["risk_to_t4"]["R3"])
    if not {"EXACT_HEAD_CERTIFICATION","R3_FULL_CERTIFICATION_CHAIN"} <= r3_t4:
        raise T3T4SelectionError("R3 T4 floor is missing")

    cert = policy.get("certification_sensitive_covered_impacts")
    if not isinstance(cert, dict) or set(cert) != {"EVIDENCE_PROVENANCE"}:
        raise T3T4SelectionError("certification-sensitive impact set drift")
    cert_ids = _validate_ids(cert["EVIDENCE_PROVENANCE"], "certification EVIDENCE_PROVENANCE")
    if not {"EXACT_HEAD_CERTIFICATION","PROVENANCE_CERTIFICATION"} <= cert_ids:
        raise T3T4SelectionError("provenance certification floor is missing")
    if not cert_ids <= t4_ids:
        raise T3T4SelectionError("certification-sensitive mapping references unknown T4 ids")


def select_requirements(
    t2_result: dict[str, Any],
    risk_class: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    if t2_result.get("t2_version") != 1:
        raise T3T4SelectionError("selector requires T2 version 1")
    if risk_class not in policy["risk_order"]:
        raise T3T4SelectionError(f"invalid active AWU risk class: {risk_class!r}")

    residual = t2_result.get("remaining_uncovered_impacts")
    covered = t2_result.get("t2_covered_impacts")
    if not isinstance(residual, list) or not isinstance(covered, list):
        raise T3T4SelectionError("T2 impact evidence is incomplete")
    if set(residual) & set(covered):
        raise T3T4SelectionError("T2 impact cannot be both covered and uncovered")

    known = _known_impacts()
    unknown = sorted((set(residual) | set(covered)) - known)
    if unknown:
        raise T3T4SelectionError(f"T2 emitted unknown impacts: {unknown}")

    t3: set[str] = set(policy["risk_to_t3"][risk_class])
    t4: set[str] = set(policy["risk_to_t4"][risk_class])
    reasons: list[dict[str, str]] = []

    for impact in sorted(set(residual)):
        selected = policy["residual_impact_to_t3"][impact]
        if not selected:
            raise T3T4SelectionError(
                f"residual impact has no T3 requirement and would disappear: {impact}"
            )
        t3.update(selected)
        for requirement in selected:
            reasons.append({
                "tier":"T3","requirement":requirement,"reason":f"RESIDUAL_IMPACT:{impact}"
            })

    for impact in sorted(set(covered)):
        selected = policy["certification_sensitive_covered_impacts"].get(impact, [])
        t4.update(selected)
        for requirement in selected:
            reasons.append({
                "tier":"T4","requirement":requirement,
                "reason":f"CERTIFICATION_SENSITIVE_IMPACT:{impact}"
            })

    for requirement in policy["risk_to_t3"][risk_class]:
        reasons.append({
            "tier":"T3","requirement":requirement,"reason":f"RISK_CLASS:{risk_class}"
        })
    for requirement in policy["risk_to_t4"][risk_class]:
        reasons.append({
            "tier":"T4","requirement":requirement,"reason":f"RISK_CLASS:{risk_class}"
        })

    # Stable de-duplication of evidence.
    unique_reasons = {
        (item["tier"], item["requirement"], item["reason"]): item for item in reasons
    }
    return {
        "selector_version":1,
        "risk_class":risk_class,
        "t3_required":bool(t3),
        "t4_required":bool(t4),
        "t3_requirements":sorted(t3),
        "t4_requirements":sorted(t4),
        "selection_reasons":[
            unique_reasons[key] for key in sorted(unique_reasons)
        ],
        "requirements_executed":[],
        "assurance_executed":False,
        "certification_executed":False,
    }


def repository_run(t2_result: dict[str, Any] | None = None) -> dict[str, Any]:
    started=time.perf_counter()
    policy=_json(POLICY_PATH)
    validate_policy(policy)

    precomputed=t2_result is not None
    if t2_result is None:
        t2=_module("t3t4_prerequisite_t2", ROOT / "scripts/governance/run_t2.py")
        try:
            t2_result=t2.repository_run()
        except t2.T2Error as exc:
            raise T3T4SelectionError(f"T2 prerequisite failed: {exc}") from exc
    elif not isinstance(t2_result,dict):
        raise T3T4SelectionError("precomputed T2 result must be an object")
    active=_module("t3t4_active_awu", ROOT / "scripts/governance/resolve_active_awu.py")
    try:
        _path, awu, _evidence=active.resolve_active_awu()
    except active.ActiveAwuError as exc:
        raise T3T4SelectionError(str(exc)) from exc

    risk=awu.get("planning",{}).get("risk_class")
    result=select_requirements(t2_result, risk, policy)
    result.update({
        "active_awu":awu["id"],
        "scope_base_sha":awu["scope"]["scope_base_sha"],
        "prerequisite_t2_source":"PRECOMPUTED" if precomputed else "COMPUTED",
        "t2_remaining_uncovered_impacts":t2_result["remaining_uncovered_impacts"],
        "t2_covered_impacts":t2_result["t2_covered_impacts"],
        "selected_validation_tiers":["T0","T1","T2"]
            + (["T3"] if result["t3_required"] else [])
            + (["T4"] if result["t4_required"] else []),
        "completed_validation_tiers":["T0","T1","T2"],
        "elapsed_ms":round((time.perf_counter()-started)*1000,3),
        "network_used":False,
        "full_suite_executed":False,
    })
    return result


def main() -> int:
    try:
        result=repository_run()
    except T3T4SelectionError as exc:
        print(f"T3_T4_SELECTION_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
