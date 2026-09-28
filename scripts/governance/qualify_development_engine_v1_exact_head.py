#!/usr/bin/env python3
"""Emit Development Engine V1 exact-head qualification material using ENG-06 controls."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AWU_PATH = ROOT / "engineering" / "work_units" / "ENG-09.4-WU02.json"
EXPECTED_WORKFLOW = "Development Engine V1 Exact Head Qualification"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class EngineV1ExactHeadQualificationError(ValueError):
    pass


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise EngineV1ExactHeadQualificationError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EngineV1ExactHeadQualificationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EngineV1ExactHeadQualificationError(f"{path} must contain an object")
    return value


def _git_head() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise EngineV1ExactHeadQualificationError(
            f"cannot resolve Git HEAD: {proc.stderr.strip()}"
        )
    head = proc.stdout.strip()
    if SHA40.fullmatch(head) is None:
        raise EngineV1ExactHeadQualificationError(f"invalid Git HEAD: {head!r}")
    return head


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EngineV1ExactHeadQualificationError(message)


def _workflow_identity(head: str) -> tuple[int, str, int]:
    run_raw = os.environ.get("GITHUB_RUN_ID")
    workflow = os.environ.get("GITHUB_WORKFLOW")
    attempt_raw = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    github_sha = os.environ.get("GITHUB_SHA")

    _require(run_raw is not None and run_raw.isdigit(), "GITHUB_RUN_ID missing/invalid")
    run_id = int(run_raw)
    _require(run_id > 0, "GITHUB_RUN_ID must be positive")
    _require(workflow == EXPECTED_WORKFLOW, f"unexpected workflow identity: {workflow!r}")
    _require(attempt_raw.isdigit() and int(attempt_raw) > 0, "GITHUB_RUN_ATTEMPT invalid")
    _require(github_sha == head, f"GITHUB_SHA does not equal checked-out HEAD: {github_sha!r}")
    return run_id, workflow, int(attempt_raw)


def _bound_paths(candidate_policy: dict[str, Any]) -> list[str]:
    evidence = candidate_policy.get("evidence_sources")
    _require(isinstance(evidence, dict) and len(evidence) == 8, "candidate evidence set drift")
    paths = [
        "config/governance/development_engine_v1_certification_policy_v1.json",
        "engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_CANDIDATE.json",
        "scripts/governance/validate_development_engine_v1_certification.py",
        "scripts/governance/selftest_development_engine_v1_certification.py",
        "engineering/work_units/ENG-09.4-WU02.json",
        "scripts/governance/qualify_development_engine_v1_exact_head.py",
        ".github/workflows/eng09-wu02-development-engine-v1-qualification.yml",
    ]
    paths.extend(binding["path"] for _, binding in sorted(evidence.items()))
    _require(len(paths) == 15 and len(set(paths)) == 15, "exact-head bound path set drift")
    return paths


def qualify() -> dict[str, Any]:
    candidate_validator = _module(
        "eng09_v1_candidate_validator",
        ROOT / "scripts/governance/validate_development_engine_v1_certification.py",
    )
    exact = _module(
        "eng09_exact_head",
        ROOT / "scripts/governance/validate_certification_exact_head_binding.py",
    )
    assurance = _module(
        "eng09_deep_assurance",
        ROOT / "scripts/governance/validate_certification_deep_assurance.py",
    )

    try:
        candidate = candidate_validator.validate_repository()
    except candidate_validator.EngineV1CertificationError as exc:
        raise EngineV1ExactHeadQualificationError(
            f"WU01 candidate validation failed: {exc}"
        ) from exc

    awu = _json(AWU_PATH)
    _require(awu.get("id") == "ENG-09.4-WU02", "active qualification AWU identity drift")
    _require(awu.get("status") == "IN_PROGRESS", "qualification AWU must be IN_PROGRESS")
    risk = awu.get("planning", {}).get("risk_class")
    _require(risk == "R2", f"qualification risk-class drift: {risk!r}")
    scope_base = awu.get("scope", {}).get("scope_base_sha")
    _require(
        isinstance(scope_base, str) and SHA40.fullmatch(scope_base) is not None,
        "qualification scope base invalid",
    )

    head = _git_head()
    run_id, workflow, run_attempt = _workflow_identity(head)

    exact_policy, lifecycle, evidence, proof, selection = exact._load_policies(ROOT)
    exact.validate_policy(exact_policy, lifecycle, evidence, proof, selection)

    (
        assurance_policy,
        assurance_selection,
        exact_policy_for_assurance,
        security_policy,
        assurance_evidence,
    ) = assurance._load_policies(ROOT)
    assurance.validate_policy(
        assurance_policy,
        assurance_selection,
        exact_policy_for_assurance,
        security_policy,
        assurance_evidence,
    )
    _require(
        selection == assurance_selection,
        "exact-head and deep-assurance selection policies disagree",
    )

    core = {
        "candidate_id": candidate["candidate_id"],
        "head_sha": head,
        "risk_class": risk,
    }
    required_t3: list[str] = []
    required_t4 = ["EXACT_HEAD_CERTIFICATION"]
    context = {
        "awu_id": awu["id"],
        "scope_base_sha": scope_base,
        "required_t3": required_t3,
        "required_t4": required_t4,
    }

    candidate_policy = _json(
        ROOT / "config/governance/development_engine_v1_certification_policy_v1.json"
    )
    paths = _bound_paths(candidate_policy)
    binding = exact.build_input_binding(
        core,
        paths,
        context,
        exact_policy,
        selection,
        root=ROOT,
    )
    exact.validate_input_binding(binding)

    ci_run = {
        "run_id": run_id,
        "workflow": workflow,
        "head_sha": head,
        "conclusion": "success",
    }
    bundle = exact.build_evidence_bundle(binding, [ci_run], exact_policy)
    exact.validate_evidence_bundle(bundle, binding, exact_policy)

    selector = {
        "selector_version": 1,
        "t3_required": False,
        "t3_requirements": [],
        "selection_reasons": [],
    }
    plan = assurance.build_assurance_plan(
        selector,
        head,
        assurance_policy,
        assurance_selection,
    )
    assurance.validate_plan(plan)
    assurance_verdict = assurance.evaluate_assurance(
        plan,
        [],
        assurance_policy,
    )
    _require(
        assurance_verdict.get("status") == "NOT_REQUIRED"
        and assurance_verdict.get("satisfied") is True,
        "unexpected deep-assurance verdict for R2 exact-head qualification",
    )

    gate = candidate.get("material", {}).get("certification_gate", {})
    _require(gate.get("certified") is False, "candidate was already marked certified")
    _require(
        gate.get("business_unlock_allowed") is False
        and gate.get("runtime_unlock_allowed") is False,
        "candidate already carries unlock authority",
    )
    blocker = candidate.get("material", {}).get("blocking_finding", {})
    _require(
        blocker.get("id") == "BOOT-FINDING-001"
        and blocker.get("observed") is True,
        "business-unlock blocker missing from candidate",
    )

    return {
        "schema_version": 1,
        "evidence_kind": "development_engine_v1_exact_head_qualification_v1",
        "status": "PASS_PENDING_ACTUAL_GITHUB_RUN_SUCCESS_CONFIRMATION",
        "candidate_id": candidate["candidate_id"],
        "candidate_core": core,
        "candidate_material_sha256": candidate["material_sha256"],
        "scope_base_sha": scope_base,
        "bound_paths": paths,
        "input_binding": binding,
        "exact_head_bundle": bundle,
        "deep_assurance_plan": plan,
        "deep_assurance_verdict": assurance_verdict,
        "required_t3": required_t3,
        "required_t4": required_t4,
        "workflow_run": {
            "run_id": run_id,
            "run_attempt": run_attempt,
            "workflow": workflow,
            "head_sha": head,
            "declared_conclusion": "success",
            "evidence_valid_only_if_actual_run_conclusion": "success",
        },
        "safety": {
            "business_unlock_allowed": False,
            "runtime_unlock_allowed": False,
            "lot45_merge_allowed": False,
            "lot46_unlock_allowed": False,
            "trade_allowed": False,
            "execution_allowed": False,
            "blocking_finding_id": "BOOT-FINDING-001",
        },
    }


def main() -> int:
    try:
        result = qualify()
    except (
        EngineV1ExactHeadQualificationError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"DEVELOPMENT_ENGINE_V1_EXACT_HEAD_INVALID: {exc}", file=sys.stderr)
        return 1
    print(
        "DEVELOPMENT_ENGINE_V1_EXACT_HEAD_QUALIFICATION="
        + json.dumps(result, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
