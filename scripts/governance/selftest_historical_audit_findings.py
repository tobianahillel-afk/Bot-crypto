#!/usr/bin/env python3
"""Adversarial qualification for ENG-07.4 historical findings registries."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"historical findings negative scenario unexpectedly passed: {label}")


def _fixture() -> tuple[ModuleType, dict[str, Any], dict[str, Any], dict[str, Any]]:
    validator = _module(
        "historical_findings_adversarial_validator",
        ROOT / "scripts" / "governance" / "validate_historical_audit_findings.py",
    )
    mapping_mod = _module(
        "historical_findings_adversarial_mapping",
        ROOT / "scripts" / "governance" / "validate_historical_audit_mapping.py",
    )
    mapping, manifest, plan = mapping_mod._synthetic_bundle()
    return validator, mapping, manifest, plan


def _finding(
    *,
    batch: int,
    lot: int,
    index: int,
    requirement_id: str,
    severity: str = "MAJOR",
    status: str = "OPEN",
    disposition: str = "UNRESOLVED",
    rationale: str | None = None,
) -> dict[str, Any]:
    return {
        "finding_id": f"HIST-FIND-B{batch:03d}-L{lot:03d}-F{index:03d}",
        "requirement_id": requirement_id,
        "finding_type": "CONTROL_GAP",
        "severity": severity,
        "previous_severity": None,
        "severity_change_rationale": None,
        "status": status,
        "disposition": disposition,
        "owner": "engineering-audit",
        "summary": f"Synthetic finding {index} for qualification.",
        "rationale": rationale,
        "references": [
            {
                "path": "docs/LOT_SPECIFICATION_STANDARD.md",
                "locator": f"synthetic finding {index}",
            }
        ],
    }


def _rehash(validator: ModuleType, registry: dict[str, Any]) -> None:
    registry["registry_identity_sha256"] = validator._sha256(
        validator.registry_material(registry)
    )


def main() -> int:
    validator, mapping, manifest, plan = _fixture()
    error = validator.HistoricalAuditFindingsError
    batch = manifest["batch_index"]
    lot = mapping["lot"]
    req = mapping["requirements"][0]["requirement_id"]

    clean = validator.build_registry(mapping, manifest, [])
    validator.validate_registry(clean, mapping, manifest, plan)

    first = _finding(batch=batch, lot=lot, index=1, requirement_id=req)
    populated = validator.build_registry(mapping, manifest, [first])
    validator.validate_registry(populated, mapping, manifest, plan)

    second = _finding(batch=batch, lot=lot, index=2, requirement_id=req)
    two = validator.build_registry(mapping, manifest, [first, second])
    validator.validate_registry(two, mapping, manifest, plan)

    probes: list[tuple[str, Any]] = []

    def add(label: str, mutate: Any) -> None:
        value = copy.deepcopy(populated)
        mutate(value)
        _rehash(validator, value)
        probes.append(
            (
                label,
                lambda v=value: validator.validate_registry(v, mapping, manifest, plan),
            )
        )

    add("forged manifest identity", lambda x: x.__setitem__("manifest_identity_sha256", "0" * 64))
    add("forged mapping identity", lambda x: x.__setitem__("mapping_identity_sha256", "1" * 64))
    add("forged plan identity", lambda x: x.__setitem__("plan_identity_sha256", "2" * 64))
    add("forged batch identity", lambda x: x.__setitem__("batch_identity_sha256", "3" * 64))

    def lot45(x: dict[str, Any]) -> None:
        x["lot"] = 45
        x["registry_id"] = f"HIST-FIND-B{batch:03d}-L045"
        x["findings"][0]["finding_id"] = f"HIST-FIND-B{batch:03d}-L045-F001"

    add("Lot45 registry", lot45)
    add("unknown requirement", lambda x: x["findings"][0].__setitem__("requirement_id", "UNKNOWN-REQ"))
    add("missing owner", lambda x: x["findings"][0].__setitem__("owner", ""))

    def bad_disposition(x: dict[str, Any]) -> None:
        x["findings"][0]["status"] = "OPEN"
        x["findings"][0]["disposition"] = "RESOLVED"
        x["findings"][0]["rationale"] = "not allowed while open"

    add("status disposition mismatch", bad_disposition)

    def missing_rationale(x: dict[str, Any]) -> None:
        x["findings"][0]["status"] = "OPEN"
        x["findings"][0]["disposition"] = "DEFERRED"
        x["findings"][0]["rationale"] = None

    add("deferred without rationale", missing_rationale)

    def silent_downgrade(x: dict[str, Any]) -> None:
        x["findings"][0]["previous_severity"] = "MAJOR"
        x["findings"][0]["severity"] = "MINOR"
        x["findings"][0]["severity_change_rationale"] = None

    add("silent severity downgrade", silent_downgrade)
    add(
        "path traversal",
        lambda x: x["findings"][0]["references"][0].__setitem__("path", "../secret.txt"),
    )

    def malformed_ref(x: dict[str, Any]) -> None:
        x["findings"][0]["references"][0].pop("locator")

    add("malformed reference", malformed_ref)

    duplicate = validator.build_registry(mapping, manifest, [first, copy.deepcopy(first)])
    _rehash(validator, duplicate)
    probes.append(
        (
            "duplicate finding ids",
            lambda: validator.validate_registry(duplicate, mapping, manifest, plan),
        )
    )

    unsorted_first = _finding(batch=batch, lot=lot, index=2, requirement_id=req)
    unsorted_second = _finding(batch=batch, lot=lot, index=1, requirement_id=req)
    unsorted = validator.build_registry(mapping, manifest, [unsorted_first, unsorted_second])
    _rehash(validator, unsorted)
    probes.append(
        (
            "unsorted finding ids",
            lambda: validator.validate_registry(unsorted, mapping, manifest, plan),
        )
    )

    bad_count = copy.deepcopy(populated)
    bad_count["finding_count"] = 2
    _rehash(validator, bad_count)
    probes.append(
        (
            "finding count mismatch",
            lambda: validator.validate_registry(bad_count, mapping, manifest, plan),
        )
    )

    bad_result = copy.deepcopy(populated)
    bad_result["audit_result"] = "CLEAN"
    _rehash(validator, bad_result)
    probes.append(
        (
            "audit result mismatch",
            lambda: validator.validate_registry(bad_result, mapping, manifest, plan),
        )
    )

    tampered = copy.deepcopy(populated)
    tampered["findings"][0]["summary"] = "tampered without rehash"
    probes.append(
        (
            "registry identity tamper",
            lambda: validator.validate_registry(tampered, mapping, manifest, plan),
        )
    )

    for label, fn in probes:
        _expect(error, fn, label)

    print(
        "HISTORICAL_AUDIT_FINDINGS_SELFTEST_PASS "
        f"positive=3 negative={len(probes)} total={len(probes) + 3}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
