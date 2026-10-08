#!/usr/bin/env python3
"""Pure ENG-06.6 post-merge tree-equivalence and certification-reuse verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "certification_post_merge_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class CertificationPostMergeError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificationPostMergeError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CertificationPostMergeError(f"{path} must contain an object")
    return value


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
        raise CertificationPostMergeError(f"value is not canonical JSON: {exc}") from exc


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise CertificationPostMergeError("unsupported post-merge policy version")
    if policy.get("policy_kind") != "certification_post_merge_v1":
        raise CertificationPostMergeError("invalid post-merge policy kind")
    if policy.get("semantics") != "TREE_EQUIVALENCE_REUSE_OR_BOUNDED_REVALIDATION_NO_SIDE_EFFECTS":
        raise CertificationPostMergeError("post-merge semantics drift")
    expected_sources = {
        "promotion_policy_source":"config/governance/certification_promotion_v1.json",
        "exact_head_policy_source":"config/governance/certification_exact_head_binding_v1.json",
        "provenance_policy_source":"config/governance/certification_provenance_v1.json",
        "proof_reuse_policy_source":"config/governance/proof_reuse_policy_v1.json",
    }
    for key, expected in expected_sources.items():
        if policy.get(key) != expected:
            raise CertificationPostMergeError(f"{key} drift")
    if policy.get("target_branch") != "main":
        raise CertificationPostMergeError("post-merge target branch must remain main")
    if policy.get("allowed_merge_methods") != ["MERGE","SQUASH","REBASE"]:
        raise CertificationPostMergeError("allowed merge method set/order drift")
    if policy.get("reuse_decision") != "POST_MERGE_VERIFIED_REUSE":
        raise CertificationPostMergeError("reuse decision drift")
    if policy.get("revalidation_decision") != "REVALIDATION_REQUIRED":
        raise CertificationPostMergeError("revalidation decision drift")
    if policy.get("revalidation_scope") != "RECOMPUTE_DIFF_IMPACT_AND_TIERS":
        raise CertificationPostMergeError("bounded revalidation scope drift")
    if policy.get("require_exact_tree_equivalence") is not True:
        raise CertificationPostMergeError("exact tree equivalence must remain mandatory")
    forbidden = policy.get("forbidden_output_fields")
    if not isinstance(forbidden, list) or not forbidden:
        raise CertificationPostMergeError("forbidden authority output set missing")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise CertificationPostMergeError("post-merge path must remain zero-paid-cost")


def _validate_promotion(result: dict[str, Any]) -> tuple[str, str, dict[str, str]]:
    expected = {
        "promotion_version","decision","source_state","target_state","candidate_id",
        "head_sha","reasons","evidence_identities",
    }
    if not isinstance(result, dict) or set(result) != expected:
        raise CertificationPostMergeError("promotion result shape mismatch")
    if result["promotion_version"] != 1:
        raise CertificationPostMergeError("unsupported promotion result version")
    if result["decision"] != "PROMOTION_ALLOWED" or result["target_state"] != "CERTIFIED":
        raise CertificationPostMergeError("source promotion is not an allowed CERTIFIED transition")
    if result["source_state"] != "CERTIFICATION_READY" or result["reasons"] != []:
        raise CertificationPostMergeError("source promotion lifecycle state/reasons invalid")
    candidate_id = result["candidate_id"]
    head = result["head_sha"]
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CertificationPostMergeError("promotion candidate id invalid")
    if not isinstance(head, str) or SHA40.fullmatch(head) is None:
        raise CertificationPostMergeError("promotion head must be lowercase SHA-40")
    identities = result["evidence_identities"]
    required = {
        "exact_head_bundle_identity_sha256",
        "assurance_identity_sha256",
        "provenance_identity_sha256",
        "attestation_id",
        "certification_verdict_identity_sha256",
    }
    if not isinstance(identities, dict) or set(identities) != required:
        raise CertificationPostMergeError("promotion evidence identity set mismatch")
    for key in required - {"attestation_id"}:
        if not isinstance(identities[key], str) or SHA64.fullmatch(identities[key]) is None:
            raise CertificationPostMergeError(f"promotion identity invalid: {key}")
    if not isinstance(identities["attestation_id"], str) or not identities["attestation_id"].strip():
        raise CertificationPostMergeError("promotion attestation id missing")
    return candidate_id, head, identities


def _validate_certified_record(
    record: dict[str, Any],
    promotion: dict[str, Any],
    candidate_id: str,
    head: str,
    identities: dict[str, str],
) -> None:
    expected = {
        "candidate_id","candidate_head_sha","candidate_tree_sha","promotion_result_sha256",
        "exact_head_bundle_identity_sha256","provenance_identity_sha256",
        "certification_verdict_identity_sha256",
    }
    if not isinstance(record, dict) or set(record) != expected:
        raise CertificationPostMergeError("certified candidate record shape mismatch")
    if record["candidate_id"] != candidate_id or record["candidate_head_sha"] != head:
        raise CertificationPostMergeError("certified candidate identity differs from promotion")
    if SHA40.fullmatch(record["candidate_tree_sha"]) is None:
        raise CertificationPostMergeError("certified candidate tree must be lowercase SHA-40")
    if record["promotion_result_sha256"] != _sha256_json(promotion):
        raise CertificationPostMergeError("promotion result hash binding mismatch")
    if record["exact_head_bundle_identity_sha256"] != identities["exact_head_bundle_identity_sha256"]:
        raise CertificationPostMergeError("exact-head identity binding mismatch")
    if record["provenance_identity_sha256"] != identities["provenance_identity_sha256"]:
        raise CertificationPostMergeError("provenance identity binding mismatch")
    if record["certification_verdict_identity_sha256"] != identities["certification_verdict_identity_sha256"]:
        raise CertificationPostMergeError("certification verdict identity binding mismatch")


def _validate_merge_record(
    merge: dict[str, Any],
    candidate_id: str,
    candidate_head: str,
    policy: dict[str, Any],
) -> list[str]:
    expected = {
        "target_branch","merged_head_sha","merged_tree_sha","source_candidate_id",
        "source_candidate_head_sha","pr_number","merge_method",
    }
    if not isinstance(merge, dict) or set(merge) != expected:
        raise CertificationPostMergeError("merge record shape mismatch")
    reasons: list[str] = []
    if merge["target_branch"] != policy["target_branch"]:
        reasons.append("WRONG_TARGET_BRANCH")
    for field in ("merged_head_sha","merged_tree_sha","source_candidate_head_sha"):
        if not isinstance(merge[field], str) or SHA40.fullmatch(merge[field]) is None:
            reasons.append(f"INVALID_{field.upper()}")
    if merge["source_candidate_id"] != candidate_id:
        reasons.append("SOURCE_CANDIDATE_ID_MISMATCH")
    if merge["source_candidate_head_sha"] != candidate_head:
        reasons.append("SOURCE_CANDIDATE_HEAD_MISMATCH")
    if not isinstance(merge["pr_number"], int) or isinstance(merge["pr_number"], bool) or merge["pr_number"] <= 0:
        reasons.append("INVALID_PR_NUMBER")
    if merge["merge_method"] not in policy["allowed_merge_methods"]:
        reasons.append("UNSUPPORTED_MERGE_METHOD")
    return reasons


def _revalidation(
    candidate_id: str | None,
    merged_head: str | None,
    reasons: list[str],
    policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "post_merge_version":1,
        "decision":policy["revalidation_decision"],
        "candidate_id":candidate_id,
        "merged_head_sha":merged_head,
        "reasons":sorted(set(reasons)),
        "reuse_prior_certification":False,
        "post_merge_identity_sha256":None,
        "revalidation_scope":policy["revalidation_scope"],
        "full_regression_rerun":None,
        "t4_rerun":None,
    }


def evaluate_post_merge(
    *,
    promotion_result: dict[str, Any],
    certified_candidate: dict[str, Any],
    merge_record: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    validate_policy(policy)
    try:
        candidate_id, head, identities = _validate_promotion(promotion_result)
        _validate_certified_record(certified_candidate, promotion_result, candidate_id, head, identities)
    except CertificationPostMergeError:
        candidate_id = promotion_result.get("candidate_id") if isinstance(promotion_result, dict) else None
        merged_head = merge_record.get("merged_head_sha") if isinstance(merge_record, dict) else None
        return _revalidation(candidate_id, merged_head, ["INVALID_PRIOR_CERTIFICATION_RECORD"], policy)

    try:
        reasons = _validate_merge_record(merge_record, candidate_id, head, policy)
    except CertificationPostMergeError:
        return _revalidation(candidate_id, None, ["INVALID_MERGE_RECORD"], policy)

    if not reasons and merge_record["merged_tree_sha"] != certified_candidate["candidate_tree_sha"]:
        reasons.append("MERGED_TREE_DIFFERS_FROM_CERTIFIED_TREE")
    if reasons:
        return _revalidation(candidate_id, merge_record.get("merged_head_sha"), reasons, policy)

    material = {
        "material_version":1,
        "candidate_id":candidate_id,
        "certified_candidate_head_sha":head,
        "certified_candidate_tree_sha":certified_candidate["candidate_tree_sha"],
        "promotion_result_sha256":certified_candidate["promotion_result_sha256"],
        "provenance_identity_sha256":certified_candidate["provenance_identity_sha256"],
        "certification_verdict_identity_sha256":certified_candidate["certification_verdict_identity_sha256"],
        "merge":{
            "target_branch":merge_record["target_branch"],
            "merged_head_sha":merge_record["merged_head_sha"],
            "merged_tree_sha":merge_record["merged_tree_sha"],
            "source_candidate_id":merge_record["source_candidate_id"],
            "source_candidate_head_sha":merge_record["source_candidate_head_sha"],
            "pr_number":merge_record["pr_number"],
            "merge_method":merge_record["merge_method"],
        },
    }
    identity = _sha256_json(material)
    result = {
        "post_merge_version":1,
        "decision":policy["reuse_decision"],
        "candidate_id":candidate_id,
        "merged_head_sha":merge_record["merged_head_sha"],
        "reasons":[],
        "reuse_prior_certification":True,
        "post_merge_identity_sha256":identity,
        "revalidation_scope":None,
        "full_regression_rerun":False,
        "t4_rerun":False,
    }
    if set(policy["forbidden_output_fields"]) & set(result):
        raise CertificationPostMergeError("post-merge result leaked forbidden authority fields")
    return result


def synthetic_fixture() -> dict[str, Any]:
    promotion = {
        "promotion_version":1,
        "decision":"PROMOTION_ALLOWED",
        "source_state":"CERTIFICATION_READY",
        "target_state":"CERTIFIED",
        "candidate_id":"ENG-06.6-POST-MERGE-SELFTEST",
        "head_sha":"a" * 40,
        "reasons":[],
        "evidence_identities":{
            "exact_head_bundle_identity_sha256":"1" * 64,
            "assurance_identity_sha256":"2" * 64,
            "provenance_identity_sha256":"3" * 64,
            "attestation_id":"synthetic-attestation-1",
            "certification_verdict_identity_sha256":"4" * 64,
        },
    }
    certified = {
        "candidate_id":promotion["candidate_id"],
        "candidate_head_sha":promotion["head_sha"],
        "candidate_tree_sha":"b" * 40,
        "promotion_result_sha256":_sha256_json(promotion),
        "exact_head_bundle_identity_sha256":"1" * 64,
        "provenance_identity_sha256":"3" * 64,
        "certification_verdict_identity_sha256":"4" * 64,
    }
    merge = {
        "target_branch":"main",
        "merged_head_sha":"c" * 40,
        "merged_tree_sha":certified["candidate_tree_sha"],
        "source_candidate_id":certified["candidate_id"],
        "source_candidate_head_sha":certified["candidate_head_sha"],
        "pr_number":66,
        "merge_method":"SQUASH",
    }
    return {"promotion_result":promotion,"certified_candidate":certified,"merge_record":merge}


def self_check() -> None:
    policy = _json(POLICY_PATH)
    validate_policy(policy)
    fixture = synthetic_fixture()
    result = evaluate_post_merge(policy=policy, **fixture)
    if result["decision"] != policy["reuse_decision"]:
        raise CertificationPostMergeError(f"synthetic exact-tree reuse failed: {result}")
    if result["full_regression_rerun"] is not False or result["t4_rerun"] is not False:
        raise CertificationPostMergeError("exact tree reuse unexpectedly requests redundant rerun")
    if set(policy["forbidden_output_fields"]) & set(result):
        raise CertificationPostMergeError("post-merge self-check leaked authority")
    print("CERTIFICATION_POST_MERGE_SELF_CHECK_PASS")


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
            if set(request) != {"promotion_result","certified_candidate","merge_record"}:
                raise CertificationPostMergeError("post-merge request shape mismatch")
            result = evaluate_post_merge(policy=policy, **request)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    except (CertificationPostMergeError, KeyError, TypeError, ValueError) as exc:
        print(f"CERTIFICATION_POST_MERGE_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
