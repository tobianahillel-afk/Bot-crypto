#!/usr/bin/env python3
"""Validate and emit the ENG-06.4 native GitHub attestation transport probe."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "certification_attestation_transport_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class AttestationTransportError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AttestationTransportError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AttestationTransportError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AttestationTransportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _provenance() -> ModuleType:
    return _module(
        "attestation_transport_provenance",
        ROOT / "scripts" / "governance" / "validate_certification_provenance.py",
    )


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise AttestationTransportError("unsupported transport policy version")
    if policy.get("policy_kind") != "certification_attestation_transport_v1":
        raise AttestationTransportError("invalid transport policy kind")
    if policy.get("semantics") != "NATIVE_GITHUB_ATTESTATION_TRANSPORT_ONLY_NO_PROMOTION":
        raise AttestationTransportError("transport semantics drift")
    expected_sources = {
        "provenance_policy_source":"config/governance/certification_provenance_v1.json",
        "action_pin_registry_source":"config/governance/action_pin_registry_v1.json",
        "workflow_permission_policy_source":"config/governance/workflow_permission_policy_v1.json",
        "action_supply_chain_policy_source":"config/governance/action_supply_chain_policy_v1.json",
    }
    for key, expected in expected_sources.items():
        if policy.get(key) != expected:
            raise AttestationTransportError(f"{key} drift")
    if policy.get("workflow_path") != ".github/workflows/certification-provenance.yml":
        raise AttestationTransportError("transport workflow path drift")
    if policy.get("action") != {
        "repository":"actions/attest",
        "source_ref":"v4.2.2",
        "approved_commit_sha":"1e69f48acb82d1966a394da916b4c1698aa569d6",
        "license":"MIT",
    }:
        raise AttestationTransportError("actions/attest evidence drift")
    if policy.get("allowed_ref") != "refs/heads/engineering/bootstrap-development-engine":
        raise AttestationTransportError("transport ref must remain engineering-only")
    if policy.get("permissions") != {"read":["contents"],"write":["id-token","attestations"]}:
        raise AttestationTransportError("least-privilege transport permissions drift")
    if policy.get("subject_name") != "certification-provenance-envelope.json":
        raise AttestationTransportError("attestation subject name drift")
    if policy.get("predicate_type") != (
        "https://github.com/tobianahillel-afk/Bot-crypto/attestations/"
        "certification-provenance/v1"
    ):
        raise AttestationTransportError("predicate type drift")
    if policy.get("probe") != {
        "candidate_id":"ENG-06.4-ATTESTATION-PROBE",
        "risk_class":"R2",
        "assurance_status":"NOT_REQUIRED",
        "domain_integrity_path":"config/governance/certification_provenance_v1.json",
        "awu_id":"ENG-06.4-WU02",
    }:
        raise AttestationTransportError("engineering probe identity drift")
    if policy.get("transport") != {
        "push_to_registry":False,
        "create_storage_record":False,
        "show_summary":False,
    }:
        raise AttestationTransportError("transport must remain non-registry and low-noise")
    if policy.get("forbidden_write_scopes") != [
        "actions","artifact-metadata","checks","contents","packages","pull-requests","security-events"
    ]:
        raise AttestationTransportError("forbidden write scope set drift")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise AttestationTransportError("attestation transport must remain zero-paid-cost")


def validate_action_registry(policy: dict[str, Any]) -> None:
    registry = _json(ROOT / policy["action_pin_registry_source"])
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise AttestationTransportError("action pin registry entries missing")
    matching = [x for x in entries if isinstance(x, dict) and x.get("repository") == "actions/attest"]
    if len(matching) != 1:
        raise AttestationTransportError("actions/attest must have one registry entry")
    entry = matching[0]
    if entry.get("license") != "MIT" or entry.get("public") is not True or entry.get("archived") is not False:
        raise AttestationTransportError("actions/attest repository evidence invalid")
    if entry.get("legacy_replacements") != {}:
        raise AttestationTransportError("actions/attest needs no legacy replacement")
    pins = entry.get("approved_pins")
    if not isinstance(pins, list) or len(pins) != 1:
        raise AttestationTransportError("actions/attest must have exactly one approved pin")
    action = policy["action"]
    expected = {
        "source_ref":action["source_ref"],
        "ref_object_type":"commit",
        "ref_object_sha":action["approved_commit_sha"],
        "approved_commit_sha":action["approved_commit_sha"],
        "license_url":"https://raw.githubusercontent.com/actions/attest/v4.2.2/LICENSE",
    }
    if pins[0] != expected:
        raise AttestationTransportError("actions/attest approved pin drift")


def validate_permission_policy(policy: dict[str, Any]) -> None:
    permissions = _json(ROOT / policy["workflow_permission_policy_source"])
    approvals = permissions.get("approved_write_scopes")
    if not isinstance(approvals, list):
        raise AttestationTransportError("permission approvals missing")
    workflow = policy["workflow_path"]
    selected = [item for item in approvals if isinstance(item, dict) and item.get("workflow") == workflow]
    scopes = sorted(item.get("scope") for item in selected)
    if scopes != sorted(policy["permissions"]["write"]):
        raise AttestationTransportError(f"transport write approvals mismatch: {scopes}")
    if len(selected) != len(scopes):
        raise AttestationTransportError("duplicate transport write approval")
    for item in selected:
        rationale = item.get("rationale")
        if not isinstance(rationale, str) or len(rationale.strip()) < 20:
            raise AttestationTransportError("transport write approval rationale missing")


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AttestationTransportError(f"workflow missing {label}: {needle}")


def validate_workflow(policy: dict[str, Any], text: str) -> None:
    action = policy["action"]
    _require(text, f"actions/attest@{action['approved_commit_sha']} # v4.2.2", "exact actions/attest pin")
    _require(text, "permissions:\n  contents: read\n  id-token: write\n  attestations: write\n", "least-privilege permissions")
    _require(text, "if: github.ref == 'refs/heads/engineering/bootstrap-development-engine'", "engineering-only job guard")
    _require(text, f"subject-name: {policy['subject_name']}", "subject name")
    _require(text, "subject-digest: sha256:${{ steps.probe.outputs.subject_sha256 }}", "canonical subject digest")
    _require(text, f"predicate-type: {policy['predicate_type']}", "predicate type")
    _require(text, "predicate-path: ${{ runner.temp }}/certification-provenance-envelope.json", "predicate path")
    for key in ("push-to-registry: false","create-storage-record: false","show-summary: false"):
        _require(text, key, key)
    for scope in policy["forbidden_write_scopes"]:
        if f"{scope}: write" in text:
            raise AttestationTransportError(f"forbidden workflow write scope: {scope}")
    for token in ("GO_LOT45","GO_LOT46","BUSINESS_DEVELOPMENT_UNLOCK","promotion_verdict","T4_CERTIFIED"):
        if token in text:
            raise AttestationTransportError(f"business/certification claim forbidden in transport: {token}")


def validate_documents(policy: dict[str, Any]) -> None:
    validate_policy(policy)
    validate_action_registry(policy)
    validate_permission_policy(policy)
    validate_workflow(policy, (ROOT / policy["workflow_path"]).read_text(encoding="utf-8"))


def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AttestationTransportError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise AttestationTransportError(f"cannot hash {path}: {exc}") from exc


def build_probe(
    *,
    head_sha: str,
    tree_sha: str,
    workflow_ref: str,
    run_id: int,
    run_attempt: int,
    domain_digest: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    validate_policy(policy)
    if SHA40.fullmatch(head_sha) is None or SHA40.fullmatch(tree_sha) is None:
        raise AttestationTransportError("probe head/tree must be lowercase 40-hex")
    if workflow_ref != policy["allowed_ref"]:
        raise AttestationTransportError("probe workflow ref is not the engineering ref")
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise AttestationTransportError("probe run id invalid")
    if not isinstance(run_attempt, int) or isinstance(run_attempt, bool) or run_attempt <= 0:
        raise AttestationTransportError("probe run attempt invalid")
    if SHA64.fullmatch(domain_digest) is None:
        raise AttestationTransportError("probe domain digest must be lowercase SHA-256")

    provenance = _provenance()
    provenance_policy, lifecycle, exact_head, assurance_policy, evidence = provenance._load_policies()
    provenance.validate_policy(provenance_policy, lifecycle, exact_head, assurance_policy, evidence)
    candidate = {
        "candidate_id":policy["probe"]["candidate_id"],
        "head_sha":head_sha,
        "risk_class":policy["probe"]["risk_class"],
    }
    input_material = {
        "material_version":1,
        "candidate":candidate,
        "git_tree_sha":tree_sha,
        "context":{"awu_id":policy["probe"]["awu_id"],"probe_kind":"NATIVE_ATTESTATION_TRANSPORT_ONLY"},
    }
    input_binding = {
        "binding_version":1,
        "input_identity_sha256":provenance._sha256_json(input_material),
        "material":input_material,
    }
    plan_material = {
        "candidate_head":head_sha,
        "t3_requirements":[],
        "selection_reasons":[],
        "controls":[],
        "execution_model":"TRANSPORT_PROBE_NOT_CERTIFICATION",
    }
    plan = {
        "plan_version":1,
        "plan_identity_sha256":provenance._sha256_json(plan_material),
        "manual_review_required":False,
        "material":plan_material,
    }
    verdict_material = {
        "plan_identity_sha256":plan["plan_identity_sha256"],
        "status":policy["probe"]["assurance_status"],
        "satisfied":True,
        "missing_controls":[],
        "manual_review_required":False,
        "evidence_runs":[],
    }
    verdict = {**verdict_material,"assurance_identity_sha256":provenance._sha256_json(verdict_material)}
    workflow = {
        "repository":"tobianahillel-afk/Bot-crypto",
        "workflow_path":policy["workflow_path"],
        "workflow_ref":workflow_ref,
        "workflow_sha":head_sha,
        "run_id":run_id,
        "run_attempt":run_attempt,
    }
    refs = [{
        "path":policy["probe"]["domain_integrity_path"],
        "algorithm":"sha256",
        "digest":domain_digest,
    }]
    envelope = provenance.build_provenance(
        input_binding,plan,verdict,workflow,refs,provenance_policy,
        metadata={"notes":"ENGINEERING_TRANSPORT_PROBE_ONLY_NO_BUSINESS_OR_T4_CERTIFICATION"},
    )
    provenance.validate_provenance(envelope, provenance_policy)
    if envelope["material"]["candidate"]["candidate_id"] != policy["probe"]["candidate_id"]:
        raise AttestationTransportError("probe candidate identity changed")
    if envelope["material"]["deep_assurance"]["status"] != "NOT_REQUIRED":
        raise AttestationTransportError("transport probe cannot claim executed deep assurance")
    if envelope["attestation_subject"]["digest"]["sha256"] != envelope["provenance_identity_sha256"]:
        raise AttestationTransportError("transport subject is not the canonical provenance identity")
    return envelope


def emit_probe(path: Path, output_path: Path | None, env: Mapping[str, str]) -> dict[str, Any]:
    policy = _json(POLICY_PATH)
    validate_documents(policy)
    if env.get("GITHUB_REPOSITORY") != "tobianahillel-afk/Bot-crypto":
        raise AttestationTransportError("probe repository mismatch")
    workflow_ref = env.get("GITHUB_REF", "")
    if workflow_ref != policy["allowed_ref"]:
        raise AttestationTransportError("probe may run only on the engineering branch")
    head = env.get("GITHUB_SHA", "")
    if head != _git("rev-parse", "HEAD"):
        raise AttestationTransportError("GITHUB_SHA differs from checked-out HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    try:
        run_id = int(env.get("GITHUB_RUN_ID", ""))
        run_attempt = int(env.get("GITHUB_RUN_ATTEMPT", ""))
    except ValueError as exc:
        raise AttestationTransportError("GitHub run identity is invalid") from exc
    envelope = build_probe(
        head_sha=head,
        tree_sha=tree,
        workflow_ref=workflow_ref,
        run_id=run_id,
        run_attempt=run_attempt,
        domain_digest=_file_sha256(ROOT / policy["probe"]["domain_integrity_path"]),
        policy=policy,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output_path is not None:
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(f"subject_sha256={envelope['provenance_identity_sha256']}\n")
            handle.write(f"subject_name={policy['subject_name']}\n")
            handle.write(f"predicate_type={policy['predicate_type']}\n")
    return envelope


def verify_action_outputs(attestation_id: str, attestation_url: str, bundle_path: Path) -> None:
    if not attestation_id.strip():
        raise AttestationTransportError("native attestation id missing")
    prefix = "https://github.com/tobianahillel-afk/Bot-crypto/attestations/"
    if not attestation_url.startswith(prefix):
        raise AttestationTransportError("native attestation URL is not canonical")
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AttestationTransportError(f"native attestation bundle invalid: {exc}") from exc
    if not isinstance(bundle, dict) or not bundle:
        raise AttestationTransportError("native attestation bundle must be a non-empty object")


def self_check() -> None:
    policy = _json(POLICY_PATH)
    validate_documents(policy)
    envelope = build_probe(
        head_sha="a" * 40,
        tree_sha="b" * 40,
        workflow_ref=policy["allowed_ref"],
        run_id=1,
        run_attempt=1,
        domain_digest="c" * 64,
        policy=policy,
    )
    if envelope["provenance_kind"] != "certification_provenance_envelope_v1":
        raise AttestationTransportError("probe did not use canonical provenance envelope")
    print("CERTIFICATION_ATTESTATION_TRANSPORT_SELF_CHECK_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--emit-probe", type=Path)
    group.add_argument("--verify-action-outputs", action="store_true")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--attestation-id")
    parser.add_argument("--attestation-url")
    parser.add_argument("--bundle-path", type=Path)
    args = parser.parse_args()
    try:
        if args.self_check:
            self_check()
        elif args.emit_probe is not None:
            envelope = emit_probe(args.emit_probe, args.github_output, os.environ)
            print(f"CERTIFICATION_ATTESTATION_PROBE_EMITTED sha256={envelope['provenance_identity_sha256']}")
        else:
            if args.attestation_id is None or args.attestation_url is None or args.bundle_path is None:
                raise AttestationTransportError("native attestation outputs are incomplete")
            verify_action_outputs(args.attestation_id, args.attestation_url, args.bundle_path)
            print("CERTIFICATION_ATTESTATION_NATIVE_OUTPUTS_VALID")
    except (AttestationTransportError, KeyError, TypeError, ValueError) as exc:
        print(f"CERTIFICATION_ATTESTATION_TRANSPORT_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
