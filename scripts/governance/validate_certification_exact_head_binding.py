#!/usr/bin/env python3
"""Validate exact-head certification evidence binding for ENG-06.2."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/governance/certification_exact_head_binding_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
CANDIDATE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
AWU_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ExactHeadBindingError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExactHeadBindingError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExactHeadBindingError(f"{path} must contain an object")
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
        raise ExactHeadBindingError(f"value is not canonical JSON: {exc}") from exc
    return rendered.encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256(_canonical(value))


def _git(
    root: Path,
    *args: str,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=text,
    )


def _git_text(root: Path, *args: str) -> str:
    proc = _git(root, *args)
    if proc.returncode != 0:
        raise ExactHeadBindingError(
            f"git {' '.join(args)} failed: {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _load_policies(root: Path = ROOT) -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    policy = _json(root / "config/governance/certification_exact_head_binding_v1.json")
    lifecycle = _json(root / policy["lifecycle_policy_source"])
    evidence = _json(root / policy["evidence_policy_source"])
    proof = _json(root / policy["proof_reuse_policy_source"])
    assurance = _json(root / policy["assurance_policy_source"])
    return policy, lifecycle, evidence, proof, assurance


def validate_policy(
    policy: dict[str, Any],
    lifecycle: dict[str, Any],
    evidence: dict[str, Any],
    proof: dict[str, Any],
    assurance: dict[str, Any],
) -> None:
    if policy.get("schema_version") != 1:
        raise ExactHeadBindingError("unsupported exact-head policy version")
    if policy.get("policy_kind") != "certification_exact_head_binding_v1":
        raise ExactHeadBindingError("invalid exact-head policy kind")
    if policy.get("semantics") != (
        "EXACT_HEAD_TREE_BLOB_AND_CI_EVIDENCE_BINDING_FAIL_CLOSED"
    ):
        raise ExactHeadBindingError("exact-head binding semantics drift")
    expected_sources = {
        "lifecycle_policy_source": "config/governance/certification_candidate_lifecycle_v1.json",
        "evidence_policy_source": "engineering/AGENT_CAPABILITIES.json",
        "proof_reuse_policy_source": "config/governance/proof_reuse_policy_v1.json",
        "assurance_policy_source": "config/governance/validation_t3_t4_policy_v1.json",
    }
    for key, expected in expected_sources.items():
        if policy.get(key) != expected:
            raise ExactHeadBindingError(f"{key} drift")
    if policy.get("content_hash_algorithm") != "sha256":
        raise ExactHeadBindingError("content hash must remain sha256")
    if policy.get("repository_object_hash") != "sha1":
        raise ExactHeadBindingError("repository object hash policy drift")
    if policy.get("allowed_git_blob_modes") != ["100644", "100755"]:
        raise ExactHeadBindingError("allowed Git blob modes drift")
    if policy.get("required_ci_evidence_class") != "EXACT_GITHUB_ACTIONS_RUN":
        raise ExactHeadBindingError("CI evidence class drift")
    if policy.get("required_ci_conclusion") != "success":
        raise ExactHeadBindingError("CI success conclusion drift")
    if policy.get("candidate_fields") != ["candidate_id", "head_sha", "risk_class"]:
        raise ExactHeadBindingError("candidate field set/order drift")
    if policy.get("context_fields") != [
        "awu_id", "scope_base_sha", "required_t3", "required_t4"
    ]:
        raise ExactHeadBindingError("binding context field set/order drift")
    if policy.get("ci_run_fields") != [
        "run_id", "workflow", "head_sha", "conclusion"
    ]:
        raise ExactHeadBindingError("CI run field set/order drift")
    if not isinstance(policy.get("max_bound_files"), int) or not 1 <= policy["max_bound_files"] <= 500:
        raise ExactHeadBindingError("invalid max_bound_files")
    if not isinstance(policy.get("max_ci_runs"), int) or not 1 <= policy["max_ci_runs"] <= 128:
        raise ExactHeadBindingError("invalid max_ci_runs")

    if lifecycle.get("policy_kind") != "certification_candidate_lifecycle_v1":
        raise ExactHeadBindingError("lifecycle policy source identity drift")
    evidence_classes = evidence.get("evidence_classes")
    if not isinstance(evidence_classes, dict):
        raise ExactHeadBindingError("agent evidence class catalog missing")
    exact_run = evidence_classes.get("EXACT_GITHUB_ACTIONS_RUN")
    if not isinstance(exact_run, dict) or exact_run.get("required_fields") != [
        "run_id", "head_sha", "conclusion"
    ]:
        raise ExactHeadBindingError("EXACT_GITHUB_ACTIONS_RUN evidence contract drift")

    forbidden_tiers = set(proof.get("forbidden_tiers", []))
    forbidden_subjects = set(proof.get("forbidden_subject_ids", []))
    if "T4" not in forbidden_tiers:
        raise ExactHeadBindingError("T4 proof reuse must remain forbidden")
    if "EXACT_HEAD_CERTIFICATION" not in forbidden_subjects:
        raise ExactHeadBindingError("EXACT_HEAD_CERTIFICATION reuse must remain forbidden")

    if assurance.get("risk_order") != ["R0", "R1", "R2", "R3"]:
        raise ExactHeadBindingError("assurance risk order drift")
    if "EXACT_HEAD_CERTIFICATION" not in assurance.get("t4_requirement_ids", []):
        raise ExactHeadBindingError("exact-head T4 requirement missing")


def _safe_repo_path(path_text: str, root: Path) -> str:
    if not isinstance(path_text, str) or not path_text:
        raise ExactHeadBindingError("bound path must be a non-empty string")
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise ExactHeadBindingError(f"bound path escapes repository: {path_text!r}")
    normalized = path.as_posix()
    if normalized in {".", ""} or "\n" in normalized or "\r" in normalized:
        raise ExactHeadBindingError(f"invalid bound path: {path_text!r}")
    root_resolved = root.resolve()
    try:
        (root / path).resolve(strict=False).relative_to(root_resolved)
    except ValueError as exc:
        raise ExactHeadBindingError(f"bound path escapes repository: {path_text!r}") from exc
    return normalized


def _validate_candidate(
    candidate: dict[str, Any],
    assurance: dict[str, Any],
) -> None:
    if set(candidate) != {"candidate_id", "head_sha", "risk_class"}:
        raise ExactHeadBindingError("candidate shape mismatch")
    candidate_id = candidate["candidate_id"]
    head = candidate["head_sha"]
    risk = candidate["risk_class"]
    if not isinstance(candidate_id, str) or CANDIDATE_ID.fullmatch(candidate_id) is None:
        raise ExactHeadBindingError("invalid candidate_id")
    if not isinstance(head, str) or SHA40.fullmatch(head) is None:
        raise ExactHeadBindingError("candidate head must be lowercase SHA-40")
    if risk not in assurance["risk_order"]:
        raise ExactHeadBindingError(f"unknown candidate risk class: {risk}")


def _unique_string_list(value: Any, label: str, allowed: set[str]) -> list[str]:
    if not isinstance(value, list) or len(value) != len(set(value)):
        raise ExactHeadBindingError(f"{label} must be a unique list")
    if any(not isinstance(item, str) or item not in allowed for item in value):
        raise ExactHeadBindingError(f"{label} contains unknown requirement id")
    return value


def _validate_context(
    context: dict[str, Any],
    candidate: dict[str, Any],
    assurance: dict[str, Any],
) -> None:
    if set(context) != {"awu_id", "scope_base_sha", "required_t3", "required_t4"}:
        raise ExactHeadBindingError("binding context shape mismatch")
    if not isinstance(context["awu_id"], str) or AWU_ID.fullmatch(context["awu_id"]) is None:
        raise ExactHeadBindingError("invalid binding awu_id")
    if not isinstance(context["scope_base_sha"], str) or SHA40.fullmatch(
        context["scope_base_sha"]
    ) is None:
        raise ExactHeadBindingError("scope_base_sha must be lowercase SHA-40")
    required_t3 = _unique_string_list(
        context["required_t3"], "required_t3", set(assurance["t3_requirement_ids"])
    )
    required_t4 = _unique_string_list(
        context["required_t4"], "required_t4", set(assurance["t4_requirement_ids"])
    )
    risk = candidate["risk_class"]
    if not set(assurance["risk_to_t3"][risk]) <= set(required_t3):
        raise ExactHeadBindingError(f"{risk} T3 requirement floor missing")
    if not set(assurance["risk_to_t4"][risk]) <= set(required_t4):
        raise ExactHeadBindingError(f"{risk} T4 requirement floor missing")


def _head_sha(root: Path) -> str:
    head = _git_text(root, "rev-parse", "HEAD")
    if SHA40.fullmatch(head) is None:
        raise ExactHeadBindingError(f"repository HEAD is not SHA-40: {head!r}")
    return head


def _tree_sha(root: Path) -> str:
    tree = _git_text(root, "rev-parse", "HEAD^{tree}")
    if SHA40.fullmatch(tree) is None:
        raise ExactHeadBindingError(f"repository tree is not SHA-40: {tree!r}")
    return tree


def _blob_record(root: Path, path_text: str, policy: dict[str, Any]) -> dict[str, Any]:
    path = _safe_repo_path(path_text, root)
    diff = _git(root, "diff", "--quiet", "HEAD", "--", path)
    if diff.returncode == 1:
        raise ExactHeadBindingError(f"bound path is dirty relative to HEAD: {path}")
    if diff.returncode != 0:
        raise ExactHeadBindingError(f"cannot verify bound path cleanliness: {path}")

    proc = _git(root, "ls-tree", "-z", "HEAD", "--", path, text=False)
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        raise ExactHeadBindingError(f"cannot resolve bound Git object {path}: {stderr}")
    raw = proc.stdout
    if not raw:
        raise ExactHeadBindingError(f"bound path is untracked or absent at HEAD: {path}")
    entries = [entry for entry in raw.split(b"\0") if entry]
    if len(entries) != 1:
        raise ExactHeadBindingError(f"bound path did not resolve to one Git object: {path}")
    try:
        header, returned = entries[0].split(b"\t", 1)
        mode_raw, type_raw, sha_raw = header.split(b" ", 2)
        mode = mode_raw.decode("ascii")
        object_type = type_raw.decode("ascii")
        blob_sha = sha_raw.decode("ascii")
        returned_path = returned.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ExactHeadBindingError(f"malformed ls-tree record for {path}") from exc
    if returned_path != path:
        raise ExactHeadBindingError(f"Git path mismatch: {returned_path!r} != {path!r}")
    if object_type != "blob":
        raise ExactHeadBindingError(f"bound path is not a blob: {path}")
    if mode not in policy["allowed_git_blob_modes"]:
        raise ExactHeadBindingError(f"forbidden Git mode {mode} for bound path: {path}")
    if SHA40.fullmatch(blob_sha) is None:
        raise ExactHeadBindingError(f"invalid Git blob SHA for {path}")

    blob = _git(root, "cat-file", "blob", blob_sha, text=False)
    if blob.returncode != 0:
        stderr = blob.stderr.decode("utf-8", errors="replace")
        raise ExactHeadBindingError(f"cannot read Git blob {blob_sha}: {stderr}")
    return {
        "path": path,
        "mode": mode,
        "git_blob_sha": blob_sha,
        "sha256": _sha256(blob.stdout),
        "bytes": len(blob.stdout),
    }


def build_input_binding(
    candidate: dict[str, Any],
    bound_paths: list[str],
    context: dict[str, Any],
    policy: dict[str, Any],
    assurance: dict[str, Any],
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_candidate(candidate, assurance)
    _validate_context(context, candidate, assurance)
    if not isinstance(bound_paths, list) or not bound_paths:
        raise ExactHeadBindingError("bound_paths must be a non-empty list")
    if len(bound_paths) != len(set(bound_paths)):
        raise ExactHeadBindingError("duplicate bound path")
    if len(bound_paths) > policy["max_bound_files"]:
        raise ExactHeadBindingError("bound path count exceeds policy limit")

    actual_head = _head_sha(root)
    if actual_head != candidate["head_sha"]:
        raise ExactHeadBindingError(
            f"candidate head does not equal checked-out HEAD: {candidate['head_sha']} != {actual_head}"
        )

    records = sorted(
        (_blob_record(root, path, policy) for path in bound_paths),
        key=lambda item: item["path"],
    )
    material = {
        "material_version": 1,
        "candidate": dict(candidate),
        "git_tree_sha": _tree_sha(root),
        "bound_blobs": records,
        "context": {
            "awu_id": context["awu_id"],
            "scope_base_sha": context["scope_base_sha"],
            "required_t3": sorted(context["required_t3"]),
            "required_t4": sorted(context["required_t4"]),
        },
    }
    return {
        "binding_version": 1,
        "input_identity_sha256": _sha256_json(material),
        "material": material,
    }


def validate_input_binding(binding: dict[str, Any]) -> None:
    if set(binding) != {"binding_version", "input_identity_sha256", "material"}:
        raise ExactHeadBindingError("input binding shape mismatch")
    if binding["binding_version"] != 1:
        raise ExactHeadBindingError("unsupported input binding version")
    identity = binding["input_identity_sha256"]
    material = binding["material"]
    if not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise ExactHeadBindingError("input identity must be lowercase SHA-256")
    if not isinstance(material, dict):
        raise ExactHeadBindingError("input binding material missing")
    if _sha256_json(material) != identity:
        raise ExactHeadBindingError("input binding self-integrity mismatch")


def validate_ci_runs(
    candidate_head: str,
    runs: list[dict[str, Any]],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(runs, list) or not runs:
        raise ExactHeadBindingError("at least one exact CI run is required")
    if len(runs) > policy["max_ci_runs"]:
        raise ExactHeadBindingError("CI evidence count exceeds policy limit")
    seen: set[int] = set()
    normalized: list[dict[str, Any]] = []
    expected_fields = set(policy["ci_run_fields"])
    for item in runs:
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise ExactHeadBindingError("CI run evidence shape mismatch")
        run_id = item["run_id"]
        workflow = item["workflow"]
        head = item["head_sha"]
        conclusion = item["conclusion"]
        if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
            raise ExactHeadBindingError("CI run_id must be positive integer")
        if run_id in seen:
            raise ExactHeadBindingError(f"duplicate CI run id: {run_id}")
        seen.add(run_id)
        if not isinstance(workflow, str) or not workflow.strip() or len(workflow) > 160:
            raise ExactHeadBindingError("CI workflow name invalid")
        if head != candidate_head:
            raise ExactHeadBindingError(
                f"CI run {run_id} is bound to wrong head: {head!r}"
            )
        if conclusion != policy["required_ci_conclusion"]:
            raise ExactHeadBindingError(
                f"CI run {run_id} conclusion is not success: {conclusion!r}"
            )
        normalized.append(
            {
                "run_id": run_id,
                "workflow": workflow.strip(),
                "head_sha": head,
                "conclusion": conclusion,
            }
        )
    return sorted(normalized, key=lambda item: (item["run_id"], item["workflow"]))


def build_evidence_bundle(
    input_binding: dict[str, Any],
    runs: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    validate_input_binding(input_binding)
    material = input_binding["material"]
    candidate = material.get("candidate")
    if not isinstance(candidate, dict):
        raise ExactHeadBindingError("input binding candidate missing")
    normalized_runs = validate_ci_runs(candidate["head_sha"], runs, policy)
    bundle_material = {
        "bundle_version": 1,
        "candidate": candidate,
        "input_identity_sha256": input_binding["input_identity_sha256"],
        "ci_evidence_class": policy["required_ci_evidence_class"],
        "ci_runs": normalized_runs,
    }
    return {
        "bundle_version": 1,
        "bundle_identity_sha256": _sha256_json(bundle_material),
        "material": bundle_material,
    }


def validate_evidence_bundle(
    bundle: dict[str, Any],
    input_binding: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    if set(bundle) != {"bundle_version", "bundle_identity_sha256", "material"}:
        raise ExactHeadBindingError("evidence bundle shape mismatch")
    if bundle["bundle_version"] != 1:
        raise ExactHeadBindingError("unsupported evidence bundle version")
    identity = bundle["bundle_identity_sha256"]
    material = bundle["material"]
    if not isinstance(identity, str) or SHA64.fullmatch(identity) is None:
        raise ExactHeadBindingError("bundle identity must be lowercase SHA-256")
    if not isinstance(material, dict) or _sha256_json(material) != identity:
        raise ExactHeadBindingError("evidence bundle self-integrity mismatch")
    validate_input_binding(input_binding)
    if material.get("input_identity_sha256") != input_binding["input_identity_sha256"]:
        raise ExactHeadBindingError("bundle is bound to a different input identity")
    candidate = input_binding["material"]["candidate"]
    if material.get("candidate") != candidate:
        raise ExactHeadBindingError("bundle candidate differs from input binding")
    runs = material.get("ci_runs")
    if not isinstance(runs, list):
        raise ExactHeadBindingError("bundle CI evidence missing")
    normalized = validate_ci_runs(candidate["head_sha"], runs, policy)
    if normalized != runs:
        raise ExactHeadBindingError("bundle CI evidence is not canonically ordered")
    if material.get("ci_evidence_class") != policy["required_ci_evidence_class"]:
        raise ExactHeadBindingError("bundle CI evidence class drift")


def self_check(root: Path = ROOT) -> None:
    policy, lifecycle, evidence, proof, assurance = _load_policies(root)
    validate_policy(policy, lifecycle, evidence, proof, assurance)
    head = _head_sha(root)
    tree = _tree_sha(root)
    if SHA40.fullmatch(head) is None or SHA40.fullmatch(tree) is None:
        raise ExactHeadBindingError("repository identity self-check failed")
    left = {"a": 1, "b": ["x", "y"]}
    right = {"b": ["x", "y"], "a": 1}
    if _sha256_json(left) != _sha256_json(right):
        raise ExactHeadBindingError("canonical hashing is not deterministic")
    print(f"CERTIFICATION_EXACT_HEAD_SELF_CHECK_PASS head={head} tree={tree}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    try:
        if not args.self_check:
            raise ExactHeadBindingError("only --self-check is exposed during ENG-06.2")
        self_check()
    except ExactHeadBindingError as exc:
        print(f"CERTIFICATION_EXACT_HEAD_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
