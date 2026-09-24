#!/usr/bin/env python3
"""Re-qualify ENG-07 against canonical immutable historical evidence protection."""

from __future__ import annotations

import argparse
import ast
import copy
import fnmatch
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = (
    ROOT / "config" / "governance" /
    "historical_audit_evidence_protection_policy_v1.json"
)
ENG07_MANIFEST = ROOT / "engineering" / "lots" / "ENG-07.json"
WORK_UNITS = ROOT / "engineering" / "work_units"


class HistoricalAuditEvidenceProtectionError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalAuditEvidenceProtectionError(
            f"cannot load {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise HistoricalAuditEvidenceProtectionError(
            f"{path} must contain an object"
        )
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise HistoricalAuditEvidenceProtectionError(
            f"cannot import {path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise HistoricalAuditEvidenceProtectionError(
            "unsupported audit evidence protection policy version"
        )
    if policy.get("policy_kind") != (
        "historical_audit_evidence_protection_policy_v1"
    ):
        raise HistoricalAuditEvidenceProtectionError(
            "invalid audit evidence protection policy kind"
        )
    if policy.get("semantics") != (
        "BIND_AUDIT_ENGINE_TO_CANONICAL_IMMUTABLE_EVIDENCE_WITHOUT_WRITE_AUTHORITY"
    ):
        raise HistoricalAuditEvidenceProtectionError(
            "audit evidence protection semantics drift"
        )

    canonical = policy.get("canonical_protection")
    if canonical != {
        "policy_path":"engineering/HISTORICAL_EVIDENCE_PROTECTION.json",
        "validator_path":"scripts/governance/validate_historical_evidence_protection.py",
        "expected_policy_kind":"historical_evidence_protection",
        "comparison_base":"origin/main",
    }:
        raise HistoricalAuditEvidenceProtectionError(
            "canonical historical protection binding drift"
        )

    expected_policies = [
        "config/governance/historical_audit_findings_policy_v1.json",
        "config/governance/historical_audit_report_policy_v1.json",
    ]
    if policy.get("audit_policy_bindings") != expected_policies:
        raise HistoricalAuditEvidenceProtectionError(
            "audit policy binding set/order drift"
        )

    expected_validators = [
        "scripts/governance/plan_historical_audit_batches.py",
        "scripts/governance/validate_historical_audit_manifest.py",
        "scripts/governance/validate_historical_audit_mapping.py",
        "scripts/governance/validate_historical_audit_findings.py",
        "scripts/governance/validate_historical_audit_report.py",
    ]
    if policy.get("audit_validator_paths") != expected_validators:
        raise HistoricalAuditEvidenceProtectionError(
            "audit validator path set/order drift"
        )

    permissions = policy.get("required_mutation_permissions")
    if not isinstance(permissions, dict) or not permissions or any(
        value is not False for value in permissions.values()
    ):
        raise HistoricalAuditEvidenceProtectionError(
            "required mutation permissions must all remain false"
        )

    authority = policy.get("authority")
    if not isinstance(authority, dict) or not authority or any(
        value is not False for value in authority.values()
    ):
        raise HistoricalAuditEvidenceProtectionError(
            "audit/remediation authority flags must all remain false"
        )

    prefixes = policy.get("forbidden_scope_prefixes")
    if prefixes != [
        "src/crypto_quant_bot/","data/audit/","reports/lot","contracts/"
    ]:
        raise HistoricalAuditEvidenceProtectionError(
            "forbidden audit scope prefixes drift"
        )

    queue_fields = policy.get("forbidden_queue_fields")
    if not isinstance(queue_fields, list) or not queue_fields:
        raise HistoricalAuditEvidenceProtectionError(
            "forbidden remediation queue fields missing"
        )
    if len(queue_fields) != len(set(queue_fields)):
        raise HistoricalAuditEvidenceProtectionError(
            "forbidden remediation queue fields duplicated"
        )


def validate_canonical_protection(policy: dict[str, Any]) -> dict[str, Any]:
    canonical = policy["canonical_protection"]
    canonical_policy = _load(ROOT / canonical["policy_path"])
    if canonical_policy.get("policy_kind") != canonical["expected_policy_kind"]:
        raise HistoricalAuditEvidenceProtectionError(
            "canonical evidence protection kind drift"
        )
    if canonical_policy.get("comparison_base") != canonical["comparison_base"]:
        raise HistoricalAuditEvidenceProtectionError(
            "canonical evidence comparison base drift"
        )

    module = _module(
        "eng07_canonical_historical_protection",
        ROOT / canonical["validator_path"],
    )
    try:
        module.validate(canonical_policy)
    except module.EvidenceProtectionError as exc:
        raise HistoricalAuditEvidenceProtectionError(
            f"canonical historical evidence protection invalid: {exc}"
        ) from exc
    return canonical_policy


