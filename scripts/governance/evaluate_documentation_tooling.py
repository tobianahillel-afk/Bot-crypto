#!/usr/bin/env python3
"""Validate the deterministic ENG-05.6 documentation-tooling evaluation."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config" / "governance" / "documentation_tooling_candidates_v1.json"
REPORT_PATH = ROOT / "engineering" / "DOCUMENTATION_TOOLING_EVALUATION.md"


class DocumentationToolingError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentationToolingError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DocumentationToolingError(f"{path} must contain an object")
    return value


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise DocumentationToolingError(f"{label} must be an exact 40-hex Git SHA")
    return value


def _zero_cost(cost: Any, candidate_id: str) -> None:
    expected = {"paid_license", "paid_api", "paid_saas", "paid_runner"}
    if not isinstance(cost, dict) or set(cost) != expected:
        raise DocumentationToolingError(f"{candidate_id}: invalid cost object")
    if any(value is not False for value in cost.values()):
        raise DocumentationToolingError(f"{candidate_id}: mandatory paid capability is forbidden")


def _candidate_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        raise DocumentationToolingError("candidates must be a list")
    result: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("id"), str):
            raise DocumentationToolingError("candidate identity missing")
        if candidate["id"] in result:
            raise DocumentationToolingError(f"duplicate candidate: {candidate['id']}")
        result[candidate["id"]] = candidate
    return result


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise DocumentationToolingError("unsupported documentation tooling schema_version")
    if registry.get("registry_kind") != "documentation_tooling_candidates_v1":
        raise DocumentationToolingError("invalid documentation tooling registry kind")
    if registry.get("semantics") != "AUDIT_BEFORE_ADOPTION_NO_EXTERNAL_EXECUTION":
        raise DocumentationToolingError("tooling evaluation semantics drift")
    if registry.get("observed_on") != "2026-09-24":
        raise DocumentationToolingError("candidate observation date drift")

    allowed_verdicts = {"ADOPT", "ADOPT_PARTIALLY", "COPY_PATTERN", "REJECT"}
    if set(registry.get("verdicts", [])) != allowed_verdicts:
        raise DocumentationToolingError("verdict vocabulary drift")

    constraints = registry.get("project_constraints")
    if not isinstance(constraints, dict):
        raise DocumentationToolingError("project constraints missing")
    required_constraints = {
        "mandatory_path_zero_cost": True,
        "mandatory_path_network_allowed": False,
        "external_tool_authority_allowed": False,
        "external_execution_performed_in_this_awu": False,
        "spec_kit_artifacts_present": False,
    }
    for key, expected in required_constraints.items():
        if constraints.get(key) is not expected:
            raise DocumentationToolingError(f"project constraint drift: {key}")

    candidates = _candidate_map(registry)
    if set(candidates) != {"DOCGUARD", "VALE", "LYCHEE"}:
        raise DocumentationToolingError("candidate set drift")

    for candidate_id, candidate in candidates.items():
        release = candidate.get("release")
        if not isinstance(release, dict):
            raise DocumentationToolingError(f"{candidate_id}: release metadata missing")
        tag = release.get("tag")
        if not isinstance(tag, str) or not tag or tag.lower() in {
            "latest", "main", "master", "stable", "nightly"
        }:
            raise DocumentationToolingError(f"{candidate_id}: floating release tag forbidden")
        _sha(release.get("source_commit"), f"{candidate_id}.release.source_commit")
        if "tag_object_sha" in release:
            _sha(release["tag_object_sha"], f"{candidate_id}.release.tag_object_sha")
        if not isinstance(release.get("published_at"), str) or not release["published_at"].endswith("Z"):
            raise DocumentationToolingError(f"{candidate_id}: release timestamp missing")

        license_info = candidate.get("license")
        if not isinstance(license_info, dict) or license_info.get("permissive") is not True:
            raise DocumentationToolingError(f"{candidate_id}: permissive license required")
        if license_info.get("spdx") not in {"MIT", "MIT OR Apache-2.0"}:
            raise DocumentationToolingError(f"{candidate_id}: license outside approved set")

        _zero_cost(candidate.get("cost"), candidate_id)
        if candidate.get("authority_role") != "NON_AUTHORITATIVE":
            raise DocumentationToolingError(f"{candidate_id}: authority conflict")
        verdict = candidate.get("verdict")
        if verdict not in allowed_verdicts:
            raise DocumentationToolingError(f"{candidate_id}: invalid verdict")
        network = candidate.get("network")
        if not isinstance(network, dict) or network.get("mandatory_mode_network_required") is not False:
            raise DocumentationToolingError(f"{candidate_id}: mandatory network dependency forbidden")
        if candidate.get("mandatory_path") is not False:
            raise DocumentationToolingError(f"{candidate_id}: WU02 cannot make tool mandatory")
        if verdict == "ADOPT_PARTIALLY" and candidate.get("benchmark_followup") is not True:
            raise DocumentationToolingError(
                f"{candidate_id}: partial adoption requires bounded benchmark follow-up"
            )
        if verdict == "COPY_PATTERN" and candidate.get("benchmark_followup") is not False:
            raise DocumentationToolingError(
                f"{candidate_id}: copy-pattern verdict must not imply runtime benchmark"
            )

    docguard = candidates["DOCGUARD"]
    if docguard["verdict"] != "COPY_PATTERN":
        raise DocumentationToolingError(
            "DocGuard must remain COPY_PATTERN while Spec Kit is absent and governance overlap is high"
        )
    if docguard.get("overlap_with_current_engine") != "HIGH":
        raise DocumentationToolingError("DocGuard overlap classification drift")
    runtime = docguard.get("runtime", {})
    if runtime.get("kind") != "NODE_CLI":
        raise DocumentationToolingError("DocGuard runtime classification drift")
    if runtime.get("python_wrapper_delegates_to_npx") is not True:
        raise DocumentationToolingError("DocGuard Python-wrapper fact drift")
    if runtime.get("pinned_runtime_dependencies") != ["@babel/parser@7.29.8"]:
        raise DocumentationToolingError("DocGuard pinned runtime dependency drift")

    vale = candidates["VALE"]
    if vale["verdict"] != "ADOPT_PARTIALLY":
        raise DocumentationToolingError("Vale must remain benchmark-before-adoption")
    if vale.get("runtime", {}).get("kind") != "STATIC_GO_BINARY":
        raise DocumentationToolingError("Vale runtime classification drift")
    if vale.get("network", {}).get("core_lint_offline") is not True:
        raise DocumentationToolingError("Vale offline capability required")

    lychee = candidates["LYCHEE"]
    if lychee["verdict"] != "ADOPT_PARTIALLY":
        raise DocumentationToolingError("lychee must remain benchmark-before-adoption")
    if lychee.get("runtime", {}).get("kind") != "STATIC_RUST_BINARY":
        raise DocumentationToolingError("lychee runtime classification drift")
    if lychee.get("network", {}).get("offline_flag_supported") is not True:
        raise DocumentationToolingError("lychee offline mode required")

    follow = registry.get("follow_up")
    if not isinstance(follow, dict) or follow.get("benchmark_aw_u_required") is not True:
        raise DocumentationToolingError("bounded follow-up benchmark is required")
    if follow.get("proposed_aw_u_id") != "ENG-05.6-WU03":
        raise DocumentationToolingError("follow-up AWU id drift")
    expected_benchmarks = sorted(
        candidate_id
        for candidate_id, candidate in candidates.items()
        if candidate.get("benchmark_followup") is True
    )
    if sorted(follow.get("benchmark_candidates", [])) != expected_benchmarks:
        raise DocumentationToolingError("follow-up benchmark candidate set mismatch")


def render_report(registry: dict[str, Any]) -> str:
    candidates = _candidate_map(registry)
    ordered = [candidates["DOCGUARD"], candidates["VALE"], candidates["LYCHEE"]]
    tick = chr(96)
    lines = [
        "# Documentation Tooling Evaluation — ENG-05.6",
        "",
        f"> Generated from {tick}config/governance/documentation_tooling_candidates_v1.json{tick}.",
        "> This phase evaluates candidates only; it does not install or execute them.",
        "",
        f"Observed: **{registry['observed_on']}**",
        "",
        "## Verdicts",
        "",
        "| Tool | Release | License | Runtime | Verdict | Immediate decision |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in ordered:
        lines.append(
            f"| {candidate['display_name']} | {candidate['release']['tag']} | "
            f"{candidate['license']['spdx']} | {candidate['runtime']['kind']} | "
            f"**{candidate['verdict']}** | {candidate['proposed_scope']} |"
        )

    lines.extend(["", "## Candidate rationale", ""])
    for candidate in ordered:
        lines.extend([
            f"### {candidate['display_name']}",
            "",
            f"- Repository: {tick}{candidate['repository']}{tick}",
            f"- Exact source commit: {tick}{candidate['release']['source_commit']}{tick}",
            f"- Published: {tick}{candidate['release']['published_at']}{tick}",
            f"- Current-engine overlap: {tick}{candidate['overlap_with_current_engine']}{tick}",
            f"- Authority: {tick}{candidate['authority_role']}{tick}",
            f"- Rationale: {candidate['rationale']}",
            f"- Rollback: {candidate['rollback']}",
            "",
        ])

    follow = registry["follow_up"]
    lines.extend([
        "## Follow-up",
        "",
        f"- Benchmark AWU required: {tick}{str(follow['benchmark_aw_u_required']).lower()}{tick}",
        f"- Proposed AWU: {tick}{follow['proposed_aw_u_id']}{tick}",
        "- Benchmark candidates: "
        + ", ".join(f"{tick}{item}{tick}" for item in follow["benchmark_candidates"]),
        f"- DocGuard revisit condition: {tick}{follow['docguard_revisit_condition']}{tick}",
        "",
        "The mandatory path remains zero-cost, offline, non-LLM and governed by the project's",
        "existing canonical state. External tools may only add bounded lint evidence.",
        "",
    ])
    return "\n".join(lines)


def _expect_failure(
    registry: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    label: str,
) -> None:
    scenario = copy.deepcopy(registry)
    mutate(scenario)
    try:
        validate_registry(scenario)
    except DocumentationToolingError:
        return
    raise AssertionError(f"documentation-tooling negative scenario unexpectedly passed: {label}")


def self_check(registry: dict[str, Any]) -> None:
    validate_registry(registry)
    _expect_failure(
        registry,
        lambda r: r["candidates"][0]["release"].__setitem__("tag", "latest"),
        "floating tag",
    )
    _expect_failure(
        registry,
        lambda r: r["candidates"][1]["release"].__setitem__("source_commit", "deadbeef"),
        "missing exact commit",
    )
    _expect_failure(
        registry,
        lambda r: r["candidates"][1]["cost"].__setitem__("paid_saas", True),
        "paid SaaS",
    )
    _expect_failure(
        registry,
        lambda r: r["candidates"][2].__setitem__("authority_role", "CANONICAL"),
        "authority conflict",
    )
    _expect_failure(
        registry,
        lambda r: r["candidates"][2]["network"].__setitem__(
            "mandatory_mode_network_required", True
        ),
        "mandatory network",
    )
    _expect_failure(
        registry,
        lambda r: r["candidates"][0].__setitem__("verdict", "ADOPT"),
        "DocGuard premature adoption",
    )
    _expect_failure(
        registry,
        lambda r: r["candidates"][1].__setitem__("benchmark_followup", False),
        "partial adoption without benchmark",
    )
    _expect_failure(
        registry,
        lambda r: r["follow_up"].__setitem__("benchmark_candidates", ["DOCGUARD"]),
        "follow-up candidate mismatch",
    )
    print("DOCUMENTATION_TOOLING_SELF_CHECK_PASS probes=8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.check == args.self_check:
        print(
            "DOCUMENTATION_TOOLING_INVALID: choose exactly one of --check or --self-check",
            file=sys.stderr,
        )
        return 1
    try:
        registry = _load(REGISTRY_PATH)
        validate_registry(registry)
        if args.self_check:
            self_check(registry)
            return 0
        expected = render_report(registry)
        actual = REPORT_PATH.read_text(encoding="utf-8")
        if actual != expected:
            raise DocumentationToolingError(
                "evaluation report drift; regenerate from candidate registry"
            )
    except (DocumentationToolingError, OSError) as exc:
        print(f"DOCUMENTATION_TOOLING_INVALID: {exc}", file=sys.stderr)
        return 1
    print("DOCUMENTATION_TOOLING_VALID candidates=3 follow_up=ENG-05.6-WU03")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
