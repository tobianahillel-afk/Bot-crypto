#!/usr/bin/env python3
"""Validate read-only historical audit manifests and lifecycle transitions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "config" / "governance" / "historical_audit_manifest_v1.schema.json"
LIFECYCLE_PATH = ROOT / "config" / "governance" / "historical_audit_lifecycle_v1.json"
BATCHING_PATH = ROOT / "config" / "governance" / "historical_audit_batching_v1.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
MANIFEST_ID = re.compile(r"^HIST-AUDIT-BATCH-[0-9]{3}$")


class HistoricalAuditManifestError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalAuditManifestError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HistoricalAuditManifestError(f"{path} must contain an object")
    return value


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HistoricalAuditManifestError(f"non-canonical manifest value: {exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("title") != "Crypto Quant Bot Historical Audit Manifest V1":
        raise HistoricalAuditManifestError("manifest schema title drift")
    required = schema.get("required")
    expected = [
        "schema_version","manifest_kind","manifest_id","manifest_identity_sha256","status","mode",
        "plan_identity_sha256","batch_identity_sha256","batch_index","lots","complexity_total",
        "isolated_oversized","source_binding","permissions","blockers"
    ]
    if required != expected:
        raise HistoricalAuditManifestError("manifest schema required fields drift")
    props = schema.get("properties")
    if not isinstance(props, dict):
        raise HistoricalAuditManifestError("manifest schema properties missing")
    if props.get("schema_version", {}).get("const") != 1:
        raise HistoricalAuditManifestError("manifest schema version drift")
    if props.get("manifest_kind", {}).get("const") != "historical_audit_manifest_v1":
        raise HistoricalAuditManifestError("manifest kind schema drift")
    if props.get("mode", {}).get("const") != "READ_ONLY":
        raise HistoricalAuditManifestError("manifest read-only schema drift")
    if props.get("lots", {}).get("items", {}).get("maximum") != 44:
        raise HistoricalAuditManifestError("manifest schema permits non-historical lots")


def validate_lifecycle_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1 or policy.get("policy_kind") != "historical_audit_lifecycle_v1":
        raise HistoricalAuditManifestError("invalid historical audit lifecycle identity")
    if policy.get("semantics") != "READ_ONLY_FAIL_CLOSED_BATCH_LIFECYCLE":
        raise HistoricalAuditManifestError("historical audit lifecycle semantics drift")
    states = ["PLANNED","READY","IN_PROGRESS","REVIEW_REQUIRED","COMPLETE","BLOCKED"]
    if policy.get("states") != states:
        raise HistoricalAuditManifestError("historical audit lifecycle state set drift")
    if policy.get("initial_state") != "PLANNED" or policy.get("terminal_states") != ["COMPLETE"]:
        raise HistoricalAuditManifestError("historical audit lifecycle boundary drift")
    expected = {
        "PLANNED":["READY","BLOCKED"],
        "READY":["IN_PROGRESS","BLOCKED"],
        "IN_PROGRESS":["REVIEW_REQUIRED","BLOCKED"],
        "REVIEW_REQUIRED":["COMPLETE","BLOCKED"],
        "BLOCKED":["READY"],
        "COMPLETE":[],
    }
    if policy.get("allowed_transitions") != expected:
        raise HistoricalAuditManifestError("historical audit transition graph drift")
    if policy.get("blockers_rule") != "BLOCKED_REQUIRES_NONEMPTY_OTHER_STATES_REQUIRE_EMPTY":
        raise HistoricalAuditManifestError("historical audit blockers rule drift")


def validate_transition(source: str, target: str, policy: dict[str, Any]) -> None:
    validate_lifecycle_policy(policy)
    if source not in policy["states"] or target not in policy["states"]:
        raise HistoricalAuditManifestError("unknown historical audit lifecycle state")
    if source == target:
        raise HistoricalAuditManifestError("same-state lifecycle transition forbidden")
    if target not in policy["allowed_transitions"][source]:
        raise HistoricalAuditManifestError(f"illegal historical audit transition: {source}->{target}")


def manifest_material(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "manifest_identity_sha256"}


def validate_manifest(manifest: dict[str, Any]) -> None:
    schema = _load(SCHEMA_PATH)
    lifecycle = _load(LIFECYCLE_PATH)
    batching = _load(BATCHING_PATH)
    validate_schema_contract(schema)
    validate_lifecycle_policy(lifecycle)

    required = schema["required"]
    if list(manifest.keys()) != required:
        raise HistoricalAuditManifestError("manifest field order/set drift")
    if manifest["schema_version"] != 1 or manifest["manifest_kind"] != "historical_audit_manifest_v1":
        raise HistoricalAuditManifestError("manifest identity/version drift")
    if MANIFEST_ID.fullmatch(manifest["manifest_id"]) is None:
        raise HistoricalAuditManifestError("manifest_id malformed")
    if manifest["manifest_id"] != f"HIST-AUDIT-BATCH-{manifest['batch_index']:03d}":
        raise HistoricalAuditManifestError("manifest_id does not bind batch_index")
    if manifest["status"] not in lifecycle["states"]:
        raise HistoricalAuditManifestError("unknown manifest lifecycle status")
    if manifest["mode"] != "READ_ONLY":
        raise HistoricalAuditManifestError("historical audit manifest must be READ_ONLY")
    for field in ("plan_identity_sha256", "batch_identity_sha256", "manifest_identity_sha256"):
        value = manifest[field]
        if not isinstance(value, str) or SHA64.fullmatch(value) is None:
            raise HistoricalAuditManifestError(f"{field} must be lowercase SHA-256")

    batch_index = manifest["batch_index"]
    if not isinstance(batch_index, int) or isinstance(batch_index, bool) or batch_index < 1:
        raise HistoricalAuditManifestError("batch_index invalid")
    lots = manifest["lots"]
    if (
        not isinstance(lots, list)
        or not 1 <= len(lots) <= batching["max_lots_per_batch"]
        or any(not isinstance(x, int) or isinstance(x, bool) for x in lots)
    ):
        raise HistoricalAuditManifestError("manifest lots invalid")
    if lots != sorted(lots) or len(lots) != len(set(lots)):
        raise HistoricalAuditManifestError("manifest lots must be ordered and unique")
    if any(x < 0 or x > 44 for x in lots):
        raise HistoricalAuditManifestError("manifest includes non-historical lot")

    complexity = manifest["complexity_total"]
    if not isinstance(complexity, int) or isinstance(complexity, bool) or complexity < 1:
        raise HistoricalAuditManifestError("manifest complexity_total invalid")
    isolated = manifest["isolated_oversized"]
    if not isinstance(isolated, bool):
        raise HistoricalAuditManifestError("isolated_oversized must be boolean")
    budget = batching["complexity"]["normal_batch_budget"]
    if isolated:
        if len(lots) != 1 or complexity <= budget:
            raise HistoricalAuditManifestError("malformed oversized historical batch")
    elif complexity > budget:
        raise HistoricalAuditManifestError("normal historical batch exceeds complexity budget")

    source = manifest["source_binding"]
    expected_source_keys = [
        "repository","certified_baseline_lot","certified_baseline_verdict","source_head_sha"
    ]
    if not isinstance(source, dict) or list(source.keys()) != expected_source_keys:
        raise HistoricalAuditManifestError("source_binding shape drift")
    if source["repository"] != "tobianahillel-afk/Bot-crypto":
        raise HistoricalAuditManifestError("repository binding drift")
    if source["certified_baseline_lot"] != 44:
        raise HistoricalAuditManifestError("certified baseline lot drift")
    if source["certified_baseline_verdict"] != "GO_LOT44_POST_MERGE":
        raise HistoricalAuditManifestError("certified baseline verdict drift")
    if not isinstance(source["source_head_sha"], str) or SHA40.fullmatch(source["source_head_sha"]) is None:
        raise HistoricalAuditManifestError("source head must be lowercase SHA-40")

    permissions = manifest["permissions"]
    expected_permissions = {
        "historical_evidence_write":False,
        "business_code_write":False,
        "remediation_write":False,
        "runtime_mutation":False,
    }
    if permissions != expected_permissions:
        raise HistoricalAuditManifestError("historical audit manifest permissions must all be false")

    blockers = manifest["blockers"]
    if (
        not isinstance(blockers, list)
        or len(blockers) > 20
        or len(blockers) != len(set(blockers))
        or any(not isinstance(x, str) or not x.strip() or len(x) > 300 for x in blockers)
    ):
        raise HistoricalAuditManifestError("manifest blockers invalid")
    if manifest["status"] == "BLOCKED":
        if not blockers:
            raise HistoricalAuditManifestError("BLOCKED manifest requires explicit blocker")
    elif blockers:
        raise HistoricalAuditManifestError("non-BLOCKED manifest cannot carry blockers")

    expected_identity = _sha256(manifest_material(manifest))
    if manifest["manifest_identity_sha256"] != expected_identity:
        raise HistoricalAuditManifestError("manifest identity mismatch")


def build_manifest(
    *,
    batch: dict[str, Any],
    plan_identity_sha256: str,
    source_head_sha: str,
    status: str = "PLANNED",
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    blockers = [] if blockers is None else list(blockers)
    material = {
        "schema_version":1,
        "manifest_kind":"historical_audit_manifest_v1",
        "manifest_id":f"HIST-AUDIT-BATCH-{batch['batch_index']:03d}",
        "status":status,
        "mode":"READ_ONLY",
        "plan_identity_sha256":plan_identity_sha256,
        "batch_identity_sha256":batch["batch_identity_sha256"],
        "batch_index":batch["batch_index"],
        "lots":[item["lot"] for item in batch["lots"]],
        "complexity_total":batch["complexity_total"],
        "isolated_oversized":batch["isolated_oversized"],
        "source_binding":{
            "repository":"tobianahillel-afk/Bot-crypto",
            "certified_baseline_lot":44,
            "certified_baseline_verdict":"GO_LOT44_POST_MERGE",
            "source_head_sha":source_head_sha,
        },
        "permissions":{
            "historical_evidence_write":False,
            "business_code_write":False,
            "remediation_write":False,
            "runtime_mutation":False,
        },
        "blockers":blockers,
    }
    ordered = {
        "schema_version":material["schema_version"],
        "manifest_kind":material["manifest_kind"],
        "manifest_id":material["manifest_id"],
        "manifest_identity_sha256":"",
        "status":material["status"],
        "mode":material["mode"],
        "plan_identity_sha256":material["plan_identity_sha256"],
        "batch_identity_sha256":material["batch_identity_sha256"],
        "batch_index":material["batch_index"],
        "lots":material["lots"],
        "complexity_total":material["complexity_total"],
        "isolated_oversized":material["isolated_oversized"],
        "source_binding":material["source_binding"],
        "permissions":material["permissions"],
        "blockers":material["blockers"],
    }
    ordered["manifest_identity_sha256"] = _sha256(manifest_material(ordered))
    return ordered


def self_check() -> None:
    planner_path = ROOT / "scripts" / "governance" / "plan_historical_audit_batches.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("historical_manifest_planner", planner_path)
    if spec is None or spec.loader is None:
        raise HistoricalAuditManifestError("cannot import historical batch planner")
    planner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = planner
    spec.loader.exec_module(planner)
    plan = planner.plan_batches(planner.synthetic_request(), planner._load(planner.POLICY_PATH))
    manifest = build_manifest(
        batch=plan["batches"][0],
        plan_identity_sha256=plan["plan_identity_sha256"],
        source_head_sha="a" * 40,
    )
    validate_manifest(manifest)
    replay = build_manifest(
        batch=plan["batches"][0],
        plan_identity_sha256=plan["plan_identity_sha256"],
        source_head_sha="a" * 40,
    )
    if _canonical(manifest) != _canonical(replay):
        raise HistoricalAuditManifestError("manifest deterministic replay mismatch")
    validate_transition("PLANNED", "READY", _load(LIFECYCLE_PATH))
    print(f"HISTORICAL_AUDIT_MANIFEST_SELF_CHECK_PASS id={manifest['manifest_identity_sha256']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--transition", nargs=2, metavar=("SOURCE", "TARGET"))
    args = parser.parse_args()
    try:
        selected = sum(bool(x) for x in (args.self_check, args.manifest, args.transition))
        if selected != 1:
            raise HistoricalAuditManifestError("select exactly one validation mode")
        if args.self_check:
            self_check()
        elif args.manifest:
            validate_manifest(_load(args.manifest))
            print("HISTORICAL_AUDIT_MANIFEST_VALID")
        else:
            validate_transition(args.transition[0], args.transition[1], _load(LIFECYCLE_PATH))
            print("HISTORICAL_AUDIT_TRANSITION_VALID")
    except (HistoricalAuditManifestError, KeyError, TypeError) as exc:
        print(f"HISTORICAL_AUDIT_MANIFEST_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