def validate_permission_object(
    value: dict[str, Any],
    expected: dict[str, bool],
    label: str,
) -> None:
    if value.get("mutation_permissions") != expected:
        raise HistoricalAuditEvidenceProtectionError(
            f"audit policy gained mutation authority: {label}"
        )


def validate_mutation_permissions(policy: dict[str, Any]) -> None:
    expected = policy["required_mutation_permissions"]
    for path_text in policy["audit_policy_bindings"]:
        validate_permission_object(_load(ROOT / path_text), expected, path_text)


def _import_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _call_name(node: ast.Call) -> tuple[str | None, str | None]:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id, None
    if isinstance(func, ast.Attribute):
        return None, func.attr
    return None, None


def validate_source_text_no_write(
    path_text: str,
    source: str,
    policy: dict[str, Any],
) -> None:
    try:
        tree = ast.parse(source, filename=path_text)
    except SyntaxError as exc:
        raise HistoricalAuditEvidenceProtectionError(
            f"cannot statically inspect audit validator {path_text}: {exc}"
        ) from exc

    bad_imports = sorted(
        _import_roots(tree) & set(policy["forbidden_import_roots"])
    )
    if bad_imports:
        raise HistoricalAuditEvidenceProtectionError(
            f"audit validator imports mutation-capable client: "
            f"{path_text}: {bad_imports}"
        )

    forbidden_names = set(policy["forbidden_call_names"])
    forbidden_attrs = set(policy["forbidden_call_attributes"])
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name, attr = _call_name(node)
        if name in forbidden_names or attr in forbidden_attrs:
            call = name if name is not None else attr
            raise HistoricalAuditEvidenceProtectionError(
                f"audit validator contains forbidden write primitive: "
                f"{path_text}:{getattr(node, 'lineno', '?')}:{call}"
            )


def validate_no_write_validators(policy: dict[str, Any]) -> None:
    for path_text in policy["audit_validator_paths"]:
        path = ROOT / path_text
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise HistoricalAuditEvidenceProtectionError(
                f"cannot read audit validator {path_text}: {exc}"
            ) from exc
        validate_source_text_no_write(path_text, source, policy)


def _pattern_hits_forbidden(path_pattern: str, prefixes: list[str]) -> bool:
    if path_pattern.startswith(tuple(prefixes)):
        return True
    probe_paths = [
        "src/crypto_quant_bot/example.py",
        "data/audit/example.json",
        "reports/lot44/example.json",
        "contracts/example.json",
    ]
    return any(fnmatch.fnmatchcase(probe, path_pattern) for probe in probe_paths)


def validate_allowed_paths(
    awu_name: str,
    allowed: list[Any],
    protected: set[str],
    prefixes: list[str],
) -> None:
    for candidate in allowed:
        if not isinstance(candidate, str):
            raise HistoricalAuditEvidenceProtectionError(
                f"ENG-07 AWU contains non-string allowed path: {awu_name}"
            )
        if candidate in protected:
            raise HistoricalAuditEvidenceProtectionError(
                f"ENG-07 AWU can edit protected historical evidence: "
                f"{awu_name}:{candidate}"
            )
        if _pattern_hits_forbidden(candidate, prefixes):
            raise HistoricalAuditEvidenceProtectionError(
                f"ENG-07 AWU scope reaches historical/business prefix: "
                f"{awu_name}:{candidate}"
            )


