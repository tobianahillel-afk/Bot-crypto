#!/usr/bin/env python3
"""Adversarial qualification for deterministic historical audit reports and queues."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        "finding_id": f"{registry_id}-F{index:03d}",
        "requirement_id": requirement_id,
        "finding_type": "CONTROL_GAP",
        "severity": severity,
        "previous_severity": None,
        "severity_change_rationale": None,
        "status": status,
        "disposition": disposition,
        "owner": owner,
        "summary": f"Synthetic {severity.lower()} report qualification finding.",
        "rationale": rationale,
        "references": [
            {
                "path": "docs/LOT_SPECIFICATION_STANDARD.md",
                "locator": "synthetic report adversarial qualification",
            }
        ],
    }


def _rehash_report(mod: ModuleType, report: dict[str, Any]) -> None:
    report["report_identity_sha256"] = mod._sha256(mod.report_material(report))


def _expect_invalid(
    mod: ModuleType,
    report: dict[str, Any],
    registry: dict[str, Any],
    mapping: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
    label: str,
) -> None:
    try:
        mod.validate_report(report, registry, mapping, manifest, plan)
    except mod.HistoricalAuditReportError:
        return
    raise AssertionError(f"historical report negative scenario unexpectedly passed: {label}")


def main() -> int:
    mod = _module(
        "historical_report_adversarial_target",
        ROOT / "scripts" / "governance" / "validate_historical_audit_report.py",
    )
    findings_mod = _module(
        "historical_report_adversarial_findings",
        ROOT / "scripts" / "governance" / "validate_historical_audit_findings.py",
    )
    mapping_mod = _module(
        "historical_report_adversarial_mapping",
        ROOT / "scripts" / "governance" / "validate_historical_audit_mapping.py",
    )
    mapping, manifest, plan = mapping_mod._synthetic_bundle()
    registry_id = f"HIST-FIND-B{manifest['batch_index']:03d}-L{mapping['lot']:03d}"
    requirement_id = mapping["requirements"][0]["requirement_id"]

    findings = [
        _finding(
            registry_id=registry_id,
            index=1,
            requirement_id=requirement_id,
            severity="MINOR",
            status="OPEN",
            disposition="DEFERRED",
            owner="owner-minor",
            rationale="Synthetic deferral rationale.",
        ),
        _finding(
            registry_id=registry_id,
            index=2,
            requirement_id=requirement_id,
            severity="BLOCKER",
            status="OPEN",
            disposition="UNRESOLVED",
            owner="owner-blocker",
            rationale=None,
        ),
        _finding(
            registry_id=registry_id,
            index=3,
            requirement_id=requirement_id,
            severity="MAJOR",
            status="OPEN",
            disposition="REMEDIATION_REQUIRED",
            owner="owner-major",
            rationale="Synthetic remediation rationale.",
        ),
        _finding(
            registry_id=registry_id,
            index=4,
            requirement_id=requirement_id,
            severity="INFO",
            status="CLOSED",
            disposition="RESOLVED",
            owner="owner-closed",
            rationale="Synthetic resolution rationale.",
        ),
    ]
    registry = findings_mod.build_registry(mapping, manifest, findings)
    report = mod.build_report(registry, mapping, manifest, plan)
    mod.validate_report(report, registry, mapping, manifest, plan)

    assert report["report_status"] == "BLOCKED"
    assert report["finding_count"] == 4
    assert report["open_finding_count"] == 3
    assert report["closed_finding_count"] == 1
    assert report["severity_counts"] == {
        "BLOCKER": 1, "MAJOR": 1, "MINOR": 1, "INFO": 1
    }
    assert report["open_severity_counts"] == {
        "BLOCKER": 1, "MAJOR": 1, "MINOR": 1, "INFO": 0
    }
    queue = report["remediation_queue"]
    assert [item["finding_id"] for item in queue] == [
        f"{registry_id}-F002",
        f"{registry_id}-F003",
        f"{registry_id}-F001",
    ]
    assert [item["queue_id"] for item in queue] == [
        f"HIST-REMED-B{manifest['batch_index']:03d}-L{mapping['lot']:03d}-Q001",
        f"HIST-REMED-B{manifest['batch_index']:03d}-L{mapping['lot']:03d}-Q002",
        f"HIST-REMED-B{manifest['batch_index']:03d}-L{mapping['lot']:03d}-Q003",
    ]
    assert [item["owner"] for item in queue] == [
        "owner-blocker", "owner-major", "owner-minor"
    ]
    assert all(item["finding_id"] != f"{registry_id}-F004" for item in queue)

    cases: list[tuple[str, Callable[[], None]]] = []

    def report_case(label: str, mutate: Callable[[dict[str, Any]], None], *, rehash: bool = True) -> None:
        def run() -> None:
            candidate = copy.deepcopy(report)
            mutate(candidate)
            if rehash:
                _rehash_report(mod, candidate)
            _expect_invalid(mod, candidate, registry, mapping, manifest, plan, label)
        cases.append((label, run))

    report_case(
        "registry identity binding",
        lambda x: x.__setitem__("registry_identity_sha256", "0" * 64),
    )
    report_case(
        "manifest identity binding",
        lambda x: x.__setitem__("manifest_identity_sha256", "0" * 64),
    )
    report_case(
        "mapping identity binding",
        lambda x: x.__setitem__("mapping_identity_sha256", "0" * 64),
    )
    report_case(
        "plan identity binding",
        lambda x: x.__setitem__("plan_identity_sha256", "0" * 64),
    )
    report_case(
        "batch identity binding",
        lambda x: x.__setitem__("batch_identity_sha256", "0" * 64),
    )
    report_case(
        "lot binding",
        lambda x: x.__setitem__("lot", (x["lot"] + 1) % 45),
    )
    report_case(
        "audit-result binding",
        lambda x: x.__setitem__("audit_result", "CLEAN"),
    )
    report_case(
        "finding count",
        lambda x: x.__setitem__("finding_count", x["finding_count"] + 1),
    )
    report_case(
        "open finding count",
        lambda x: x.__setitem__("open_finding_count", x["open_finding_count"] + 1),
    )
    report_case(
        "closed finding count",
        lambda x: x.__setitem__("closed_finding_count", x["closed_finding_count"] + 1),
    )
    report_case(
        "severity counts",
        lambda x: x["severity_counts"].__setitem__("INFO", x["severity_counts"]["INFO"] + 1),
    )
    report_case(
        "open severity counts",
        lambda x: x["open_severity_counts"].__setitem__(
            "INFO", x["open_severity_counts"]["INFO"] + 1
        ),
    )
    report_case(
        "report status",
        lambda x: x.__setitem__("report_status", "ACTION_REQUIRED"),
    )
    report_case(
        "queue omission",
        lambda x: x["remediation_queue"].pop(),
    )
    report_case(
        "queue duplication",
        lambda x: x["remediation_queue"].__setitem__(
            2, copy.deepcopy(x["remediation_queue"][1])
        ),
    )
    report_case(
        "queue reordering",
        lambda x: x["remediation_queue"].__setitem__(
            slice(0, 2), [x["remediation_queue"][1], x["remediation_queue"][0]]
        ),
    )
    report_case(
        "queue priority",
        lambda x: x["remediation_queue"][0].__setitem__("priority", "P1"),
    )
    report_case(
        "queue triage action",
        lambda x: x["remediation_queue"][0].__setitem__("triage_action", "REMEDIATE"),
    )
    report_case(
        "queue owner",
        lambda x: x["remediation_queue"][0].__setitem__("owner", "forged-owner"),
    )
    report_case(
        "queue id continuity",
        lambda x: x["remediation_queue"][0].__setitem__(
            "queue_id",
            f"HIST-REMED-B{manifest['batch_index']:03d}-L{mapping['lot']:03d}-Q009",
        ),
    )
    report_case(
        "extra queue entry",
        lambda x: x["remediation_queue"].append(copy.deepcopy(x["remediation_queue"][-1])),
    )
    report_case(
        "report identity tamper",
        lambda x: x.__setitem__("report_identity_sha256", "f" * 64),
        rehash=False,
    )

    def source_case(label: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        def run() -> None:
            forged = copy.deepcopy(registry)
            mutate(forged)
            findings_mod._rehash(forged)
            _expect_invalid(mod, report, forged, mapping, manifest, plan, label)
        cases.append((label, run))

    source_case(
        "source manifest binding",
        lambda x: x.__setitem__("manifest_identity_sha256", "1" * 64),
    )
    source_case(
        "source mapping binding",
        lambda x: x.__setitem__("mapping_identity_sha256", "2" * 64),
    )
    source_case(
        "source plan binding",
        lambda x: x.__setitem__("plan_identity_sha256", "3" * 64),
    )
    source_case(
        "source batch binding",
        lambda x: x.__setitem__("batch_identity_sha256", "4" * 64),
    )
    source_case(
        "source Lot45 exclusion",
        lambda x: x.__setitem__("lot", 45),
    )
    source_case(
        "source audit result mismatch",
        lambda x: x.__setitem__("audit_result", "CLEAN"),
    )

    for _label, run in cases:
        run()

    if len(cases) < 16:
        raise AssertionError("historical report adversarial suite too small")
    print(f"HISTORICAL_AUDIT_REPORT_SELFTEST_PASS probes={len(cases) + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
