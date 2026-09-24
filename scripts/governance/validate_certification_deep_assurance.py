#!/usr/bin/env python3
"""Validate risk-proportional T3 assurance using existing exact-head workflow evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/governance/certification_deep_assurance_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class DeepAssuranceError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeepAssuranceError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DeepAssuranceError(f"{path} must contain an object")
    return value


def _canonical(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DeepAssuranceError(f"value is not canonical JSON: {exc}") from exc
    return rendered.encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load_policies(root: Path = ROOT) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    policy = _json(root / "config/governance/certification_deep_assurance_v1.json")
    selection = _json(root / policy["selection_policy_source"])
    exact_head = _json(root / policy["exact_head_policy_source"])
    security = _json(root / policy["security_engine_policy_source"])
    evidence = _json(root / policy["evidence_policy_source"])
    return policy, selection, exact_head, security, evidence


def validate_policy(
    policy: dict[str, Any],
    selection: dict[str, Any],
    exact_head: dict[str, Any],
    security: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    if policy.get("schema_version") != 1:
        raise DeepAssuranceError("unsupported deep-assurance policy version")
    if policy.get("policy_kind") != "certification_deep_assurance_v1":
        raise DeepAssuranceError("invalid deep-assurance policy kind")
    if policy.get("semantics") != (
        "T3_REASON_TO_EXISTING_EXACT_HEAD_WORKFLOW_EVIDENCE_FAIL_CLOSED"
    ):
        raise DeepAssuranceError("deep-assurance semantics drift")
    expected_sources = {
        "selection_policy_source": "config/governance/validation_t3_t4_policy_v1.json",
        "exact_head_policy_source": "config/governance/certification_exact_head_binding_v1.json",
        "security_engine_policy_source": "config/governance/security_engine_verification_policy_v1.json",
        "evidence_policy_source": "engineering/AGENT_CAPABILITIES.json",
    }
    for key, expected in expected_sources.items():
        if policy.get(key) != expected:
            raise DeepAssuranceError(f"{key} drift")
    if policy.get("execution_model") != (
        "EXISTING_EVENT_TRIGGERED_WORKFLOWS_NO_DUPLICATE_SCANNER_RUNS"
    ):
        raise DeepAssuranceError("deep-assurance execution model drift")
    if policy.get("required_conclusion") != "success":
        raise DeepAssuranceError("deep-assurance success conclusion drift")
    if policy.get("exact_run_fields") != [
        "control_id", "run_id", "workflow", "head_sha", "conclusion"
    ]:
        raise DeepAssuranceError("exact-run evidence shape drift")
    if not isinstance(policy.get("max_evidence_runs"), int) or not 1 <= policy["max_evidence_runs"] <= 64:
        raise DeepAssuranceError("invalid max_evidence_runs")

    t3_ids = selection.get("t3_requirement_ids")
    if not isinstance(t3_ids, list):
        raise DeepAssuranceError("T3 requirement catalog missing")
    mapping = policy.get("requirement_reason_controls")
    if not isinstance(mapping, dict) or set(mapping) != set(t3_ids):
        raise DeepAssuranceError("every T3 requirement must have an assurance mapping")

    catalog = policy.get("control_catalog")
    if not isinstance(catalog, dict) or not catalog:
        raise DeepAssuranceError("assurance control catalog missing")
    security_paths = set(security.get("security_workflows", []))
    for control_id, control in catalog.items():
        if not isinstance(control, dict) or set(control) != {
            "automatic", "workflow_name", "workflow_path"
        }:
            raise DeepAssuranceError(f"invalid control catalog entry: {control_id}")
        if control["automatic"]:
            if not isinstance(control["workflow_name"], str) or not control["workflow_name"]:
                raise DeepAssuranceError(f"automatic control lacks workflow name: {control_id}")
            path = control["workflow_path"]
            if control_id == "ENGINEERING_BOOTSTRAP":
                if path != ".github/workflows/engineering-bootstrap.yml":
                    raise DeepAssuranceError("engineering bootstrap control path drift")
            elif path not in security_paths:
                raise DeepAssuranceError(
                    f"automatic assurance control is not an ENG-04 security workflow: {control_id}"
                )
        else:
            if control_id != "MANUAL_REVIEW" or control["workflow_name"] is not None or control["workflow_path"] is not None:
                raise DeepAssuranceError("manual review control shape drift")

    for requirement, reasons in mapping.items():
        if not isinstance(reasons, dict) or not reasons:
            raise DeepAssuranceError(f"assurance requirement has no reason mapping: {requirement}")
        for reason, controls in reasons.items():
            if not isinstance(reason, str) or ":" not in reason:
                raise DeepAssuranceError(f"invalid assurance reason: {reason!r}")
            if not isinstance(controls, list) or not controls or len(controls) != len(set(controls)):
                raise DeepAssuranceError(f"invalid control set for {requirement}/{reason}")
            unknown = sorted(set(controls) - set(catalog))
            if unknown:
                raise DeepAssuranceError(
                    f"assurance mapping references unknown controls: {unknown}"
                )

    if exact_head.get("required_ci_evidence_class") != "EXACT_GITHUB_ACTIONS_RUN":
        raise DeepAssuranceError("exact-head CI evidence class drift")
    if exact_head.get("required_ci_conclusion") != "success":
        raise DeepAssuranceError("exact-head CI conclusion drift")
    classes = evidence.get("evidence_classes")
    if not isinstance(classes, dict) or "EXACT_GITHUB_ACTIONS_RUN" not in classes:
        raise DeepAssuranceError("agent exact-run evidence class missing")

    r3_t3 = set(selection.get("risk_to_t3", {}).get("R3", []))
    if "RISK_EXECUTION_ASSURANCE" not in r3_t3:
        raise DeepAssuranceError("R3 selector T3 assurance floor drift")
    r3_t4 = set(selection.get("risk_to_t4", {}).get("R3", []))
    if not {"EXACT_HEAD_CERTIFICATION", "R3_FULL_CERTIFICATION_CHAIN"} <= r3_t4:
        raise DeepAssuranceError("R3 selector T4 certification floor drift")

    r3_controls = set(mapping["RISK_EXECUTION_ASSURANCE"].get("RISK_CLASS:R3", []))
    if r3_controls != {"ENGINEERING_BOOTSTRAP", "SAST", "SECRET_SCANNING"}:
        raise DeepAssuranceError("R3 assurance floor drift")
    manual = mapping["MANUAL_DEEP_REVIEW"]
    if any(set(controls) != {"MANUAL_REVIEW"} for controls in manual.values()):
        raise DeepAssuranceError("manual deep review must remain non-automatic")


def _validate_selector(
    selector: dict[str, Any],
    selection_policy: dict[str, Any],
) -> tuple[list[str], list[dict[str, str]]]:
    if selector.get("selector_version") != 1:
        raise DeepAssuranceError("unsupported selector result version")
    requirements = selector.get("t3_requirements")
    if not isinstance(requirements, list) or len(requirements) != len(set(requirements)):
        raise DeepAssuranceError("selector T3 requirements invalid")
    known = set(selection_policy["t3_requirement_ids"])
    if any(item not in known for item in requirements):
        raise DeepAssuranceError("selector emitted unknown T3 requirement")
    if selector.get("t3_required") is not bool(requirements):
        raise DeepAssuranceError("selector t3_required flag disagrees with requirements")

    raw_reasons = selector.get("selection_reasons")
    if not isinstance(raw_reasons, list):
        raise DeepAssuranceError("selector selection_reasons missing")
    reasons: list[dict[str, str]] = []
    for item in raw_reasons:
        if not isinstance(item, dict) or set(item) != {"tier", "requirement", "reason"}:
            raise DeepAssuranceError("selector reason shape invalid")
        if item["tier"] != "T3":
            continue
        if item["requirement"] not in requirements:
            raise DeepAssuranceError("selector reason references unselected T3 requirement")
        if not isinstance(item["reason"], str) or not item["reason"]:
            raise DeepAssuranceError("selector T3 reason missing")
        reasons.append(item)
    for requirement in requirements:
        if not any(item["requirement"] == requirement for item in reasons):
            raise DeepAssuranceError(
                f"selected T3 requirement lacks selection reason: {requirement}"
            )
    return sorted(requirements), sorted(
        reasons, key=lambda item: (item["requirement"], item["reason"])
    )


def build_assurance_plan(
    selector: dict[str, Any],
    candidate_head: str,
    policy: dict[str, Any],
    selection_policy: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(candidate_head, str) or SHA40.fullmatch(candidate_head) is None:
        raise DeepAssuranceError("candidate_head must be lowercase SHA-40")
    requirements, reasons = _validate_selector(selector, selection_policy)
    controls: set[str] = set()
    evidence_reasons: list[dict[str, Any]] = []
    mapping = policy["requirement_reason_controls"]
    for item in reasons:
        requirement = item["requirement"]
        reason = item["reason"]
        reason_map = mapping[requirement]
        selected = reason_map.get(reason)
        if selected is None:
            raise DeepAssuranceError(
                f"no deep-assurance mapping for {requirement} reason {reason}"
            )
        controls.update(selected)
        evidence_reasons.append(
            {
                "requirement": requirement,
                "reason": reason,
                "controls": sorted(selected),
            }
        )

    rendered_controls = [
        {
            "control_id": control_id,
            **policy["control_catalog"][control_id],
        }
        for control_id in sorted(controls)
    ]
    manual = any(not item["automatic"] for item in rendered_controls)
    material = {
        "plan_version": 1,
        "candidate_head": candidate_head,
        "t3_requirements": requirements,
        "selection_reasons": evidence_reasons,
        "controls": rendered_controls,
        "execution_model": policy["execution_model"],
    }
    return {
        "plan_version": 1,
        "plan_identity_sha256": _sha256_json(material),
        "manual_review_required": manual,
        "material": material,
    }


def validate_plan(plan: dict[str, Any]) -> None:
    if set(plan) != {
        "plan_version", "plan_identity_sha256", "manual_review_required", "material"
    }:
        raise DeepAssuranceError("assurance plan shape mismatch")
    if plan["plan_version"] != 1:
        raise DeepAssuranceError("unsupported assurance plan version")
    identity = plan["plan_identity_sha256"]
    material = plan["material"]
    if not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise DeepAssuranceError("assurance plan identity invalid")
    if not isinstance(material, dict) or _sha256_json(material) != identity:
        raise DeepAssuranceError("assurance plan self-integrity mismatch")
    controls = material.get("controls")
    if not isinstance(controls, list):
        raise DeepAssuranceError("assurance plan controls missing")
    manual = any(
        isinstance(item, dict) and item.get("automatic") is False for item in controls
    )
    if plan["manual_review_required"] is not manual:
        raise DeepAssuranceError("manual review flag disagrees with plan controls")


def evaluate_assurance(
    plan: dict[str, Any],
    evidence_runs: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    validate_plan(plan)
    if not isinstance(evidence_runs, list):
        raise DeepAssuranceError("evidence_runs must be a list")
    if len(evidence_runs) > policy["max_evidence_runs"]:
        raise DeepAssuranceError("assurance evidence count exceeds policy limit")

    material = plan["material"]
    candidate_head = material["candidate_head"]
    controls = material["controls"]
    automatic = {
        item["control_id"]: item for item in controls if item["automatic"] is True
    }
    manual_required = plan["manual_review_required"]

    if not automatic and not manual_required:
        if evidence_runs:
            raise DeepAssuranceError("unselected assurance evidence is forbidden")
        result_material = {
            "plan_identity_sha256": plan["plan_identity_sha256"],
            "status": "NOT_REQUIRED",
            "satisfied": True,
            "evidence_runs": [],
        }
        return {
            **result_material,
            "assurance_identity_sha256": _sha256_json(result_material),
        }

    seen_controls: set[str] = set()
    seen_runs: set[int] = set()
    normalized: list[dict[str, Any]] = []
    expected_fields = set(policy["exact_run_fields"])
    for item in evidence_runs:
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise DeepAssuranceError("assurance run evidence shape mismatch")
        control_id = item["control_id"]
        if control_id not in automatic:
            raise DeepAssuranceError(
                f"evidence supplied for unselected/non-automatic control: {control_id}"
            )
        if control_id in seen_controls:
            raise DeepAssuranceError(f"duplicate assurance control evidence: {control_id}")
        seen_controls.add(control_id)
        run_id = item["run_id"]
        if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
            raise DeepAssuranceError("assurance run_id must be positive integer")
        if run_id in seen_runs:
            raise DeepAssuranceError(f"duplicate assurance run id: {run_id}")
        seen_runs.add(run_id)
        expected = automatic[control_id]
        if item["workflow"] != expected["workflow_name"]:
            raise DeepAssuranceError(
                f"wrong workflow for {control_id}: {item['workflow']!r}"
            )
        if item["head_sha"] != candidate_head:
            raise DeepAssuranceError(f"stale/wrong-head assurance evidence: {control_id}")
        if item["conclusion"] != policy["required_conclusion"]:
            raise DeepAssuranceError(f"failed assurance evidence: {control_id}")
        normalized.append(dict(item))

    missing = sorted(set(automatic) - seen_controls)
    normalized.sort(key=lambda item: item["control_id"])
    if missing:
        status = "INCOMPLETE"
        satisfied = False
    elif manual_required:
        status = "MANUAL_REVIEW_REQUIRED"
        satisfied = False
    else:
        status = "PASS"
        satisfied = True

    result_material = {
        "plan_identity_sha256": plan["plan_identity_sha256"],
        "status": status,
        "satisfied": satisfied,
        "missing_controls": missing,
        "manual_review_required": manual_required,
        "evidence_runs": normalized,
    }
    return {
        **result_material,
        "assurance_identity_sha256": _sha256_json(result_material),
    }


def self_check(root: Path = ROOT) -> None:
    policy, selection, exact_head, security, evidence = _load_policies(root)
    validate_policy(policy, selection, exact_head, security, evidence)
    empty_selector = {
        "selector_version": 1,
        "t3_required": False,
        "t3_requirements": [],
        "selection_reasons": [],
    }
    plan = build_assurance_plan(
        empty_selector, "1" * 40, policy, selection
    )
    verdict = evaluate_assurance(plan, [], policy)
    if verdict["status"] != "NOT_REQUIRED" or verdict["satisfied"] is not True:
        raise DeepAssuranceError("empty T3 plan self-check failed")
    print("CERTIFICATION_DEEP_ASSURANCE_SELF_CHECK_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    try:
        if not args.self_check:
            raise DeepAssuranceError("only --self-check is exposed during ENG-06.3")
        self_check()
    except DeepAssuranceError as exc:
        print(f"CERTIFICATION_DEEP_ASSURANCE_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
