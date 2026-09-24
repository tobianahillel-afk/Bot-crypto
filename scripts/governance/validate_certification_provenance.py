#!/usr/bin/env python3
"""Validate ENG-06.4 canonical certification provenance semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class CertificationProvenanceError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificationProvenanceError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CertificationProvenanceError(f"{path} must contain an object")
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
        raise CertificationProvenanceError(f"value is not canonical JSON: {exc}") from exc
    return rendered.encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load_policies(root: Path = ROOT) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    policy = _json(root / "config/governance/certification_provenance_v1.json")
    lifecycle = _json(root / policy["lifecycle_policy_source"])
    exact_head = _json(root / policy["exact_head_policy_source"])
    assurance = _json(root / policy["deep_assurance_policy_source"])
    evidence = _json(root / policy["evidence_policy_source"])
    return policy, lifecycle, exact_head, assurance, evidence


def validate_policy(
    policy: dict[str, Any],
    lifecycle: dict[str, Any],
    exact_head: dict[str, Any],
    assurance: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    if policy.get("schema_version") != 1:
        raise CertificationProvenanceError("unsupported provenance policy version")
    if policy.get("policy_kind") != "certification_provenance_v1":
        raise CertificationProvenanceError("invalid provenance policy kind")
    if policy.get("semantics") != (
        "CANONICAL_PROVENANCE_ENVELOPE_PRESERVES_DOMAIN_INTEGRITY_DIGESTS"
    ):
        raise CertificationProvenanceError("provenance semantics drift")
    expected_sources = {
        "lifecycle_policy_source": "config/governance/certification_candidate_lifecycle_v1.json",
        "exact_head_policy_source": "config/governance/certification_exact_head_binding_v1.json",
        "deep_assurance_policy_source": "config/governance/certification_deep_assurance_v1.json",
        "evidence_policy_source": "engineering/AGENT_CAPABILITIES.json",
    }
    for key, expected in expected_sources.items():
        if policy.get(key) != expected:
            raise CertificationProvenanceError(f"{key} drift")
    if policy.get("canonical_repository") != "tobianahillel-afk/Bot-crypto":
        raise CertificationProvenanceError("canonical repository drift")
    if policy.get("provenance_hash_algorithm") != "sha256":
        raise CertificationProvenanceError("provenance hash algorithm drift")
    if policy.get("domain_digest_algorithms") != ["sha256"]:
        raise CertificationProvenanceError("domain digest algorithm policy drift")
    subject = policy.get("attestation_subject")
    if subject != {
        "name": "certification-provenance-envelope.json",
        "digest_algorithm": "sha256",
    }:
        raise CertificationProvenanceError("attestation subject contract drift")
    if policy.get("workflow_identity_fields") != [
        "repository","workflow_path","workflow_ref","workflow_sha","run_id","run_attempt"
    ]:
        raise CertificationProvenanceError("workflow identity field contract drift")
    if policy.get("domain_integrity_fields") != ["path","algorithm","digest"]:
        raise CertificationProvenanceError("domain-integrity field contract drift")
    if not isinstance(policy.get("max_domain_integrity_refs"), int) or not 1 <= policy["max_domain_integrity_refs"] <= 1024:
        raise CertificationProvenanceError("invalid domain integrity reference limit")

    if lifecycle.get("policy_kind") != "certification_candidate_lifecycle_v1":
        raise CertificationProvenanceError("lifecycle source identity drift")
    if exact_head.get("policy_kind") != "certification_exact_head_binding_v1":
        raise CertificationProvenanceError("exact-head source identity drift")
    if assurance.get("policy_kind") != "certification_deep_assurance_v1":
        raise CertificationProvenanceError("deep-assurance source identity drift")
    if "EXACT_GITHUB_ACTIONS_RUN" not in evidence.get("evidence_classes", {}):
        raise CertificationProvenanceError("agent exact-run evidence class missing")


def _candidate_from_input_binding(binding: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if not isinstance(binding, dict) or set(binding) != {
        "binding_version","input_identity_sha256","material"
    }:
        raise CertificationProvenanceError("exact-input binding shape mismatch")
    if binding["binding_version"] != 1:
        raise CertificationProvenanceError("unsupported exact-input binding version")
    material = binding["material"]
    identity = binding["input_identity_sha256"]
    if not isinstance(material, dict) or not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise CertificationProvenanceError("exact-input binding identity invalid")
    if _sha256_json(material) != identity:
        raise CertificationProvenanceError("exact-input binding self-integrity mismatch")
    candidate = material.get("candidate")
    if not isinstance(candidate, dict) or set(candidate) != {
        "candidate_id","head_sha","risk_class"
    }:
        raise CertificationProvenanceError("exact-input candidate missing")
    if not isinstance(candidate["candidate_id"], str) or SAFE_ID.fullmatch(candidate["candidate_id"]) is None:
        raise CertificationProvenanceError("invalid candidate id")
    if not isinstance(candidate["head_sha"], str) or SHA40.fullmatch(candidate["head_sha"]) is None:
        raise CertificationProvenanceError("invalid candidate head")
    return candidate, identity


def _validate_assurance_plan(plan: dict[str, Any]) -> tuple[str, str]:
    if not isinstance(plan, dict) or set(plan) != {
        "plan_version","plan_identity_sha256","manual_review_required","material"
    }:
        raise CertificationProvenanceError("deep-assurance plan shape mismatch")
    if plan["plan_version"] != 1:
        raise CertificationProvenanceError("unsupported assurance plan version")
    identity = plan["plan_identity_sha256"]
    material = plan["material"]
    if not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise CertificationProvenanceError("assurance plan identity invalid")
    if not isinstance(material, dict) or _sha256_json(material) != identity:
        raise CertificationProvenanceError("assurance plan self-integrity mismatch")
    head = material.get("candidate_head")
    if not isinstance(head, str) or SHA40.fullmatch(head) is None:
        raise CertificationProvenanceError("assurance plan candidate head invalid")
    return head, identity


def _validate_assurance_verdict(
    verdict: dict[str, Any],
    plan_identity: str,
) -> tuple[str, str]:
    if not isinstance(verdict, dict):
        raise CertificationProvenanceError("assurance verdict missing")
    identity = verdict.get("assurance_identity_sha256")
    if not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise CertificationProvenanceError("assurance verdict identity invalid")
    material = {
        key: value
        for key, value in verdict.items()
        if key != "assurance_identity_sha256"
    }
    if _sha256_json(material) != identity:
        raise CertificationProvenanceError("assurance verdict self-integrity mismatch")
    if verdict.get("plan_identity_sha256") != plan_identity:
        raise CertificationProvenanceError("assurance verdict is bound to a different plan")
    if verdict.get("satisfied") is not True:
        raise CertificationProvenanceError("unsatisfied assurance cannot produce provenance")
    status = verdict.get("status")
    if status not in {"PASS","NOT_REQUIRED"}:
        raise CertificationProvenanceError(
            f"non-certifiable assurance status: {status!r}"
        )
    return status, identity


def _validate_workflow_identity(
    workflow: dict[str, Any],
    candidate_head: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(workflow, dict) or list(workflow) != policy["workflow_identity_fields"]:
        raise CertificationProvenanceError("workflow identity shape/order mismatch")
    if workflow["repository"] != policy["canonical_repository"]:
        raise CertificationProvenanceError("workflow repository mismatch")
    path = workflow["workflow_path"]
    if not isinstance(path, str) or not path.startswith(".github/workflows/") or ".." in Path(path).parts:
        raise CertificationProvenanceError("workflow path is not repository-safe")
    ref = workflow["workflow_ref"]
    if not isinstance(ref, str) or not (
        ref.startswith("refs/heads/") or ref.startswith("refs/tags/")
    ):
        raise CertificationProvenanceError("workflow ref must be an explicit Git ref")
    sha = workflow["workflow_sha"]
    if sha != candidate_head:
        raise CertificationProvenanceError("workflow SHA must equal candidate head")
    run_id = workflow["run_id"]
    attempt = workflow["run_attempt"]
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise CertificationProvenanceError("workflow run_id invalid")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt <= 0:
        raise CertificationProvenanceError("workflow run_attempt invalid")
    return dict(workflow)


def _domain_refs(refs: list[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(refs, list) or not refs:
        raise CertificationProvenanceError("at least one domain integrity reference is required")
    if len(refs) > policy["max_domain_integrity_refs"]:
        raise CertificationProvenanceError("domain integrity reference count exceeds limit")
    fields = set(policy["domain_integrity_fields"])
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in refs:
        if not isinstance(item, dict) or set(item) != fields:
            raise CertificationProvenanceError("domain integrity reference shape mismatch")
        path = item["path"]
        if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
            raise CertificationProvenanceError(f"unsafe domain integrity path: {path!r}")
        path = Path(path).as_posix()
        if path in seen:
            raise CertificationProvenanceError(f"duplicate domain integrity path: {path}")
        seen.add(path)
        if item["algorithm"] not in policy["domain_digest_algorithms"]:
            raise CertificationProvenanceError("domain digest algorithm not allowed")
        digest = item["digest"]
        if not isinstance(digest, str) or SHA64.fullmatch(digest) is None:
            raise CertificationProvenanceError("domain digest must be lowercase SHA-256")
        normalized.append({"path":path,"algorithm":item["algorithm"],"digest":digest})
    return sorted(normalized,key=lambda item:item["path"])


def build_provenance(
    input_binding: dict[str, Any],
    assurance_plan: dict[str, Any],
    assurance_verdict: dict[str, Any],
    workflow_identity: dict[str, Any],
    domain_integrity_refs: list[dict[str, Any]],
    policy: dict[str, Any],
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate, input_identity = _candidate_from_input_binding(input_binding)
    assurance_head, plan_identity = _validate_assurance_plan(assurance_plan)
    if assurance_head != candidate["head_sha"]:
        raise CertificationProvenanceError(
            "assurance plan and exact-input binding target different candidate heads"
        )
    assurance_status, assurance_identity = _validate_assurance_verdict(
        assurance_verdict, plan_identity
    )
    workflow = _validate_workflow_identity(
        workflow_identity, candidate["head_sha"], policy
    )
    refs = _domain_refs(domain_integrity_refs, policy)
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise CertificationProvenanceError("provenance metadata must be an object")

    material = {
        "material_version":1,
        "candidate":candidate,
        "exact_input_identity_sha256":input_identity,
        "deep_assurance":{
            "plan_identity_sha256":plan_identity,
            "assurance_identity_sha256":assurance_identity,
            "status":assurance_status,
        },
        "workflow":workflow,
        "domain_integrity_refs":refs,
    }
    identity = _sha256_json(material)
    subject = {
        "name":policy["attestation_subject"]["name"],
        "digest":{"sha256":identity},
    }
    return {
        "schema_version":1,
        "provenance_kind":"certification_provenance_envelope_v1",
        "provenance_identity_sha256":identity,
        "attestation_subject":subject,
        "material":material,
        "metadata":metadata,
    }


def validate_provenance(envelope: dict[str, Any], policy: dict[str, Any]) -> None:
    if not isinstance(envelope, dict) or set(envelope) != {
        "schema_version","provenance_kind","provenance_identity_sha256",
        "attestation_subject","material","metadata"
    }:
        raise CertificationProvenanceError("provenance envelope shape mismatch")
    if envelope["schema_version"] != 1 or envelope["provenance_kind"] != (
        "certification_provenance_envelope_v1"
    ):
        raise CertificationProvenanceError("provenance envelope version/kind invalid")
    material = envelope["material"]
    identity = envelope["provenance_identity_sha256"]
    if not isinstance(material, dict) or not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise CertificationProvenanceError("provenance envelope identity invalid")
    if _sha256_json(material) != identity:
        raise CertificationProvenanceError("provenance envelope self-integrity mismatch")
    expected_subject = {
        "name":policy["attestation_subject"]["name"],
        "digest":{"sha256":identity},
    }
    if envelope["attestation_subject"] != expected_subject:
        raise CertificationProvenanceError("attestation subject does not match provenance identity")
    if not isinstance(envelope["metadata"], dict):
        raise CertificationProvenanceError("provenance metadata must be an object")
    refs = material.get("domain_integrity_refs")
    if not isinstance(refs, list) or _domain_refs(refs, policy) != refs:
        raise CertificationProvenanceError("domain integrity references are not canonical")


def self_check(root: Path = ROOT) -> None:
    policy, lifecycle, exact_head, assurance, evidence = _load_policies(root)
    validate_policy(policy, lifecycle, exact_head, assurance, evidence)
    left={"a":1,"b":["x","y"]}
    right={"b":["x","y"],"a":1}
    if _sha256_json(left) != _sha256_json(right):
        raise CertificationProvenanceError("canonical provenance hashing is unstable")
    print("CERTIFICATION_PROVENANCE_SELF_CHECK_PASS")


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check",action="store_true")
    args=parser.parse_args()
    try:
        if not args.self_check:
            raise CertificationProvenanceError("only --self-check is exposed during ENG-06.4-WU01")
        self_check()
    except CertificationProvenanceError as exc:
        print(f"CERTIFICATION_PROVENANCE_INVALID: {exc}",file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
