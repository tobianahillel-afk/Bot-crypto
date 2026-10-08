#!/usr/bin/env python3
"""Pure fail-closed ENG-06.5 certification promotion decision."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "certification_promotion_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class CertificationPromotionError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificationPromotionError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CertificationPromotionError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CertificationPromotionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CertificationPromotionError(f"value is not canonical JSON: {exc}") from exc


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _modules() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType]:
    lifecycle = _module(
        "promotion_lifecycle",
        ROOT / "scripts/governance/validate_certification_candidate_lifecycle.py",
    )
    exact = _module(
        "promotion_exact_head",
        ROOT / "scripts/governance/validate_certification_exact_head_binding.py",
    )
    assurance = _module(
        "promotion_deep_assurance",
        ROOT / "scripts/governance/validate_certification_deep_assurance.py",
    )
    provenance = _module(
        "promotion_provenance",
        ROOT / "scripts/governance/validate_certification_provenance.py",
    )
    return lifecycle, exact, assurance, provenance


def _source_policies(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "lifecycle": _json(ROOT / policy["lifecycle_policy_source"]),
        "exact_head": _json(ROOT / policy["exact_head_policy_source"]),
        "deep_assurance": _json(ROOT / policy["deep_assurance_policy_source"]),
        "provenance": _json(ROOT / policy["provenance_policy_source"]),
        "attestation": _json(ROOT / policy["attestation_transport_policy_source"]),
    }


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise CertificationPromotionError("unsupported promotion policy version")
    if policy.get("policy_kind") != "certification_promotion_v1":
        raise CertificationPromotionError("invalid promotion policy kind")
    if policy.get("semantics") != "PURE_FAIL_CLOSED_CERTIFICATION_PROMOTION_DECISION_NO_SIDE_EFFECTS":
        raise CertificationPromotionError("promotion semantics drift")
    expected_sources = {
        "lifecycle_policy_source":"config/governance/certification_candidate_lifecycle_v1.json",
        "exact_head_policy_source":"config/governance/certification_exact_head_binding_v1.json",
        "deep_assurance_policy_source":"config/governance/certification_deep_assurance_v1.json",
        "provenance_policy_source":"config/governance/certification_provenance_v1.json",
        "attestation_transport_policy_source":"config/governance/certification_attestation_transport_v1.json",
    }
    for key, expected in expected_sources.items():
        if policy.get(key) != expected:
            raise CertificationPromotionError(f"{key} drift")
    if policy.get("required_source_state") != "CERTIFICATION_READY":
        raise CertificationPromotionError("promotion source state must remain CERTIFICATION_READY")
    if policy.get("target_state") != "CERTIFIED":
        raise CertificationPromotionError("promotion target state must remain CERTIFIED")
    if policy.get("required_certification_verdict") != "PASS":
        raise CertificationPromotionError("promotion requires explicit PASS verdict")
    if policy.get("native_attestation_transport") != "GITHUB_NATIVE_ARTIFACT_ATTESTATION":
        raise CertificationPromotionError("native attestation transport identity drift")
    if policy.get("forbidden_candidate_ids") != ["ENG-06.4-ATTESTATION-PROBE"]:
        raise CertificationPromotionError("engineering probe exclusion drift")
    expected_fields = [
        "candidate_id","head_sha","risk_class","exact_head_bundle_identity_sha256",
        "assurance_identity_sha256","provenance_identity_sha256",
        "attestation_subject_sha256","status",
    ]
    if policy.get("certification_verdict_material_fields") != expected_fields:
        raise CertificationPromotionError("certification verdict material fields drift")
    forbidden = policy.get("forbidden_output_fields")
    if not isinstance(forbidden, list) or not forbidden:
        raise CertificationPromotionError("forbidden authority output fields missing")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise CertificationPromotionError("promotion path must remain zero-paid-cost")


def validate_attestation_evidence(
    evidence: dict[str, Any],
    candidate: dict[str, Any],
    provenance_identity: str,
    provenance_policy: dict[str, Any],
    policy: dict[str, Any],
) -> str:
    expected = {
        "attestation_version","transport","candidate_id","head_sha","risk_class",
        "subject_name","subject_sha256","attestation_id","attestation_url",
    }
    if not isinstance(evidence, dict) or set(evidence) != expected:
        raise CertificationPromotionError("native attestation evidence shape mismatch")
    if evidence["attestation_version"] != 1:
        raise CertificationPromotionError("unsupported native attestation evidence version")
    if evidence["transport"] != policy["native_attestation_transport"]:
        raise CertificationPromotionError("native attestation transport mismatch")
    for field in ("candidate_id","head_sha","risk_class"):
        if evidence[field] != candidate[field]:
            raise CertificationPromotionError(f"attestation candidate {field} mismatch")
    if evidence["subject_name"] != provenance_policy["attestation_subject"]["name"]:
        raise CertificationPromotionError("attestation subject name mismatch")
    if evidence["subject_sha256"] != provenance_identity:
        raise CertificationPromotionError("attestation subject digest differs from provenance identity")
    if SHA64.fullmatch(evidence["subject_sha256"]) is None:
        raise CertificationPromotionError("attestation subject digest invalid")
    attestation_id = evidence["attestation_id"]
    if not isinstance(attestation_id, str) or not attestation_id.strip():
        raise CertificationPromotionError("native attestation id missing")
    prefix = "https://github.com/tobianahillel-afk/Bot-crypto/attestations/"
    url = evidence["attestation_url"]
    if not isinstance(url, str) or not url.startswith(prefix):
        raise CertificationPromotionError("native attestation URL is not canonical")
    return attestation_id.strip()


def build_certification_verdict(
    candidate: dict[str, Any],
    exact_head_identity: str,
    assurance_identity: str,
    provenance_identity: str,
    attestation_subject: str,
    *,
    status: str = "PASS",
) -> dict[str, Any]:
    material = {
        "candidate_id":candidate["candidate_id"],
        "head_sha":candidate["head_sha"],
        "risk_class":candidate["risk_class"],
        "exact_head_bundle_identity_sha256":exact_head_identity,
        "assurance_identity_sha256":assurance_identity,
        "provenance_identity_sha256":provenance_identity,
        "attestation_subject_sha256":attestation_subject,
        "status":status,
    }
    return {
        "verdict_version":1,
        "verdict_identity_sha256":_sha256_json(material),
        "material":material,
    }


def validate_certification_verdict(
    verdict: dict[str, Any],
    candidate: dict[str, Any],
    exact_head_identity: str,
    assurance_identity: str,
    provenance_identity: str,
    attestation_subject: str,
    policy: dict[str, Any],
) -> None:
    if not isinstance(verdict, dict) or set(verdict) != {
        "verdict_version","verdict_identity_sha256","material"
    }:
        raise CertificationPromotionError("certification verdict shape mismatch")
    if verdict["verdict_version"] != 1:
        raise CertificationPromotionError("unsupported certification verdict version")
    identity = verdict["verdict_identity_sha256"]
    material = verdict["material"]
    if not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise CertificationPromotionError("certification verdict identity invalid")
    if not isinstance(material, dict) or list(material) != policy["certification_verdict_material_fields"]:
        raise CertificationPromotionError("certification verdict material field order/set drift")
    if _sha256_json(material) != identity:
        raise CertificationPromotionError("certification verdict self-integrity mismatch")
    expected = {
        "candidate_id":candidate["candidate_id"],
        "head_sha":candidate["head_sha"],
        "risk_class":candidate["risk_class"],
        "exact_head_bundle_identity_sha256":exact_head_identity,
        "assurance_identity_sha256":assurance_identity,
        "provenance_identity_sha256":provenance_identity,
        "attestation_subject_sha256":attestation_subject,
        "status":policy["required_certification_verdict"],
    }
    if material != expected:
        raise CertificationPromotionError("certification verdict is not bound to exact promotion evidence")


def _deny(
    candidate: dict[str, Any] | None,
    source_state: str | None,
    reasons: list[str],
) -> dict[str, Any]:
    result = {
        "promotion_version":1,
        "decision":"PROMOTION_DENIED",
        "source_state":source_state,
        "target_state":None,
        "candidate_id":candidate.get("candidate_id") if isinstance(candidate, dict) else None,
        "head_sha":candidate.get("head_sha") if isinstance(candidate, dict) else None,
        "reasons":sorted(set(reasons)),
        "evidence_identities":{},
    }
    return result


def evaluate_promotion(
    *,
    candidate: dict[str, Any],
    input_binding: dict[str, Any],
    exact_head_bundle: dict[str, Any],
    assurance_plan: dict[str, Any],
    assurance_verdict: dict[str, Any],
    provenance_envelope: dict[str, Any],
    native_attestation: dict[str, Any],
    certification_verdict: dict[str, Any],
    blockers: list[str],
    policy: dict[str, Any],
) -> dict[str, Any]:
    validate_policy(policy)
    modules = _modules()
    lifecycle, exact, assurance, provenance = modules
    sources = _source_policies(policy)
    lifecycle_policy = sources["lifecycle"]
    exact_policy = sources["exact_head"]
    assurance_policy = sources["deep_assurance"]
    provenance_policy = sources["provenance"]

    reasons: list[str] = []
    source_state = candidate.get("state") if isinstance(candidate, dict) else None
    try:
        life_policy, evidence_policy, selection_policy = lifecycle._load_policies()
        lifecycle.validate_policy(life_policy, evidence_policy, selection_policy)
        lifecycle.validate_candidate(candidate, life_policy, evidence_policy, selection_policy)
    except Exception:
        return _deny(candidate, source_state, ["INVALID_LIFECYCLE_CANDIDATE"])

    core = {
        "candidate_id":candidate["candidate_id"],
        "head_sha":candidate["head_sha"],
        "risk_class":candidate["risk_class"],
    }
    if candidate["candidate_id"] in policy["forbidden_candidate_ids"]:
        reasons.append("FORBIDDEN_ENGINEERING_TRANSPORT_PROBE")
    if source_state != policy["required_source_state"]:
        reasons.append("SOURCE_STATE_NOT_CERTIFICATION_READY")
    if not candidate["evidence_fresh"]:
        reasons.append("STALE_LIFECYCLE_EVIDENCE")
    if set(candidate["required_t3"]) != set(candidate["satisfied_t3"]):
        reasons.append("UNSATISFIED_T3_REQUIREMENTS")
    if set(candidate["required_t4"]) != set(candidate["satisfied_t4"]):
        reasons.append("UNSATISFIED_T4_REQUIREMENTS")
    if not isinstance(blockers, list) or any(not isinstance(x, str) or not x for x in blockers):
        reasons.append("INVALID_BLOCKER_SET")
    elif blockers:
        reasons.append("OPEN_BLOCKERS")

    try:
        exact.validate_input_binding(input_binding)
        if input_binding["material"].get("candidate") != core:
            raise CertificationPromotionError("input candidate mismatch")
        context = input_binding["material"].get("context")
        if not isinstance(context, dict):
            raise CertificationPromotionError("input context missing")
        if set(context.get("required_t3", [])) != set(candidate["required_t3"]):
            raise CertificationPromotionError("input T3 selection mismatch")
        if set(context.get("required_t4", [])) != set(candidate["required_t4"]):
            raise CertificationPromotionError("input T4 selection mismatch")
        exact.validate_evidence_bundle(exact_head_bundle, input_binding, exact_policy)
    except Exception:
        reasons.append("INVALID_EXACT_HEAD_EVIDENCE")

    assurance_identity = None
    try:
        assurance.validate_plan(assurance_plan)
        if assurance_plan["material"].get("candidate_head") != candidate["head_sha"]:
            raise CertificationPromotionError("assurance head mismatch")
        if set(assurance_plan["material"].get("t3_requirements", [])) != set(candidate["required_t3"]):
            raise CertificationPromotionError("assurance T3 selection mismatch")
        status, assurance_identity = provenance._validate_assurance_verdict(
            assurance_verdict,
            assurance_plan["plan_identity_sha256"],
        )
        if status not in {"PASS","NOT_REQUIRED"} or assurance_verdict.get("satisfied") is not True:
            raise CertificationPromotionError("deep assurance is not satisfied")
    except Exception:
        reasons.append("INVALID_DEEP_ASSURANCE")

    provenance_identity = None
    try:
        provenance.validate_provenance(provenance_envelope, provenance_policy)
        provenance_identity = provenance_envelope["provenance_identity_sha256"]
        material = provenance_envelope["material"]
        if material.get("candidate") != core:
            raise CertificationPromotionError("provenance candidate mismatch")
        if material.get("exact_input_identity_sha256") != input_binding["input_identity_sha256"]:
            raise CertificationPromotionError("provenance exact-input mismatch")
        deep = material.get("deep_assurance")
        if not isinstance(deep, dict):
            raise CertificationPromotionError("provenance assurance binding missing")
        if deep.get("plan_identity_sha256") != assurance_plan["plan_identity_sha256"]:
            raise CertificationPromotionError("provenance plan mismatch")
        if assurance_identity is None or deep.get("assurance_identity_sha256") != assurance_identity:
            raise CertificationPromotionError("provenance assurance mismatch")
        if material.get("workflow", {}).get("workflow_sha") != candidate["head_sha"]:
            raise CertificationPromotionError("provenance workflow head mismatch")
    except Exception:
        reasons.append("INVALID_CANONICAL_PROVENANCE")

    attestation_id = None
    if provenance_identity is not None:
        try:
            attestation_id = validate_attestation_evidence(
                native_attestation,
                core,
                provenance_identity,
                provenance_policy,
                policy,
            )
        except CertificationPromotionError:
            reasons.append("INVALID_NATIVE_ATTESTATION")
    else:
        reasons.append("INVALID_NATIVE_ATTESTATION")

    exact_identity = exact_head_bundle.get("bundle_identity_sha256") if isinstance(exact_head_bundle, dict) else None
    if (
        not isinstance(exact_identity, str)
        or SHA64.fullmatch(exact_identity) is None
        or assurance_identity is None
        or provenance_identity is None
    ):
        reasons.append("INCOMPLETE_CERTIFICATION_IDENTITIES")
    else:
        try:
            validate_certification_verdict(
                certification_verdict,
                core,
                exact_identity,
                assurance_identity,
                provenance_identity,
                native_attestation.get("subject_sha256") if isinstance(native_attestation, dict) else "",
                policy,
            )
        except CertificationPromotionError:
            reasons.append("INVALID_CERTIFICATION_VERDICT")

    if reasons:
        return _deny(candidate, source_state, reasons)

    after = dict(candidate)
    after["state"] = policy["target_state"]
    after["evidence_bindings"] = dict(candidate["evidence_bindings"])
    after["evidence_bindings"]["EXACT_HEAD_CERTIFICATION_EVIDENCE"] = "EXACT_GITHUB_ACTIONS_RUN"
    after["evidence_bindings"]["CERTIFICATION_VERDICT_PASS"] = "REPOSITORY_ARTIFACT"
    try:
        life_policy, evidence_policy, selection_policy = lifecycle._load_policies()
        lifecycle.validate_transition(
            candidate,
            after,
            life_policy,
            evidence_policy,
            selection_policy,
        )
    except Exception:
        return _deny(candidate, source_state, ["LIFECYCLE_CERTIFIED_TRANSITION_REJECTED"])

    result = {
        "promotion_version":1,
        "decision":"PROMOTION_ALLOWED",
        "source_state":source_state,
        "target_state":policy["target_state"],
        "candidate_id":candidate["candidate_id"],
        "head_sha":candidate["head_sha"],
        "reasons":[],
        "evidence_identities":{
            "exact_head_bundle_identity_sha256":exact_identity,
            "assurance_identity_sha256":assurance_identity,
            "provenance_identity_sha256":provenance_identity,
            "attestation_id":attestation_id,
            "certification_verdict_identity_sha256":certification_verdict["verdict_identity_sha256"],
        },
    }
    forbidden = set(policy["forbidden_output_fields"])
    if forbidden & set(result):
        raise CertificationPromotionError("promotion result leaked forbidden authority fields")
    return result


def synthetic_fixture(policy: dict[str, Any]) -> dict[str, Any]:
    lifecycle, exact, assurance, provenance = _modules()
    _, _, selection_policy = lifecycle._load_policies()
    exact_policy, *_ = exact._load_policies()
    assurance_policy, selection, *_ = assurance._load_policies()
    provenance_policy, *_ = provenance._load_policies()

    core = {
        "candidate_id":"ENG-06.5-PROMOTION-SELFTEST",
        "head_sha":"a" * 40,
        "risk_class":"R1",
    }
    required_t3: list[str] = []
    required_t4 = ["EXACT_HEAD_CERTIFICATION","PROVENANCE_CERTIFICATION"]
    candidate = {
        **core,
        "state":"CERTIFICATION_READY",
        "evidence_fresh":True,
        "evidence_bindings":{
            "CANDIDATE_REF_BOUND":"EXACT_GITHUB_REF",
            "VALIDATION_PASS_BOUND":"EXACT_GITHUB_ACTIONS_RUN",
            "ASSURANCE_SELECTION_BOUND":"REPOSITORY_ARTIFACT",
            "NO_OPEN_BLOCKER":"REPOSITORY_ARTIFACT",
        },
        "required_t3":required_t3,
        "satisfied_t3":list(required_t3),
        "required_t4":required_t4,
        "satisfied_t4":list(required_t4),
    }
    input_material = {
        "material_version":1,
        "candidate":core,
        "git_tree_sha":"b" * 40,
        "bound_blobs":[],
        "context":{
            "awu_id":"ENG-06.5-WU01",
            "scope_base_sha":"c" * 40,
            "required_t3":required_t3,
            "required_t4":sorted(required_t4),
        },
    }
    input_binding = {
        "binding_version":1,
        "input_identity_sha256":exact._sha256_json(input_material),
        "material":input_material,
    }
    exact_bundle = exact.build_evidence_bundle(
        input_binding,
        [{
            "run_id":7001,
            "workflow":"Synthetic Exact Head Certification",
            "head_sha":core["head_sha"],
            "conclusion":"success",
        }],
        exact_policy,
    )
    selector = {
        "selector_version":1,
        "t3_required":False,
        "t3_requirements":[],
        "selection_reasons":[],
    }
    assurance_plan = assurance.build_assurance_plan(
        selector,
        core["head_sha"],
        assurance_policy,
        selection,
    )
    assurance_verdict = assurance.evaluate_assurance(assurance_plan, [], assurance_policy)
    provenance_envelope = provenance.build_provenance(
        input_binding,
        assurance_plan,
        assurance_verdict,
        {
            "repository":"tobianahillel-afk/Bot-crypto",
            "workflow_path":".github/workflows/engineering-bootstrap.yml",
            "workflow_ref":"refs/heads/engineering/bootstrap-development-engine",
            "workflow_sha":core["head_sha"],
            "run_id":7002,
            "run_attempt":1,
        },
        [{
            "path":"synthetic/domain-integrity.json",
            "algorithm":"sha256",
            "digest":"d" * 64,
        }],
        provenance_policy,
        metadata={"notes":"SYNTHETIC_PROMOTION_SELFTEST_ONLY"},
    )
    provenance_identity = provenance_envelope["provenance_identity_sha256"]
    native_attestation = {
        "attestation_version":1,
        "transport":policy["native_attestation_transport"],
        **core,
        "subject_name":provenance_policy["attestation_subject"]["name"],
        "subject_sha256":provenance_identity,
        "attestation_id":"synthetic-attestation-7003",
        "attestation_url":"https://github.com/tobianahillel-afk/Bot-crypto/attestations/7003",
    }
    verdict = build_certification_verdict(
        core,
        exact_bundle["bundle_identity_sha256"],
        assurance_verdict["assurance_identity_sha256"],
        provenance_identity,
        native_attestation["subject_sha256"],
    )
    return {
        "candidate":candidate,
        "input_binding":input_binding,
        "exact_head_bundle":exact_bundle,
        "assurance_plan":assurance_plan,
        "assurance_verdict":assurance_verdict,
        "provenance_envelope":provenance_envelope,
        "native_attestation":native_attestation,
        "certification_verdict":verdict,
        "blockers":[],
    }


def self_check() -> None:
    policy = _json(POLICY_PATH)
    validate_policy(policy)
    fixture = synthetic_fixture(policy)
    result = evaluate_promotion(policy=policy, **fixture)
    if result["decision"] != "PROMOTION_ALLOWED" or result["target_state"] != "CERTIFIED":
        raise CertificationPromotionError(f"synthetic promotion did not pass: {result}")
    if set(policy["forbidden_output_fields"]) & set(result):
        raise CertificationPromotionError("self-check promotion output leaked authority")
    print("CERTIFICATION_PROMOTION_SELF_CHECK_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--request", type=Path)
    args = parser.parse_args()
    try:
        policy = _json(POLICY_PATH)
        validate_policy(policy)
        if args.self_check:
            self_check()
        else:
            request = _json(args.request)
            required = {
                "candidate","input_binding","exact_head_bundle","assurance_plan",
                "assurance_verdict","provenance_envelope","native_attestation",
                "certification_verdict","blockers",
            }
            if set(request) != required:
                raise CertificationPromotionError("promotion request shape mismatch")
            result = evaluate_promotion(policy=policy, **request)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    except (CertificationPromotionError, KeyError, TypeError, ValueError) as exc:
        print(f"CERTIFICATION_PROMOTION_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
