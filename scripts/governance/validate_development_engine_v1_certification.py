#!/usr/bin/env python3
"""Validate the bounded Development Engine V1 pre-T4 certification candidate."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "development_engine_v1_certification_policy_v1.json"
CANDIDATE_PATH = ROOT / "engineering" / "DEVELOPMENT_ENGINE_V1_CERTIFICATION_CANDIDATE.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class EngineV1CertificationError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EngineV1CertificationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EngineV1CertificationError(f"{path} must contain an object")
    return value


def _canonical(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise EngineV1CertificationError(f"value is not canonical JSON: {exc}") from exc
    return text.encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _head_blob_sha(path: str, root: Path = ROOT) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise EngineV1CertificationError(f"unsafe evidence path: {path}")
    proc = subprocess.run(
        ["git", "rev-parse", f"HEAD:{candidate.as_posix()}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise EngineV1CertificationError(
            f"cannot resolve exact HEAD blob for {path}: {proc.stderr.strip()}"
        )
    blob = proc.stdout.strip()
    if SHA40.fullmatch(blob) is None:
        raise EngineV1CertificationError(f"invalid Git blob SHA for {path}: {blob!r}")
    return blob


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EngineV1CertificationError(message)


def validate_policy(policy: dict[str, Any]) -> None:
    _require(policy.get("schema_version") == 1, "unsupported V1 certification policy version")
    _require(
        policy.get("policy_kind") == "development_engine_v1_certification_policy_v1",
        "invalid V1 certification policy kind",
    )
    _require(
        policy.get("semantics")
        == "BOUNDED_EXACT_EVIDENCE_PRE_T4_CANDIDATE_FAIL_CLOSED",
        "V1 certification semantics drift",
    )
    _require(policy.get("engine_version") == "V1", "engine version drift")
    _require(
        policy.get("candidate_kind")
        == "development_engine_v1_certification_candidate_v1",
        "candidate kind drift",
    )
    _require(
        policy.get("candidate_status")
        == "CERTIFICATION_CANDIDATE_READY_FOR_EXACT_HEAD_QUALIFICATION",
        "candidate status floor drift",
    )
    _require(
        policy.get("forbidden_candidate_statuses") == ["CERTIFIED"],
        "CERTIFIED floor drift",
    )
    _require(
        policy.get("state_source") == "config/governance/project_state.json",
        "state source drift",
    )

    expected_keys = {
        "lot45_profile",
        "security_engine",
        "mandatory_cost",
        "cold_start",
        "interruption_recovery",
        "critical_r3_bypass",
        "lot45_pilot",
        "timing_budget",
    }
    sources = policy.get("evidence_sources")
    _require(
        isinstance(sources, dict) and set(sources) == expected_keys,
        "evidence source set drift",
    )
    paths: set[str] = set()
    for name, binding in sources.items():
        _require(
            isinstance(binding, dict) and set(binding) == {"path", "blob_sha"},
            f"invalid evidence binding {name}",
        )
        path = binding["path"]
        blob = binding["blob_sha"]
        _require(
            isinstance(path, str) and path and path not in paths,
            f"invalid or duplicate evidence path {name}",
        )
        _require(
            isinstance(blob, str) and SHA40.fullmatch(blob) is not None,
            f"invalid evidence blob SHA {name}",
        )
        paths.add(path)

    _require(
        policy.get("fast_budgets_ms")
        == {
            "T0": 250,
            "T1": 500,
            "T2": 750,
            "TOTAL": 1500,
            "COLD_START": 1000,
            "INTERRUPTION_RECOVERY": 1000,
            "RECOVERY_SELFTEST": 1000,
        },
        "FAST budget floor drift",
    )
    assembly = policy.get("assembly")
    _require(isinstance(assembly, dict), "assembly binding missing")
    _require(
        assembly.get("work_unit_id") == "ENG-09.4-WU01",
        "assembly work-unit drift",
    )
    _require(
        assembly.get("base_head_sha")
        == "77d581d2d16643ffa636fcc336148fa57c43c60c",
        "assembly base head drift",
    )
    _require(
        assembly.get("pre_assembly_bootstrap")
        == {
            "run_id": 36457626752,
            "conclusion": "success",
            "head_sha": "77d581d2d16643ffa636fcc336148fa57c43c60c",
        },
        "pre-assembly bootstrap binding drift",
    )
    _require(
        policy.get("required_later_t4") == ["EXACT_HEAD_CERTIFICATION"],
        "later T4 floor drift",
    )
    _require(
        policy.get("required_r3_floor")
        == {
            "t3": ["RISK_EXECUTION_ASSURANCE"],
            "t4": ["EXACT_HEAD_CERTIFICATION", "R3_FULL_CERTIFICATION_CHAIN"],
        },
        "R3 assurance floor drift",
    )


def load_evidence(
    policy: dict[str, Any], root: Path = ROOT
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    payloads: dict[str, dict[str, Any]] = {}
    blobs: dict[str, str] = {}
    for name, binding in policy["evidence_sources"].items():
        path = root / binding["path"]
        payloads[name] = _json(path)
        observed = _head_blob_sha(binding["path"], root)
        _require(
            observed == binding["blob_sha"],
            f"evidence blob drift for {name}: {observed}",
        )
        blobs[name] = observed
    return payloads, blobs


def validate_state(state: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    _require(
        state.get("project", {}).get("canonical_name") == "Crypto Quant Bot V3.1-Ops",
        "project identity drift",
    )
    business = state.get("business_track")
    safety = state.get("safety")
    _require(
        isinstance(business, dict) and isinstance(safety, dict),
        "state safety/business sections missing",
    )
    lock = policy["safety_lock"]
    _require(
        business.get("development_status") == lock["business_development"],
        "business hold drift",
    )
    _require(
        business.get("next_lot", {}).get("status") == lock["lot46_status"],
        "Lot46 lock drift",
    )
    candidate = business.get("candidate")
    _require(isinstance(candidate, dict), "business candidate state missing")
    expected_business = policy["business_candidate"]
    for key in ("lot", "pr", "status", "observed_head", "merged"):
        _require(
            candidate.get(key) == expected_business[key],
            f"Lot45 candidate drift: {key}",
        )

    for key in (
        "runtime_max",
        "trade_allowed",
        "execution_allowed",
        "live_execution",
        "leverage",
        "withdrawals",
    ):
        _require(safety.get(key) == lock[key], f"safety lock drift: {key}")

    finding = next(
        (
            item
            for item in state.get("findings", [])
            if isinstance(item, dict)
            and item.get("id") == policy["required_blocker"]["id"]
        ),
        None,
    )
    _require(isinstance(finding, dict), "BOOT-FINDING-001 missing")
    for key, value in policy["required_blocker"].items():
        _require(finding.get(key) == value, f"blocking finding drift: {key}")
    return finding


def validate_temporary_workflow_absent(
    evidence: dict[str, Any], root: Path = ROOT
) -> str:
    temp = evidence.get("temporary_qualification_workflow")
    _require(isinstance(temp, dict), "WU13 temporary-workflow evidence missing")
    path = temp.get("path")
    _require(isinstance(path, str) and path, "WU13 temporary workflow path invalid")
    _require(
        temp.get("removal_required_after_evidence_capture") is True,
        "WU13 cleanup requirement drift",
    )
    _require(
        not (root / path).exists(),
        f"temporary WU13 workflow still present: {path}",
    )
    return path


def validate_evidence(
    payloads: dict[str, dict[str, Any]],
    policy: dict[str, Any],
    root: Path = ROOT,
) -> None:
    verdicts = policy["expected_verdicts"]
    lock = policy["safety_lock"]

    profile = payloads["lot45_profile"]
    _require(
        profile.get("evidence_kind")
        == "eng09_wu13_lot45_candidate_profile_evidence_v1",
        "WU13 evidence kind drift",
    )
    _require(profile.get("status") == verdicts["lot45_profile_status"], "WU13 status drift")
    _require(
        profile.get("verdict") == verdicts["lot45_profile_verdict"],
        "WU13 verdict drift",
    )
    cp = profile.get("candidate_profile", {})
    for key in (
        "execution_allowed",
        "active_registry_adopted",
        "production_selector_visible",
        "generic_runner_executable",
        "mutation_execution_performed",
    ):
        _require(cp.get(key) is False, f"WU13 candidate profile safety drift: {key}")
    ps = profile.get("safety", {})
    _require(
        ps.get("business_development") == lock["business_development"],
        "WU13 business hold drift",
    )
    _require(ps.get("lot46_status") == lock["lot46_status"], "WU13 Lot46 lock drift")
    _require(
        ps.get("trade_allowed") is False and ps.get("execution_allowed") is False,
        "WU13 execution safety drift",
    )
    _require(
        ps.get("candidate_branch_mutated") is False
        and ps.get("candidate_merged") is False,
        "WU13 candidate mutation/merge drift",
    )
    validate_temporary_workflow_absent(profile, root)

    security = payloads["security_engine"]
    _require(security.get("verdict") == verdicts["security_engine"], "security verdict drift")
    _require(
        security.get("business_unlock_status")
        == verdicts["security_business_unlock_status"],
        "security business-unlock status drift",
    )
    _require(
        security.get("blocking_finding_id") == policy["required_blocker"]["id"],
        "security blocker id drift",
    )
    for key in ("zero_cost", "least_privilege", "approved_exact_action_pins", "risk_proportional"):
        _require(security.get(key) is True, f"security requirement failed: {key}")
    external = security.get("external_protection", {})
    _require(external.get("overall_status") == "UNPROTECTED", "external protection drift")
    _require(external.get("business_unlock_allowed") is False, "security unlocked business")
    _require(
        external.get("manual_admin_action_required") is True,
        "manual protection action requirement missing",
    )

    cost = payloads["mandatory_cost"]
    _require(
        cost.get("evidence_kind") == "mandatory_cost_zero_live_evidence_v1",
        "mandatory-cost evidence kind drift",
    )
    repo = cost.get("repository_observation", {})
    _require(
        repo.get("visibility") == "public" and repo.get("private") is False,
        "public repository cost premise drift",
    )
    facts = cost.get("github_actions_billing_observation", {}).get("facts", {})
    for key in (
        "standard_public_runner_usage_free",
        "standard_public_runner_usage_unlimited",
        "code_scanning_free_for_public_repositories",
        "dependency_review_free_for_public_repositories",
    ):
        _require(facts.get(key) is True, f"mandatory-cost fact failed: {key}")
    _require(facts.get("larger_runners_always_billed") is True, "larger runner fact missing")
    storage = cost.get("engine_storage_observation", {})
    _require(
        storage.get("paid_cache_limit_expansion_required") is False,
        "paid cache expansion became mandatory",
    )
    claim = cost.get("claim_scope", {})
    _require(claim.get("mandatory_paid_requirement_only") is True, "cost claim scope drift")
    _require(claim.get("account_wide_no_bill_claim") is False, "forbidden no-bill claim")
    _require(claim.get("optional_paid_products_excluded") is True, "paid options not excluded")

    cold = payloads["cold_start"]
    _require(cold.get("verdict") == verdicts["cold_start"], "cold-start verdict drift")
    cm = cold.get("metrics", {})
    _require(
        cm.get("elapsed_ms", 10**9) <= policy["fast_budgets_ms"]["COLD_START"],
        "cold-start budget exceeded",
    )
    _require(cm.get("conversational_context_required") is False, "cold start needs chat")
    _require(cm.get("implicit_expansion") == "FORBIDDEN", "cold-start expansion drift")

    recovery = payloads["interruption_recovery"]
    _require(recovery.get("verdict") == verdicts["interruption_recovery"], "recovery verdict drift")
    rm = recovery.get("recovery_metrics", {})
    _require(
        rm.get("elapsed_ms", 10**9) <= policy["fast_budgets_ms"]["INTERRUPTION_RECOVERY"],
        "recovery budget exceeded",
    )
    _require(rm.get("conversational_context_required") is False, "recovery needs chat")
    _require(rm.get("state_auto_healed") is False, "recovery auto-healed state")
    _require(rm.get("write_authorized") is False, "recovery authorized write")
    _require(
        rm.get("required_before_write") == "LIVE_GIT_REVERIFY_REQUIRED",
        "live-Git reverify floor drift",
    )
    rs = recovery.get("adversarial_selftest", {})
    _require(
        rs.get("elapsed_ms", 10**9) <= policy["fast_budgets_ms"]["RECOVERY_SELFTEST"],
        "recovery selftest budget exceeded",
    )

    r3 = payloads["critical_r3_bypass"]
    _require(r3.get("verdict") == verdicts["critical_r3_bypass"], "R3 verdict drift")
    _require(r3.get("same_head_evidence") is True, "R3 same-head floor missing")
    assurance = r3.get("r3_assurance", {})
    _require(assurance.get("required_t3") == policy["required_r3_floor"]["t3"], "R3 T3 drift")
    _require(assurance.get("required_t4") == policy["required_r3_floor"]["t4"], "R3 T4 drift")
    for key in ("selector_cross_layer_selftest", "exact_head", "deep_assurance"):
        _require(assurance.get(key, {}).get("status") == "PASS", f"R3 component failed: {key}")
    _require(
        all(value is False for value in r3.get("mandatory_cost", {}).values()),
        "R3 path introduced paid requirement",
    )

    pilot = payloads["lot45_pilot"]
    _require(pilot.get("pilot_verdict") == verdicts["lot45_pilot"], "pilot verdict drift")
    _require(pilot.get("business_authorization") == "NONE", "pilot authorized business")
    _require(pilot.get("candidate_ready_for_merge") is False, "pilot marked merge-ready")
    live = pilot.get("live_git", {})
    expected_business = policy["business_candidate"]
    _require(live.get("pr") == expected_business["pr"], "pilot PR drift")
    _require(live.get("state") == "open" and live.get("merged") is False, "pilot PR drift")
    _require(live.get("head_sha") == expected_business["observed_head"], "pilot head drift")
    p_safety = pilot.get("safety", {})
    _require(
        p_safety.get("business_development") == lock["business_development"],
        "pilot business hold drift",
    )
    _require(p_safety.get("lot46") == lock["lot46_status"], "pilot Lot46 drift")
    _require(
        p_safety.get("trade_allowed") is False and p_safety.get("execution_allowed") is False,
        "pilot execution safety drift",
    )

    timing = payloads["timing_budget"]
    _require(timing.get("policy_kind") == "validation_timing_budget_v1", "timing kind drift")
    _require(
        timing.get("semantics") == "ROUTINE_PATH_MEASURED_ELAPSED_FAIL_CLOSED",
        "timing semantics drift",
    )
    budgets = timing.get("budgets_ms", {})
    for key in ("T0", "T1", "T2", "TOTAL"):
        _require(budgets.get(key) == policy["fast_budgets_ms"][key], f"budget drift: {key}")
    applicability = timing.get("applicability", {})
    _require(applicability.get("routine_path") is True, "routine timing scope missing")
    for key in (
        "pytest_invoked",
        "full_suite_executed",
        "network_used",
        "deep_assurance_executed",
        "certification_executed",
    ):
        _require(applicability.get(key) is False, f"routine applicability drift: {key}")
    observed = timing.get("calibration_reference", {}).get("observed_ms", {})
    for key in ("T0", "T1", "T2", "TOTAL"):
        _require(
            isinstance(observed.get(key), (int, float)) and observed[key] <= budgets[key],
            f"FAST calibration exceeded: {key}",
        )


def build_material(
    policy: dict[str, Any],
    state: dict[str, Any],
    payloads: dict[str, dict[str, Any]],
    blobs: dict[str, str],
    root: Path = ROOT,
) -> dict[str, Any]:
    validate_policy(policy)
    finding = validate_state(state, policy)
    validate_evidence(payloads, policy, root)
    timing = payloads["timing_budget"]
    cold = payloads["cold_start"]
    recovery = payloads["interruption_recovery"]
    evidence_bindings = {
        name: {
            "path": policy["evidence_sources"][name]["path"],
            "blob_sha": blobs[name],
        }
        for name in sorted(policy["evidence_sources"])
    }
    return {
        "material_version": 1,
        "engine_version": "V1",
        "assembly": copy.deepcopy(policy["assembly"]),
        "policy_sha256": _sha256_json(policy),
        "evidence_bindings": evidence_bindings,
        "derived_verdicts": {
            "SAFE": True,
            "FAST": True,
            "ZERO_COST": True,
            "SECURITY": True,
            "LOT45_PILOT_READ_ONLY": True,
        },
        "fast": {
            "budgets_ms": copy.deepcopy(policy["fast_budgets_ms"]),
            "routine_calibration_ms": copy.deepcopy(
                timing["calibration_reference"]["observed_ms"]
            ),
            "cold_start_ms": cold["metrics"]["elapsed_ms"],
            "interruption_recovery_ms": recovery["recovery_metrics"]["elapsed_ms"],
            "recovery_selftest_ms": recovery["adversarial_selftest"]["elapsed_ms"],
        },
        "safety_lock": copy.deepcopy(policy["safety_lock"]),
        "business_candidate": copy.deepcopy(policy["business_candidate"]),
        "blocking_finding": {
            key: finding[key]
            for key in ("id", "code", "observed", "must_be_resolved_before")
        },
        "cleanup": {
            "temporary_workflow_path": payloads["lot45_profile"][
                "temporary_qualification_workflow"
            ]["path"],
            "temporary_workflow_present": False,
        },
        "certification_gate": {
            "required_later_t4": copy.deepcopy(policy["required_later_t4"]),
            "exact_head_t4_executed": False,
            "certified": False,
            "business_unlock_allowed": False,
            "runtime_unlock_allowed": False,
        },
    }


def expected_candidate(
    policy: dict[str, Any],
    state: dict[str, Any],
    payloads: dict[str, dict[str, Any]],
    blobs: dict[str, str],
    root: Path = ROOT,
) -> dict[str, Any]:
    material = build_material(policy, state, payloads, blobs, root)
    digest = _sha256_json(material)
    return {
        "schema_version": 1,
        "candidate_kind": policy["candidate_kind"],
        "status": policy["candidate_status"],
        "candidate_id": f"DEV_ENGINE_V1:{digest}",
        "material_sha256": digest,
        "material": material,
    }


def validate_candidate(candidate: dict[str, Any], expected: dict[str, Any]) -> None:
    _require(candidate.get("schema_version") == 1, "candidate schema drift")
    _require(
        candidate.get("candidate_kind")
        == "development_engine_v1_certification_candidate_v1",
        "candidate kind drift",
    )
    _require(
        candidate.get("status")
        == "CERTIFICATION_CANDIDATE_READY_FOR_EXACT_HEAD_QUALIFICATION",
        "candidate is not pre-T4 ready",
    )
    _require(candidate.get("status") != "CERTIFIED", "WU01 cannot emit CERTIFIED")
    material_hash = candidate.get("material_sha256")
    _require(
        isinstance(material_hash, str) and SHA256.fullmatch(material_hash) is not None,
        "candidate material hash malformed",
    )
    _require(
        candidate.get("candidate_id") == f"DEV_ENGINE_V1:{material_hash}",
        "candidate id/hash binding mismatch",
    )
    _require(
        isinstance(candidate.get("material"), dict)
        and _sha256_json(candidate["material"]) == material_hash,
        "candidate material self-integrity mismatch",
    )
    gate = candidate["material"].get("certification_gate", {})
    _require(gate.get("certified") is False, "candidate falsely claims CERTIFIED")
    _require(gate.get("exact_head_t4_executed") is False, "candidate falsely claims T4")
    _require(gate.get("business_unlock_allowed") is False, "candidate unlocks business")
    _require(gate.get("runtime_unlock_allowed") is False, "candidate unlocks runtime")
    _require(candidate == expected, "candidate differs from deterministic expected material")


def validate_repository(root: Path = ROOT) -> dict[str, Any]:
    policy = _json(root / "config/governance/development_engine_v1_certification_policy_v1.json")
    validate_policy(policy)
    state = _json(root / policy["state_source"])
    payloads, blobs = load_evidence(policy, root)
    expected = expected_candidate(policy, state, payloads, blobs, root)
    candidate = _json(
        root / "engineering/DEVELOPMENT_ENGINE_V1_CERTIFICATION_CANDIDATE.json"
    )
    validate_candidate(candidate, expected)
    return candidate


def main() -> int:
    try:
        candidate = validate_repository()
    except (EngineV1CertificationError, KeyError, TypeError) as exc:
        print(f"DEVELOPMENT_ENGINE_V1_CANDIDATE_INVALID: {exc}", file=sys.stderr)
        return 1
    print(
        "DEVELOPMENT_ENGINE_V1_CANDIDATE_VALID "
        f"id={candidate['candidate_id']} status={candidate['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