def validate_eng07_scopes(
    policy: dict[str, Any],
    canonical_policy: dict[str, Any],
) -> None:
    manifest = _load(ENG07_MANIFEST)
    required_forbidden = policy["required_parent_forbidden_scope"]
    forbidden_scope = manifest.get("forbidden_scope")
    if not isinstance(forbidden_scope, list):
        raise HistoricalAuditEvidenceProtectionError(
            "ENG-07 forbidden scope missing"
        )
    missing = [
        item for item in required_forbidden if item not in forbidden_scope
    ]
    if missing:
        raise HistoricalAuditEvidenceProtectionError(
            f"ENG-07 parent scope lost mandatory prohibition: {missing}"
        )

    protected = set(canonical_policy["protected_current_tree_paths"])
    prefixes = policy["forbidden_scope_prefixes"]
    paths = sorted(WORK_UNITS.glob(policy["work_unit_glob"]))
    if not paths:
        raise HistoricalAuditEvidenceProtectionError(
            "no ENG-07 operational work units found"
        )

    for path in paths:
        awu = _load(path)
        if awu.get("parent", {}).get("work_item_id") != "ENG-07":
            continue
        allowed = awu.get("scope", {}).get("allowed_paths")
        if not isinstance(allowed, list):
            raise HistoricalAuditEvidenceProtectionError(
                f"ENG-07 AWU missing allowed_paths: {path.name}"
            )
        validate_allowed_paths(path.name, allowed, protected, prefixes)


def validate_queue_properties(
    properties: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    normalized = {str(key).lower() for key in properties}
    forbidden = {field.lower() for field in policy["forbidden_queue_fields"]}
    overlap = sorted(normalized & forbidden)
    if overlap:
        raise HistoricalAuditEvidenceProtectionError(
            f"remediation queue gained write-authority fields: {overlap}"
        )


def validate_queue_has_no_write_authority(policy: dict[str, Any]) -> None:
    schema = _load(ROOT / policy["report_schema_path"])
    try:
        properties = schema["$defs"]["remediation_queue_item"]["properties"]
    except (KeyError, TypeError) as exc:
        raise HistoricalAuditEvidenceProtectionError(
            "report remediation queue schema missing"
        ) from exc
    if not isinstance(properties, dict):
        raise HistoricalAuditEvidenceProtectionError(
            "report remediation queue properties invalid"
        )
    validate_queue_properties(properties, policy)


def validate_repository(policy: dict[str, Any]) -> None:
    validate_policy(policy)
    canonical = validate_canonical_protection(policy)
    validate_mutation_permissions(policy)
    validate_no_write_validators(policy)
    validate_eng07_scopes(policy, canonical)
    validate_queue_has_no_write_authority(policy)


def _expect_invalid(fn: Any, label: str) -> None:
    try:
        fn()
    except HistoricalAuditEvidenceProtectionError:
        return
    raise AssertionError(
        f"audit evidence protection negative scenario unexpectedly passed: {label}"
    )


def self_check() -> None:
    policy = _load(POLICY_PATH)
    validate_repository(policy)

    writable = copy.deepcopy(policy)
    writable["authority"]["remediation_execution_authority"] = True
    _expect_invalid(lambda: validate_policy(writable), "remediation authority")

    missing_guard = copy.deepcopy(policy)
    missing_guard["forbidden_scope_prefixes"] = [
        "src/crypto_quant_bot/","reports/lot","contracts/"
    ]
    _expect_invalid(lambda: validate_policy(missing_guard), "data/audit guard removal")

    missing_validator = copy.deepcopy(policy)
    missing_validator["audit_validator_paths"] = missing_validator[
        "audit_validator_paths"
    ][:-1]
    _expect_invalid(lambda: validate_policy(missing_validator), "validator coverage removal")

    fake_schema_policy = copy.deepcopy(policy)
    original = fake_schema_policy["report_schema_path"]
    fake_schema_policy["report_schema_path"] = (
        "config/governance/historical_audit_report_schema_v1.json"
    )
    if fake_schema_policy["report_schema_path"] != original:
        raise AssertionError("report schema policy fixture drift")

    print(
        "HISTORICAL_AUDIT_EVIDENCE_PROTECTION_SELF_CHECK_PASS "
        "repository=PASS probes=3"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    try:
        policy = _load(POLICY_PATH)
        if args.self_check:
            self_check()
        else:
            validate_repository(policy)
    except (
        HistoricalAuditEvidenceProtectionError,
        AssertionError,
        KeyError,
        TypeError,
    ) as exc:
        print(
            f"HISTORICAL_AUDIT_EVIDENCE_PROTECTION_INVALID: {exc}",
            file=sys.stderr,
        )
        return 1
    print(
        "HISTORICAL_AUDIT_EVIDENCE_PROTECTION_VALID"
        if args.check
        else "HISTORICAL_AUDIT_EVIDENCE_PROTECTION_SELF_CHECK_VALID"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
