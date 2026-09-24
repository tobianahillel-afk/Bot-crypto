#!/usr/bin/env python3
"""Validate source-bound read-only historical requirement traceability mappings."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "config" / "governance" / "historical_audit_mapping_schema_v1.json"
POLICY_PATH = ROOT / "config" / "governance" / "historical_audit_mapping_policy_v1.json"
MAPPING_KIND = "historical_audit_traceability_mapping_v1"
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
REQ_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,119}$")
MAPPING_ID_RE = re.compile(r"^HIST-MAP-B[0-9]{3}-L[0-9]{3}$")


class HistoricalAuditMappingError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalAuditMappingError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HistoricalAuditMappingError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise HistoricalAuditMappingError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        raise HistoricalAuditMappingError(f"non-canonical JSON value: {exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def mapping_material(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if key != "mapping_identity_sha256"}


def _validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("title") != "HistoricalAuditTraceabilityMappingV1":
        raise HistoricalAuditMappingError("mapping schema title drift")
    if schema.get("additionalProperties") is not False:
        raise HistoricalAuditMappingError("mapping schema must be closed")
    required = schema.get("required")
    expected = [
        "schema_version","mapping_kind","mode","mapping_id",
        "manifest_identity_sha256","plan_identity_sha256","batch_identity_sha256",
        "lot","requirements","mutation_permissions","mapping_identity_sha256",
    ]
    if required != expected:
        raise HistoricalAuditMappingError("mapping schema required-field drift")
    defs = schema.get("$defs")
    if not isinstance(defs, dict) or set(defs) != {
        "sha256","source_ref","location_ref","symbol_ref","test_ref","requirement"
    }:
        raise HistoricalAuditMappingError("mapping schema definitions drift")


def _validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise HistoricalAuditMappingError("unsupported mapping policy version")
    if policy.get("policy_kind") != "historical_audit_mapping_policy_v1":
        raise HistoricalAuditMappingError("invalid mapping policy kind")
    if policy.get("semantics") != "SOURCE_BOUND_READ_ONLY_TRACEABILITY_WITH_EXPLICIT_GAPS":
        raise HistoricalAuditMappingError("mapping policy semantics drift")
    if policy.get("historical_lot_range") != {"min": 0, "max": 44}:
        raise HistoricalAuditMappingError("historical lot range drift")
    if policy.get("mapping_mode") != "READ_ONLY":
        raise HistoricalAuditMappingError("mapping mode must remain READ_ONLY")
    if policy.get("coverage_statuses") != ["MAPPED","JUSTIFIED_NON_CODE","UNRESOLVED"]:
        raise HistoricalAuditMappingError("coverage status order/set drift")
    if policy.get("requirement_categories") != [
        "FUNCTIONAL","SAFETY","GOVERNANCE","DOCUMENTATION","EVIDENCE"
    ]:
        raise HistoricalAuditMappingError("requirement category drift")
    permissions = policy.get("mutation_permissions")
    if not isinstance(permissions, dict) or not permissions or any(permissions.values()):
        raise HistoricalAuditMappingError("mapping mutation permissions must all be false")
    identity = policy.get("identity")
    if not isinstance(identity, dict) or identity.get("algorithm") != "sha256":
        raise HistoricalAuditMappingError("mapping identity policy drift")
    if identity.get("excluded_fields") != ["mapping_identity_sha256"]:
        raise HistoricalAuditMappingError("mapping identity exclusion drift")
    prefixes = policy.get("reference_prefixes")
    expected_kinds = {
        "requirement_source","design_section","implementation_symbol",
        "test_id","contract_artifact","evidence_artifact",
    }
    if not isinstance(prefixes, dict) or set(prefixes) != expected_kinds:
        raise HistoricalAuditMappingError("mapping reference prefix policy drift")
    for kind, values in prefixes.items():
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            raise HistoricalAuditMappingError(f"invalid reference prefixes for {kind}")


def _safe_path(path: Any, prefixes: list[str], label: str) -> str:
    if not isinstance(path, str) or not path:
        raise HistoricalAuditMappingError(f"{label} path missing")
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HistoricalAuditMappingError(f"{label} path escapes repository: {path!r}")
    normalized = candidate.as_posix()
    if normalized != path:
        raise HistoricalAuditMappingError(f"{label} path is not canonical: {path!r}")
    if not any(normalized.startswith(prefix) for prefix in prefixes):
        raise HistoricalAuditMappingError(
            f"{label} path outside allowed prefixes: {normalized}"
        )
    return normalized


def _nonempty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HistoricalAuditMappingError(f"{label} must be non-empty")
    return value


def _validate_unique_refs(
    values: Any,
    *,
    kind: str,
    prefixes: list[str],
    text_key: str,
) -> list[dict[str, str]]:
    if not isinstance(values, list):
        raise HistoricalAuditMappingError(f"{kind} references must be a list")
    seen: set[bytes] = set()
    result: list[dict[str, str]] = []
    for item in values:
        if not isinstance(item, dict) or set(item) != {"path", text_key}:
            raise HistoricalAuditMappingError(f"invalid {kind} reference shape")
        _safe_path(item["path"], prefixes, kind)
        _nonempty_text(item[text_key], f"{kind}.{text_key}")
        encoded = _canonical(item)
        if encoded in seen:
            raise HistoricalAuditMappingError(f"duplicate {kind} reference")
        seen.add(encoded)
        result.append(item)
    return result


def _validate_source(value: Any, policy: dict[str, Any]) -> None:
    if not isinstance(value, dict) or set(value) != {
        "path","locator","requirement_sha256"
    }:
        raise HistoricalAuditMappingError("invalid requirement source shape")
    _safe_path(
        value["path"],
        policy["reference_prefixes"]["requirement_source"],
        "requirement_source",
    )
    _nonempty_text(value["locator"], "requirement_source.locator")
    if not isinstance(value["requirement_sha256"], str) or SHA64_RE.fullmatch(
        value["requirement_sha256"]
    ) is None:
        raise HistoricalAuditMappingError("requirement source digest must be SHA-256")


def _validate_requirement(req: Any, policy: dict[str, Any]) -> None:
    required_keys = {
        "requirement_id","category","source","design_sections",
        "implementation_symbols","test_ids","contract_artifacts",
        "evidence_artifacts","coverage_status","justification","gap_reason",
    }
    if not isinstance(req, dict) or set(req) != required_keys:
        raise HistoricalAuditMappingError("invalid requirement mapping shape")
    req_id = req["requirement_id"]
    if not isinstance(req_id, str) or REQ_ID_RE.fullmatch(req_id) is None:
        raise HistoricalAuditMappingError(f"invalid requirement_id: {req_id!r}")
    if req["category"] not in policy["requirement_categories"]:
        raise HistoricalAuditMappingError(f"invalid requirement category: {req['category']!r}")
    _validate_source(req["source"], policy)

    refs = policy["reference_prefixes"]
    design = _validate_unique_refs(
        req["design_sections"], kind="design_section",
        prefixes=refs["design_section"], text_key="locator",
    )
    implementation = _validate_unique_refs(
        req["implementation_symbols"], kind="implementation_symbol",
        prefixes=refs["implementation_symbol"], text_key="symbol",
    )
    tests = _validate_unique_refs(
        req["test_ids"], kind="test_id",
        prefixes=refs["test_id"], text_key="test_id",
    )
    contracts = _validate_unique_refs(
        req["contract_artifacts"], kind="contract_artifact",
        prefixes=refs["contract_artifact"], text_key="locator",
    )
    evidence = _validate_unique_refs(
        req["evidence_artifacts"], kind="evidence_artifact",
        prefixes=refs["evidence_artifact"], text_key="locator",
    )

    status = req["coverage_status"]
    if status not in policy["coverage_statuses"]:
        raise HistoricalAuditMappingError(f"invalid coverage status: {status!r}")
    justification = req["justification"]
    gap_reason = req["gap_reason"]

    if status == "MAPPED":
        if not all((design, implementation, tests, contracts, evidence)):
            raise HistoricalAuditMappingError(
                f"MAPPED requirement {req_id} lacks complete traceability coverage"
            )
        if justification is not None or gap_reason is not None:
            raise HistoricalAuditMappingError(
                f"MAPPED requirement {req_id} cannot carry justification/gap reason"
            )
    elif status == "JUSTIFIED_NON_CODE":
        if not design or not evidence:
            raise HistoricalAuditMappingError(
                f"JUSTIFIED_NON_CODE requirement {req_id} needs design and evidence"
            )
        if implementation or tests:
            raise HistoricalAuditMappingError(
                f"JUSTIFIED_NON_CODE requirement {req_id} cannot invent code/tests"
            )
        _nonempty_text(justification, f"{req_id}.justification")
        if gap_reason is not None:
            raise HistoricalAuditMappingError(
                f"JUSTIFIED_NON_CODE requirement {req_id} cannot carry gap_reason"
            )
    else:
        _nonempty_text(gap_reason, f"{req_id}.gap_reason")
        if justification is not None:
            raise HistoricalAuditMappingError(
                f"UNRESOLVED requirement {req_id} cannot carry justification"
            )


def validate_mapping(
    mapping: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
) -> None:
    schema = _load(SCHEMA_PATH)
    policy = _load(POLICY_PATH)
    _validate_schema_contract(schema)
    _validate_policy(policy)

    required = {
        "schema_version","mapping_kind","mode","mapping_id",
        "manifest_identity_sha256","plan_identity_sha256","batch_identity_sha256",
        "lot","requirements","mutation_permissions","mapping_identity_sha256",
    }
    if not isinstance(mapping, dict) or set(mapping) != required:
        raise HistoricalAuditMappingError("mapping field set drift")
    if mapping["schema_version"] != 1 or mapping["mapping_kind"] != MAPPING_KIND:
        raise HistoricalAuditMappingError("mapping identity/version drift")
    if mapping["mode"] != "READ_ONLY":
        raise HistoricalAuditMappingError("mapping must remain READ_ONLY")
    if not isinstance(mapping["mapping_id"], str) or MAPPING_ID_RE.fullmatch(
        mapping["mapping_id"]
    ) is None:
        raise HistoricalAuditMappingError("invalid mapping_id")

    manifest_mod = _module(
        "historical_mapping_manifest_binding",
        ROOT / "scripts" / "governance" / "validate_historical_audit_manifest.py",
    )
    try:
        manifest_mod.validate_manifest(manifest, plan)
    except manifest_mod.HistoricalAuditManifestError as exc:
        raise HistoricalAuditMappingError(
            f"bound historical manifest invalid: {exc}"
        ) from exc

    if mapping["manifest_identity_sha256"] != manifest["manifest_identity_sha256"]:
        raise HistoricalAuditMappingError("mapping manifest identity mismatch")
    if mapping["plan_identity_sha256"] != manifest["plan_identity_sha256"]:
        raise HistoricalAuditMappingError("mapping plan identity mismatch")
    if mapping["batch_identity_sha256"] != manifest["batch_identity_sha256"]:
        raise HistoricalAuditMappingError("mapping batch identity mismatch")
    lot = mapping["lot"]
    if not isinstance(lot, int) or isinstance(lot, bool) or not 0 <= lot <= 44:
        raise HistoricalAuditMappingError("mapping lot must be historical Lot 0..44")
    if lot not in manifest["lots"]:
        raise HistoricalAuditMappingError("mapping lot is outside the bound manifest batch")
    expected_id = f"HIST-MAP-B{manifest['batch_index']:03d}-L{lot:03d}"
    if mapping["mapping_id"] != expected_id:
        raise HistoricalAuditMappingError(
            f"mapping_id does not bind batch/lot: {mapping['mapping_id']} != {expected_id}"
        )
    if mapping["mutation_permissions"] != policy["mutation_permissions"]:
        raise HistoricalAuditMappingError("mapping mutation permissions drift")

    requirements = mapping["requirements"]
    if not isinstance(requirements, list) or not requirements:
        raise HistoricalAuditMappingError("mapping requirements must be non-empty")
    ids = [req.get("requirement_id") if isinstance(req, dict) else None for req in requirements]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise HistoricalAuditMappingError(
            "requirements must be strictly sorted and unique by requirement_id"
        )
    for req in requirements:
        _validate_requirement(req, policy)

    identity = mapping["mapping_identity_sha256"]
    if not isinstance(identity, str) or SHA64_RE.fullmatch(identity) is None:
        raise HistoricalAuditMappingError("mapping identity must be SHA-256")
    if identity != _sha256(mapping_material(mapping)):
        raise HistoricalAuditMappingError("mapping identity mismatch")


def _synthetic_bundle() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest_mod = _module(
        "historical_mapping_manifest_fixture",
        ROOT / "scripts" / "governance" / "validate_historical_audit_manifest.py",
    )
    plan = manifest_mod._synthetic_plan()
    manifest = manifest_mod._valid_manifest(plan)
    lot = manifest["lots"][0]
    requirement = {
        "requirement_id": f"LOT{lot:02d}-REQ-SYNTHETIC",
        "category": "SAFETY",
        "source": {
            "path": "docs/LOT_SPECIFICATION_STANDARD.md",
            "locator": "synthetic requirement",
            "requirement_sha256": hashlib.sha256(b"synthetic requirement").hexdigest(),
        },
        "design_sections": [
            {"path": "docs/DECISION_AUDITABILITY_AND_TRACEABILITY_STANDARD.md", "locator": "section 10"}
        ],
        "implementation_symbols": [
            {"path": "scripts/validate_traceability_contract.py", "symbol": "main"}
        ],
        "test_ids": [
            {"path": "tests/test_synthetic_traceability.py", "test_id": "test_synthetic"}
        ],
        "contract_artifacts": [
            {"path": "contracts/schemas/decision_evidence_envelope_v1.schema.json", "locator": "schema"}
        ],
        "evidence_artifacts": [
            {"path": "reports/lot_synthetic_report.md", "locator": "synthetic evidence"}
        ],
        "coverage_status": "MAPPED",
        "justification": None,
        "gap_reason": None,
    }
    mapping = {
        "schema_version": 1,
        "mapping_kind": MAPPING_KIND,
        "mode": "READ_ONLY",
        "mapping_id": f"HIST-MAP-B{manifest['batch_index']:03d}-L{lot:03d}",
        "manifest_identity_sha256": manifest["manifest_identity_sha256"],
        "plan_identity_sha256": manifest["plan_identity_sha256"],
        "batch_identity_sha256": manifest["batch_identity_sha256"],
        "lot": lot,
        "requirements": [requirement],
        "mutation_permissions": _load(POLICY_PATH)["mutation_permissions"],
        "mapping_identity_sha256": "",
    }
    mapping["mapping_identity_sha256"] = _sha256(mapping_material(mapping))
    return mapping, manifest, plan


def self_check() -> None:
    mapping, manifest, plan = _synthetic_bundle()
    validate_mapping(mapping, manifest, plan)
    first = _sha256(mapping_material(mapping))
    second = _sha256(mapping_material(json.loads(_canonical(mapping).decode("utf-8"))))
    if first != second:
        raise HistoricalAuditMappingError("canonical mapping replay mismatch")
    print("HISTORICAL_AUDIT_MAPPING_SELF_CHECK_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    try:
        if args.self_check:
            if any((args.mapping, args.manifest, args.plan)):
                raise HistoricalAuditMappingError(
                    "--self-check cannot be combined with mapping inputs"
                )
            self_check()
        else:
            if not all((args.mapping, args.manifest, args.plan)):
                raise HistoricalAuditMappingError(
                    "--mapping, --manifest and --plan are required together"
                )
            validate_mapping(_load(args.mapping), _load(args.manifest), _load(args.plan))
            print("HISTORICAL_AUDIT_MAPPING_VALID")
    except (HistoricalAuditMappingError, KeyError, TypeError) as exc:
        print(f"HISTORICAL_AUDIT_MAPPING_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
