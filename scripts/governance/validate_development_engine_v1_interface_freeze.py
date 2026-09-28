#!/usr/bin/env python3
"""Validate the frozen Development Engine V1 bootstrap compatibility surface."""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/governance/development_engine_v1_interface_freeze_v1.json"


class EngineV1InterfaceFreezeError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EngineV1InterfaceFreezeError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EngineV1InterfaceFreezeError(f"{path} must contain an object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EngineV1InterfaceFreezeError(message)


def _safe_file(path_text: str, root: Path = ROOT) -> Path:
    _require(isinstance(path_text, str) and bool(path_text), "interface path must be non-empty")
    rel = Path(path_text)
    _require(not rel.is_absolute() and ".." not in rel.parts, f"unsafe interface path: {path_text}")
    full = (root / rel).resolve()
    try:
        full.relative_to(root.resolve())
    except ValueError as exc:
        raise EngineV1InterfaceFreezeError(f"interface path escapes repository: {path_text}") from exc
    _require(full.is_file(), f"frozen V1 interface path missing: {path_text}")
    return full


def validate_policy(policy: dict[str, Any]) -> None:
    _require(policy.get("schema_version") == 1, "unsupported interface-freeze schema version")
    _require(
        policy.get("policy_kind") == "development_engine_v1_interface_freeze_v1",
        "invalid interface-freeze policy kind",
    )
    _require(
        policy.get("semantics") == "STABLE_COMPATIBILITY_SURFACE_WITH_DYNAMIC_STATE_PAYLOADS",
        "V1 freeze semantics drift",
    )
    _require(policy.get("engine_version") == "V1", "engine version drift")
    _require(policy.get("canonical_project") == "Crypto Quant Bot V3.1-Ops", "project identity drift")

    bootstrap = policy.get("bootstrap")
    _require(isinstance(bootstrap, dict), "bootstrap contract missing")
    expected_order = [
        "AGENTS.md",
        "config/governance/project_state.json",
        "engineering/CONTEXT_MAP.json",
    ]
    _require(bootstrap.get("read_order") == expected_order, "three-file bootstrap order drift")
    _require(bootstrap.get("max_bootstrap_files") == 3, "bootstrap file budget drift")
    _require(bootstrap.get("human_entrypoint") == "AGENTS.md", "human entrypoint drift")
    _require(
        bootstrap.get("current_authority") == "config/governance/project_state.json",
        "current authority path drift",
    )
    _require(
        bootstrap.get("generated_context_route") == "engineering/CONTEXT_MAP.json",
        "context route path drift",
    )
    _require(
        bootstrap.get("active_awu_resolver") == "scripts/governance/resolve_active_awu.py",
        "AWU resolver path drift",
    )
    _require(
        bootstrap.get("external_git_verifier") == "scripts/governance/verify_external_git_state.py",
        "external Git verifier path drift",
    )
    for value in bootstrap.values():
        if isinstance(value, str) and "/" in value:
            _safe_file(value)

    cli = policy.get("stable_cli_contracts")
    _require(isinstance(cli, dict), "stable CLI contract missing")
    expected_cli = {
        "resolve_active_awu": ["python", "scripts/governance/resolve_active_awu.py"],
        "verify_external_git_state": [
            "python", "scripts/governance/verify_external_git_state.py", "--mode", "github"
        ],
        "check_context_map": ["python", "scripts/governance/render_context_map.py", "--check"],
        "check_current_status": ["python", "scripts/governance/render_current_status.py", "--check"],
    }
    _require(cli == expected_cli, "stable CLI contract drift")
    for argv in cli.values():
        _require(all(isinstance(x, str) and x for x in argv), "CLI argv contains invalid value")
        _require(shlex.join(argv), "CLI argv is empty")

    compatibility = policy.get("compatibility")
    _require(isinstance(compatibility, dict), "compatibility rules missing")
    for key in (
        "incompatible_change_requires_new_interface_version",
        "v1_must_not_silently_move_paths",
        "v1_must_not_invert_authority",
        "v1_must_not_freeze_dynamic_payload_bytes",
    ):
        _require(compatibility.get(key) is True, f"compatibility floor weakened: {key}")
    _require(compatibility.get("paid_dependency_required") is False, "paid dependency introduced")
    _require(
        compatibility.get("mandatory_llm_review_required") is False,
        "mandatory LLM review introduced",
    )

    dynamic = policy.get("dynamic_not_frozen")
    _require(isinstance(dynamic, list) and len(dynamic) >= 7, "dynamic-not-frozen declarations missing")
    _require(
        any(item.startswith("config/governance/project_state.json#") for item in dynamic),
        "project state dynamic fields were byte-frozen",
    )
    _require(
        any(item.startswith("engineering/CONTEXT_MAP.json#") for item in dynamic),
        "context map dynamic fields were byte-frozen",
    )


def _validate_json_interfaces(policy: dict[str, Any], root: Path = ROOT) -> None:
    interfaces = policy.get("json_interfaces")
    _require(isinstance(interfaces, list) and len(interfaces) == 6, "JSON interface set drift")
    seen: set[str] = set()
    for interface in interfaces:
        _require(isinstance(interface, dict), "JSON interface entry invalid")
        path = interface.get("path")
        _require(isinstance(path, str) and path not in seen, "duplicate/invalid JSON interface path")
        seen.add(path)
        value = _json(_safe_file(path, root))
        required = interface.get("required_values")
        _require(isinstance(required, dict) and required, f"required JSON identity missing: {path}")
        for key, expected in required.items():
            _require(value.get(key) == expected, f"{path}.{key} drift: {value.get(key)!r} != {expected!r}")
        _require(
            isinstance(interface.get("dynamic_payload"), bool),
            f"dynamic_payload marker missing: {path}",
        )


def _validate_agents(policy: dict[str, Any], root: Path = ROOT) -> None:
    agents = _safe_file("AGENTS.md", root).read_text(encoding="utf-8")
    expected_phrases = [
        "This file is the mandatory first entry point for any coding or audit agent.",
        "Read `config/governance/project_state.json`.",
        "Read `engineering/CONTEXT_MAP.json` for the generated bounded route; it never overrides canonical state.",
        "resolve the single active AWU with `python scripts/governance/resolve_active_awu.py`",
        "`python scripts/governance/verify_external_git_state.py --mode github` is the canonical live check",
        "Current work authorization → `config/governance/project_state.json`.",
        "Human summaries/handoffs → convenience only; never override higher authority.",
        "Chat history/model memory → never a source of authorization.",
    ]
    for phrase in expected_phrases:
        _require(phrase in agents, f"AGENTS V1 interface phrase missing: {phrase}")

    context_policy = _json(_safe_file("config/governance/context_map_policy_v1.json", root))
    _require(
        context_policy.get("bootstrap_read_order") == policy["bootstrap"]["read_order"],
        "context policy bootstrap order disagrees with V1 freeze",
    )
    _require(
        context_policy.get("state_source") == policy["bootstrap"]["current_authority"],
        "context policy authority source disagrees with V1 freeze",
    )
    _require(
        context_policy.get("active_awu_resolver") == policy["bootstrap"]["active_awu_resolver"],
        "context policy AWU resolver disagrees with V1 freeze",
    )


def _validate_active_awu(policy: dict[str, Any], root: Path = ROOT) -> None:
    context = _json(_safe_file("engineering/CONTEXT_MAP.json", root))
    active = context.get("active_work")
    _require(isinstance(active, dict), "active context work missing")
    awu_path = active.get("awu_path")
    _require(isinstance(awu_path, str), "active AWU path missing from context map")
    awu = _json(_safe_file(awu_path, root))
    contract = policy.get("active_awu_contract")
    _require(isinstance(contract, dict), "active AWU contract missing")
    _require(awu.get("schema_version") == contract.get("schema_version") == 1, "AWU schema drift")
    _require(awu.get("kind") == contract.get("kind") == "agent_work_unit", "AWU kind drift")
    _require(awu.get("status") == "IN_PROGRESS", "active AWU is not IN_PROGRESS")
    _require(
        context.get("authority", {}).get("current_state") == policy["bootstrap"]["current_authority"],
        "context map authority inversion",
    )
    _require(
        context.get("authority", {}).get("resume_hint_is_authoritative") is False,
        "handoff became authoritative",
    )


def _validate_certification(policy: dict[str, Any], root: Path = ROOT) -> None:
    identity = policy.get("certification_identity")
    _require(isinstance(identity, dict), "certification identity missing")
    evidence = _json(_safe_file(identity["evidence_path"], root))
    exact = evidence.get("exact_identities")
    _require(isinstance(exact, dict), "certification exact identities missing")
    _require(evidence.get("qualified_head_sha") == identity["qualified_head_sha"], "qualified head drift")
    _require(
        exact.get("candidate_material_sha256") == identity["candidate_material_sha256"],
        "candidate material identity drift",
    )
    _require(
        exact.get("input_identity_sha256") == identity["input_identity_sha256"],
        "certification input identity drift",
    )
    _require(
        exact.get("bundle_identity_sha256") == identity["bundle_identity_sha256"],
        "certification bundle identity drift",
    )
    authority = evidence.get("authority_separation")
    _require(isinstance(authority, dict), "certification authority separation missing")
    for key in (
        "business_development_unlocked",
        "runtime_unlocked",
        "lot45_merge_allowed",
        "lot46_unlock_allowed",
        "trade_allowed",
        "execution_allowed",
    ):
        _require(authority.get(key) is False, f"certification improperly grants authority: {key}")


def _validate_safety(policy: dict[str, Any], root: Path = ROOT) -> None:
    state = _json(_safe_file("config/governance/project_state.json", root))
    floor = policy.get("safety_floor")
    _require(isinstance(floor, dict), "safety floor missing")
    _require(state["business_track"]["development_status"] == floor["business_development"], "business pause drift")
    _require(state["business_track"]["candidate"]["status"] == floor["lot45_status"], "Lot45 status drift")
    _require(state["business_track"]["next_lot"]["status"] == floor["lot46_status"], "Lot46 lock drift")
    finding = next((x for x in state.get("findings", []) if x.get("id") == floor["blocking_finding_id"]), None)
    _require(isinstance(finding, dict) and finding.get("observed") is True, "BOOT-FINDING-001 disappeared")
    safety = state.get("safety", {})
    for key in ("trade_allowed", "execution_allowed", "live_execution", "leverage", "withdrawals"):
        _require(safety.get(key) == floor[key], f"safety floor drift: {key}")


def validate_repository(root: Path = ROOT) -> dict[str, Any]:
    policy = _json(root / POLICY_PATH.relative_to(ROOT))
    validate_policy(policy)
    _validate_json_interfaces(policy, root)
    _validate_agents(policy, root)
    _validate_active_awu(policy, root)
    _validate_certification(policy, root)
    _validate_safety(policy, root)
    return {
        "schema_version": 1,
        "validation_kind": "development_engine_v1_interface_freeze_validation_v1",
        "status": "PASS",
        "engine_version": "V1",
        "bootstrap_read_order": policy["bootstrap"]["read_order"],
        "dynamic_payloads_frozen": False,
        "business_authority_granted": False,
        "runtime_authority_granted": False,
    }


def main() -> int:
    try:
        result = validate_repository()
    except (EngineV1InterfaceFreezeError, KeyError, TypeError) as exc:
        print(f"DEVELOPMENT_ENGINE_V1_INTERFACE_FREEZE_INVALID: {exc}", file=sys.stderr)
        return 1
    print("DEVELOPMENT_ENGINE_V1_INTERFACE_FREEZE=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
