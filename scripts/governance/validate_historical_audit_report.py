#!/usr/bin/env python3
"""Validate deterministic read-only historical audit reports and remediation queues."""

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
SCHEMA_PATH = ROOT / "config" / "governance" / "historical_audit_report_schema_v1.json"
POLICY_PATH = ROOT / "config" / "governance" / "historical_audit_report_policy_v1.json"
REPORT_KIND = "historical_audit_report_v1"
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
REPORT_ID_RE = re.compile(r"^HIST-REPORT-B[0-9]{3}-L[0-9]{3}$")
QUEUE_ID_RE = re.compile(r"^HIST-REMED-B[0-9]{3}-L[0-9]{3}-Q[0-9]{3}$")


class HistoricalAuditReportError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalAuditReportError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HistoricalAuditReportError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise HistoricalAuditReportError(f"cannot import {path}")
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
        raise HistoricalAuditReportError(f"non-canonical JSON value: {exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def report_material(report: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in report.items() if key != "report_identity_sha256"}


def _validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("title") != "HistoricalAuditReportV1":
        raise HistoricalAuditReportError("report schema title drift")
    if schema.get("additionalProperties") is not False:
        raise HistoricalAuditReportError("report schema must be closed")
    expected = [
        "schema_version","report_kind","mode","report_id","findings_registry_id",
        "registry_identity_sha256","manifest_identity_sha256","mapping_identity_sha256",
        "plan_identity_sha256","batch_identity_sha256","lot","audit_result","report_status",
        "finding_count","open_finding_count","closed_finding_count","severity_counts",
        "open_severity_counts","remediation_queue_count","remediation_queue",
        "mutation_permissions","report_identity_sha256",
    ]
    if schema.get("required") != expected:
        raise HistoricalAuditReportError("report schema required-field drift")
    defs = schema.get("$defs")
    if not isinstance(defs, dict) or set(defs) != {
        "sha256","severity_counts","remediation_queue_item"
    }:
        raise HistoricalAuditReportError("report schema definitions drift")


def _validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise HistoricalAuditReportError("unsupported report policy version")
    if policy.get("policy_kind") != "historical_audit_report_policy_v1":
        raise HistoricalAuditReportError("invalid report policy kind")
    if policy.get("semantics") != (
        "SOURCE_BOUND_READ_ONLY_REPORT_WITH_OWNER_BOUND_REMEDIATION_QUEUE"
    ):
        raise HistoricalAuditReportError("report policy semantics drift")
    if policy.get("historical_lot_range") != {"min":0,"max":44}:
        raise HistoricalAuditReportError("historical lot range drift")
    if policy.get("report_mode") != "READ_ONLY":
        raise HistoricalAuditReportError("historical audit report must remain READ_ONLY")
    if policy.get("report_statuses") != [
        "CLEAN","BLOCKED","ACTION_REQUIRED","RESOLVED"
    ]:
        raise HistoricalAuditReportError("report status set/order drift")
    if policy.get("severity_order") != ["BLOCKER","MAJOR","MINOR","INFO"]:
        raise HistoricalAuditReportError("severity order drift")
    if policy.get("priority_order") != ["P0","P1","P2","P3"]:
        raise HistoricalAuditReportError("priority order drift")
    if policy.get("severity_priority") != {
        "BLOCKER":"P0","MAJOR":"P1","MINOR":"P2","INFO":"P3"
    }:
        raise HistoricalAuditReportError("severity-to-priority mapping drift")
    if policy.get("open_disposition_triage_actions") != {
        "UNRESOLVED":"TRIAGE_REQUIRED",
        "REMEDIATION_REQUIRED":"REMEDIATE",
        "DEFERRED":"TRACK_DEFERRED",
    }:
        raise HistoricalAuditReportError("disposition-to-triage mapping drift")
    permissions = policy.get("mutation_permissions")
    if not isinstance(permissions, dict) or not permissions or any(permissions.values()):
        raise HistoricalAuditReportError("report mutation permissions must all be false")
    identity = policy.get("identity")
    if not isinstance(identity, dict) or identity.get("algorithm") != "sha256":
        raise HistoricalAuditReportError("report identity policy drift")
    if identity.get("excluded_fields") != ["report_identity_sha256"]:
        raise HistoricalAuditReportError("report identity exclusion drift")


def _zero_counts(policy: dict[str, Any]) -> dict[str, int]:
    return {severity:0 for severity in policy["severity_order"]}


def _derive_counts(
    findings: list[dict[str, Any]],
    policy: dict[str, Any],
) -> tuple[dict[str, int], dict[str, int]]:
    all_counts = _zero_counts(policy)
    open_counts = _zero_counts(policy)
    for finding in findings:
        severity = finding["severity"]
        all_counts[severity] += 1
        if finding["status"] == "OPEN":
            open_counts[severity] += 1
    return all_counts, open_counts


def _derive_status(
    findings: list[dict[str, Any]],
    open_counts: dict[str, int],
) -> str:
    if not findings:
        return "CLEAN"
    if open_counts["BLOCKER"] > 0:
        return "BLOCKED"
    if any(finding["status"] == "OPEN" for finding in findings):
        return "ACTION_REQUIRED"
    return "RESOLVED"


def _derive_queue(
    findings: list[dict[str, Any]],
    *,
    batch_index: int,
    lot: int,
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    priority_index = {
        priority:index for index, priority in enumerate(policy["priority_order"])
    }
    open_findings = [finding for finding in findings if finding["status"] == "OPEN"]
    ordered = sorted(
        open_findings,
        key=lambda finding: (
            priority_index[policy["severity_priority"][finding["severity"]]],
            finding["finding_id"],
        ),
    )
    queue: list[dict[str, Any]] = []
    for index, finding in enumerate(ordered, 1):
        disposition = finding["disposition"]
        try:
            triage_action = policy["open_disposition_triage_actions"][disposition]
        except KeyError as exc:
            raise HistoricalAuditReportError(
                f"OPEN finding has no triage action: {disposition}"
            ) from exc
        queue.append({
            "queue_id":f"HIST-REMED-B{batch_index:03d}-L{lot:03d}-Q{index:03d}",
            "finding_id":finding["finding_id"],
            "requirement_id":finding["requirement_id"],
            "finding_type":finding["finding_type"],
            "severity":finding["severity"],
            "priority":policy["severity_priority"][finding["severity"]],
            "disposition":disposition,
            "triage_action":triage_action,
            "owner":finding["owner"],
        })
    return queue


def _derived_report_fields(
    registry: dict[str, Any],
    manifest: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    findings = registry["findings"]
    all_counts, open_counts = _derive_counts(findings, policy)
    queue = _derive_queue(
        findings,
        batch_index=manifest["batch_index"],
        lot=registry["lot"],
        policy=policy,
    )
    open_count = sum(open_counts.values())
    return {
        "report_status":_derive_status(findings, open_counts),
        "finding_count":len(findings),
        "open_finding_count":open_count,
        "closed_finding_count":len(findings) - open_count,
        "severity_counts":all_counts,
        "open_severity_counts":open_counts,
        "remediation_queue_count":len(queue),
        "remediation_queue":queue,
    }


def validate_report(
    report: dict[str, Any],
    registry: dict[str, Any],
    mapping: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
) -> None:
    schema = _load(SCHEMA_PATH)
    policy = _load(POLICY_PATH)
    _validate_schema_contract(schema)
    _validate_policy(policy)

    findings_mod = _module(
        "historical_report_findings_binding",
        ROOT / "scripts" / "governance" / "validate_historical_audit_findings.py",
    )
    try:
        findings_mod.validate_registry(registry, mapping, manifest, plan)
    except findings_mod.HistoricalAuditFindingsError as exc:
        raise HistoricalAuditReportError(
            f"bound historical findings registry invalid: {exc}"
        ) from exc

    required = schema["required"]
    if not isinstance(report, dict) or list(report.keys()) != required:
        raise HistoricalAuditReportError("report field order/set drift")
    if report["schema_version"] != 1 or report["report_kind"] != REPORT_KIND:
        raise HistoricalAuditReportError("report identity/version drift")
    if report["mode"] != "READ_ONLY":
        raise HistoricalAuditReportError("historical audit report must remain READ_ONLY")
    if not isinstance(report["report_id"], str) or REPORT_ID_RE.fullmatch(report["report_id"]) is None:
        raise HistoricalAuditReportError("invalid report_id")

    lot = registry["lot"]
    batch_index = manifest["batch_index"]
    expected_report_id = f"HIST-REPORT-B{batch_index:03d}-L{lot:03d}"
    if report["report_id"] != expected_report_id:
        raise HistoricalAuditReportError("report_id does not bind batch/lot")

    bindings = {
        "findings_registry_id":registry["registry_id"],
        "registry_identity_sha256":registry["registry_identity_sha256"],
        "manifest_identity_sha256":registry["manifest_identity_sha256"],
        "mapping_identity_sha256":registry["mapping_identity_sha256"],
        "plan_identity_sha256":registry["plan_identity_sha256"],
        "batch_identity_sha256":registry["batch_identity_sha256"],
        "lot":lot,
        "audit_result":registry["audit_result"],
    }
    for field, expected in bindings.items():
        if report[field] != expected:
            raise HistoricalAuditReportError(f"report {field} binding mismatch")

    if not isinstance(lot, int) or isinstance(lot, bool) or not 0 <= lot <= 44:
        raise HistoricalAuditReportError("report lot must remain historical Lot 0..44")
    if report["mutation_permissions"] != policy["mutation_permissions"]:
        raise HistoricalAuditReportError("report mutation permissions drift")

    derived = _derived_report_fields(registry, manifest, policy)
    for field, expected in derived.items():
        if report[field] != expected:
            raise HistoricalAuditReportError(f"report derived field mismatch: {field}")

    queue = report["remediation_queue"]
    queue_ids = [item.get("queue_id") if isinstance(item, dict) else None for item in queue]
    expected_queue_ids = [
        f"HIST-REMED-B{batch_index:03d}-L{lot:03d}-Q{index:03d}"
        for index in range(1, len(queue) + 1)
    ]
    if queue_ids != expected_queue_ids:
        raise HistoricalAuditReportError("remediation queue ids are not contiguous/deterministic")
    if any(
        not isinstance(queue_id, str) or QUEUE_ID_RE.fullmatch(queue_id) is None
        for queue_id in queue_ids
    ):
        raise HistoricalAuditReportError("invalid remediation queue id")

    identity = report["report_identity_sha256"]
    if not isinstance(identity, str) or SHA64_RE.fullmatch(identity) is None:
        raise HistoricalAuditReportError("report identity must be SHA-256")
    if identity != _sha256(report_material(report)):
        raise HistoricalAuditReportError("report identity mismatch")


def build_report(
    registry: dict[str, Any],
    mapping: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    policy = _load(POLICY_PATH)
    findings_mod = _module(
        "historical_report_findings_builder_binding",
        ROOT / "scripts" / "governance" / "validate_historical_audit_findings.py",
    )
    try:
        findings_mod.validate_registry(registry, mapping, manifest, plan)
    except findings_mod.HistoricalAuditFindingsError as exc:
        raise HistoricalAuditReportError(
            f"cannot build report from invalid findings registry: {exc}"
        ) from exc

    lot = registry["lot"]
    batch_index = manifest["batch_index"]
    derived = _derived_report_fields(registry, manifest, policy)
    report = {
        "schema_version":1,
        "report_kind":REPORT_KIND,
        "mode":"READ_ONLY",
        "report_id":f"HIST-REPORT-B{batch_index:03d}-L{lot:03d}",
        "findings_registry_id":registry["registry_id"],
        "registry_identity_sha256":registry["registry_identity_sha256"],
        "manifest_identity_sha256":registry["manifest_identity_sha256"],
        "mapping_identity_sha256":registry["mapping_identity_sha256"],
        "plan_identity_sha256":registry["plan_identity_sha256"],
        "batch_identity_sha256":registry["batch_identity_sha256"],
        "lot":lot,
        "audit_result":registry["audit_result"],
        **derived,
        "mutation_permissions":copy.deepcopy(policy["mutation_permissions"]),
        "report_identity_sha256":"",
    }
    report["report_identity_sha256"] = _sha256(report_material(report))
    return report


def _finding(
    *,
    registry_id: str,
    index: int,
    requirement_id: str,
    severity: str,
    status: str,
    disposition: str,
    owner: str,
    rationale: str | None,
) -> dict[str, Any]:
    return {
        "finding_id":f"{registry_id}-F{index:03d}",
        "requirement_id":requirement_id,
        "finding_type":"CONTROL_GAP",
        "severity":severity,
        "previous_severity":None,
        "severity_change_rationale":None,
        "status":status,
        "disposition":disposition,
        "owner":owner,
        "summary":f"Synthetic {severity.lower()} control gap.",
        "rationale":rationale,
        "references":[
            {"path":"docs/LOT_SPECIFICATION_STANDARD.md","locator":"synthetic report finding"}
        ],
    }


def self_check() -> None:
    findings_mod = _module(
        "historical_report_findings_fixture",
        ROOT / "scripts" / "governance" / "validate_historical_audit_findings.py",
    )
    mapping_mod = _module(
        "historical_report_mapping_fixture",
        ROOT / "scripts" / "governance" / "validate_historical_audit_mapping.py",
    )
    mapping, manifest, plan = mapping_mod._synthetic_bundle()
    registry_id = f"HIST-FIND-B{manifest['batch_index']:03d}-L{mapping['lot']:03d}"
    requirement_id = mapping["requirements"][0]["requirement_id"]

    clean_registry = findings_mod.build_registry(mapping, manifest, [])
    clean_report = build_report(clean_registry, mapping, manifest, plan)
    validate_report(clean_report, clean_registry, mapping, manifest, plan)
    assert clean_report["report_status"] == "CLEAN"
    assert clean_report["remediation_queue"] == []

    blocker = _finding(
        registry_id=registry_id,index=1,requirement_id=requirement_id,
        severity="BLOCKER",status="OPEN",disposition="UNRESOLVED",
        owner="owner-blocker",rationale=None,
    )
    blocked_registry = findings_mod.build_registry(mapping, manifest, [blocker])
    blocked_report = build_report(blocked_registry, mapping, manifest, plan)
    validate_report(blocked_report, blocked_registry, mapping, manifest, plan)
    assert blocked_report["report_status"] == "BLOCKED"
    assert blocked_report["remediation_queue"][0]["priority"] == "P0"
    assert blocked_report["remediation_queue"][0]["owner"] == "owner-blocker"

    major = _finding(
        registry_id=registry_id,index=1,requirement_id=requirement_id,
        severity="MAJOR",status="OPEN",disposition="REMEDIATION_REQUIRED",
        owner="owner-major",rationale="Synthetic remediation is required.",
    )
    action_registry = findings_mod.build_registry(mapping, manifest, [major])
    action_report = build_report(action_registry, mapping, manifest, plan)
    validate_report(action_report, action_registry, mapping, manifest, plan)
    assert action_report["report_status"] == "ACTION_REQUIRED"
    assert action_report["remediation_queue"][0]["triage_action"] == "REMEDIATE"

    closed = _finding(
        registry_id=registry_id,index=1,requirement_id=requirement_id,
        severity="MINOR",status="CLOSED",disposition="RESOLVED",
        owner="owner-resolved",rationale="Synthetic finding resolved.",
    )
    resolved_registry = findings_mod.build_registry(mapping, manifest, [closed])
    resolved_report = build_report(resolved_registry, mapping, manifest, plan)
    validate_report(resolved_report, resolved_registry, mapping, manifest, plan)
    assert resolved_report["report_status"] == "RESOLVED"
    assert resolved_report["remediation_queue"] == []

    print("HISTORICAL_AUDIT_REPORT_SELF_CHECK_PASS scenarios=4")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    try:
        inputs = (args.report, args.registry, args.mapping, args.manifest, args.plan)
        if args.self_check:
            if any(inputs):
                raise HistoricalAuditReportError(
                    "--self-check cannot be combined with report inputs"
                )
            self_check()
        else:
            if not all(inputs):
                raise HistoricalAuditReportError(
                    "--report, --registry, --mapping, --manifest and --plan are required together"
                )
            validate_report(
                _load(args.report),
                _load(args.registry),
                _load(args.mapping),
                _load(args.manifest),
                _load(args.plan),
            )
            print("HISTORICAL_AUDIT_REPORT_VALID")
    except (
        HistoricalAuditReportError,
        AssertionError,
        KeyError,
        TypeError,
    ) as exc:
        print(f"HISTORICAL_AUDIT_REPORT_INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
