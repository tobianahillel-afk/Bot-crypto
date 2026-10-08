#!/usr/bin/env python3
"""Build and validate fail-closed exact-input proof-reuse fingerprints."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
POLICY_PATH=ROOT/"config"/"governance"/"proof_reuse_policy_v1.json"


class ProofReuseError(ValueError):
    pass


def _json(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise ProofReuseError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value,dict):
        raise ProofReuseError(f"{path} must contain an object")
    return value


def _canonical(value:Any)->bytes:
    try:
        text=json.dumps(
            value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False
        )
    except (TypeError,ValueError) as exc:
        raise ProofReuseError(f"value is not canonical-JSON encodable: {exc}") from exc
    return text.encode("utf-8")


def _sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value:Any)->str:
    return _sha256_bytes(_canonical(value))


def validate_policy(policy:dict[str,Any])->None:
    if policy.get("schema_version")!=1:
        raise ProofReuseError("unsupported proof reuse policy schema_version")
    if policy.get("policy_kind")!="proof_reuse_policy_v1":
        raise ProofReuseError("invalid proof reuse policy kind")
    if policy.get("semantics")!="EXACT_INPUT_CANONICAL_SHA256_FAIL_CLOSED":
        raise ProofReuseError("proof reuse semantics drift")
    reusable=policy.get("reusable_subjects")
    if not isinstance(reusable,dict) or set(reusable)!={"T1","T2"}:
        raise ProofReuseError("reusable subjects must be explicit T1/T2 allowlists")
    for tier,subjects in reusable.items():
        if not isinstance(subjects,list) or not subjects or len(subjects)!=len(set(subjects)):
            raise ProofReuseError(f"invalid reusable subject list for {tier}")
        if any(not isinstance(x,str) or not x for x in subjects):
            raise ProofReuseError(f"invalid reusable subject id for {tier}")
    if policy.get("forbidden_tiers")!=["T0","T3","T4"]:
        raise ProofReuseError("T0/T3/T4 must remain forbidden for reuse")
    forbidden=policy.get("forbidden_subject_ids")
    if not isinstance(forbidden,list) or "EXACT_HEAD_CERTIFICATION" not in forbidden:
        raise ProofReuseError("exact-head certification must remain non-reusable")
    if policy.get("required_result")!="PASS":
        raise ProofReuseError("only PASS proof reuse is permitted")
    if policy.get("environment_fields")!=[
        "python_implementation","python_version","platform","machine"
    ]:
        raise ProofReuseError("environment binding fields drift")
    max_files=policy.get("max_bound_files")
    max_params=policy.get("max_parameters_bytes")
    if not isinstance(max_files,int) or not 1<=max_files<=500:
        raise ProofReuseError("invalid max_bound_files")
    if not isinstance(max_params,int) or not 128<=max_params<=1024*1024:
        raise ProofReuseError("invalid max_parameters_bytes")


def subject_reusable(tier:str,subject_id:str,policy:dict[str,Any])->bool:
    if tier in policy["forbidden_tiers"]:
        return False
    if subject_id in policy["forbidden_subject_ids"]:
        return False
    return subject_id in policy["reusable_subjects"].get(tier,[])


def _safe_file(path_text:str,root:Path=ROOT)->Path:
    if not isinstance(path_text,str) or not path_text:
        raise ProofReuseError("bound file path must be non-empty string")
    rel=Path(path_text)
    if rel.is_absolute() or ".." in rel.parts:
        raise ProofReuseError(f"bound path escapes repository: {path_text!r}")
    path=root/rel
    try:
        if path.is_symlink():
            raise ProofReuseError(f"symlink binding forbidden: {path_text}")
        if not path.is_file():
            raise ProofReuseError(f"bound file missing or non-regular: {path_text}")
        resolved=path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError,ValueError) as exc:
        if isinstance(exc,ProofReuseError):
            raise
        raise ProofReuseError(f"unsafe bound file {path_text}: {exc}") from exc
    return path


def digest_files(paths:list[str],root:Path=ROOT)->list[dict[str,Any]]:
    if not isinstance(paths,list) or not paths:
        raise ProofReuseError("each proof file-binding group must be non-empty")
    if len(paths)!=len(set(paths)):
        raise ProofReuseError("duplicate bound file path")
    records=[]
    for path_text in sorted(paths):
        path=_safe_file(path_text,root)
        try:
            data=path.read_bytes()
        except OSError as exc:
            raise ProofReuseError(f"cannot read bound file {path_text}: {exc}") from exc
        records.append({
            "path":Path(path_text).as_posix(),
            "sha256":_sha256_bytes(data),
            "bytes":len(data),
        })
    return records


def current_environment()->dict[str,str]:
    return {
        "python_implementation":platform.python_implementation(),
        "python_version":platform.python_version(),
        "platform":sys.platform,
        "machine":platform.machine() or "unknown",
    }


def build_material(
    *,
    tier:str,
    subject_id:str,
    input_paths:list[str],
    policy_paths:list[str],
    implementation_paths:list[str],
    parameters:dict[str,Any],
    environment:dict[str,str],
    policy:dict[str,Any],
    root:Path=ROOT,
)->dict[str,Any]:
    if not subject_reusable(tier,subject_id,policy):
        raise ProofReuseError(f"subject is not reusable: {tier}:{subject_id}")
    if not isinstance(parameters,dict):
        raise ProofReuseError("parameters must be an object")
    if len(_canonical(parameters))>policy["max_parameters_bytes"]:
        raise ProofReuseError("proof parameters exceed policy size limit")
    expected_env=set(policy["environment_fields"])
    if not isinstance(environment,dict) or set(environment)!=expected_env:
        raise ProofReuseError("environment binding must exactly match policy fields")
    if any(not isinstance(v,str) or not v for v in environment.values()):
        raise ProofReuseError("environment binding values must be non-empty strings")
    total=len(input_paths)+len(policy_paths)+len(implementation_paths)
    if total>policy["max_bound_files"]:
        raise ProofReuseError(
            f"bound file count {total} exceeds policy limit {policy['max_bound_files']}"
        )
    return {
        "material_version":1,
        "subject":{"tier":tier,"id":subject_id},
        "inputs":digest_files(input_paths,root),
        "policies":digest_files(policy_paths,root),
        "implementations":digest_files(implementation_paths,root),
        "parameters":parameters,
        "environment":dict(sorted(environment.items())),
    }


def proof_key(material:dict[str,Any])->str:
    return _sha256_json(material)


def issue_proof(
    material:dict[str,Any],
    *,
    result:str,
    metadata:dict[str,Any]|None=None,
)->dict[str,Any]:
    if result not in {"PASS","FAIL"}:
        raise ProofReuseError("proof result must be PASS or FAIL")
    if metadata is None:
        metadata={}
    if not isinstance(metadata,dict):
        raise ProofReuseError("proof metadata must be an object")
    return {
        "schema_version":1,
        "proof_kind":"exact_input_reuse_proof_v1",
        "proof_key":proof_key(material),
        "result":result,
        "material":material,
        "metadata":metadata,
    }


def validate_candidate_integrity(proof:dict[str,Any],policy:dict[str,Any])->None:
    if proof.get("schema_version")!=1 or proof.get("proof_kind")!="exact_input_reuse_proof_v1":
        raise ProofReuseError("candidate proof shape/version invalid")
    material=proof.get("material")
    if not isinstance(material,dict):
        raise ProofReuseError("candidate proof material missing")
    key=proof.get("proof_key")
    if not isinstance(key,str) or len(key)!=64:
        raise ProofReuseError("candidate proof key malformed")
    if proof_key(material)!=key:
        raise ProofReuseError("candidate proof self-integrity mismatch")
    subject=material.get("subject")
    if not isinstance(subject,dict):
        raise ProofReuseError("candidate subject missing")
    tier=subject.get("tier")
    subject_id=subject.get("id")
    if not isinstance(tier,str) or not isinstance(subject_id,str):
        raise ProofReuseError("candidate subject invalid")
    if not subject_reusable(tier,subject_id,policy):
        raise ProofReuseError(f"candidate subject is not reusable: {tier}:{subject_id}")
    if proof.get("result")!=policy["required_result"]:
        raise ProofReuseError("candidate proof result is not reusable PASS")
    metadata=proof.get("metadata")
    if not isinstance(metadata,dict):
        raise ProofReuseError("candidate proof metadata must be an object")


def evaluate_reuse(
    candidate:dict[str,Any],
    expected_material:dict[str,Any],
    policy:dict[str,Any],
)->dict[str,Any]:
    validate_candidate_integrity(candidate,policy)
    expected=proof_key(expected_material)
    if candidate["proof_key"]!=expected:
        return {
            "reusable":False,
            "reason":"EXACT_INPUT_KEY_MISMATCH",
            "candidate_key":candidate["proof_key"],
            "expected_key":expected,
        }
    if candidate["material"]!=expected_material:
        raise ProofReuseError("canonical-key collision or non-canonical material mismatch")
    return {
        "reusable":True,
        "reason":"EXACT_INPUT_MATCH",
        "candidate_key":candidate["proof_key"],
        "expected_key":expected,
    }


def _self_check(policy:dict[str,Any])->None:
    validate_policy(policy)
    if subject_reusable("T4","EXACT_HEAD_CERTIFICATION",policy):
        raise ProofReuseError("T4 unexpectedly reusable")
    first={"a":1,"b":[2,3]}
    second={"b":[2,3],"a":1}
    if _sha256_json(first)!=_sha256_json(second):
        raise ProofReuseError("canonical JSON ordering is not deterministic")
    print("PROOF_REUSE_SELF_CHECK_PASS")


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check",action="store_true")
    parser.add_argument("--request",type=Path)
    parser.add_argument("--candidate",type=Path)
    args=parser.parse_args()
    try:
        policy=_json(POLICY_PATH)
        validate_policy(policy)
        if args.self_check:
            _self_check(policy)
            return 0
        if args.request is None:
            raise ProofReuseError("--request is required unless --self-check is used")
        request=_json(args.request)
        material=build_material(
            tier=request["tier"],
            subject_id=request["subject_id"],
            input_paths=request["input_paths"],
            policy_paths=request["policy_paths"],
            implementation_paths=request["implementation_paths"],
            parameters=request.get("parameters",{}),
            environment=request.get("environment",current_environment()),
            policy=policy,
        )
        if args.candidate is None:
            print(json.dumps({
                "eligible":True,
                "proof_key":proof_key(material),
                "material":material,
            },sort_keys=True,separators=(",",":")))
            return 0
        candidate=_json(args.candidate)
        print(json.dumps(
            evaluate_reuse(candidate,material,policy),
            sort_keys=True,separators=(",",":"),
        ))
        return 0
    except (ProofReuseError,KeyError,TypeError) as exc:
        print(f"PROOF_REUSE_INVALID: {exc}",file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
