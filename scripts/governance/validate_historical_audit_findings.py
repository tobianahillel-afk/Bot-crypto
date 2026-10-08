#!/usr/bin/env python3
"""Validate source-bound read-only historical audit findings registries."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "config" / "governance" / "historical_audit_findings_schema_v1.json"
POLICY_PATH = ROOT / "config" / "governance" / "historical_audit_findings_policy_v1.json"
REGISTRY_KIND = "historical_audit_findings_registry_v1"
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
REGISTRY_ID_RE = re.compile(r"^HIST-FIND-B[0-9]{3}-L[0-9]{3}$")
FINDING_ID_RE = re.compile(r"^HIST-FIND-B[0-9]{3}-L[0-9]{3}-F[0-9]{3}$")


class HistoricalAuditFindingsError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalAuditFindingsError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HistoricalAuditFindingsError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise HistoricalAuditFindingsError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HistoricalAuditFindingsError(f"non-canonical JSON value: {exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def registry_material(registry: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in registry.items() if key != "registry_identity_sha256"}


def _validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("title") != "HistoricalAuditFindingsRegistryV1":
        raise HistoricalAuditFindingsError("findings schema title drift")
    if schema.get("additionalProperties") is not False:
        raise HistoricalAuditFindingsError("findings schema must be closed")
    expected = [
        "schema_version","registry_kind","mode","registry_id",
        "manifest_identity_sha256","mapping_identity_sha256",
        "plan_identity_sha256","batch_identity_sha256","lot",
        "audit_result","finding_count","findings","mutation_permissions",
        "registry_identity_sha256",
    ]
    if schema.get("required") != expected:
        raise HistoricalAuditFindingsError("findings schema required-field drift")
    defs = schema.get("$defs")
    if not isinstance(defs, dict) or set(defs) != {"sha256","repository_ref","finding"}:
        raise HistoricalAuditFindingsError("findings schema definitions drift")


def _validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise HistoricalAuditFindingsError("unsupported findings policy version")
    if policy.get("policy_kind") != "historical_audit_findings_policy_v1":
        raise HistoricalAuditFindingsError("invalid findings policy kind")
    if policy.get("semantics") != "SOURCE_BOUND_READ_ONLY_FINDINGS_WITH_EXPLICIT_DISPOSITION":
        raise HistoricalAuditFindingsError("findings policy semantics drift")
    if policy.get("historical_lot_range") != {"min":0,"max":44}:
        raise HistoricalAuditFindingsError("historical lot range drift")
    if policy.get("registry_mode") != "READ_ONLY":
        raise HistoricalAuditFindingsError("findings registry must remain READ_ONLY")
    if policy.get("audit_results") != ["CLEAN","FINDINGS"]:
        raise HistoricalAuditFindingsError("audit result order/set drift")
    if policy.get("severity_order") != ["BLOCKER","MAJOR","MINOR","INFO"]:
        raise HistoricalAuditFindingsError("severity order drift")
    if policy.get("statuses") != ["OPEN","CLOSED"]:
        raise HistoricalAuditFindingsError("finding status set drift")
    expected_dispositions = [
        "UNRESOLVED","REMEDIATION_REQUIRED","DEFERRED",
        "ACCEPTED_RISK","FALSE_POSITIVE","RESOLVED",
    ]
    if policy.get("dispositions") != expected_dispositions:
        raise HistoricalAuditFindingsError("finding disposition set drift")
    if policy.get("status_dispositions") != {
        "OPEN":["UNRESOLVED","REMEDIATION_REQUIRED","DEFERRED"],
        "CLOSED":["ACCEPTED_RISK","FALSE_POSITIVE","RESOLVED"],
    }:
        raise HistoricalAuditFindingsError("status/disposition policy drift")
    permissions = policy.get("mutation_permissions")
    if not isinstance(permissions, dict) or not permissions or any(permissions.values()):
        raise HistoricalAuditFindingsError("findings mutation permissions must all be false")
    identity = policy.get("identity")
    if not isinstance(identity, dict) or identity.get("algorithm") != "sha256":
        raise HistoricalAuditFindingsError("findings identity policy drift")
    if identity.get("excluded_fields") != ["registry_identity_sha256"]:
        raise HistoricalAuditFindingsError("findings identity exclusion drift")
    prefixes = policy.get("reference_prefixes")
    if not isinstance(prefixes, list) or not prefixes or len(prefixes) != len(set(prefixes)):
        raise HistoricalAuditFindingsError("findings reference prefixes invalid")


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HistoricalAuditFindingsError(f"{label} must be non-empty")
    return value


def _safe_path(path: Any, prefixes: list[str]) -> str:
    if not isinstance(path, str) or not path:
        raise HistoricalAuditFindingsError("finding reference path missing")
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() != path:
        raise HistoricalAuditFindingsError(f"finding reference path is unsafe: {path!r}")
    if not any(path.startswith(prefix) for prefix in prefixes):
        raise HistoricalAuditFindingsError(f"finding reference path outside allowed prefixes: {path}")
    return path


def _validate_references(values: Any, policy: dict[str, Any]) -> None:
    if not isinstance(values, list) or not values:
        raise HistoricalAuditFindingsError("finding references must be non-empty")
    seen: set[bytes] = set()
    for item in values:
        if not isinstance(item, dict) or set(item) != {"path","locator"}:
            raise HistoricalAuditFindingsError("invalid finding reference shape")
        _safe_path(item["path"], policy["reference_prefixes"])
        _nonempty(item["locator"], "finding reference locator")
        encoded = _canonical(item)
        if encoded in seen:
            raise HistoricalAuditFindingsError("duplicate finding reference")
        seen.add(encoded)


def _validate_finding(
    finding: Any,
    *,
    policy: dict[str, Any],
    expected_id: str,
    requirement_ids: set[str],
) -> None:
    required = {
        "finding_id","requirement_id","finding_type","severity",
        "previous_severity","severity_change_rationale","status","disposition",
        "owner","summary","rationale","references",
    }
    if not isinstance(finding, dict) or set(finding) != required:
        raise HistoricalAuditFindingsError("invalid finding field set")
    if finding["finding_id"] != expected_id or FINDING_ID_RE.fullmatch(finding["finding_id"]) is None:
        raise HistoricalAuditFindingsError("finding_id is not deterministic for batch/lot/index")
    if finding["requirement_id"] not in requirement_ids:
        raise HistoricalAuditFindingsError(
            f"finding references unknown requirement_id: {finding['requirement_id']}"
        )
    if finding["finding_type"] not in policy["finding_types"]:
        raise HistoricalAuditFindingsError("unknown finding_type")
    severity = finding["severity"]
    previous = finding["previous_severity"]
    if severity not in policy["severity_order"]:
        raise HistoricalAuditFindingsError("unknown finding severity")
    if previous is not None and previous not in policy["severity_order"]:
        raise HistoricalAuditFindingsError("unknown previous severity")
    change_reason = finding["severity_change_rationale"]
    if previous is None:
        if change_reason is not None:
            raise HistoricalAuditFindingsError("new finding cannot carry severity change rationale")
    else:
        if previous == severity:
            raise HistoricalAuditFindingsError("previous severity must differ from current severity")
        _nonempty(change_reason, "severity_change_rationale")

    status = finding["status"]
    disposition = finding["disposition"]
    if status not in policy["statuses"]:
        raise HistoricalAuditFindingsError("unknown finding status")
    if disposition not in policy["status_dispositions"][status]:
        raise HistoricalAuditFindingsError("finding disposition incompatible with status")
    _nonempty(finding["owner"], "finding owner")
    _nonempty(finding["summary"], "finding summary")
    rationale = finding["rationale"]
    if disposition in policy["rationale_required_dispositions"]:
        _nonempty(rationale, "finding rationale")
    elif rationale is not None:
        raise HistoricalAuditFindingsError("UNRESOLVED finding rationale must be null")
    _validate_references(finding["references"], policy)


def validate_registry(
    registry: dict[str, Any],
    mapping: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
) -> None:
    schema = _load(SCHEMA_PATH)
    policy = _load(POLICY_PATH)
    _validate_schema_contract(schema)
    _validate_policy(policy)

    mapping_mod = _module(
        "historical_findings_mapping_binding",
        ROOT / "scripts" / "governance" / "validate_historical_audit_mapping.py",
    )
    try:
        mapping_mod.validate_mapping(mapping, manifest, plan)
    except mapping_mod.HistoricalAuditMappingError as exc:
        raise HistoricalAuditFindingsError(f"bound historical mapping invalid: {exc}") from exc

    required = schema["required"]
    if not isinstance(registry, dict) or list(registry.keys()) != required:
        raise HistoricalAuditFindingsError("findings registry field order/set drift")
    if registry["schema_version"] != 1 or registry["registry_kind"] != REGISTRY_KIND:
        raise HistoricalAuditFindingsError("findings registry identity/version drift")
    if registry["mode"] != "READ_ONLY":
        raise HistoricalAuditFindingsError("findings registry must remain READ_ONLY")
    if not isinstance(registry["registry_id"], str) or REGISTRY_ID_RE.fullmatch(registry["registry_id"]) is None:
        raise HistoricalAuditFindingsError("invalid findings registry_id")

    bindings = {
        "manifest_identity_sha256": manifest["manifest_identity_sha256"],
        "mapping_identity_sha256": mapping["mapping_identity_sha256"],
        "plan_identity_sha256": manifest["plan_identity_sha256"],
        "batch_identity_sha256": manifest["batch_identity_sha256"],
        "lot": mapping["lot"],
    }
    for field, expected in bindings.items():
        if registry[field] != expected:
            raise HistoricalAuditFindingsError(f"findings registry {field} binding mismatch")
    lot = registry["lot"]
    if not isinstance(lot, int) or isinstance(lot, bool) or not 0 <= lot <= 44:
        raise HistoricalAuditFindingsError("findings registry lot must be historical Lot 0..44")
    if lot not in manifest["lots"]:
        raise HistoricalAuditFindingsError("findings registry lot outside bound manifest batch")
    expected_registry_id = f"HIST-FIND-B{manifest['batch_index']:03d}-L{lot:03d}"
    if registry["registry_id"] != expected_registry_id:
        raise HistoricalAuditFindingsError("findings registry_id does not bind batch/lot")
    if registry["mutation_permissions"] != policy["mutation_permissions"]:
        raise HistoricalAuditFindingsError("findings mutation permissions drift")

    findings = registry["findings"]
    if not isinstance(findings, list):
        raise HistoricalAuditFindingsError("findings must be a list")
    if registry["finding_count"] != len(findings):
        raise HistoricalAuditFindingsError("finding_count mismatch")
    expected_result = "CLEAN" if not findings else "FINDINGS"
    if registry["audit_result"] != expected_result:
        raise HistoricalAuditFindingsError("audit_result does not match findings presence")

    ids = [item.get("finding_id") if isinstance(item, dict) else None for item in findings]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise HistoricalAuditFindingsError("finding ids must be strictly sorted and unique")
    req_ids = {req["requirement_id"] for req in mapping["requirements"]}
    prefix = f"HIST-FIND-B{manifest['batch_index']:03d}-L{lot:03d}-F"
    for index, finding in enumerate(findings, 1):
        _validate_finding(
            finding,
            policy=policy,
            expected_id=f"{prefix}{index:03d}",
            requirement_ids=req_ids,
        )

    identity = registry["registry_identity_sha256"]
    if not isinstance(identity, str) or SHA64_RE.fullmatch(identity) is None:
        raise HistoricalAuditFindingsError("findings registry identity must be SHA-256")
    if identity != _sha256(registry_material(registry)):
        raise HistoricalAuditFindingsError("findings registry identity mismatch")


def build_registry(
    mapping: dict[str, Any],
    manifest: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    policy = _load(POLICY_PATH)
    lot = mapping["lot"]
    material = {
        "schema_version":1,
        "registry_kind":REGISTRY_KIND,
        "mode":"READ_ONLY",
        "registry_id":f"HIST-FIND-B{manifest['batch_index']:03d}-L{lot:03d}",
        "manifest_identity_sha256":manifest["manifest_identity_sha256"],
        "mapping_identity_sha256":mapping["mapping_identity_sha256"],
        "plan_identity_sha256":manifest["plan_identity_sha256"],
        "batch_identity_sha256":manifest["batch_identity_sha256"],
        "lot":lot,
        "audit_result":"CLEAN" if not findings else "FINDINGS",
        "finding_count":len(findings),
        "findings":copy.deepcopy(findings),
        "mutation_permissions":copy.deepcopy(policy["mutation_permissions"]),
        "registry_identity_sha256":"",
    }
    material["registry_identity_sha256"] = _sha256(registry_material(material))
    return material


def _rehash(registry: dict[str, Any]) -> None:
    registry["registry_identity_sha256"] = _sha256(registry_material(registry))


def _expect_invalid(
    registry: dict[str, Any],
    mapping: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
    label: str,
) -> None:
    try:
        validate_registry(registry, mapping, manifest, plan)
    except HistoricalAuditFindingsError:
        return
    raise AssertionError(f"findings negative scenario unexpectedly passed: {label}")


def self_check() -> None:
    mapping_mod = _module(
        "historical_findings_mapping_fixture",
        ROOT / "scripts" / "governance" / "validate_historical_audit_mapping.py",
    )
    mapping, manifest, plan = mapping_mod._synthetic_bundle()
    validate_registry(build_registry(mapping, manifest, []), mapping, manifest, plan)

    lot = mapping["lot"]
    finding = {
        "finding_id":f"HIST-FIND-B{manifest['batch_index']:03d}-L{lot:03d}-F001",
        "requirement_id":mapping["requirements"][0]["requirement_id"],
        "finding_type":"CONTROL_GAP",
        "severity":"MAJOR",
        "previous_severity":None,
        "severity_change_rationale":None,
        "status":"OPEN",
        "disposition":"UNRESOLVED",
        "owner":"engineering-audit",
        "summary":"Synthetic control gap for contract qualification.",
        "rationale":None,
        "references":[
            {"path":"docs/LOT_SPECIFICATION_STANDARD.md","locator":"synthetic finding"}
        ],
    }
    populated = build_registry(mapping, manifest, [finding])
    validate_registry(populated, mapping, manifest, plan)

    unknown_req = copy.deepcopy(populated)
    unknown_req["findings"][0]["requirement_id"] = "UNKNOWN-REQ"
    _rehash(unknown_req)
    _expect_invalid(unknown_req, mapping, manifest, plan, "unknown requirement")

    bad_disposition = copy.deepcopy(populated)
    bad_disposition["findings"][0]["disposition"] = "ACCEPTED_RISK"
    bad_disposition["findings"][0]["status"] = "CLOSED"
    bad_disposition["findings"][0]["rationale"] = None
    _rehash(bad_disposition)
    _expect_invalid(bad_disposition, mapping, manifest, plan, "closed disposition without rationale")

    traversal = copy.deepcopy(populated)
    traversal["findings"][0]["references"][0]["path"] = "../secret.txt"
    _rehash(traversal)
    _expect_invalid(traversal, mapping, manifest, plan, "path traversal")

    downgrade = copy.deepcopy(populated)
    downgrade["findings"][0]["severity"] = "MINOR"
    downgrade["findings"][0]["previous_severity"] = "MAJOR"
    downgrade["findings"][0]["severity_change_rationale"] = None
    _rehash(downgrade)
    _expect_invalid(downgrade, mapping, manifest, plan, "silent severity downgrade")

    late_lot = copy.deepcopy(populated)
    late_lot["lot"] = 45
    _rehash(late_lot)
    _expect_invalid(late_lot, mapping, manifest, plan, "Lot45 registry")

    tampered = copy.deepcopy(populated)
    tampered["findings"][0]["summary"] = "tampered"
    _expect_invalid(tampered, mapping, manifest, plan, "identity tamper")

    print("HISTORICAL_AUDIT_FINDINGS_SELF_CHECK_PASS probes=7")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    try:
        if args.self_check:
            if any((args.registry, args.mapping, args.manifest, args.plan)):
                raise HistoricalAuditFindingsError(
                    "--self-check cannot be combined with registry inputs"
                )
            self_check()
        else:
            if not all((args.registry, args.mapping, args.manifest, args.plan)):
                raise HistoricalAuditFindingsError(
                    "--registry, --mapping, --manifest and --plan are required together"
                )
            validate_registry(
                _load(args.registry), _load(args.mapping), _load(args.manifest), _load(args.plan)
            )
            print("HISTORICAL_AUDIT_FINDINGS_VALID")
    except (HistoricalAuditFindingsError, AssertionError, KeyError, TypeError) as exc:
        print(f"HISTORICAL_AUDIT_FINDINGS_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
